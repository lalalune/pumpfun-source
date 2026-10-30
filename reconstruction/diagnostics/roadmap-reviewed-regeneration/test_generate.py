"""Actual archived-generator and guarded-generator source-admission regression."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
PACKAGE = Path(__file__).resolve().parent
ARCHIVE = Path('research/tooling-roadmap-call-classification-20261029')


class ReviewedRegenerationTests(unittest.TestCase):
    def layout(self, root):
        for relative in [Path('scripts/reconstruction_roadmap.py'), Path('scripts/window_elf_reader.py')]:
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        shutil.copytree(ROOT / ARCHIVE, root / ARCHIVE,
                        ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        for name in ['pump', 'pump_amm', 'mayhem']:
            relative = Path(f'evidence/original/{name}/deployed.so')
            target = root / relative
            target.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / relative, target)

    def run_python(self, *args, cwd):
        return subprocess.run([sys.executable, '-B', '-X', 'utf8', *map(str, args)],
                              cwd=cwd, capture_output=True, text=True, encoding='utf-8')

    def test_changed_crlf_source_is_not_self_authorizing(self):
        with tempfile.TemporaryDirectory(prefix='pump-roadmap-admission-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-roadmap-admission-'))
            self.layout(root)
            source = root / 'scripts/reconstruction_roadmap.py'
            changed = source.read_bytes().replace(b'\r\n', b'\n') + b'\n# Not a reviewed source revision.\n'
            source.write_bytes(changed.replace(b'\n', b'\r\n'))
            # Actual legacy generator silently admits this unreviewed CRLF input.
            old = self.run_python(root / ARCHIVE / 'proof.py', cwd=root)
            self.assertEqual(old.returncode, 0, old.stdout + old.stderr)
            output = root / 'guarded'
            fixed = self.run_python(PACKAGE / 'generate.py', '--repo', root, '--output', output, cwd=root)
            self.assertNotEqual(fixed.returncode, 0)
            self.assertIn('unreviewed source: scripts/reconstruction_roadmap.py', fixed.stderr)
            self.assertFalse(output.exists())

    def test_reviewed_lf_and_crlf_keep_real_analysis_and_prior_packet(self):
        with tempfile.TemporaryDirectory(prefix='pump-roadmap-admission-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-roadmap-admission-'))
            self.layout(root)
            prior = {p.relative_to(root / ARCHIVE).as_posix(): p.read_bytes()
                     for p in (root / ARCHIVE).rglob('*') if p.is_file()}
            for form in ['lf', 'crlf']:
                source = root / 'scripts/reconstruction_roadmap.py'
                raw = source.read_bytes().replace(b'\r\n', b'\n')
                source.write_bytes(raw if form == 'lf' else raw.replace(b'\n', b'\r\n'))
                output = root / form
                fixed = self.run_python(PACKAGE / 'generate.py', '--repo', root, '--output', output, cwd=root)
                self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
                report = json.loads((output / 'observations.json').read_text(encoding='utf-8'))
                self.assertEqual(report['totals']['call_sites'], 23160)
                bindings = json.loads((output / 'inputs.json').read_text(encoding='utf-8'))
                self.assertEqual(bindings['scripts/reconstruction_roadmap.py'], hashlib.sha256(source.read_bytes()).hexdigest())
                manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
                self.assertEqual(set(manifest), {'observations.json', 'inputs.json'})
                for name, digest in manifest.items():
                    self.assertEqual(hashlib.sha256((output / name).read_bytes()).hexdigest(), digest)
            self.assertEqual(prior, {p.relative_to(root / ARCHIVE).as_posix(): p.read_bytes()
                                    for p in (root / ARCHIVE).rglob('*') if p.is_file()})


if __name__ == '__main__':
    unittest.main()
