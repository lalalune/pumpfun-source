import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location("retained_analysis", Path(__file__).with_name("generate.py"))
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def hashes(folder):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir()}


class RetentionTests(unittest.TestCase):
    def test_real_capture_packet_survives_a_different_program_request(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "analysis"
            legacy = Path(temporary) / "legacy"
            subprocess.run([sys.executable, "-E", "-X", "utf8", str(GEN.ROOT / "scripts/analyze_program.py"),
                            "--program", "mayhem", "--output", str(legacy)],
                           cwd=GEN.ROOT, capture_output=True, check=True)
            GEN.generate("mayhem", output)
            before = hashes(output)
            self.assertEqual(before, hashes(legacy))
            self.assertEqual(len(before), 8)
            summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["program"], "mayhem")
            self.assertGreater(summary["total_windows"], 0)
            self.assertEqual(summary["deployed_sha256"], hashlib.sha256(
                (GEN.ROOT / "evidence/original/mayhem/deployed.so").read_bytes()).hexdigest())
            with self.assertRaises(FileExistsError):
                GEN.generate("pump_fees", output)
            self.assertEqual(hashes(output), before)
            result = subprocess.run([sys.executable, "-E", "-X", "utf8", str(output / "verify.py")],
                                    capture_output=True, check=True)
            self.assertIn(b"All checks passed", result.stdout)

    def test_existing_file_and_empty_directory_are_retained(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "existing"
            output.write_bytes(b"older packet")
            with self.assertRaises(FileExistsError):
                GEN.generate("mayhem", output)
            self.assertEqual(output.read_bytes(), b"older packet")
            directory = Path(temporary) / "empty"
            directory.mkdir()
            with self.assertRaises(FileExistsError):
                GEN.generate("mayhem", directory)
            self.assertEqual(list(directory.iterdir()), [])

    def copied_helpers(self, root):
        (root / "scripts").mkdir()
        for name in GEN.HELPERS:
            shutil.copyfile(GEN.ROOT / name, root / name)

    def test_failed_actual_analysis_does_not_publish_or_leave_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copied_helpers(root)
            output = root / "analysis"
            # This repository-shaped copy deliberately has no captured program.
            with self.assertRaises(subprocess.CalledProcessError):
                GEN.generate("mayhem", output, root)
            self.assertFalse(output.exists())
            self.assertEqual(sorted(p.name for p in root.iterdir()), ["scripts"])

    def test_unreviewed_helper_is_rejected_before_generation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.copied_helpers(root)
            helper = root / "scripts/analyze_program.py"
            helper.write_bytes(helper.read_bytes() + b"\n# unreviewed drift\n")
            with self.assertRaisesRegex(ValueError, "Unreviewed"):
                GEN.generate("mayhem", root / "analysis", root)
            self.assertFalse((root / "analysis").exists())


if __name__ == "__main__":
    unittest.main()
