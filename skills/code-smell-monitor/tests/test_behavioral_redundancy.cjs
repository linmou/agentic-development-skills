'use strict';
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const { analyze, sourceFiles } = require('../scripts/behavioral_redundancy.cjs');
const ts = require('typescript');

const helper = `const supabase: any = {};
export async function readRoomMessagePages(roomId: string) {
  return await supabase.from('messages').select('*').eq('room_id', roomId).order('id');
}
export function startRoomMessageSync(roomId: string) {
  const reconcile = async () => { await readRoomMessagePages(roomId); };
  void reconcile();
  return { stop: () => {} };
}`;
const membership = `import {useCallback, useState} from 'react';
import {readRoomMessagePages} from './roomMessageSync';
export function useRoomMembership() {
  const [currentRoom,setCurrentRoom] = useState<{id:string}|null>(null);
  const joinRoom = useCallback(async (roomId: string) => {
    await readRoomMessagePages(roomId);
    setCurrentRoom({id:roomId});
  }, []);
  return {currentRoom,setCurrentRoom,joinRoom};
}`;
const realtime = `import {useEffect, useState} from 'react';
import {startRoomMessageSync} from './roomMessageSync';
export function useRoomRealtime({currentRoom}:any) {
  const [typingUsers,setTypingUsers] = useState<any[]>([]);
  const currentRoomId=currentRoom?.id;
  useEffect(()=>{
    if (!currentRoomId) return;
    const sync=startRoomMessageSync(currentRoomId);
    return ()=>sync.stop();
  },[currentRoomId]);
  useEffect(()=>{
    const interval = setInterval(()=> {
      const now=Date.now();
      setTypingUsers(prev=>prev.filter(t=>now-t.timestamp<5000));
    },1000);
    return ()=>clearInterval(interval);
  },[]);
  return {typingUsers};
}`;
const wiring = `import {useRoomMembership} from './useRoomMembership';
import {useRoomRealtime} from './useRoomRealtime';
export function RoomProvider() {
  const {currentRoom,setCurrentRoom,joinRoom} = useRoomMembership();
  useRoomRealtime({currentRoom,setCurrentRoom});
  return joinRoom;
}`;
function fixture(files) {
  const repo = fs.mkdtempSync(path.join(os.tmpdir(), 'csm-behavior-'));
  fs.mkdirSync(path.join(repo, 'src'));
  fs.writeFileSync(path.join(repo, 'package.json'), '{"name":"csm-fixture"}');
  for (const [name, text] of Object.entries(files)) fs.writeFileSync(path.join(repo, 'src', name), text);
  const scanned = sourceFiles(repo, 100);
  const result = analyze(ts, repo, scanned.files, scanned.omitted);
  return { result, cleanup() { fs.rmSync(repo, { recursive:true, force:true }); } };
}
const base = () => ({'roomMessageSync.ts':helper, 'useRoomMembership.ts':membership,
    'useRoomRealtime.ts':realtime, 'RoomContext.tsx':wiring});

test('detects two room-history reads via React state/effect and cross-file call graph', () => {
  const run = fixture(base());
  try {
    assert.equal(run.result.status, 'covered');
    const overlap = run.result.findings.find(x => x.type === 'state_effect_resource_overlap');
    assert.ok(overlap, JSON.stringify(run.result));
    assert.equal(overlap.resource, 'db:messages');
    assert.equal(overlap.source.entrypoint, 'joinRoom');
    assert.equal(overlap.wiring.provider, 'useRoomMembership');
    assert.equal(overlap.wiring.consumer, 'useRoomRealtime');
    assert.deepEqual(overlap.source.path.map(x=>x.name), ['joinRoom','readRoomMessagePages']);
    assert.ok(overlap.counterpart.path.map(x=>x.name).includes('reconcile'));
    assert.ok(overlap.counterpart.path.map(x=>x.name).includes('readRoomMessagePages'));
    assert.match(overlap.note,/Recovery/);
    assert.ok(run.result.findings.some(x=>x.type==='periodic_state_allocation'));
  } finally { run.cleanup(); }
});
test('requires state transition and explicit wiring rather than same table names', () => {
  const noSetter = base();
  noSetter['useRoomMembership.ts'] = membership.replace('setCurrentRoom({id:roomId});','/* no update */');
  const a = fixture(noSetter);
  try { assert.ok(!a.result.findings.some(x=>x.type==='state_effect_resource_overlap')); }
  finally { a.cleanup(); }
  const noWire = base();
  delete noWire['RoomContext.tsx'];
  const b = fixture(noWire);
  try { assert.ok(!b.result.findings.some(x=>x.type==='state_effect_resource_overlap')); }
  finally { b.cleanup(); }
});
test('does not confuse different database resources', () => {
  const files = base();
  files['useRoomMembership.ts'] = membership.replace("'./roomMessageSync'","'./readOther'").replaceAll('readRoomMessagePages','readOther');
  files['readOther.ts'] = "const supabase:any={};export async function readOther(roomId:string){return supabase.from('other_table').select('*').eq('room_id',roomId);}";
  const run = fixture(files);
  try { assert.ok(!run.result.findings.some(x=>x.type==='state_effect_resource_overlap')); }
  finally { run.cleanup(); }
});
test('flags repeated same-callee reads with identical arguments', () => {
  const run = fixture({'duplicates.ts':`const supabase:any={};
    async function load(id:string){return supabase.from('messages').select('*').eq('room_id',id);}
    export async function init(id:string){await load(id); await load(id);}`});
  try { assert.ok(run.result.findings.some(x=>x.type==='same_entrypoint_repeated_read')); }
  finally { run.cleanup(); }
});
test('reports partial coverage for missing relative imports', () => {
  const run = fixture({'missing.ts': "import {x} from './missingModule';export const y=x;"});
  try { assert.equal(run.result.status,'partial'); assert.ok(run.result.omissions.unresolved_relative_imports.length); }
  finally { run.cleanup(); }
});
test('does not flag periodic setter that returns previous state unmodified', () => {
  const run = fixture({'timer.ts':`import {useState} from 'react';
    export function useTimer(){const [items,setItems]=useState<any[]>([]);
      setInterval(()=>setItems(prev=>prev),1000);return items;}`});
  try { assert.ok(!run.result.findings.some(x=>x.type==='periodic_state_allocation')); }
  finally { run.cleanup(); }
});
