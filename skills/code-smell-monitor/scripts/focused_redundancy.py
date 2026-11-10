#!/usr/bin/env python3
# Purpose: Collect focused redundancy evidence once and publish bounded, resumable navigation pages.
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any

import code_smell_monitor as monitor
from compact_redundancy import build_index, indexed_knip


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def scope_files(repo: Path, scope_file: Path) -> list[str]:
    repo = repo.resolve()
    names = [line.strip() for line in scope_file.read_text().splitlines() if line.strip()]
    if not names or len(names) != len(set(names)):
        raise ValueError('Scope must be nonempty without duplicate paths')
    result = []
    for name in names:
        location = (repo / name).resolve()
        if Path(name).is_absolute() or not location.is_relative_to(repo) or not location.is_file():
            raise ValueError(f'Invalid scope path: {name}')
        if location.suffix not in monitor.JS_EXTENSIONS or location.name.endswith(('.d.ts', '.d.mts', '.d.cts')):
            raise ValueError(f'Not an implementation source file: {name}')
        result.append(location.relative_to(repo).as_posix())
    if len(result) != len(set(result)):
        raise ValueError('Scope contains aliases of the same file')
    return sorted(result)


def identity(repo: Path, out: Path, scope: list[str], commands: list[tuple[str, list[str] | None]]) -> dict[str, Any]:
    files: list[tuple[str, str]] = []
    excluded = {'.git', 'node_modules', '.eft', '__pycache__', 'evals', 'evaluation', 'evaluations',
                'experiments', 'output', '.code-smell-monitor', 'reports', 'tmp'}
    for directory, dirs, names in os.walk(repo, followlinks=False):
        dirs[:] = sorted(d for d in dirs if d not in excluded
                         and not (Path(directory) / d).is_symlink()
                         and not (Path(directory) / d).resolve().is_relative_to(out))
        for name in sorted(names):
            item = Path(directory) / name
            if not item.is_symlink() and not item.resolve().is_relative_to(out):
                files.append((item.relative_to(repo).as_posix(), digest(item)))
    lock = repo / 'node_modules/.package-lock.json'
    if lock.exists():
        files.append(('node_modules/.package-lock.json', digest(lock)))
    scripts = [Path(__file__), Path(__file__).with_name('source_inventory.cjs'),
               Path(monitor.__file__), Path(monitor.__file__).with_name('behavioral_redundancy.cjs'),
               Path(monitor.__file__).with_name('compact_redundancy.py')]
    tools = []
    for name, command in commands:
        executable = Path(shutil.which(command[0]) or command[0]).resolve() if command else None
        version = monitor.run_command([str(executable), '--version'], repo) if executable and executable.is_file() else None
        packages = {}
        if executable:
            for parent in executable.parents:
                for filename in ('package.json', '.package-lock.json'):
                    manifest = parent / filename
                    if manifest.is_file():
                        packages[str(manifest)] = digest(manifest)
                if parent.name == 'node_modules':
                    break
        tools.append([name, command, str(executable), digest(executable) if executable and executable.is_file() else None,
                      {key: version[key] for key in ('exit_code', 'stdout', 'stderr')} if version else None, packages])
    for name in ['node', 'python3']:
        tools.append([name, monitor.run_command([name, '--version'], repo)['stdout'].strip()])
    ts = repo / 'node_modules/typescript/package.json'
    if ts.exists():
        files.append(('node_modules/typescript/package.json', digest(ts)))
    return {'repo': str(repo), 'scope': scope,
            'excluded_hash_directories': sorted(excluded),
            'scope_sha256': {name: digest(repo / name) for name in scope},
            'inputs_sha256': hashlib.sha256(json.dumps(sorted(files)).encode()).hexdigest(),
            'scripts': {str(item): digest(item) for item in scripts}, 'tools': tools}


def resume_state(out: Path, current: dict[str, Any]) -> dict[str, Any]:
    path = out / 'focused-state.json'
    if path.exists():
        state = json.loads(path.read_text())
        if state.get('identity') != current:
            raise ValueError('Resume identity mismatch: use a new output directory; inputs or tools changed')
        return state
    state = {'identity': current, 'completed': {}}
    save(path, state)
    return state


def pages(out: Path, section: str, records: list[Any], source: str, maximum: int) -> list[dict[str, Any]]:
    """Preserve every ordinal; replace oversized display records only with explicit raw locators."""
    result: list[dict[str, Any]] = []
    lines: list[str] = []
    byte_count = 0
    first = 0
    def flush() -> None:
        nonlocal lines, byte_count, first
        if not lines:
            return
        relative = f'pages/{section}-{len(result) + 1:03d}.jsonl'
        target = out / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(''.join(lines))
        result.append({'path': relative, 'records': len(lines), 'bytes': byte_count, 'first': first})
        first += len(lines)
        lines, byte_count = [], 0
    for ordinal, record in enumerate(records):
        row = {'i': ordinal, 'record': record}
        line = json.dumps(row, separators=(',', ':'), ensure_ascii=False) + '\n'
        if len(line.encode()) > maximum:
            line = json.dumps({'i': ordinal, 'oversized': True, 'raw': f'{source}/{ordinal}',
                               'bytes': len(line.encode())}, separators=(',', ':')) + '\n'
        size = len(line.encode())
        if size > maximum:
            raise ValueError('Page limit cannot hold a raw locator')
        if lines and (byte_count + size > maximum or len(lines) >= 50):
            flush()
        lines.append(line)
        byte_count += size
    flush()
    for position, item in enumerate(result):
        item.update(total=len(records), end=item['first'] + item['records'],
                    next=result[position + 1]['path'] if position + 1 < len(result) else None)
    return result


def classify(name: str, raw: Path, result: dict[str, Any], payload: Any) -> str:
    if result['timed_out']:
        return 'timed_out'
    if result['exit_code'] in (126, 127):
        return 'unavailable'
    if name.startswith('knip') and result['exit_code'] in (0, 1) and isinstance(payload, dict):
        try:
            return 'findings' if indexed_knip(payload) else 'clean'
        except ValueError:
            return 'failed'
    if name == 'jscpd' and result['exit_code'] == 0 and (raw / 'jscpd_report/jscpd-report.json').exists():
        return 'findings' if json.loads((raw / 'jscpd_report/jscpd-report.json').read_text()).get('duplicates') else 'clean'
    if name in ('behavioral_redundancy', 'source_inventory') and isinstance(payload, dict):
        if payload.get('status') in ('partial', 'failed', 'unavailable'):
            return str(payload['status'])
        if result['exit_code'] == 0:
            return 'findings' if payload.get('findings') else 'clean'
    return 'failed'


def prepare(repo: Path, scope_file: Path, out: Path, page_bytes: int) -> dict[str, Any]:
    repo, out = repo.resolve(), out.resolve()
    scope = scope_files(repo, scope_file)
    if out == repo or repo.is_relative_to(out):
        raise ValueError('Output must not contain repository')
    raw = out / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    scripts = Path(monitor.__file__).parent
    commands = [
        ('source_inventory', ['node', str(Path(__file__).with_name('source_inventory.cjs')), '--repo', str(repo), '--scope-file', str(scope_file.resolve())]),
        ('knip_dead_code', monitor.node_runner(repo, 'knip', ['--reporter', 'json'], 'never')),
        ('knip_production', monitor.node_runner(repo, 'knip', ['--production', '--reporter', 'json'], 'never')),
        ('jscpd', monitor.node_runner(repo, 'jscpd', monitor.jscpd_args(scope, raw), 'never')),
        ('behavioral_redundancy', ['node', str(scripts / 'behavioral_redundancy.cjs'), '--repo', str(repo)]),
    ]
    state = resume_state(out, identity(repo, out, scope, commands))
    results = []
    for position, (name, command) in enumerate(commands, 1):
        print(f'[{position}/{len(commands)}] {name}', file=sys.stderr, flush=True)
        if name in state['completed']:
            record = state['completed'][name]
            for relative, expected in record['artifacts'].items():
                if not (out / relative).is_file() or digest(out / relative) != expected:
                    raise ValueError(f'Resume artifact missing or changed: {relative}')
            results.append(record['result'])
            continue
        result = monitor.run_command(command, repo, timeout=600) if command else {
            'cmd': [name], 'exit_code': 127, 'stdout': '', 'stderr': 'Tool unavailable; installation disabled',
            'duration_seconds': 0, 'timed_out': False}
        monitor.write_raw(raw, name, result)
        payload = monitor.maybe_json_file(raw, name, result)
        record = {key: value for key, value in result.items() if key not in ('stdout', 'stderr')}
        record.update(name=name, status=classify(name, raw, result, payload), raw=f'raw/{name}.stdout.txt')
        artifacts = {str(item.relative_to(out)): digest(item) for item in raw.glob(name + '.*') if item.is_file()}
        if name == 'jscpd':
            artifacts.update({str(item.relative_to(out)): digest(item) for item in (raw / 'jscpd_report').glob('*') if item.is_file()})
        state['completed'][name] = {'result': record, 'artifacts': artifacts}
        save(out / 'focused-state.json', state)
        results.append(record)
    coverage = {'complete': all(r['status'] in ('clean', 'findings') for r in results),
                'assessed': ['unused_code', 'clones', 'static_behavioral_candidates', 'syntax_navigation'],
                'not_assessed': ['type_safety', 'security', 'dependency_health', 'general_complexity'],
                'note': 'Focused advisory evidence; not the general monitor invocation-contract result.'}
    save(out / 'summary.json', {'repo': str(repo), 'scope': scope, 'results': results, 'coverage': coverage})
    index = build_index(out, True)
    save(out / 'candidate-index.json', index)
    source = json.loads((raw / 'source_inventory.json').read_text()) if (raw / 'source_inventory.json').exists() else {'records': [], 'errors': ['Source inventory unavailable']}
    section_records = {'source_units': source.get('records', []), 'knip': index.get('knip', []),
                       'behavioral': index.get('behavioral', {}).get('findings', []), 'clones': index.get('clones', [])}
    page_index = {section: pages(out, section, records,
                  'raw/source_inventory.json#/records' if section == 'source_units' else f'candidate-index.json#/{section}' + ('/findings' if section == 'behavioral' else ''), page_bytes)
                  for section, records in section_records.items()}
    file_rows = []
    units = section_records['source_units']
    for ordinal, row in enumerate(units):
        if row[0] == 'file':
            end = next((i for i in range(ordinal + 1, len(units)) if units[i][0] == 'file'), len(units))
            file_rows.append({'file': row[1], 'lines': row[2], 'source_ordinal': ordinal,
                              'functions': sum(unit[0] == 'function' for unit in units[ordinal:end]),
                              'hooks': sum(unit[0] == 'hook' for unit in units[ordinal:end]),
                              'pages': [item['path'] for item in page_index['source_units'] if item['first'] < end and item['end'] > ordinal]})
    save(out / 'source-files.json', file_rows)
    page_index['source_files'] = pages(out, 'source_files', file_rows, 'source-files.json#', page_bytes)
    overview = {'status': 'complete' if coverage['complete'] and index['index_status'] == 'complete' else 'partial',
                'repo': str(repo), 'scope_files': len(scope), 'checks': results, 'coverage': coverage,
                'source_columns': source.get('columns'), 'source_errors': source.get('errors'),
                'candidate_errors': index.get('errors'), 'knip_scope': index.get('knip_scope'),
                'page_byte_limit': page_bytes, 'pages': page_index,
                'note': 'Navigation and unvalidated candidates. Read source_files pages for scope breadth and selected source_units pages for navigation; expand complete source boundaries before claims. This overview is the page sidecar: first/end are half-open record ordinals, total and next show completeness/continuation. Raw records remain in candidate-index.json and raw/source_inventory.json.'}
    save(out / 'overview.json', overview)
    return overview


def main() -> int:
    parser = argparse.ArgumentParser(description='Prepare focused redundancy evidence and bounded source/candidate pages.')
    parser.add_argument('--repo', type=Path, required=True)
    parser.add_argument('--scope-file', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--page-bytes', type=int, default=6000)
    args = parser.parse_args()
    if args.page_bytes < 512:
        parser.error('--page-bytes must be at least512')
    try:
        overview = prepare(args.repo, args.scope_file, args.out, args.page_bytes)
    except (ValueError, OSError, KeyError) as error:
        print(f'Preparation failed: {error}', file=sys.stderr)
        return 2
    print(json.dumps({'status': overview['status'], 'overview': str(args.out / 'overview.json'),
                      'pages': {name: [item['path'] for item in items] for name, items in overview['pages'].items()}}))
    return 0 if overview['status'] == 'complete' else 2


if __name__ == '__main__':
    raise SystemExit(main())
