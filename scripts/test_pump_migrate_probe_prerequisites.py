#!/usr/bin/env python3
"""The legacy migrate probe's control case must reach a successful captured migrate."""
import contextlib
import io
from pathlib import Path
import runpy
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import probe_report  # noqa: E402


class PrerequisiteCasesTests(unittest.TestCase):
    def published_rows(self):
        reports = []
        with mock.patch.object(probe_report, 'write_json_report',
                               lambda path, rows: reports.append((Path(path), rows))), \
                contextlib.redirect_stdout(io.StringIO()):
            runpy.run_path(str(ROOT / 'scripts/pump_migrate_probe.py'), run_name='__main__')
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0][0], ROOT / 'work/pump-migrate-recovery/prerequisites.json')
        return reports[0][1]

    def test_control_succeeds_and_the_incomplete_curve_alone_fails(self):
        rows = self.published_rows()
        control = rows[0]
        self.assertIsNone(control['error'], control['logs'][-4:])
        incomplete = next(row for row in rows if row['case'].get('complete') == 0)
        self.assertIn('InstructionErrorCustom(6006)', incomplete['error'])


if __name__ == '__main__':
    unittest.main()
