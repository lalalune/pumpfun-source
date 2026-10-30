"""Path-boundary regressions for the current binding verifier."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import verify_current_bindings


class CurrentBindingsPathTests(unittest.TestCase):
    def test_verify_maps_rejects_symlinked_ancestor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            outside = root / "outside"
            outside.mkdir()
            data = b"tracked bytes\n"
            (outside / "input.py").write_bytes(data)
            os.symlink(outside, root / "alias", target_is_directory=True)
            tracked = {"alias/input.py"}
            groups = {"source": {"alias/input.py": hashlib.sha256(data).hexdigest()}}

            with self.assertRaisesRegex(AssertionError, "Symlink ancestry"):
                verify_current_bindings.verify_maps(root, groups, tracked)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs need POSIX")
    def test_fifo_input_is_rejected_without_blocking(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            os.mkfifo(root / "input.py")
            script = """
import importlib.util
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("verify_current_bindings", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
try:
    module.verify_maps(Path(sys.argv[2]),
                       {"source": {"input.py": "0" * 64}},
                       {"input.py"})
except AssertionError as error:
    if "Nonregular input" not in str(error):
        raise
else:
    raise SystemExit("a FIFO was accepted")
"""
            module = Path(__file__).resolve().parents[1] / "scripts/verify_current_bindings.py"
            try:
                result = subprocess.run(
                    [sys.executable, "-B", "-c", script, str(module), str(root)],
                    capture_output=True, text=True, timeout=3,
                )
            except subprocess.TimeoutExpired:
                self.fail("read_regular blocked on a FIFO")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
