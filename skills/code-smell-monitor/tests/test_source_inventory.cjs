#!/usr/bin/env node
// Tests source_inventory.cjs: complete function/hook boundaries, strict scope and parse-error disclosure.
'use strict';
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const assert = require('node:assert/strict');
const {inventory, readScope} = require('../scripts/source_inventory.cjs');
const modules = process.argv[2];
assert.ok(modules, 'Pass a project node_modules directory containing TypeScript');
const root = fs.mkdtempSync(path.join(os.tmpdir(), 'source-inventory-test-'));
try {
  fs.writeFileSync(path.join(root, 'package.json'), '{}');
  fs.symlinkSync(modules, path.join(root, 'node_modules'));
  fs.writeFileSync(path.join(root, 'a.tsx'), 'export function View() {\n  const work = () => 1;\n  React.useEffect(() => {\n    work();\n    return () => work();\n  }, [work]);\n  return null;\n}\n');
  const scope = path.join(root, 'scope.txt');
  fs.writeFileSync(scope, 'a.tsx\n');
  const result = inventory(root, scope);
  assert.equal(result.status, 'complete');
  assert.deepEqual(result.files, ['a.tsx']);
  const effect = result.records.find(row => row[0] === 'hook');
  assert.deepEqual(effect.slice(2), ['useEffect', 3, 6, 'View:1', [3, 6], [6, 6]]);
  assert.ok(result.records.some(row => row[0] === 'function' && row[2] === 'View' && row[3] === 1 && row[4] === 8));
  assert.ok(result.records.some(row => row[0] === 'function' && row[2] === 'work'));
  fs.writeFileSync(path.join(root, 'bad.ts'), 'function broken( {');
  fs.writeFileSync(scope, 'bad.ts\n');
  assert.equal(inventory(root, scope).status, 'partial');
  assert.ok(inventory(root, scope).errors.length);
  fs.writeFileSync(scope, 'a.tsx\na.tsx\n');
  assert.throws(() => readScope(root, scope), /duplicates/);
  fs.writeFileSync(scope, '../escape.ts\n');
  assert.throws(() => readScope(root, scope));
  console.log('source inventory tests passed');
} finally {
  fs.rmSync(root, {recursive: true});
}
