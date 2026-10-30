"""Audit the nested receipt-log shape accepted by the strict ordered checker."""
import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pump_diagnostic_audit as gate


LEFT = 'Program log: AnchorError caused by account: user. Error Code: ConstraintOwner. Error Number: 2004. Error Message: An owner constraint was violated.'
RIGHT = LEFT.replace('2004', '2005')


class DiagnosticMetadataTests(unittest.TestCase):
    def test_concurrent_cli_publication_retains_one_complete_receipt(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / 'receipt.json', root / 'audit.json'
            raw = json.dumps({'suites': {'recorded': [self.pair()]}}).encode('utf-8')
            source.write_bytes(raw)
            command = [sys.executable, str(Path(gate.__file__).resolve()),
                       '--report', str(source), '--output', str(output)]
            # This fixture contains a real diagnostic mismatch, so the single
            # successful publisher returns 1 too. Publication losers must fail
            # specifically because the destination already exists.
            processes = [subprocess.Popen(command, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE) for _ in range(4)]
            results = [process.communicate(timeout=30) for process in processes]
            published = [i for i, (_, stderr) in enumerate(results) if not stderr]
            self.assertEqual(len(published), 1, results)
            self.assertEqual(processes[published[0]].returncode, 1)
            for i, process in enumerate(processes):
                if i != published[0]:
                    self.assertNotEqual(process.returncode, 0)
                    self.assertIn(b'FileExistsError', results[i][1])
            receipt = json.loads(output.read_bytes())
            self.assertEqual(receipt['source_report_sha256'], hashlib.sha256(raw).hexdigest())
            self.assertEqual(receipt['log_bearing_cases'], 1)
            self.assertEqual(len(receipt['mismatches']), 1)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(list(root.glob('.audit.json.*')), [])

    def pair(self, left=LEFT, right=RIGHT):
        return {'original': {'metadata': {'logs': [left]}},
                'candidate': {'metadata': {'logs': [right]}}}

    def test_nested_diagnostic_difference_is_not_skipped(self):
        report = gate.audit({'retained': [self.pair()]})
        self.assertEqual(report['log_bearing_cases'], 1)
        self.assertEqual(report['coverage'], {'retained': 1})
        self.assertEqual(len(report['mismatches']), 1)
        self.assertEqual(report['mismatches'][0]['original_logs'], [LEFT])
        self.assertEqual(report['mismatches'][0]['candidate_logs'], [RIGHT])

    def test_nested_and_flat_receipts_have_identical_results(self):
        nested = self.pair()
        flat = {side: {'logs': row['metadata']['logs']}
                for side, row in nested.items()}
        self.assertEqual(gate.audit({'suite': [nested]}), gate.audit({'suite': [flat]}))

    def test_direct_logs_including_empty_lists_remain_authoritative(self):
        pair = self.pair()
        for side in pair.values():
            side['logs'] = []
        self.assertEqual(gate.audit({'suite': [pair]})['log_bearing_cases'], 0)
        for side in pair.values():
            side['logs'] = [LEFT]
        self.assertEqual(gate.audit({'suite': [pair]})['mismatches'], [])
        self.assertEqual(gate.logs(pair['candidate']), [LEFT])

    def test_missing_or_non_log_metadata_does_not_add_coverage(self):
        for value in ({}, {'metadata': None}, {'metadata': []},
                      {'metadata': {'logs': 'not a log list'}},
                      {'metadata': {'logs': [None, 42]}}):
            with self.subTest(value=value):
                self.assertEqual(gate.logs(value), [])
        self.assertEqual(gate.logs({'metadata': {'logs': [None, LEFT]}}), [LEFT])

    def test_cli_rejects_nested_diagnostic_mismatch_and_preserves_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'receipt.json'
            output = Path(directory) / 'audit.json'
            raw = (json.dumps({'suites': {'recorded': [self.pair()]}}) + '\n').encode('utf-8')
            source.write_bytes(raw)
            command = [sys.executable, str(Path(gate.__file__).resolve()),
                       '--report', str(source), '--output', str(output)]
            result = subprocess.run(command, capture_output=True, encoding='utf-8')
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            report = json.loads(output.read_text(encoding='utf-8'))
            self.assertEqual(report['log_bearing_cases'], 1)
            self.assertEqual(len(report['mismatches']), 1)
            self.assertEqual(source.read_bytes(), raw)


if __name__ == '__main__':
    unittest.main()
