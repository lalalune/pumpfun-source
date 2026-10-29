"""Path-boundary regressions for the current binding verifier."""
import hashlib
import os
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
