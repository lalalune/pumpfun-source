#!/usr/bin/env python3
"""A finished quote-control match must reach a report in a new folder."""
import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import pump_quote_control_function_match as matcher  # noqa: E402


class ReportParentTests(unittest.TestCase):
    def test_report_parent_is_created_after_the_analysis(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            candidate = folder / 'candidate.so'
            candidate.write_bytes(matcher.ORIGINAL.read_bytes())
            report = folder / 'new' / 'nested' / 'report.json'
            text = matcher.sections(candidate.read_bytes())['.text']
            argv = ['tool', str(candidate), '--objdump', 'not-executed',
                    '--output', str(report)]
            with mock.patch.object(sys, 'argv', argv), \
                    mock.patch.object(matcher, 'candidate_functions',
                                      return_value=[(text['addr'], 8, 'quote_control_entry')]), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    matcher.main()
                except FileNotFoundError as error:
                    self.fail(f'finished analysis was lost: {error}')
            self.assertEqual(json.loads(report.read_text())['functions'][0]['symbol'],
                             'quote_control_entry')


if __name__ == '__main__':
    unittest.main()
