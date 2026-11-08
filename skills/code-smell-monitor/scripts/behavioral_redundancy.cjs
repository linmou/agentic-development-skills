#!/usr/bin/env node
// Static, advisory JS/TS redundancy signals: resource-call overlap, React state/effect
// lifecycle overlap, and periodic state allocation. No target code is executed.
'use strict';
const fs = require('fs');
const path = require('path');
const { createRequire } = require('module');

function argsOf(argv) {
  const opts = { repo: '.', out: null, maxFiles: 6000 };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--repo') opts.repo = argv[++i];
    else if (argv[i] === '--out') opts.out = argv[++i];
    else if (argv[i] === '--max-files') opts.maxFiles = Number(argv[++i]);
    else throw new Error('Unknown argument: ' + argv[i]);
  }
  opts.repo = path.resolve(opts.repo);
  if (!Number.isInteger(opts.maxFiles) || opts.maxFiles < 1) throw new Error('Invalid --max-files');
  return opts;
}
function loadTS(repo) {
  for (const where of [path.join(repo, 'package.json'), __filename]) {
    try { return createRequire(where)('typescript'); } catch (_) { /* try next */ }
  }
  // Globally installed Node toolchain is supported when NODE_PATH is configured.
  try { return require('typescript'); } catch (_) { return null; }
}
function sourceFiles(repo, limit) {
  const found = [], omitted = [];
  const exclude = new Set(['node_modules','.git','.next','dist','build','coverage','.code-smell-monitor','vendor','__tests__','e2e','evals']);
  function walk(dir) {
    for (const item of fs.readdirSync(dir, { withFileTypes: true })) {
      if (item.isSymbolicLink()) continue;
      const full = path.join(dir, item.name);
      if (item.isDirectory()) {
        if (!exclude.has(item.name) && !item.name.startsWith('.')) walk(full);
      } else if (/\.(ts|tsx|js|jsx|mts|cts)$/.test(item.name) && !/\.(test|spec|d)\.[jt]sx?$/.test(item.name)) {
        if (found.length < limit) found.push(full); else omitted.push(full);
      }
    }
  }
  walk(repo);
  return { files: found.sort(), omitted };
}
function main() {
  const options = argsOf(process.argv.slice(2));
  const ts = loadTS(options.repo);
  if (!ts) {
    process.stderr.write('TypeScript compiler API not available in analyzed package or monitor environment\n');
    process.exit(127);
  }
  const { files, omitted } = sourceFiles(options.repo, options.maxFiles);
  const output = analyze(ts, options.repo, files, omitted);
  const json = JSON.stringify(output, null, 2);
  if (options.out) fs.writeFileSync(options.out, json + '\n');
  else process.stdout.write(json + '\n');
  if (output.status === 'failed') process.exit(2);
}
function analyze(ts, repo, filenames, omitted = []) {
  const nodes = new Map(), fnByKey = new Map(), aliases = new Map();
  const direct = new Map(), calls = new Map(), setters = [], effects = [], hookWires = [], timerFindings = [], directSameFn = [];
  const unresolved = [], parseErrors = [];
  const rel = p => path.relative(repo, p).split(path.sep).join('/');
  const opts = { allowJs: true, checkJs: false, skipLibCheck: true, noEmit: true,
    target: ts.ScriptTarget.ES2020, jsx: ts.JsxEmit.React, module: ts.ModuleKind.CommonJS,
    moduleResolution: ts.ModuleResolutionKind.NodeJs };
  const configPath = ts.findConfigFile(repo, ts.sys.fileExists, 'tsconfig.json');
  if (configPath) {
    const conf = ts.readConfigFile(configPath, ts.sys.readFile);
    if (!conf.error) {
      const parsed = ts.parseJsonConfigFileContent(conf.config, ts.sys, path.dirname(configPath));
      Object.assign(opts, parsed.options, { noEmit: true, allowJs: true, skipLibCheck: true });
    }
  }
  let program, checker;
  try { program = ts.createProgram(filenames, opts); checker = program.getTypeChecker(); }
  catch (e) { return {status: 'failed', error: String(e), findings: []}; }
  const sourceSet = new Set(filenames.map(f => path.resolve(f)));
  const own = program.getSourceFiles().filter(f => sourceSet.has(path.resolve(f.fileName)));
  const loc = n => {
    const where = n.getSourceFile().getLineAndCharacterOfPosition(n.getStart());
    return { file: rel(n.getSourceFile().fileName), line: where.line + 1, column: where.character + 1 };
  };
  const memberName = node => node && ts.isIdentifier(node) ? node.text : node && ts.isPropertyAccessExpression(node) ? node.name.text : '';
  const symbolKey = node => {
    if (!node) return null;
    try {
      let symbol = checker.getSymbolAtLocation(node);
      if (!symbol) return null;
      if (symbol.flags & ts.SymbolFlags.Alias) symbol = checker.getAliasedSymbol(symbol);
      const decl = symbol.valueDeclaration || symbol.declarations?.[0];
      return decl && sourceSet.has(path.resolve(decl.getSourceFile().fileName))
        ? `${rel(decl.getSourceFile().fileName)}:${decl.getStart()}` : null;
    } catch (_) { return null; }
  };
  const functionOf = (node, name, keyNode) => {
    const location = loc(node);
    const key = keyNode ? symbolKey(keyNode) : null;
    const id = key || `${location.file}:${node.getStart()}:${name}`;
    if (!nodes.has(id)) {
      nodes.set(id, { id, name, ...location, node, parentFn: null, reads: [], stateSetters: new Set() });
      if (key) fnByKey.set(key, id);
    }
    return id;
  };
  const sourceAliases = new Map();
  const stateNames = new Map();
  const hookReturns = new Map();
  const hookFunctions = new Map();
  const effectParents = new Map();
  const callNames = n => {
    if (ts.isIdentifier(n)) return n.text;
    if (ts.isPropertyAccessExpression(n)) return n.name.text;
    return '';
  };
  function identifiersIn(node, set = new Set()) {
    if (ts.isIdentifier(node)) set.add(node.text);
    ts.forEachChild(node, c => identifiersIn(c, set));
    return set;
  }
  function initializerAliases(n) {
    if (!ts.isVariableDeclaration(n) || !ts.isIdentifier(n.name) || !n.initializer) return;
    sourceAliases.set(`${loc(n).file}:${n.name.text}`, [...identifiersIn(n.initializer)].filter(i => i !== n.name.text));
  }
  function dependencies(effectCall) {
    const arr = effectCall.arguments[1];
    if (!arr || !ts.isArrayLiteralExpression(arr)) return [];
    const source = loc(effectCall).file;
    const refs = new Set();
    for (const item of arr.elements) {
      for (const ident of identifiersIn(item)) {
        refs.add(ident);
        const todo = [ident], seen = new Set();
        while (todo.length) {
          const next = todo.pop();
          if (seen.has(next)) continue;
          seen.add(next);
          refs.add(next);
          for (const alias of sourceAliases.get(`${source}:${next}`) || []) todo.push(alias);
        }
      }
    }
    return [...refs].sort();
  }
  // First pass: record declaration keys, lexical function nodes and aliases.
  for (const sf of own) {
    const filename = rel(sf.fileName);
    if (sf.parseDiagnostics?.length) parseErrors.push({ file: filename, count: sf.parseDiagnostics.length });
    for (const statement of sf.statements) {
      if (!ts.isImportDeclaration(statement) || !ts.isStringLiteral(statement.moduleSpecifier)) continue;
      const spec = statement.moduleSpecifier.text;
      if (!spec.startsWith('.')) continue;
      const resolved = ts.resolveModuleName(spec, sf.fileName, opts, ts.sys).resolvedModule;
      if (!resolved || !fs.existsSync(resolved.resolvedFileName)) {
        unresolved.push({ file: filename, module: spec });
      }
    }
    function visit(n, currentFn = null) {
      if (ts.isVariableDeclaration(n)) initializerAliases(n);
      let fid = currentFn;
      if (ts.isFunctionDeclaration(n) && n.name) fid = functionOf(n, n.name.text, n.name);
      else if (ts.isVariableDeclaration(n) && n.initializer && ts.isIdentifier(n.name)) {
        const expr = n.initializer;
        if (ts.isArrowFunction(expr) || ts.isFunctionExpression(expr)) fid = functionOf(expr, n.name.text, n.name);
        else if (ts.isCallExpression(expr) && ['useCallback','useMemo'].includes(callNames(expr.expression)) && expr.arguments.length
                 && (ts.isArrowFunction(expr.arguments[0]) || ts.isFunctionExpression(expr.arguments[0]))) {
          fid = functionOf(expr.arguments[0], n.name.text, n.name);
        }
      } else if (ts.isMethodDeclaration(n) && n.name) fid = functionOf(n, n.name.getText(), n.name);
      if (fid && currentFn && fid !== currentFn) nodes.get(fid).parentFn = currentFn;
      // Callback passed to a useEffect is its own event-triggered root, not an immediate call.
      if (ts.isCallExpression(n) && callNames(n.expression) === 'useEffect' && n.arguments.length
          && (ts.isArrowFunction(n.arguments[0]) || ts.isFunctionExpression(n.arguments[0]))) {
        const cb = n.arguments[0];
        const eid = functionOf(cb, `useEffect@${loc(n).line}`, null);
        nodes.get(eid).parentFn = fid;
        effects.push({ id: eid, owner: fid, file: filename, line: loc(n).line, call: n });
        for (const arg of n.arguments.slice(1)) visit(arg, fid);
        visit(cb, eid);
        return;
      }
      if (ts.isVariableDeclaration(n) && ts.isArrayBindingPattern(n.name) && ts.isCallExpression(n.initializer || {})
          && callNames(n.initializer.expression) === 'useState') {
        const names = n.name.elements.map(e => e.name.getText());
        if (names.length >= 2) {
          stateNames.set(`${filename}:${names[1]}`, names[0]);
          if (fid) nodes.get(fid).stateSetters.add(names[1]);
        }
      }
      if (ts.isFunctionDeclaration(n) && n.name?.text?.startsWith('use')) hookFunctions.set(n.name.text, fid);
      if (ts.isReturnStatement(n) && fid && n.expression && ts.isObjectLiteralExpression(n.expression)) {
        const values = n.expression.properties.flatMap(p => ts.isShorthandPropertyAssignment(p) ? [p.name.text]
          : ts.isPropertyAssignment(p) ? [p.name.getText()] : []);
        hookReturns.set(fid, new Set([...(hookReturns.get(fid)||[]), ...values]));
      }
      ts.forEachChild(n, c => visit(c, fid));
    }
    visit(sf);
  }
  // Reconcile aliases may be discovered after effects in the first pass.
  for (const e of effects) e.deps = dependencies(e.call);
  // Second pass: cross-file function calls, resource operations and state setter sites.
  const funStack = [];
  const exprText = n => n ? n.getText().slice(0, 120) : '';
  const findTopChain = from => {
    let n = from;
    while (n.parent && (ts.isPropertyAccessExpression(n.parent) || ts.isCallExpression(n.parent))
           && (n.parent.expression === n || (ts.isPropertyAccessExpression(n.parent) && n.parent.expression === n))) n = n.parent;
    return n;
  };
  const collectOp = (call, currentFn) => {
    if (!currentFn || !ts.isPropertyAccessExpression(call.expression) || call.expression.name.text !== 'from'
        || !call.arguments.length || !ts.isStringLiteral(call.arguments[0])) return;
    const table = call.arguments[0].text;
    const chain = findTopChain(call).getText();
    const operation = /\.select\s*\(/.test(chain) ? 'read' : /\.(upsert|insert|update|delete)\s*\(/.test(chain) ? 'write' : 'unknown';
    if (operation === 'unknown') return;
    const key = [...chain.matchAll(/\.eq\s*\(\s*['"]([^'"]+)['"]\s*,\s*([\w.]+)/g)]
      .map(m=>`${m[1]}=${m[2]}`).join(',');
    const entry = { operation, resource: `db:${table}`, key, at: loc(call), expression: chain.slice(0, 190) };
    nodes.get(currentFn).reads.push(entry);
  };
  function visit2(node, currentFn = null) {
    let fid = currentFn;
    const location = loc(node);
    if (ts.isFunctionDeclaration(node) && node.name) fid = functionOf(node, node.name.text, node.name);
    else if (ts.isVariableDeclaration(node) && node.initializer && ts.isIdentifier(node.name)) {
      const e = node.initializer;
      if (ts.isArrowFunction(e) || ts.isFunctionExpression(e)) fid = functionOf(e, node.name.text, node.name);
      else if (ts.isCallExpression(e) && ['useCallback','useMemo'].includes(callNames(e.expression)) && e.arguments.length
               && (ts.isArrowFunction(e.arguments[0]) || ts.isFunctionExpression(e.arguments[0]))) {
        fid = functionOf(e.arguments[0], node.name.text, node.name);
      }
    } else if (ts.isMethodDeclaration(node) && node.name) fid = functionOf(node, node.name.getText(), node.name);
    if (ts.isCallExpression(node) && callNames(node.expression) === 'useEffect' && node.arguments.length
        && (ts.isArrowFunction(node.arguments[0]) || ts.isFunctionExpression(node.arguments[0]))) {
      const eid = functionOf(node.arguments[0], `useEffect@${location.line}`, null);
      for (const arg of node.arguments.slice(1)) visit2(arg, fid);
      visit2(node.arguments[0], eid);
      return;
    }
    if (ts.isCallExpression(node) && fid) {
      const call = node.expression;
      let target = symbolKey(ts.isPropertyAccessExpression(call) ? call.name : call);
      if (target && fnByKey.has(target)) {
        const to = fnByKey.get(target);
        if (to !== fid) {
          const list = calls.get(fid) || [];
          list.push({ to, at: location, args: node.arguments.map(exprText) });
          calls.set(fid, list);
        }
      }
      if (ts.isIdentifier(call) && /^set[A-Z]/.test(call.text)) {
        const p = nodes.get(fid);
        p.stateSetters.add(call.text);
      }
      if (callNames(call) === 'setInterval' && node.arguments[0] && (ts.isArrowFunction(node.arguments[0]) || ts.isFunctionExpression(node.arguments[0]))) {
        const cb = node.arguments[0], setters = [];
        function collect(n) {
          if (ts.isCallExpression(n) && ts.isIdentifier(n.expression) && /^set[A-Z]/.test(n.expression.text)) {
            const setter = n.expression.text;
            const returnsNew = n.arguments.some(a => ts.isArrowFunction(a) && /\.(filter|map|slice|concat)\s*\(|\[\.\.\.|\{\s*\.\.\./.test(a.getText()));
            if (returnsNew && stateNames.has(`${location.file}:${setter}`)) setters.push(setter);
          }
          ts.forEachChild(n, collect);
        }
        collect(cb);
        if (setters.length) timerFindings.push({ type: 'periodic_state_allocation', classification: 'candidate',
          at: location, setter: [...new Set(setters)], timer: exprText(node.arguments[1]),
          explanation: 'Periodic callback may allocate a new state value even when its logical contents are unchanged.' });
      }
      collectOp(node, fid);
    }
    ts.forEachChild(node, c => visit2(c, fid));
  }
  for (const sf of own) visit2(sf);
  // Resolve callees transitively; report shortest concrete path to every observed resource access.
  const memo = new Map();
  function operations(fid, seen = new Set(), depth = 0) {
    if (seen.has(fid) || depth > 10) return [];
    const fn = nodes.get(fid); if (!fn) return [];
    const result = fn.reads.map(op => ({ ...op, path: [{ name: fn.name, file: fn.file, line: fn.line }] }));
    for (const edge of calls.get(fid) || []) {
      for (const op of operations(edge.to, new Set([...seen, fid]), depth + 1)) {
        result.push({ ...op, path: [{ name: fn.name, file: fn.file, line: fn.line }, ...op.path] });
      }
    }
    return result;
  }
  // Discover which custom hooks share state/commands inside the same component.
  for (const sf of own) {
    const fnInvocations = new Map();
    function traverse(n) {
      if (ts.isVariableDeclaration(n) && ts.isObjectBindingPattern(n.name) && n.initializer && ts.isCallExpression(n.initializer)
          && ts.isIdentifier(n.initializer.expression) && /^use[A-Z]/.test(n.initializer.expression.text)) {
        const hook = n.initializer.expression.text;
        const props = n.name.elements.map(e => e.name.getText());
        fnInvocations.set(hook, props);
      }
      if (ts.isCallExpression(n) && ts.isIdentifier(n.expression) && /^use[A-Z]/.test(n.expression.text)
          && n.arguments[0] && ts.isObjectLiteralExpression(n.arguments[0])) {
        hookWires.push({ consumer: n.expression.text, args: new Set([...identifiersIn(n.arguments[0])]),
          inFile: rel(sf.fileName), line: loc(n).line, providers: null });
      }
      ts.forEachChild(n, traverse);
    }
    traverse(sf);
    for (const wire of hookWires.filter(w => w.inFile === rel(sf.fileName))) wire.providers = new Map(fnInvocations);
  }
  const findings = [];
  const seenPair = new Set();
  for (const wire of hookWires) {
    for (const [provider, props] of wire.providers) {
      if (provider === wire.consumer) continue;
      const shared = props.filter(v => wire.args.has(v));
      if (!shared.length) continue;
      const pfn = [...nodes.values()].find(f => f.name === provider);
      const cfn = [...nodes.values()].find(f => f.name === wire.consumer);
      if (!pfn || !cfn) continue;
      const exposed = hookReturns.get(pfn.id) || new Set();
      for (const e of effects.filter(e => e.owner === cfn.id && e.deps.some(d => shared.includes(d)))) {
        const effectOps = operations(e.id).filter(op => op.operation === 'read');
        if (!effectOps.length) continue;
        for (const prop of props.filter(p => exposed.has(p))) {
          const init = [...nodes.values()].find(f => f.file === pfn.file && f.name === prop);
          if (!init) continue;
          const before = operations(init.id).filter(op => op.operation === 'read');
          const changes = [...init.stateSetters].filter(setter => shared.some(x =>
            stateNames.get(`${init.file}:${setter}`) === x || setter === `set${x[0]?.toUpperCase()}${x.slice(1)}`));
          if (!changes.length) continue;
          for (const a of before) for (const b of effectOps) {
            if (a.resource !== b.resource) continue;
            const pair = [a.at.file, a.at.line, b.at.file, b.at.line, prop].join(':');
            if (seenPair.has(pair)) continue;
            seenPair.add(pair);
            findings.push({ type: 'state_effect_resource_overlap', classification: 'candidate', resource: a.resource,
              resourceKey: a.key || b.key || 'unknown', trigger: `state update ${changes[0]} -> effect dependency ${e.deps.filter(x=>shared.includes(x)).join(', ')}`,
              source: { entrypoint: prop, ...loc(init.node), path: a.path, operation: a.at },
              counterpart: { entrypoint: `useEffect@${e.line}`, file: e.file, line: e.line, path: b.path, operation: b.at },
              wiring: { file: wire.inFile, line: wire.line, provider, consumer: wire.consumer, sharedState: shared },
              note: 'Both paths can read the same resource around a state transition. Recovery/subscription timing may justify both reads.' });
          }
        }
      }
    }
  }
  // Same-entrypoint duplicate read calls to the same callee (distinct call sites).
  for (const fn of nodes.values()) {
    const byTarget = new Map();
    for (const edge of calls.get(fn.id) || []) {
      const ops = operations(edge.to).filter(op => op.operation === 'read');
      for (const op of ops) {
        const key = `${edge.to}|${op.resource}|${edge.args.join(',')}`;
        const arr = byTarget.get(key) || [];
        arr.push({ at: edge.at, op }); byTarget.set(key, arr);
      }
    }
    for (const sites of byTarget.values()) {
      const unique = [...new Map(sites.map(s => [`${s.at.file}:${s.at.line}:${s.at.column}`, s])).values()];
      if (unique.length < 2) continue;
      findings.push({ type: 'same_entrypoint_repeated_read', classification: 'candidate', source: loc(fn.node),
        resource: unique[0].op.resource, callSites: unique.map(s => s.at),
        note: 'The same entrypoint calls a read-producing callee multiple times with comparable arguments; control-flow guards may make paths exclusive.' });
    }
  }
  findings.push(...timerFindings);
  return { status: (parseErrors.length || omitted.length || unresolved.length) ? 'partial' : 'covered',
    detector: 'typescript-compiler-api', analysis_scope: 'package', scanned_files: own.length,
    omissions: { file_limit: omitted.length, parse_errors: parseErrors, unresolved_relative_imports: unresolved },
    findings, limitations: [
      'Static call paths cannot establish runtime ordering or whether repeated reads are necessary.',
      'Dynamic/reflective calls and unresolved imports may hide paths.',
      'State/effect overlap detection currently covers directly wired custom React hooks with visible state names.',
      'No application code is executed or mutated.'
    ] };
}
if (require.main === module) main();
module.exports = { analyze, argsOf, sourceFiles };
