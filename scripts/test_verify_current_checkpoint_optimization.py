"""Regression checks for optimized-Python survival in the current-checkpoint verifier.

Sibling of tests/test_checkpoint_manifest_paths.py, which proves the
manifest seal/hash checks in verify_manifest survive -O because they raise
explicitly: the generic verify() path expressed its own binding checks --
candidate suffix, checkpoint membership, comparison-report path, selected
toolchain, toolchain command, helper transitions -- as bare asserts, so
under -O (or PYTHONOPTIMIZE=1) a report naming an unsupported toolchain
verified with PASS. The driver below builds an isolated checkpoint whose
manifest seal is computed from its own bytes (so the fixture is
self-consistent) and patches CHECKPOINTS to that seal, then runs verify()
under the requested interpreter mode.
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = Path(__file__).resolve().parent

DRIVER = r'''
import hashlib, json, sys, tempfile
from pathlib import Path
import verify_current_checkpoint as checkpoint

toolchain = sys.argv[1]
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    name = "repro/pump_fees/sharing-second-pump-cpi-main-v144"
    package = root / name
    (package / "main/controls").mkdir(parents=True)
    manifest_raw = b"{}\n"
    seal = hashlib.sha256(manifest_raw).hexdigest()
    (package / "manifest.json").write_bytes(manifest_raw)
    candidate = b"candidate-bytes\n"
    candidate_sha = hashlib.sha256(candidate).hexdigest()
    (package / "main/candidate.so").write_bytes(candidate)
    (package / "main/build-comparison.json").write_text(json.dumps({
        "selected_toolchain": toolchain,
        "command": ["build", "--tools-version", toolchain],
        "comparison": {"candidate_sha256": candidate_sha},
        "source_sha256": {},
    }))
    (package / "main/controls/gate-before.json").write_text(
        json.dumps({"helpers": {}}))
    (package / "verify.py").write_text("import sys; sys.exit(0)\n")
    (root / "repro/status.json").write_text(json.dumps({"pump_fees": {
        "candidate_artifact": name + "/main/candidate.so",
        "candidate_sha256": candidate_sha,
        "comparison_report": name + "/main/build-comparison.json",
    }}))
    checkpoint.CHECKPOINTS = {name: (seal, "helpers", None)}
    result = checkpoint.verify("pump_fees", root)
    print(json.dumps(result))
'''


def run_driver(toolchain, optimized):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(SCRIPTS)
    command = [sys.executable]
    if optimized:
        command.append("-O")
    command += ["-c", DRIVER, toolchain]
    return subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


class CurrentCheckpointOptimizationTests(unittest.TestCase):
    def test_optimized_python_rejects_unsupported_toolchain(self):
        completed = run_driver("v9.99", optimized=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("AssertionError", completed.stderr)

    def test_optimized_python_accepts_supported_toolchain(self):
        completed = run_driver("v1.44", optimized=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn('"status": "PASS"', completed.stdout)

    def test_normal_python_rejects_unsupported_toolchain(self):
        completed = run_driver("v9.99", optimized=False)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("AssertionError", completed.stderr)


if __name__ == "__main__":
    unittest.main()
