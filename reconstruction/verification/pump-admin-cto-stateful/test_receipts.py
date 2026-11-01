"""Actual retained-byte admission and publication controls, using captured images."""
import base64
import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lifecycle as life
import verify as reader


class ActualReceiptAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = life.CAPTURED['pump_original']
        cls.report = life.run_suite(cls.candidate)
        cls.report['negative_controls'] = life.negative_control(cls.report)

    def test_genuine_twenty_transactions_are_distinct_and_admitted(self):
        self.assertEqual(reader.verify(self.report, self.candidate), [])
        for side in ('original', 'candidate'):
            rows = [r for case in self.report['cases'] for r in case[side]['receipts']]
            self.assertEqual((len(rows), len({r['signature'] for r in rows})), (20, 20))

    def test_empty_signature_bytes_cannot_use_cached_true_flags(self):
        report = copy.deepcopy(self.report)
        for side in ('original', 'candidate'):
            row = report['cases'][0][side]['receipts'][0]
            tx = life.Transaction.from_bytes(base64.b64decode(row['transaction_base64']))
            row['transaction_base64'] = base64.b64encode(bytes([0]) + bytes(tx.message)).decode()
        self.assertTrue(reader.verify(report, self.candidate))

    def test_snapshot_type_hash_continuity_and_rollback_are_recomputed(self):
        for mode in ('type', 'continuity', 'rollback', 'events'):
            report = copy.deepcopy(self.report)
            for side in ('original', 'candidate'):
                rows = report['cases'][0][side]['receipts']
                if mode == 'type':
                    account = next(a for a in rows[0]['before'].values() if a)
                    account['lamports'] = float(account['lamports'])
                elif mode == 'continuity':
                    rows[1]['before'][str(life.GLOBAL)]['lamports'] += 1
                    rows[1]['before_hash'] = life.canonical_hash(rows[1]['before'])
                elif mode == 'rollback':
                    row = next(r for r in rows if r['error'])
                    row['after'][str(life.GLOBAL)]['lamports'] += 1
                    row['after_hash'] = life.canonical_hash(row['after'])
                    row['rollback_nonfee_equal'] = True
                else:
                    next(r for r in rows if r['events'])['events'] = []
            with self.subTest(mode=mode):
                self.assertTrue(reader.verify(report, self.candidate))

    def test_replacing_candidate_after_snapshot_cannot_rebind_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'candidate.so'
            before = self.candidate.read_bytes()
            candidate.write_bytes(before)
            real = life.run_image
            def replace(*args, **kwargs):
                result = real(*args, **kwargs)
                candidate.write_bytes(b'changed after snapshot')
                return result
            with mock.patch.object(life, 'run_image', side_effect=replace):
                report = life.run_suite(candidate)
            self.assertEqual(report['program_sha256']['pump_candidate'], hashlib.sha256(before).hexdigest())
            self.assertEqual(report['mismatch_cases'], [])

    def test_staging_failure_and_concurrent_output_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'report.json.gz'
            with mock.patch('pump_differential_output.os.fsync', side_effect=OSError('injected fsync')):
                with self.assertRaises(OSError): life.write_report(output, self.report)
            self.assertFalse(output.exists())
            self.assertEqual(list(output.parent.glob('.report.json.gz.*')), [])
            real_link = sys.modules['pump_differential_output'].os.link
            def late(source, destination, *args, **kwargs):
                Path(destination).write_bytes(b'concurrent report')
                return real_link(source, destination, *args, **kwargs)
            with mock.patch('pump_differential_output.os.link', side_effect=late):
                with self.assertRaises(FileExistsError): life.write_report(output, self.report)
            self.assertEqual(output.read_bytes(), b'concurrent report')
            self.assertEqual(list(output.parent.glob('.report.json.gz.*')), [])


if __name__ == '__main__':
    unittest.main()
