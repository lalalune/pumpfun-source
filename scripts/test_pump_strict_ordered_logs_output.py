#!/usr/bin/env python3
"""A finished strict-log audit must reach a report in a new folder."""
import contextlib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pump_strict_ordered_logs as gate  # noqa: E402


class StrictOrderedLogOutputTests(unittest.TestCase):
    def test_report_parent_is_created_after_the_audit(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / "candidate.so"
            candidate.write_bytes(b"candidate")
            report = root / "report.json"
            output = root / "new" / "nested" / "strict.json"
            report.write_text(json.dumps({
                "original_sha256": gate.ORIGINAL,
                "candidate_sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
                "case_count": 1,
                "suites": {"case": [{"original": {"logs": ["same"]},
                                      "candidate": {"logs": ["same"]}}]},
            }), encoding="utf-8")
            argv = ["pump_strict_ordered_logs.py", "--report", str(report),
                    "--candidate", str(candidate), "--output", str(output)]
            with mock.patch.object(sys, "argv", argv), \
                    contextlib.redirect_stdout(io.StringIO()):
                try:
                    gate.main()
                except FileNotFoundError as error:
                    self.fail(f"finished audit was lost: {error}")
            self.assertEqual(json.loads(output.read_text())["case_pairs"], 1)
            self.assertEqual(list(output.parent.glob(".strict.json.*")), [])


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/pump_strict_ordered_logs.py'


@unittest.skipUnless(os.name == 'posix', 'requires a POSIX filename component limit')
class LongOutputTests(unittest.TestCase):
    def test_long_output_preserves_audit_and_no_replace(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            limit = os.pathconf(directory, 'PC_NAME_MAX')
            if limit < 64:
                self.skipTest('unusually short filesystem component limit')
            output = directory / ('a' * (limit - len('.json')) + '.json')
            # Establish that the requested final path is supported independently
            # of the auditor's temporary-file naming scheme.
            output.write_bytes(b'filename control')
            output.unlink()
            candidate = ROOT / 'evidence/original/pump/deployed.so'
            original = candidate.read_bytes()
            digest = hashlib.sha256(original).hexdigest()
            fixture = json.loads((ROOT / 'tests/fixtures/strict-ordered-logs/set-params-rejection.json').read_bytes())
            self.assertEqual(digest, fixture['original_sha256'])
            report = directory / 'retained-control.json'
            report.write_text(json.dumps({
                'original_sha256': digest, 'candidate_sha256': digest,
                'case_count': 1, 'suites': {'retained-control': [{
                    'original': {'logs': fixture['logs']},
                    'candidate': {'logs': list(fixture['logs'])},
                }]},
            }), encoding='utf-8')
            before_report = report.read_bytes()
            command = [sys.executable, '-B', str(SCRIPT), '--report', str(report),
                       '--candidate', str(candidate), '--output', str(output),
                       '--expected-pairs', '1']
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            published = output.read_bytes()
            receipt = json.loads(published)
            self.assertEqual(receipt['case_pairs'], 1)
            self.assertEqual(receipt['strict_ordered_log_mismatch_cases'], 0)
            self.assertEqual(receipt['source_report_sha256'], hashlib.sha256(before_report).hexdigest())
            second = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(second.returncode, 0)
            self.assertEqual(output.read_bytes(), published)
            self.assertEqual(report.read_bytes(), before_report)
            self.assertEqual(candidate.read_bytes(), original)
            self.assertEqual(sorted(p.name for p in directory.iterdir()),
                             sorted([report.name, output.name]))


if __name__ == "__main__":
    unittest.main()
