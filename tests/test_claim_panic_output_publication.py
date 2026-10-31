#!/usr/bin/env python3
"""The claim-panic diagnostic must publish safely without input corruption or replacement."""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/pump_claim_panic_differential.py'
CANDIDATE = ROOT / 'evidence/original/pump/deployed.so'
DATA = (
    'evidence/original/pump/deployed.so',
    'evidence/dependencies/spl_token_2022/deployed.so',
    'evidence/dependencies/associated_token/deployed.so',
    'research/imported-lab/analysis/pump_fun/curve-fresh-trades-v3-signed-surfpool.json',
    'evidence/upstream/pump.json',
)
DRIVER = r'''
import os,sys
from pathlib import Path
root,output,mode=sys.argv[1:];root=Path(root);output=Path(output)
sys.path.insert(0,str(root/'scripts'))
import pump_claim_panic_differential as module
import pump_differential_output as publisher
real_fsync=publisher.os.fsync
def fsync(fd):
    (root/'publication-reached').write_text(mode)
    real_fsync(fd)
    if mode=='fsync':raise OSError('controlled fsync failure')
    if mode=='late-file':output.write_bytes(b'concurrent receipt')
    if mode=='late-alias':os.link(root/'candidate.so',output)
publisher.os.fsync=fsync
if mode=='candidate-replaced':
    publisher.os.fsync=real_fsync
    real_capture=module.full_capture
    def capture():
        real_run,source=real_capture()
        count=0
        def run(binary,case):
            nonlocal count
            count+=1
            if count!=2:return real_run(binary,case)
            candidate=root/'candidate.so';original=candidate.read_bytes()
            candidate.write_bytes((root/'wrong.so').read_bytes())
            try:
                result=real_run(binary,case)
                (root/'replacement-reached').write_text('actual candidate VM executed')
                return result
            finally:candidate.write_bytes(original)
        return run,source
    module.full_capture=capture
if mode=='link':
    def fail_link(*args,**kwargs):raise OSError('controlled link failure')
    publisher.os.link=fail_link
sys.argv=[str(root/'scripts'/'pump_claim_panic_differential.py'),'--candidate',str(root/'candidate.so'),'--output',str(output)]
raise SystemExit(module.main())
'''


class ClaimPanicOutputPublicationTests(unittest.TestCase):
    def copy_inputs(self, root):
        (root / 'scripts').mkdir()
        for p in (ROOT / 'scripts').glob('*.py'):
            shutil.copyfile(p, root / 'scripts' / p.name)
        for relative in DATA:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        shutil.copyfile(root / DATA[0], root / 'candidate.so')

    def invoke(self, output, candidate=None):
        return subprocess.run(
            [sys.executable, '-B', str(SCRIPT), '--candidate', str(candidate or CANDIDATE),
             '--output', str(output)],
            capture_output=True, text=True, timeout=120)

    def test_dangling_symlink_target_is_not_created(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            escaped = root / 'escaped-report.gz'
            output = root / 'out.gz'
            try:
                output.symlink_to(escaped)
            except (OSError, NotImplementedError) as error:
                self.skipTest(f'symlinks are unavailable: {error}')
            result = self.invoke(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Retain prior diagnostic receipts', result.stderr)
            self.assertFalse(escaped.exists())
            self.assertTrue(output.is_symlink())

    def test_existing_receipt_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'report.gz'
            output.write_bytes(b'prior receipt\n')
            result = self.invoke(output)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Retain prior diagnostic receipts', result.stderr)
            self.assertEqual(output.read_bytes(), b'prior receipt\n')

    def test_fresh_output_receives_the_complete_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / 'report.gz'
            result = self.invoke(output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(output.read_bytes()[:2], b'\x1f\x8b')
            self.assertIn('"cases": 2', result.stdout)

    def test_plain_and_gzip_corpora_are_equal(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            plain = root / 'report.json'
            zipped = root / 'report.json.gz'
            for out in (plain, zipped):
                result = self.invoke(out)
                self.assertEqual(result.returncode, 0, result.stderr)
            raw, encoded = plain.read_bytes(), zipped.read_bytes()
            self.assertEqual(gzip.decompress(encoded), raw)
            self.assertEqual(encoded[4:8], b'\0' * 4)
            report = json.loads(raw)
            self.assertEqual(report['case_count'], 2)
            self.assertEqual(len(report['cases']), 2)
            self.assertEqual(report['mismatches'], [])

    def test_wrong_real_image_retains_failed_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wrong_candidate = ROOT / 'evidence/original/pump_fees/deployed.so'
            for suffix in ('.json', '.json.gz'):
                output = root / ('failed' + suffix)
                result = self.invoke(output, candidate=wrong_candidate)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                raw = output.read_bytes()
                report = json.loads(gzip.decompress(raw) if suffix.endswith('.gz') else raw)
                self.assertEqual(report['case_count'], 2)
                self.assertEqual(len(report['cases']), 2)
                self.assertEqual(report['candidate_sha256'], hashlib.sha256(wrong_candidate.read_bytes()).hexdigest())
                self.assertEqual(report['mismatches'], ['accrual-add-overflow', 'claimed-add-overflow'])
                for row in report['cases']:
                    self.assertIsNone(row['candidate_panic'])
                    self.assertIn('panic_message', row['differences'])
                    self.assertEqual(row['original_panic']['message'], row['expected_message'])

    def test_all_consumed_input_aliases_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copy_inputs(root)
            candidate = root / 'candidate.so'
            protected = [candidate] + [root / relative for relative in DATA]
            before = {path: path.read_bytes() for path in protected}
            for source in protected:
                for kind in ('direct', 'symlink', 'hardlink'):
                    with self.subTest(source=source.name, kind=kind):
                        output = source
                        if kind != 'direct':
                            output = root / 'alias-out'
                            output.unlink(missing_ok=True)
                            if kind == 'symlink':
                                output.symlink_to(source)
                            else:
                                os.link(source, output)
                        result = subprocess.run(
                            [sys.executable, '-B', str(root / 'scripts' / SCRIPT.name), '--candidate', str(candidate),
                             '--output', str(output)],
                            capture_output=True, text=True, timeout=30)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertTrue(
                            'Retain prior diagnostic receipts' in result.stderr or
                            'report output aliases an input' in result.stderr or
                            'choose a fresh path' in result.stderr or
                            'output must be fresh' in result.stderr
                        )
                        self.assertEqual({path: path.read_bytes() for path in protected}, before)

    def test_failed_staging_and_late_collisions_preserve_inputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.copy_inputs(root)
            protected = [root / 'candidate.so', *(root / relative for relative in DATA)]
            before = {path: path.read_bytes() for path in protected}
            controls = ['fsync', 'late-file', 'late-alias']
            if os.name != 'nt':
                controls.append('link')
            for mode in controls:
                with self.subTest(mode=mode):
                    output = root / (mode + '.json')
                    env = dict(os.environ)
                    env.pop('PYTHONOPTIMIZE', None)
                    result = subprocess.run(
                        [sys.executable, '-B', '-c', DRIVER, str(root), str(output), mode],
                        cwd=root, env=env, text=True, capture_output=True, timeout=120)
                    self.assertEqual({path: path.read_bytes() for path in protected}, before)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual((root / 'publication-reached').read_text(), mode)
                    if mode == 'late-file':
                        self.assertEqual(output.read_bytes(), b'concurrent receipt')
                        self.assertIn('output must be fresh', result.stderr)
                    elif mode == 'late-alias':
                        self.assertTrue(output.samefile(root / 'candidate.so'))
                        self.assertIn('report output aliases an input', result.stderr)
                    else:
                        self.assertFalse(os.path.lexists(output))
                        self.assertIn('controlled ' + mode + ' failure', result.stderr)

    def test_candidate_path_replacement_cannot_change_executed_snapshot(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            self.copy_inputs(root)
            shutil.copyfile(ROOT / 'evidence/original/pump_fees/deployed.so', root / 'wrong.so')
            candidate_bytes = (root / 'candidate.so').read_bytes()
            output = root / 'snapshot.json'
            result = subprocess.run(
                [sys.executable, '-B', '-c', DRIVER, str(root), str(output), 'candidate-replaced'],
                cwd=root, text=True, capture_output=True, timeout=120)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((root / 'replacement-reached').is_file())
            self.assertEqual((root / 'candidate.so').read_bytes(), candidate_bytes)
            report = json.loads(output.read_bytes())
            self.assertEqual(report['candidate_sha256'], hashlib.sha256(candidate_bytes).hexdigest())
            self.assertEqual(report['case_count'], 2)
            self.assertEqual(report['mismatches'], [])


if __name__ == '__main__':
    unittest.main()
