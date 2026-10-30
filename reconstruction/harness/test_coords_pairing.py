"""Retained-input regression; no captured code executes."""
import unittest

class SourceCoordinatePairingTests(unittest.TestCase):
    def test_cli_keeps_reused_source_descriptors_at_their_own_lines(self):
        import json
        from pathlib import Path
        import shutil
        import subprocess
        import sys
        import tempfile

        repo = Path(__file__).resolve().parents[2]
        with tempfile.TemporaryDirectory(prefix='pump-coordinate-pairing-') as temporary:
            root = Path(temporary).resolve()
            self.assertTrue(root.name.startswith('pump-coordinate-pairing-'))
            (root / 'harness').mkdir()
            (root / 'base').mkdir()
            for name in ['coords.py', 'score.py']:
                shutil.copyfile(repo / 'reconstruction/harness' / name, root / 'harness' / name)
            shutil.copyfile(repo / 'evidence/original/pump/deployed.so', root / 'base/original.so')
            shutil.copyfile(repo / 'reconstruction/base/functions.tsv', root / 'base/functions.tsv')
            result = subprocess.run(
                [sys.executable, '-B', '-X', 'utf8', str(root / 'harness/coords.py'), 'window', '0x18678'],
                capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(result.returncode, 0, result.stderr)
            sites = {site['slot']: site for site in json.loads(result.stdout)}
            for length_slot, line_slot, line in [(4296, 4288, 466), (4520, 4512, 493)]:
                self.assertEqual(sites[length_slot]['path'], 'programs/pump/src/create_v2.rs')
                self.assertEqual(sites[length_slot]['line_slot'], line_slot)
                self.assertEqual(sites[length_slot]['line'], line)


if __name__ == '__main__': unittest.main()
