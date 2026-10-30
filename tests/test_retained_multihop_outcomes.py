"""Real archived correspondence and CLI controls, without a producer or VM."""
import base64
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'reconstruction/verification/retained_multihop_outcomes.py'
PACKET = ROOT / 'research/pump-multihop-sell-fees-20261029'
spec = importlib.util.spec_from_file_location('outcome_successor', SCRIPT)
successor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(successor)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes())


def save(path, value):
    raw = (json.dumps(value, indent=2) + '\n').encode()
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


def reseal(packet):
    path = packet / 'runtime/standard/execution.json'
    receipt = read(path)
    for name in receipt['output_files']:
        raw = (path.parent / name).read_bytes()
        receipt['output_files'][name] = dict(sha256=sha(raw), bytes=len(raw))
    save(path, receipt)
    save(packet / 'MANIFEST.json', {p.relative_to(packet).as_posix(): sha(p.read_bytes())
                                 for p in packet.rglob('*') if p.is_file() and p.name != 'MANIFEST.json'})


class ExactOutcomeTests(unittest.TestCase):
    def run_cli(self, packet):
        return subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(SCRIPT),
                               '--repo-root', str(ROOT), '--packet', str(packet)],
                              capture_output=True, text=True, encoding='utf-8')

    def copy_packet(self, temporary):
        packet = Path(temporary) / 'packet'
        shutil.copytree(PACKET, packet)
        return packet

    def test_optimized_public_apis_raise_value_error(self):
        code = '''
import importlib.util
from pathlib import Path
import sys
spec = importlib.util.spec_from_file_location('optimized_successor', sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    getattr(module, sys.argv[4])(Path(sys.argv[2]), Path(sys.argv[3]))
except ValueError as error:
    print(type(error).__name__ + ': ' + str(error))
else:
    raise RuntimeError('optimized API accepted archived evidence')
'''
        for entrypoint in ('verify', 'retained_runtime'):
            with self.subTest(entrypoint=entrypoint):
                result = subprocess.run(
                    [sys.executable, '-I', '-B', '-O', '-c', code,
                     str(SCRIPT), str(PACKET), str(ROOT), entrypoint],
                    capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('ValueError: Run without -O', result.stdout)

    def test_clean_current_cli_retains_all_archived_runtime_checks(self):
        result = self.run_cli(PACKET)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report['current_source_acceptance'])
        self.assertEqual(report['archived_runtime']['case_triples'], 16)
        self.assertEqual(report['archived_runtime']['verified_signatures'], 48)
        self.assertEqual(report['archived_runtime']['structured_or_ordered_log_mismatches'], 0)

    def test_resealed_real_error_code_lookalikes_are_rejected(self):
        for code in (16063, 60630):
            with self.subTest(code=code), tempfile.TemporaryDirectory(prefix='multihop-outcome-') as temporary:
                packet = self.copy_packet(temporary)
                path = packet / 'runtime/standard/regression-thirteen.json.gz'
                report = read(path)
                for run in report['cases'][2]['runs'].values():
                    run['error'] = run['error'].replace('Custom(6063)', f'Custom({code})')
                save(path, report)
                reseal(packet)
                prior = successor.retained_runtime(packet, ROOT)
                self.assertEqual(prior['verified_signatures'], 48)
                self.assertEqual(prior['structured_or_ordered_log_mismatches'], 0)
                self.assertIn(f'Custom({code})', prior['outcomes'][2]['error'])
                result = self.run_cli(packet)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('exact declared outcome: truncated_fee_config', result.stderr)

    def test_invalid_actual_signature_still_rejects_before_outcome_check(self):
        with tempfile.TemporaryDirectory(prefix='multihop-signature-') as temporary:
            packet = self.copy_packet(temporary)
            path = packet / 'runtime/standard/arithmetic-two.json.gz'
            report = read(path)
            row = report['cases'][0]
            for role, run in row['runs'].items():
                wire = bytearray(base64.b64decode(run['transaction_base64']))
                wire[1] ^= 1
                run['transaction_base64'] = base64.b64encode(wire).decode()
                run['transaction_sha256'] = sha(wire)
                row['observations'][role]['transaction_base64'] = run['transaction_base64']
            save(path, report)
            reseal(packet)
            result = self.run_cli(packet)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('verified canonical signed wire', result.stderr)

    def test_changed_archived_checker_is_not_executed(self):
        with tempfile.TemporaryDirectory(prefix='multihop-source-pin-') as temporary:
            packet = self.copy_packet(temporary)
            path = packet / 'correspondence.py'
            path.write_bytes(path.read_bytes() + b'\n# changed source\n')
            reseal(packet)
            result = self.run_cli(packet)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('archived verifier/input source binding: correspondence.py', result.stderr)


if __name__ == '__main__':
    unittest.main()
