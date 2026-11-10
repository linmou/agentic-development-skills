#!/usr/bin/env node
// Purpose: Index exact-scope function and hook spans without evaluating code or diagnosing smells.
'use strict';
const fs = require('node:fs');
const path = require('node:path');
const {createRequire} = require('node:module');

function readScope(repo, scopeFile) {
  const names = fs.readFileSync(scopeFile, 'utf8').split(/\r?\n/).map(x => x.trim()).filter(Boolean);
  if (!names.length || new Set(names).size !== names.length) throw Error('Scope must be nonempty and contain no duplicates');
  const resolved = names.map(name => {
    if (path.isAbsolute(name)) throw Error('Scope paths must be relative');
    const full = fs.realpathSync(path.resolve(repo, name));
    const relative = path.relative(repo, full);
    if (relative.startsWith('..' + path.sep) || relative === '..' || path.isAbsolute(relative)) throw Error('Scope escapes repository');
    if (!fs.statSync(full).isFile() || !/\.(?:[cm]?[jt]s|[jt]sx)$/.test(full) || /\.d\.[cm]?ts$/.test(full)) throw Error('Scope requires JS/TS implementation files');
    return relative.split(path.sep).join('/');
  }).sort();
  if (new Set(resolved).size !== resolved.length) throw Error('Scope aliases the same file');
  return resolved;
}

function inventory(repo, scopeFile) {
  repo = fs.realpathSync(repo);
  const ts = createRequire(path.join(repo, 'package.json'))('typescript');
  const files = readScope(repo, scopeFile);
  const records = [], errors = [];
  for (const file of files) {
    const source = fs.readFileSync(path.join(repo, file), 'utf8');
    const sf = ts.createSourceFile(file, source, ts.ScriptTarget.Latest, true);
    const span = node => [sf.getLineAndCharacterOfPosition(node.getStart(sf)).line + 1,
      sf.getLineAndCharacterOfPosition(Math.max(node.getStart(sf), node.end - 1)).line + 1];
    for (const diagnostic of sf.parseDiagnostics) errors.push({file, start: diagnostic.start,
      message: ts.flattenDiagnosticMessageText(diagnostic.messageText, '\n')});
    records.push(['file', file, source.split(/\r?\n/).length]);
    function functionName(node) {
      if (node.name) return node.name.getText(sf);
      const parent = node.parent;
      if (parent && (ts.isVariableDeclaration(parent) || ts.isPropertyAssignment(parent))) return parent.name.getText(sf);
      if (parent && ts.isExportAssignment(parent)) return 'default';
      return null;
    }
    function visit(node, enclosing) {
      let owner = enclosing;
      if (ts.isFunctionLike(node) && node.body) {
        const name = functionName(node);
        if (name) {
          const bounds = span(node);
          records.push(['function', file, name, ...bounds, enclosing]);
          owner = `${name}:${bounds[0]}`;
        }
      }
      if (ts.isCallExpression(node)) {
        const callee = node.expression;
        const name = ts.isIdentifier(callee) ? callee.text : ts.isPropertyAccessExpression(callee) ? callee.name.text : '';
        if (/^use[A-Z]/.test(name)) {
          const callback = node.arguments[0];
          const dependencies = node.arguments[1];
          records.push(['hook', file, name, ...span(node), owner,
            callback && (ts.isArrowFunction(callback) || ts.isFunctionExpression(callback)) ? span(callback) : null,
            dependencies ? span(dependencies) : null]);
        }
      }
      ts.forEachChild(node, child => visit(child, owner));
    }
    visit(sf, null);
  }
  return {status: errors.length ? 'partial' : 'complete', repo, files, typescript_version: ts.version,
    columns: {file: ['kind', 'file', 'lines'], function: ['kind', 'file', 'name', 'start', 'end', 'enclosing'],
      hook: ['kind', 'file', 'callee', 'start', 'end', 'enclosing', 'callback_span', 'second_argument_span']},
    note: 'Syntax navigation only. Hook-like names are lexical, not resolved React identities. Spans include complete calls and their arguments; no semantic or reachability inference.',
    records, errors};
}

function main(argv) {
  const options = {};
  for (let i = 0; i < argv.length; i += 2) {
    if (!['--repo', '--scope-file'].includes(argv[i]) || !argv[i + 1]) throw Error('Usage: --repo DIR --scope-file FILE');
    options[argv[i]] = argv[i + 1];
  }
  if (!options['--repo'] || !options['--scope-file']) throw Error('Both --repo and --scope-file are required');
  const result = inventory(options['--repo'], options['--scope-file']);
  process.stdout.write(JSON.stringify(result) + '\n');
  return result.status === 'complete' ? 0 : 2;
}
if (require.main === module) {
  try { process.exitCode = main(process.argv.slice(2)); }
  catch (error) { process.stderr.write(String(error) + '\n'); process.exitCode = 2; }
}
module.exports = {inventory, readScope};
