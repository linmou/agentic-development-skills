#!/usr/bin/env python3
# Tests focused_redundancy.py: bounded preservation, strict scope/resume identity, failures and artifact integrity.
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))

from focused_redundancy import classify, pages, prepare, resume_state, scope_files


class FocusedTests(unittest.TestCase):
    def test_scope_rejects_escape_duplicates_and_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'a.ts').write_text('export const a = 1;')
            scope = root / 'scope.txt'
            scope.write_text('a.ts\n')
            self.assertEqual(scope_files(root, scope), ['a.ts'])
            for text in ('', 'a.ts\na.ts', '../a.ts', '/tmp/a.ts', 'absent.ts', 'scope.txt'):
                scope.write_text(text)
                with self.subTest(text=text), self.assertRaises(ValueError):
                    scope_files(root, scope)
            (root / 'alias.ts').symlink_to(root / 'a.ts')
            scope.write_text('a.ts\nalias.ts')
            with self.assertRaises(ValueError):
                scope_files(root, scope)

    def test_pages_preserve_ordinals_unicode_and_oversize_locators(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            records = [{'x': 'α' * 70} for _ in range(71)] + [{'x': 'a' * 4000}]
            index = pages(root, 'candidate', records, 'raw.json#/items', 512)
            rows: list[dict[str, Any]] = []
            for page in index:
                data = (root / page['path']).read_bytes()
                self.assertLessEqual(len(data), 512)
                rows.extend(json.loads(line) for line in data.splitlines())
            self.assertEqual([row['i'] for row in rows], list(range(len(records))))
            self.assertEqual([row['record'] for row in rows[:-1]], records[:-1])
            self.assertEqual(rows[-1]['raw'], 'raw.json#/items/71')
            self.assertTrue(rows[-1]['oversized'])
            self.assertEqual(index[0]['total'], len(records))
            self.assertEqual(index[-1]['end'], len(records))
            self.assertIsNone(index[-1]['next'])

    def test_resume_rejects_identity_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = {'source': 'a', 'tool': 'v1'}
            self.assertEqual(resume_state(root, original), resume_state(root, original))
            with self.assertRaisesRegex(ValueError, 'identity mismatch'):
                resume_state(root, {**original, 'source': 'b'})

    def test_failures_are_not_clean(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = {'exit_code': 1, 'timed_out': False}
            self.assertEqual(classify('knip_dead_code', root, result, None), 'failed')
            self.assertEqual(classify('knip_dead_code', root, result, {}), 'failed')
            self.assertEqual(classify('knip_dead_code', root, result, {'issues': []}), 'clean')
            self.assertEqual(classify('behavioral_redundancy', root, {'exit_code': 0, 'timed_out': False}, {'status': 'partial'}), 'partial')
            self.assertEqual(classify('knip_dead_code', root, {'exit_code': 124, 'timed_out': True}, None), 'timed_out')

    def test_resume_checks_saved_artifacts_before_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'a.ts').write_text('const a=1')
            scope = root / 'scope.txt'
            scope.write_text('a.ts\n')
            out = root / 'out'
            out.mkdir()
            state: dict[str, Any] = {'identity': {}, 'completed': {
                'source_inventory': {'artifacts': {'raw/source_inventory.json': 'missing'}, 'result': {}}}}
            with patch('focused_redundancy.identity', return_value={}), patch('focused_redundancy.resume_state', return_value=state):
                with self.assertRaisesRegex(ValueError, 'artifact missing or changed'):
                    prepare(root, scope, out, 512)


if __name__ == '__main__':
    unittest.main()
