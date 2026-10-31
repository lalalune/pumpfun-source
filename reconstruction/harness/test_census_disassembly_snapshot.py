"""Real SBF disassembly must describe the image whose bytes were loaded."""
import gzip
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'reconstruction/pump-main/lanes/callgraph-census'))
import census


@unittest.skipUnless(os.environ.get('PUMP_OBJDUMP'), 'requires explicit SBF llvm-objdump')
class DisassemblySnapshotTests(unittest.TestCase):
    def test_replaced_and_removed_paths_preserve_loaded_argument_evidence(self):
        builds = ROOT / 'research/pump-multihop-sell-fees-20261029/build'
        parent = gzip.decompress((builds / 'parent/symbols.so.gz').read_bytes())
        candidate = gzip.decompress((builds / 'candidate/symbols.so.gz').read_bytes())
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / 'unstripped.so'
            path.write_bytes(parent)
            functions = {s: (n, [name]) for s, n, name in census.candidate_functions(path)}
            # The parent v3_buy_costs function has 17 internal calls. The child
            # artifact has different instructions at this same address range.
            start = 0x97d40
            reference = census.Image(path, functions)
            sites = [site for site, target in reference.calls(start) if isinstance(target, int)]
            self.assertEqual(len(sites), 17)
            expected = census.arg_setup(reference, start, sites)
            for mode in ('unchanged', 'replaced', 'deleted'):
                with self.subTest(mode=mode):
                    path.write_bytes(parent)
                    image = census.Image(path, functions)
                    if mode == 'replaced':
                        replacement = path.with_suffix('.next')
                        replacement.write_bytes(candidate)
                        replacement.replace(path)
                    elif mode == 'deleted':
                        path.unlink()
                    self.assertEqual(census.arg_setup(image, start, sites), expected)
                    self.assertEqual(image.blob, parent)
                    self.assertEqual(path.exists(), mode != 'deleted')
                    if path.exists():
                        self.assertEqual(path.read_bytes(), candidate if mode == 'replaced' else parent)


if __name__ == '__main__':
    unittest.main()
