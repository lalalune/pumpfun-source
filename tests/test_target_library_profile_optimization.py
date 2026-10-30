"""Regression checks for target-library admission under optimized Python.

validate_libraries() and specification() gate the "verified" target-library
profile: a tampered library set, a symlinked entry, or an unknown profile
name must be rejected in normal, -O, and -OO modes alike. Before this fix
every check was a bare assert, so under -O a tampered set was returned as
valid and an unknown profile name silently resolved to the sbf spec.
"""

from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

DRIVER = (
    "import sys, json\n"
    "from pathlib import Path\n"
    "from pump_target_library_profile import validate_libraries, specification\n"
    "case = sys.argv[1]\n"
    "if case == 'validate':\n"
    "    validate_libraries(Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()))\n"
    "elif case == 'spec':\n"
    "    specification(sys.argv[2])\n"
    "print('OK')\n"
)

MODES = ([], ["-O"], ["-OO"])


class TargetLibraryProfileOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.libs = self.root / "libs"
        self.libs.mkdir()
        (self.libs / "self-contained").mkdir()
        self.expected_path = self.root / "expected.json"

    def run_driver(self, optimization, case, *args):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, case, *args],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def write_expected(self, mapping):
        self.expected_path.write_text(json.dumps(mapping), encoding="utf-8")
        return str(self.expected_path)

    def test_wrong_library_hash_rejected_in_all_modes(self):
        (self.libs / "libfoo.rlib").write_bytes(b"tampered")
        expected = self.write_expected(
            {"libfoo.rlib": hashlib.sha256(b"admitted").hexdigest()})
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(
                    optimization, "validate", str(self.libs), expected)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn("target-library set or hashes differ",
                              completed.stderr)

    def test_symlinked_library_entry_rejected_in_all_modes(self):
        target = self.libs / "libfoo.rlib"
        target.write_bytes(b"admitted")
        (self.libs / "liblink.rlib").symlink_to(target)
        expected = self.write_expected(
            {"libfoo.rlib": hashlib.sha256(b"admitted").hexdigest()})
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(
                    optimization, "validate", str(self.libs), expected)
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn("symlinks", completed.stderr)

    def test_unknown_profile_name_rejected_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(
                    optimization, "spec", "bogus-profile")
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn("unknown target-library profile",
                              completed.stderr)

    def test_admitted_library_set_accepted_in_all_modes(self):
        (self.libs / "libfoo.rlib").write_bytes(b"admitted")
        expected = self.write_expected(
            {"libfoo.rlib": hashlib.sha256(b"admitted").hexdigest()})
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(
                    optimization, "validate", str(self.libs), expected)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
