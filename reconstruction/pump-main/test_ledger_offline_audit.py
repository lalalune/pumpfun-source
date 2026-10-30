"""The saved-ledger audit never opens, seeds or locks the live ledger."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class OfflineLedgerAuditTests(unittest.TestCase):
    def audit(self,path,live,optimize=False):
        command = [sys.executable]+(['-O'] if optimize else [])+[str(Path(__file__).with_name('log_attempt.py')),'audit','--path',str(path)]
        return subprocess.run(command,env=dict(os.environ,PUMP_SWARM_LEDGER=str(live)),capture_output=True)

    def test_real_retained_snapshot_audits_without_live_ledger_side_effects(self):
        original = Path(__file__).with_name('ATTEMPTS.jsonl').read_bytes()
        for optimize in (False,True):
            with self.subTest(optimize=optimize), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                saved,live = root/'saved.jsonl',root/'live'/'ATTEMPTS.jsonl'
                saved.write_bytes(original)
                result = self.audit(saved,live,optimize)
                self.assertEqual(result.returncode,0,result.stderr.decode('utf-8',errors='replace'))
                report = json.loads(result.stdout)
                self.assertTrue(report['valid'])
                self.assertGreater(report['attempts'],1000)
                self.assertEqual(saved.read_bytes(),original)
                self.assertFalse(live.parent.exists())

    def test_malformed_and_missing_saved_inputs_report_errors_without_seeding(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            saved,live = root/'saved.jsonl',root/'live'/'ATTEMPTS.jsonl'
            saved.write_bytes(b'[]\n')
            result = self.audit(saved,live)
            self.assertEqual(result.returncode,1,result.stderr.decode('utf-8',errors='replace'))
            report = json.loads(result.stdout)
            self.assertFalse(report['valid'])
            self.assertEqual(report['errors'][0]['line'],1)
            self.assertEqual(saved.read_bytes(),b'[]\n')
            saved.unlink()
            result = self.audit(saved,live)
            self.assertEqual(result.returncode,2,result.stderr.decode('utf-8',errors='replace'))
            self.assertFalse(live.parent.exists())


if __name__ == '__main__': unittest.main()
