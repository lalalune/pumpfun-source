"""Exercise the saved-capture gate with a corrupted copy of a real capture."""
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENTRY = ROOT / "repro/capture-verification-mode/verify.py"


def run_verifier(script, flags=(), optimize=None):
    # Keep credentials and user Python startup settings out of this offline run.
    env = {key: os.environ[key] for key in
           ("PATH", "SystemRoot", "TEMP", "TMP") if key in os.environ}
    env["PYTHONUTF8"] = "1"
    if optimize is not None:
        env["PYTHONOPTIMIZE"] = optimize
    return subprocess.run(
        [sys.executable, "-B", *flags, str(script)],
        env=env, capture_output=True, text=True, encoding="utf-8", timeout=30,
    )


class SavedEvidenceTests(unittest.TestCase):
    def test_original_snapshot_passes(self):
        result = run_verifier(ENTRY)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("9 captures verified; no source rebuild claimed.", result.stdout)

    def test_bad_payload_cannot_pass_in_any_python_mode(self):
        with tempfile.TemporaryDirectory(prefix="pump-evidence-verifier-") as directory:
            fixture = pathlib.Path(directory)
            shutil.copytree(ROOT / "evidence", fixture / "evidence")
            (fixture / "scripts").mkdir()
            for name in ("verify_evidence.py", "capture.py", "analyze.py"):
                shutil.copy2(ROOT / "scripts" / name, fixture / "scripts" / name)
            wrapper = fixture / "repro/capture-verification-mode/verify.py"
            wrapper.parent.mkdir(parents=True)
            shutil.copy2(ENTRY, wrapper)
            payload = fixture / "evidence/original/pump/deployed.so"
            damaged = bytearray(payload.read_bytes())
            # Offset 0x1000 is within the captured Pump .text section, not a header.
            damaged[0x1000] ^= 1
            payload.write_bytes(damaged)
            for flags, optimize in (((), None), (("-O",), None),
                                    (("-OO",), None), ((), "1"), ((), "2")):
                with self.subTest(flags=flags, optimize=optimize):
                    result = run_verifier(wrapper, flags, optimize)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertNotIn("captures verified", result.stdout)

    def test_optimized_mode_gives_a_recovery_instruction(self):
        result = run_verifier(ENTRY, ("-O",))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("PYTHONOPTIMIZE", result.stderr)
        self.assertIn("-O", result.stderr)


if __name__ == "__main__":
    unittest.main()
