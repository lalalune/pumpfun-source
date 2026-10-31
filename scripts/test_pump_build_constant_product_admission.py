#!/usr/bin/env python3
"""The constant-product builder must read its inputs before claiming --output.

The output folder is created with exist_ok=False, so a folder left behind by a
run that could not start refuses the corrected rerun.
"""
import pathlib
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_pump_build_constant_product_binding import stage


def build(root, toolchain):
    return subprocess.run(
        [sys.executable, '-B', str(root / 'scripts/pump_build_constant_product.py'),
         '--toolchain', str(toolchain), '--output', str(root / 'out')],
        capture_output=True, text=True)


class OutputAdmissionTests(unittest.TestCase):
    def tree(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name) / 'tree'
        root.mkdir()
        return root, stage(root, mutate=False)

    def test_wrong_toolchain_path_leaves_the_output_free_for_a_rerun(self):
        root, toolchain = self.tree()
        self.assertNotEqual(build(root, root / 'mistyped').returncode, 0)
        self.assertFalse((root / 'out').exists())
        result = build(root, toolchain)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_capture_mismatch_does_not_claim_the_output(self):
        root, toolchain = self.tree()
        (root / 'evidence/original/pump/deployed.so').write_bytes(b'changed')
        self.assertNotEqual(build(root, toolchain).returncode, 0)
        self.assertFalse((root / 'out').exists())


if __name__ == '__main__':
    unittest.main()
