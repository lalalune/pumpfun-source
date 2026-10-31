"""Real 192-case CLI controls for fresh-only virtual reserve report publication."""
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
SCRIPT = 'pump_virtual_reserve_differential.py'
DATA = (
    'evidence/original/pump/deployed.so',
    'scripts/fixtures/signer_stub.so',
    'evidence/dependencies/spl_token_2022/deployed.so',
    'evidence/dependencies/associated_token/deployed.so',
    'research/imported-lab/analysis/pump_fun/config-snapshot.json',
)
DRIVER = r'''
import os,sys
from pathlib import Path
root,output,mode=sys.argv[1:];root=Path(root);output=Path(output)
sys.path.insert(0,str(root/'scripts'))
import pump_virtual_reserve_differential as module
import pump_differential_output as publisher
full_cases=module.cases
module.cases=lambda:list(full_cases())[:2]
real_fsync=publisher.os.fsync
def fsync(fd):
    (root/'publication-reached').write_text(mode)
    real_fsync(fd)
    if mode=='fsync':raise OSError('controlled fsync failure')
    if mode=='late-file':output.write_bytes(b'concurrent receipt')
    if mode=='late-alias':os.link(root/'candidate.so',output)
publisher.os.fsync=fsync
if mode=='link':
    def fail_link(*args,**kwargs):raise OSError('controlled link failure')
    publisher.os.link=fail_link
sys.argv=[str(root/'scripts'/'pump_virtual_reserve_differential.py'),'--candidate',str(root/'candidate.so'),'--output',str(output)]
raise SystemExit(module.main())
'''


class PumpVirtualReserveReportPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='virtual-reserve-pub-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        (self.root / 'scripts').mkdir()
        for path in (ROOT / 'scripts').glob('*.py'):
            shutil.copyfile(path, self.root / 'scripts' / path.name)
        for relative in DATA:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        shutil.copyfile(self.root / DATA[0], self.root / 'candidate.so')
        self.inputs = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in self.root.rglob('*') if p.is_file()}

    def invoke(self, output, control=None):
        env = dict(os.environ)
        env.pop('PYTHONOPTIMIZE', None)
        command = ([sys.executable, '-B', '-c', DRIVER, str(self.root), str(output), control]
                   if control else [sys.executable, '-B', str(self.root / 'scripts' / SCRIPT),
                                    '--candidate', str(self.root / 'candidate.so'), '--output', str(output)])
        return subprocess.run(command, cwd=self.root, env=env, text=True,
                              capture_output=True, timeout=300)

    def assert_inputs_retained(self):
        self.assertEqual(self.inputs, {p: hashlib.sha256(p.read_bytes()).hexdigest()
                                       for p in self.inputs})

    def test_full_plain_and_gzip_corpora_are_equal(self):
        plain = self.root / 'nested/report.json'
        zipped = self.root / 'nested/report.json.gz'
        for output in (plain, zipped):
            result = self.invoke(output)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        raw, encoded = plain.read_bytes(), zipped.read_bytes()
        self.assertEqual(gzip.decompress(encoded), raw)
        self.assertEqual(encoded[4:8], b'\0' * 4)
        report = json.loads(raw)
        self.assertEqual(report['case_count'], 192)
        self.assertEqual(len(report['cases']), 192)
        self.assertEqual(report['mismatches'], [])
        self.assert_inputs_retained()
        proof = os.environ.get('PUMP_PUBLICATION_PROOF_OUT')
        if proof:
            destination = Path(proof)
            destination.mkdir(parents=True, exist_ok=True)
            for output in (plain, zipped):
                shutil.copyfile(output, destination / output.name)

    def test_wrong_real_image_retains_complete_failed_report(self):
        candidate = self.root / 'candidate.so'
        shutil.copyfile(ROOT / 'evidence/original/mayhem/deployed.so', candidate)
        output = self.root / 'failed.json'
        result = self.invoke(output)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads(output.read_bytes())
        self.assertEqual(report['case_count'], 192)
        self.assertEqual(len(report['cases']), 192)
        self.assertTrue(report['mismatches'])
        self.assertEqual(report['candidate_sha256'], hashlib.sha256(candidate.read_bytes()).hexdigest())

    def test_existing_input_aliases_are_refused_before_execution(self):
        protected = [self.root / relative for relative in DATA] + [self.root / 'candidate.so']
        protected += [self.root / 'scripts' / name for name in
                      (SCRIPT, 'pump_differential_output.py', 'pump_amm_reusable_harness.py',
                       'pump_set_mayhem_virtual_params_differential.py', 'build_source_manifest.py')]
        for source in protected:
            for kind in ('direct', 'symlink', 'hardlink'):
                with self.subTest(source=source.name, kind=kind):
                    output = source
                    if kind != 'direct':
                        output = self.root / 'alias-output'
                        output.unlink(missing_ok=True)
                        if kind == 'symlink':
                            output.symlink_to(source)
                        else:
                            os.link(source, output)
                    result = self.invoke(output)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertTrue(
                        'report output aliases an input' in result.stderr or
                        'choose a fresh path' in result.stderr or
                        'output must be fresh' in result.stderr
                    )
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), self.inputs[source])
        self.assert_inputs_retained()

    def test_failed_staging_and_late_collisions_preserve_inputs(self):
        controls = ['fsync', 'late-file', 'late-alias']
        if os.name != 'nt':
            controls.append('link')
        for mode in controls:
            with self.subTest(mode=mode):
                output = self.root / (mode + '.json')
                result = self.invoke(output, control=mode)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertEqual((self.root / 'publication-reached').read_text(), mode)
                if mode == 'late-file':
                    self.assertEqual(output.read_bytes(), b'concurrent receipt')
                    self.assertIn('output must be fresh', result.stderr)
                elif mode == 'late-alias':
                    self.assertTrue(output.samefile(self.root / 'candidate.so'))
                    self.assertIn('report output aliases an input', result.stderr)
                else:
                    self.assertFalse(os.path.lexists(output))
                    self.assertIn('controlled ' + mode + ' failure', result.stderr)
                self.assertEqual(list(self.root.glob('.' + output.name + '.*')), [])
                self.assert_inputs_retained()


if __name__ == '__main__':
    unittest.main()
