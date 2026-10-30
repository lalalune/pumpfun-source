"""Actual retained-packet and complete batch workflow regression."""
import json
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
            retained = {p.name: p.read_bytes() for p in (ROOT / ARCHIVE).iterdir() if p.is_file()}
            for kind in ['valid', 'array', 'directory']:
                folder = root / 'research' / kind
                folder.mkdir(parents=True)
                for name, raw in retained.items():
                    (folder / name).write_bytes(raw)
                if kind == 'array':
                    (folder / 'manifest.json').write_text('[]', encoding='utf-8')
                elif kind == 'directory':
                    (folder / 'README.md').unlink()
                    (folder / 'README.md').mkdir()
            old = subprocess.run([sys.executable, '-B', '-X', 'utf8',
                                  str(root / 'scripts/revalidate_all.py'), '--output', str(root / 'before')],
                                 cwd=root, capture_output=True, text=True, encoding='utf-8')
            self.assertNotEqual(old.returncode, 0)
            self.assertIn("has no attribute 'items'", old.stderr)
            output = root / 'after'
            fixed = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(PACKAGE / 'run.py'),
                                    '--repo', str(root), '--output', str(output)],
                                   cwd=root, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
            results = json.loads((output / 'results.json').read_text(encoding='utf-8'))
            by_name = {row['packet']: row for row in results}
            # This retained packet requires an explicit repository root for its
            # verifier. The archived batch runner supplies no --repo argument;
            # preserve that independently tracked failure and the current AND gate.
            self.assertEqual(by_name['valid']['manifest_check']['status'], 'pass')
            self.assertEqual(by_name['valid']['verify_check']['status'], 'fail')
            self.assertEqual({name: row['overall'] for name, row in by_name.items()},
                             {'valid': 'fail', 'array': 'fail', 'directory': 'fail'})
            self.assertEqual(by_name['array']['manifest_check']['status'], 'fail')
            self.assertEqual(by_name['array']['manifest_check']['files_checked'], 0)
            self.assertEqual(by_name['directory']['manifest_check']['status'], 'fail')
            self.assertEqual(by_name['valid']['manifest_check']['files_checked'], 7)
            self.assertEqual(by_name['directory']['manifest_check']['files_checked'], 6)
            self.assertEqual(by_name['directory']['manifest_check']['files_expected'], 7)
            verified = subprocess.run([sys.executable, '-B', '-X', 'utf8', str(output / 'verify.py')],
                                      capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            self.assertEqual(retained, {p.name: p.read_bytes() for p in (ROOT / ARCHIVE).iterdir() if p.is_file()})


if __name__ == '__main__':
    unittest.main()
