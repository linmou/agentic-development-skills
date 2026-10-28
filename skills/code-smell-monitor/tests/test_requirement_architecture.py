"""Offline source-grounding and adapter/CLI contracts."""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


python = load('python_architecture')
requirements = load('requirement_interpretation')
monitor = load('code_smell_monitor')
graph = load('architecture_graph')


class RequirementArchitectureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)

    def write(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        return path

    def manifest(self):
        self.write('req.md', '# Requirements\nState survives reloads.\n')
        self.write('a.py', 'import b\n')
        self.write('b.py', 'import a\n')
        self.item = {'id': 'FR-1', 'kind': 'functional', 'modules': ['a.py'],
                     'source': {'path': 'req.md', 'line_start': 2, 'line_end': 2,
                                'quote': 'State survives reloads.'},
                     'rationale': 'Shared state dependencies deserve lifecycle review.',
                     'uncertainty': 'Static edges do not demonstrate state loss.'}
        self.document = {'version': 1, 'requirements': [self.item]}
        self.path = self.repo / 'mapping.json'
        self.path.write_text(json.dumps(self.document))
        payload, _ = python.collect(self.repo)
        self.architecture = graph.analyze(payload)
        return self.path

    def test_cycle_mapping_preserves_source_hash_evidence_and_uncertainty(self):
        self.manifest()
        result = requirements.interpret(self.repo, self.architecture, self.path)
        self.assertEqual(result['status'], 'covered')
        association = result['associations'][0]
        self.assertEqual(association['classification'], 'impact_hypothesis')
        self.assertEqual(association['confidence'], 'association_only')
        self.assertEqual(association['source']['quote'], 'State survives reloads.')
        self.assertEqual(len(association['source']['sha256']), 64)
        self.assertEqual(association['evidence']['members'], ['a.py', 'b.py'])
        self.assertEqual(association['uncertainty'], self.item['uncertainty'])
        self.assertEqual(self.architecture['enforced_violations'], 0)

    def test_no_requirements_never_invents_impact(self):
        self.manifest()
        result = requirements.interpret(self.repo, self.architecture, None)
        self.assertEqual(result['status'], 'not_provided')
        self.assertEqual(result['associations'], [])
        self.assertEqual(len(result['unmapped_findings']), 1)

    def test_invalid_or_stale_sources_and_mappings_are_rejected(self):
        for field, value in [('quote', 'Invented requirement'), ('line_start', 0),
                             ('line_end', True), ('path', '../outside.md')]:
            with self.subTest(field=field):
                self.manifest()
                self.item['source'][field] = value
                self.path.write_text(json.dumps(self.document))
                with self.assertRaises(ValueError):
                    requirements.interpret(self.repo, self.architecture, self.path)
        self.manifest()
        self.write('req.md', 'Changed requirement\n')
        with self.assertRaises(ValueError):
            requirements.interpret(self.repo, self.architecture, self.path)

    def test_missing_uncertainty_duplicate_ids_and_glob_mapping_rejected(self):
        for mutation in ('uncertainty', 'duplicate', 'glob'):
            with self.subTest(mutation=mutation):
                self.manifest()
                if mutation == 'uncertainty':
                    del self.item['uncertainty']
                elif mutation == 'duplicate':
                    self.document['requirements'].append(self.item)
                else:
                    self.item['modules'] = ['*.py']
                self.path.write_text(json.dumps(self.document))
                with self.assertRaises(ValueError):
                    requirements.interpret(self.repo, self.architecture, self.path)

    def test_quality_and_unmapped_requirements_do_not_fabricate_findings(self):
        self.manifest()
        self.write('other.py', '')
        self.item.update(kind='quality', modules=['other.py'])
        self.path.write_text(json.dumps(self.document))
        result = requirements.interpret(self.repo, self.architecture, self.path)
        self.assertEqual(result['associations'], [])
        self.assertEqual(result['requirements'][0]['kind'], 'quality')
        self.assertEqual(len(result['unmapped_findings']), 1)

    def test_python_relative_src_layout_and_package_initializers(self):
        self.write('src/pkg/__init__.py', '')
        self.write('src/pkg/a.py', 'from . import b\nfrom pkg.b import value\n')
        self.write('src/pkg/b.py', 'from .a import value\n')
        payload, coverage = python.collect(self.repo)
        result = graph.analyze(payload)
        self.assertEqual(coverage['status'], 'covered')
        cycles = [f for f in result['findings'] if f['category'] == 'dependency_cycle']
        self.assertEqual(cycles[0]['evidence']['members'], ['src/pkg/a.py', 'src/pkg/b.py'])
        self.assertTrue(any(i['line'] == 2 and i['status'] == 'resolved' for i in coverage['imports']))
        self.assertEqual(result['enforced_violations'], 0)

    def test_python_parse_dynamic_and_ambiguous_inputs_are_partial(self):
        self.write('src/a.py', '')
        self.write('a.py', 'bad syntax !')
        self.write('b.py', 'import a\n__import__("dynamic")\n')
        _, coverage = python.collect(self.repo)
        self.assertEqual(coverage['status'], 'partial')
        self.assertEqual(coverage['files_parsed'], 2)
        self.assertEqual({i['status'] for i in coverage['imports']},
                         {'ambiguous', 'dynamic_import_not_resolved'})

    def test_python_never_executes_target_and_excludes_generated_files(self):
        self.write('a.py', 'raise RuntimeError("MUST NOT EXECUTE")\nimport os\n')
        self.write('node_modules/dependency/bad.py', 'bad syntax !')
        self.write('.venv/bad.py', 'bad syntax !')
        _, coverage = python.collect(self.repo)
        self.assertEqual(coverage['files_parsed'], 1)
        self.assertEqual(coverage['imports'][0]['status'], 'stdlib')

    def test_python_unknown_external_import_is_partial_not_clean(self):
        self.write('a.py', 'import missing_project_or_external_module\n')
        _, coverage = python.collect(self.repo)
        self.assertEqual(coverage['status'], 'partial')
        self.assertEqual(coverage['imports'][0]['status'], 'external_or_unresolved')

    def test_cli_reports_python_graph_and_source_mapping_in_json_and_markdown(self):
        self.manifest()
        out = self.repo / 'out'
        result = subprocess.run([sys.executable, str(SCRIPTS / 'code_smell_monitor.py'),
                                 '--repo', str(self.repo), '--out', str(out), '--architecture-only',
                                 '--requirements', str(self.path), '--architecture-max-degree', '1',
                                 '--install', 'never', '--fail-on-tool-error'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads((out / 'summary.json').read_text())
        self.assertTrue(summary['coverage']['complete'])
        self.assertEqual(summary['architecture']['adapters'][0]['graph'], {'nodes': 2, 'edges': 2})
        report = (out / 'code_smell_report.md').read_text()
        for value in ('impact_hypothesis', 'State survives reloads.', 'uncertainty', 'sha256', 'dependency_cycle'):
            self.assertIn(value, report)

    def test_cli_invalid_requirements_fail_and_preserve_error_report(self):
        self.write('a.py', '')
        mapping = self.write('mapping.json', '{}')
        out = self.repo / 'out'
        result = subprocess.run([sys.executable, str(SCRIPTS / 'code_smell_monitor.py'),
                                 '--repo', str(self.repo), '--out', str(out), '--architecture-only',
                                 '--requirements', str(mapping), '--install', 'never'], capture_output=True)
        self.assertEqual(result.returncode, 2)
        summary = json.loads((out / 'summary.json').read_text())
        self.assertEqual(summary['requirement_interpretation']['status'], 'failed')

    def test_mixed_stack_never_hides_unavailable_adapter(self):
        raw = self.repo / 'raw'
        raw.mkdir()
        self.write('a.py', '')
        missing = {'status': 'unavailable', 'detector': 'dependency-cruiser', 'analysis_scope': 'package',
                   'graph': None, 'findings': [], 'enforced_violations': 0}
        with mock.patch.object(monitor, 'run_architecture', return_value=(missing, {})):
            result = monitor.analyze_architecture(self.repo, raw, {'python': True, 'javascript': True}, 'never', 12)
        self.assertEqual(result['status'], 'partial')
        self.assertEqual(len(result['adapters']), 2)

    def test_javascript_config_and_unresolved_coverage_are_preserved(self):
        raw = self.repo / 'raw'
        raw.mkdir()
        payload = {'modules': [{'source': 'a.ts', 'dependencies': [
            {'module': 'missing', 'couldNotResolve': True}]}]}
        completed = {'cmd': ['depcruise'], 'exit_code': 0, 'timed_out': False,
                     'stdout': json.dumps(payload), 'stderr': '', 'duration_seconds': 0}
        with mock.patch.object(monitor, 'node_runner', return_value=['depcruise']) as runner, \
                mock.patch.object(monitor, 'run_command', return_value=completed):
            outcome, _ = monitor.run_architecture(self.repo, raw, 'never', 12)
            self.assertIn('--no-config', runner.call_args.args[2])
            self.assertEqual(outcome['status'], 'partial')
            self.write('.dependency-cruiser.cjs', 'module.exports = {};')
            monitor.run_architecture(self.repo, raw, 'never', 12)
            self.assertNotIn('--no-config', runner.call_args.args[2])

    def test_python_no_files_and_inaccessible_directory_are_not_clean(self):
        _, evidence = python.collect(self.repo)
        self.assertEqual(evidence['status'], 'unavailable')
        def walk(*args, **kwargs):
            kwargs['onerror'](PermissionError('access denied'))
            return iter([])
        with mock.patch.object(python.os, 'walk', side_effect=walk):
            _, evidence = python.collect(self.repo)
        self.assertEqual(evidence['status'], 'partial')
        self.assertTrue(evidence['traversal_errors'])

    def test_unrepresented_typescript_is_partial_even_with_zero_unresolved_imports(self):
        raw = self.repo / 'raw'
        raw.mkdir()
        self.write('hidden.ts', 'export const value = 1;')
        completed = {'cmd': ['depcruise'], 'exit_code': 0, 'timed_out': False,
                     'stdout': '{"modules": []}', 'stderr': '', 'duration_seconds': 0}
        with mock.patch.object(monitor, 'node_runner', return_value=['depcruise']), \
                mock.patch.object(monitor, 'run_command', return_value=completed):
            outcome, _ = monitor.run_architecture(self.repo, raw, 'never', 12)
        self.assertEqual(outcome['status'], 'partial')
        self.assertEqual(outcome['unrepresented_files'], ['hidden.ts'])

    def test_ci_enforcement_depends_on_error_rule_or_explicit_strict_coverage(self):
        self.write('a.py', '')
        for violations, status, strict, expected in [(0, 'covered', False, 0),
                                                    (1, 'covered', False, 1),
                                                    (0, 'partial', False, 0),
                                                    (0, 'partial', True, 1)]:
            with self.subTest(violations=violations, status=status, strict=strict):
                outcome = {'status': status, 'adapters': [], 'findings': [],
                           'enforced_violations': violations}
                args = ['monitor', '--repo', str(self.repo), '--architecture-only', '--install', 'never',
                        '--out', str(self.repo / 'out')]
                if strict:
                    args.append('--fail-on-tool-error')
                with mock.patch.object(sys, 'argv', args), \
                        mock.patch.object(monitor, 'analyze_architecture', return_value=outcome):
                    self.assertEqual(monitor.main(), expected)


if __name__ == '__main__':
    unittest.main()
