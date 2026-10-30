"""Exercise serial publication admission before any real suite can start."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import pump_validate_all as runner


class SerialInputPreservationTests(unittest.TestCase):
    def test_serial_cli_preserves_inputs_before_first_suite(self):
        # Run the real 44-suite entry point unchanged. Admission must stop it
        # before loading a VM, including when the collision is in a late suite.
        captured = (ROOT / 'evidence/original/pump/deployed.so').read_bytes()
        for kind in ('aggregate', 'first-sidecar', 'last-sidecar', 'source'):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                candidate = root / 'candidate.so'
                candidate.write_bytes(captured)
                source = root / 'target' / 'source'
                source.mkdir(parents=True)
                source_file = source / 'lib.rs'
                source_file.write_text('// source input\n')
                output = root / 'result.json.gz'
                if kind == 'aggregate':
                    output = candidate
                elif kind == 'source':
                    output = source_file
                else:
                    name = runner.SUITES[0 if kind == 'first-sidecar' else -1][0]
                    sidecar = root / (output.name + '.suites') / (name + '.json.gz')
                    sidecar.parent.mkdir()
                    os.link(candidate, sidecar)
                before = {path: path.read_bytes() for path in (candidate, source_file)}
                existing = set(root.rglob('*'))
                result = subprocess.run(
                    [sys.executable, '-B', str(ROOT / 'scripts/pump_validate_all.py'),
                     '--candidate', str(candidate), '--source-directory', str(source),
                     '--output', str(output)], capture_output=True, text=True, timeout=30)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('validation output aliases a bound input', result.stderr)
                self.assertEqual(result.stdout, '')
                self.assertEqual(set(root.rglob('*')), existing)
                for path, contents in before.items():
                    self.assertEqual(path.read_bytes(), contents)


if __name__ == "__main__":
    unittest.main()
