#!/usr/bin/env python3
"""Imported-lab import checks must hold in every optimization mode.

scripts/verify_imported_lab.py expressed its import-integrity checks as
bare asserts: the import-manifest file hashes, the original-binary
correspondence, and the surfpool version pin. `python -O` / `-OO` and
PYTHONOPTIMIZE strip asserts, so a tampered imported file still exited 0
while the written report claimed `all_import_hashes_verified: true`.
The checks are now explicit raises, so the script keeps working under
optimized interpreters instead of refusing them.
"""

from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "verify_imported_lab.py"
VERIFIERS = [
    "pump_fun_verify_offline",
    "pump_fun_admin_surfpool_verify",
    "pump_fun_amm_v2_surfpool_verify",
    "pump_fun_curve_fresh_surfpool_verify",
    "pump_fun_curve_migration_surfpool_verify",
    "pump_fun_post_migration_amm_surfpool_verify",
    "pump_fun_fees_withdraw_surfpool_verify",
]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build_tree(root, tamper_manifest=False, tamper_binary=False):
    snapshot = root / "research" / "imported-lab"
    (snapshot / "scripts").mkdir(parents=True)
    (snapshot / "inputs" / "pump_fun").mkdir(parents=True)
    (snapshot / "analysis" / "pump_fun").mkdir(parents=True)
    (root / "scripts").mkdir(exist_ok=True)
    shutil.copy2(SCRIPTS / SCRIPT, root / "scripts" / SCRIPT)
    for name in VERIFIERS:
        (snapshot / "scripts" / f"{name}.py").write_text(
            "import sys\nsys.exit(0)\n", encoding="utf-8")
    blob = b"fake-program-bytes"
    for name in ("pump", "pump_amm", "pump_fees"):
        (snapshot / f"inputs/pump_fun/{name}.so").write_bytes(blob)
        original = root / "evidence" / "original" / name
        original.mkdir(parents=True)
        tampered = tamper_binary and name == "pump"
        (original / "deployed.so").write_bytes(
            b"other-bytes" if tampered else blob)
    notes = b"lab notes"
    (snapshot / "notes.txt").write_bytes(notes)
    files = [
        {"path": "notes.txt",
         "sha256": sha(b"tampered-notes") if tamper_manifest else sha(notes)},
        {"path": "inputs/pump_fun/pump.so", "sha256": sha(blob)},
    ]
    (root / "research" / "import-manifest.json").write_text(
        json.dumps({"commit": "abc123", "files": files}), encoding="utf-8")
    docs = root / "docsrepo"
    docs.mkdir()
    subprocess.run(["git", "init", "-q", str(docs)], check=True)
    subprocess.run(["git", "-C", str(docs), "config", "user.email", "t@t"],
                   check=True)
    subprocess.run(["git", "-C", str(docs), "config", "user.name", "t"],
                   check=True)
    (docs / "README").write_text("docs\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(docs), "add", "."], check=True)
    subprocess.run(["git", "-C", str(docs), "commit", "-qm", "docs"],
                   check=True)
    commit = subprocess.run(
        ["git", "-C", str(docs), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True).stdout.strip()
    (snapshot / "analysis" / "pump_fun" / "program-manifest.json").write_text(
        json.dumps({"official_docs_commit": commit}), encoding="utf-8")
    return docs


def run_script(root, docs, output, flags):
    return subprocess.run(
        [sys.executable, *flags, "-B",
         str(root / "scripts" / SCRIPT),
         "--docs-checkout", str(docs), "--output", str(output)],
        capture_output=True, text=True, check=False)


class ImportedLabOptimizationTests(unittest.TestCase):
    def test_tampered_manifest_fails_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory(
                    prefix="imported-lab-opt-") as temporary:
                root = Path(temporary) / "tree"
                root.mkdir()
                docs = build_tree(root, tamper_manifest=True)
                output = root / "out"
                result = run_script(root, docs, output, flags)
                self.assertNotEqual(result.returncode, 0, result.stderr[-500:])
                self.assertFalse(
                    (output / "integration-verification.json").exists(),
                    "tampered import must fail before any report is written")

    def test_mismatched_binary_fails_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory(
                    prefix="imported-lab-opt-") as temporary:
                root = Path(temporary) / "tree"
                root.mkdir()
                docs = build_tree(root, tamper_binary=True)
                output = root / "out"
                result = run_script(root, docs, output, flags)
                self.assertNotEqual(result.returncode, 0, result.stderr[-500:])
                self.assertFalse(
                    (output / "integration-verification.json").exists())

    def test_valid_import_passes_in_every_mode(self):
        for flags in ([], ["-O"], ["-OO"]):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory(
                    prefix="imported-lab-opt-") as temporary:
                root = Path(temporary) / "tree"
                root.mkdir()
                docs = build_tree(root)
                output = root / "out"
                result = run_script(root, docs, output, flags)
                self.assertEqual(result.returncode, 0,
                                 result.stdout[-500:] + result.stderr[-500:])
                report = json.loads(
                    (output / "integration-verification.json").read_text(
                        encoding="utf-8"))
                self.assertTrue(report["all_import_hashes_verified"])
                self.assertTrue(all(report["original_binary_matches"].values()))


if __name__ == "__main__":
    unittest.main()
