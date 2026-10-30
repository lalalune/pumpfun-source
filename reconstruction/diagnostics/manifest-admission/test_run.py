"""Actual retained-packet and complete batch workflow regression."""
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
ARCHIVE = 'research/tooling-roadmap-call-classification-20261029'


class ManifestAdmissionTests(unittest.TestCase):
    def test_actual_packet_batch_rejects_bad_shapes_without_aborting(self):
        with tempfile.TemporaryDirectory(prefix='pump-manifest-admission-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-manifest-admission-'))
            for name in ['revalidate_all.py', 'reconstruction_roadmap.py', 'window_elf_reader.py']:
                target = root / 'scripts' / name
                target.parent.mkdir(exist_ok=True)
                shutil.copyfile(ROOT / 'scripts' / name, target)
            for name in ['pump', 'pump_amm', 'mayhem']:
                target = root / f'evidence/original/{name}/deployed.so'
                target.parent.mkdir(parents=True)
                shutil.copyfile(ROOT / f'evidence/original/{name}/deployed.so', target)
            # The retained packet gained an archived/ subtree; copy it whole so
            # the manifest can still resolve every entry it declares.
            retained = {p.relative_to(ROOT / ARCHIVE).as_posix(): p.read_bytes()
                        for p in (ROOT / ARCHIVE).rglob('*') if p.is_file()}
            for kind in ['valid', 'array', 'directory']:
                folder = root / 'research' / kind
                folder.mkdir(parents=True)
                for name, raw in retained.items():
                    (folder / name).parent.mkdir(parents=True, exist_ok=True)
                    (folder / name).write_bytes(raw)
                if kind == 'array':
                    (folder / 'manifest.json').write_text('[]', encoding='utf-8')
                elif kind == 'directory':
                    (folder / 'README.md').unlink()
                    (folder / 'README.md').mkdir()
            # The retained batch runner used to abort the whole batch on a
            # non-object manifest with AttributeError; it now records that packet
            # as a manifest_parse_error failure and keeps judging the rest.
            old = subprocess.run([sys.executable, '-B', '-X', 'utf8',
                                  str(root / 'scripts/revalidate_all.py'), '--output', str(root / 'before')],
                                 cwd=root, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(old.returncode, 0, old.stdout + old.stderr)
            early = json.loads((root / 'before/results.json').read_text(encoding='utf-8'))
            self.assertEqual({row['packet']: row['overall'] for row in early},
                             {'valid': 'fail', 'array': 'fail', 'directory': 'fail'})
            self.assertEqual({row['packet']: row['manifest_check']['status'] for row in early},
                             {'valid': 'pass', 'array': 'manifest_parse_error', 'directory': 'fail'})
            output = root / 'after'
            fixed = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(PACKAGE / 'run.py'),
                                    '--repo', str(root), '--output', str(output)],
                                   cwd=root, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
            results = json.loads((output / 'results.json').read_text(encoding='utf-8'))
            by_name = {row['packet']: row for row in results}
            # These copies have new packet names, outside the maintained runner's
            # explicit --repo allowlist. Preserve their verifier failure and the
            # all-available-checks conjunction rather than treating manifest
            # integrity alone as complete packet acceptance.
            self.assertEqual(by_name['valid']['manifest_check']['status'], 'pass')
            self.assertEqual(by_name['valid']['verify_check']['status'], 'fail')
            self.assertEqual({name: row['overall'] for name, row in by_name.items()},
                             {'valid': 'fail', 'array': 'fail', 'directory': 'fail'})
            self.assertEqual(by_name['array']['manifest_check']['status'], 'fail')
            self.assertEqual(by_name['array']['manifest_check']['files_checked'], 0)
            self.assertEqual(by_name['directory']['manifest_check']['status'], 'fail')
            self.assertEqual(by_name['valid']['manifest_check']['files_checked'], 8)
            self.assertEqual(by_name['directory']['manifest_check']['files_checked'], 7)
            self.assertEqual(by_name['directory']['manifest_check']['files_expected'], 8)
            verified = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(output / 'verify.py')],
                                      capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            self.assertEqual(retained, {p.relative_to(ROOT / ARCHIVE).as_posix(): p.read_bytes()
                                        for p in (ROOT / ARCHIVE).rglob('*') if p.is_file()})


DRIVER = r'''
import importlib.util, sys, types
from pathlib import Path
package, root, output, mode = sys.argv[1:]
sys.path.insert(0, package)
spec = importlib.util.spec_from_file_location('manifest_runner', Path(package)/'run.py')
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)
source = (Path(root)/'scripts/revalidate_all.py').resolve()
if mode == 'source-swap':
    def create_module(name):
        source.write_text("raise RuntimeError('unreviewed source executed')\n")
        return types.ModuleType(name)
    runner.types = types.SimpleNamespace(ModuleType=create_module)
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_filename == str(source) and frame.f_code.co_name == 'write_reports':
        sys.setprofile(None)
        if mode == 'late-directory':
            Path(output).mkdir()
        elif mode == 'write-failure':
            raise OSError('controlled report publication failure')
if mode in ('late-directory', 'write-failure'):
    sys.setprofile(hook)
sys.argv = [str(Path(package)/'run.py'), '--repo', root, '--output', output]
try:
    runner.main()
finally:
    sys.setprofile(None)
'''


class ManifestCliControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='manifest-controls-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = self.root/'scripts/revalidate_all.py'
        source.parent.mkdir()
        shutil.copyfile(ROOT/'scripts/revalidate_all.py', source)
        self.source = source
        packet = self.root/'research/valid-control'
        packet.mkdir(parents=True)
        payloads = {'payload.txt': b'fixed fixture bytes', 'verify.py': b'print("fixture verification passed")\n'}
        for name, raw in payloads.items():
            (packet/name).write_bytes(raw)
        (packet/'manifest.json').write_text(json.dumps({name:hashlib.sha256(raw).hexdigest() for name,raw in payloads.items()}))
        self.packet = packet
        self.output = self.root/'audit'
        self.inputs = {p:p.read_bytes() for p in self.root.rglob('*') if p.is_file()}

    def command(self):
        return [sys.executable, '-B', str(PACKAGE/'run.py'), '--repo', str(self.root), '--output', str(self.output)]

    def invoke(self, mode):
        return subprocess.run([sys.executable, '-B', '-c', DRIVER, str(PACKAGE), str(self.root), str(self.output), mode],
                              capture_output=True, text=True, timeout=60)

    def assert_inputs_unchanged(self):
        for path, raw in self.inputs.items():
            self.assertEqual(path.read_bytes(), raw, str(path))

    def test_actual_positive_batch_and_receipt_verifier(self):
        result = subprocess.run(self.command(), capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        summary = json.loads((self.output/'summary.json').read_text())
        self.assertEqual((summary['pass'], summary['fail'], summary['total_packets']), (1,0,1))
        rows = json.loads((self.output/'results.json').read_text())
        self.assertEqual(rows[0]['manifest_check']['files_checked'],2)
        self.assertEqual(rows[0]['verify_check']['status'],'pass')
        checked = subprocess.run([sys.executable, '-B', str(self.output/'verify.py')], capture_output=True, text=True)
        self.assertEqual(checked.returncode,0,checked.stdout+checked.stderr)
        prior = {p.name:p.read_bytes() for p in self.output.iterdir()}
        again = subprocess.run(self.command(), capture_output=True, text=True)
        self.assertNotEqual(again.returncode,0)
        self.assertEqual(prior,{p.name:p.read_bytes() for p in self.output.iterdir()})
        self.assert_inputs_unchanged()

    def test_changed_revalidator_rejected_without_publication(self):
        self.source.write_bytes(self.source.read_bytes()+b'\n# changed source\n')
        result = subprocess.run(self.command(), capture_output=True, text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('reviewed revalidator source changed',result.stderr)
        self.assertFalse(self.output.exists())

    def test_admitted_source_survives_public_path_replacement(self):
        result = self.invoke('source-swap')
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('unreviewed source executed',self.source.read_text())
        self.assertEqual(json.loads((self.output/'summary.json').read_text())['pass'],1)

    def test_dangling_output_symlink_is_not_followed(self):
        target = self.root/'untouched-target'
        self.output.symlink_to(target, target_is_directory=True)
        result = subprocess.run(self.command(), capture_output=True, text=True)
        self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue(self.output.is_symlink())
        self.assertFalse(target.exists())
        self.assert_inputs_unchanged()

    def test_late_empty_directory_is_preserved(self):
        result = self.invoke('late-directory')
        self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertTrue(self.output.is_dir())
        self.assertEqual(list(self.output.iterdir()),[])
        self.assertEqual(list(self.root.glob('.audit.staging-*')),[])
        self.assert_inputs_unchanged()

    def test_staging_failure_publishes_nothing(self):
        result = self.invoke('write-failure')
        self.assertNotEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertIn('controlled report publication failure',result.stderr)
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.root.glob('.audit.staging-*')),[])
        self.assert_inputs_unchanged()


if __name__ == '__main__':
    unittest.main()
