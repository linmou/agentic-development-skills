"""Static Python import evidence. Never imports or executes the inspected project."""
from __future__ import annotations

import ast
import os
import sys
import tokenize
from pathlib import Path
from typing import Any

EXCLUDED = {'.git', '.venv', 'venv', 'env', '__pycache__', 'node_modules',
            'dist', 'build', '.code-smell-monitor'}


def collect(repo: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    repo = repo.resolve()
    paths = []
    traversal_errors: list[dict[str, str]] = []
    def traversal_error(exc: OSError) -> None:
        traversal_errors.append({'source': str(exc.filename), 'error': str(exc)})
    for directory, dirs, names in os.walk(repo, onerror=traversal_error):
        dirs[:] = sorted(d for d in dirs if d not in EXCLUDED
                         and not (Path(directory) / d).is_symlink())
        paths.extend(Path(directory) / n for n in sorted(names)
                     if n.endswith('.py') and not (Path(directory) / n).is_symlink())
    # Index both conventional repository roots and src-layout roots. Ambiguous
    # module names stay unresolved instead of selecting an arbitrary candidate.
    index: dict[str, set[str]] = {}
    for path in paths:
        relative = path.relative_to(repo).as_posix()
        parts = list(path.relative_to(repo).with_suffix('').parts)
        if parts[-1] == '__init__':
            parts.pop()
        aliases = [parts]
        if parts and parts[0] == 'src':
            aliases.append(parts[1:])
        for alias in aliases:
            if alias:
                index.setdefault('.'.join(alias), set()).add(relative)
    modules, imports, errors = [], [], []
    for path in paths:
        source = path.relative_to(repo).as_posix()
        dependencies: set[str] = set()
        try:
            with tokenize.open(path) as stream:
                tree = ast.parse(stream.read(), filename=source)
        except (SyntaxError, UnicodeError, OSError, LookupError) as exc:
            errors.append({'source': source, 'error': str(exc)})
            modules.append({'source': source, 'dependencies': []})
            continue
        package = list(path.relative_to(repo).with_suffix('').parts[:-1])
        for node in ast.walk(tree):
            requests: list[tuple[str, str | None]] = []
            if isinstance(node, ast.Import):
                requests = [(alias.name, None) for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    if node.level > len(package):
                        imports.append({'source': source, 'line': node.lineno,
                                        'status': 'invalid_relative_import'})
                        continue
                    base = package[:len(package) - node.level + 1]
                    name = '.'.join(base + ([node.module] if node.module else []))
                else:
                    name = node.module or ''
                # `from pkg import value` can import a module or a symbol.
                requests = [(name + '.' + alias.name, name) for alias in node.names]
            elif isinstance(node, ast.Call) and (
                isinstance(node.func, ast.Name) and node.func.id == '__import__'
                or isinstance(node.func, ast.Attribute) and node.func.attr == 'import_module'
            ):
                imports.append({'source': source, 'line': node.lineno,
                                'status': 'dynamic_import_not_resolved'})
            for name, fallback in requests:
                candidates = index.get(name, set())
                used_fallback = not candidates and fallback
                if used_fallback:
                    candidates = index.get(fallback, set())
                status = ('resolved' if len(candidates) == 1 else
                          'ambiguous' if candidates else 'external_or_unresolved')
                if not candidates and name.split('.')[0] in sys.stdlib_module_names:
                    status = 'stdlib'
                targets = sorted(candidates) if status == 'resolved' else []
                if used_fallback and targets == [source]:
                    targets = []  # Accessing this package's own symbol is not a self-import cycle.
                if not candidates and any(name.startswith(key + '.') for key in index):
                    status = 'unresolved_internal'
                dependencies.update(targets)
                # Importing a submodule also executes known package initializers.
                if status == 'resolved':
                    target = Path(targets[0])
                    for parent in target.parents:
                        init = (parent / '__init__.py').as_posix()
                        if init != source and (repo / init).is_file():
                            dependencies.add(init)
                imports.append({'source': source, 'line': node.lineno,
                                'module': name, 'status': status, 'targets': targets})
        modules.append({'source': source, 'dependencies': [
            {'resolved': target} for target in sorted(dependencies)]})
    incomplete = errors or traversal_errors or any(i['status'] in {
        'ambiguous', 'invalid_relative_import', 'dynamic_import_not_resolved', 'unresolved_internal',
        'external_or_unresolved'
    } for i in imports)
    return {'modules': modules}, {
        'status': 'partial' if incomplete else 'covered' if paths else 'unavailable',
        'files_discovered': len(paths), 'files_parsed': len(paths) - len(errors),
        'imports': imports, 'errors': errors, 'traversal_errors': traversal_errors,
        'limitations': [
            'Static imports only; no project code is executed.',
            'Only repository-root and src-layout module roots are indexed.',
            'External or unresolved names produce partial coverage and may include runtime path manipulation; '
            'third-party, namespace-package and dynamic dependencies are not proven complete.',
            'Conditional and TYPE_CHECKING imports are potential edges, not runtime execution claims.',
            'Symlinks and dependency/build directories are excluded.',
        ],
    }
