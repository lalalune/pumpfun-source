#!/usr/bin/env python3
"""The imported-lab manifest must cover exactly the files the verifier uses.

scripts/verify_imported_lab.py hash-checked only the files listed in
research/import-manifest.json, then executed the snapshot's verifier scripts
and trusted the docs commit named by the snapshot's program-manifest. When
the executed scripts, the program-manifest, or an extra shadowing module
were absent from the manifest, replacing them changed nothing the verifier
checked: a lab whose honest verifiers fail could be flipped to a published
report claiming all_import_hashes_verified and saved_receipt_verifiers_passed
by rewriting only unlisted files. The verifier now pins the manifest to the
exact snapshot file set before checking any hash.
"""

from pathlib import Path
import hashlib
import importlib.util
import os
import py_compile
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
SCRIPT = "verify_imported_lab.py"
# Sibling modules the script imports from scripts/ (atomic publication helpers).
HELPERS = ["deep_disassembly.py", "window_elf_reader.py", "analyze.py"]
VERIFIERS = [
    "pump_fun_verify_offline",
    "pump_fun_admin_surfpool_verify",
    "pump_fun_amm_v2_surfpool_verify",
    "pump_fun_curve_fresh_surfpool_verify",
    "pump_fun_curve_migration_surfpool_verify",
    "pump_fun_post_migration_amm_surfpool_verify",
    "pump_fun_fees_withdraw_surfpool_verify",
]
PASS = "import sys\nsys.exit(0)\n"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build_tree(root, omit=(), extra=None, tamper_listed_script=False):
    """Fixture import whose manifest lists every snapshot file, minus `omit`.

    `extra` maps an additional snapshot-relative path to its bytes; those
    files are created on disk but never listed in the manifest.
    """
    snapshot = root / "research" / "imported-lab"
    (snapshot / "scripts").mkdir(parents=True)
    (snapshot / "inputs" / "pump_fun").mkdir(parents=True)
    (snapshot / "analysis" / "pump_fun").mkdir(parents=True)
    (root / "scripts").mkdir(exist_ok=True)
    for name in (SCRIPT, *HELPERS):
        shutil.copy2(SCRIPTS / name, root / "scripts" / name)
    for name in VERIFIERS:
        (snapshot / "scripts" / f"{name}.py").write_text(PASS, encoding="utf-8")
    blob = b"fake-program-bytes"
    for name in ("pump", "pump_amm", "pump_fees"):
        (snapshot / f"inputs/pump_fun/{name}.so").write_bytes(blob)
        original = root / "evidence" / "original" / name
        original.mkdir(parents=True)
        (original / "deployed.so").write_bytes(blob)
    (snapshot / "notes.txt").write_bytes(b"lab notes")
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
    if extra:
        for relative, data in extra.items():
            target = snapshot / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    unlisted = set(omit) | set(extra or ())
    files = []
    for path in sorted(p for p in snapshot.rglob("*") if p.is_file()):
        relative = path.relative_to(snapshot).as_posix()
        if relative in unlisted:
            continue
        data = path.read_bytes()
        if tamper_listed_script and relative == "scripts/pump_fun_verify_offline.py":
            data = b"import sys\nsys.exit(1)\n"
        files.append({"path": relative, "sha256": sha(data)})
    (root / "research" / "import-manifest.json").write_text(
        json.dumps({"commit": "abc123", "files": files}), encoding="utf-8")
    return docs


def run_script(root, docs, output):
    return subprocess.run(
        [sys.executable, "-B", str(root / "scripts" / SCRIPT),
         "--docs-checkout", str(docs), "--output", str(output)],
        capture_output=True, text=True, check=False)


class ImportedLabCoverageTests(unittest.TestCase):
    def build_and_run(self, temporary, **kwargs):
        root = Path(temporary) / "tree"
        root.mkdir()
        docs = build_tree(root, **kwargs)
        return root, run_script(root, docs, root / "out")

    def test_complete_manifest_passes(self):
        with tempfile.TemporaryDirectory(prefix="imported-lab-cov-") as temporary:
            root, result = self.build_and_run(temporary)
            self.assertEqual(result.returncode, 0,
                             result.stdout[-500:] + result.stderr[-500:])
            report = json.loads(
                (root / "out" / "integration-verification.json").read_text(
                    encoding="utf-8"))
            self.assertTrue(report["all_import_hashes_verified"])
            self.assertTrue(report["saved_receipt_verifiers_passed"])

    def test_unlisted_executed_script_fails(self):
        with tempfile.TemporaryDirectory(prefix="imported-lab-cov-") as temporary:
            root, result = self.build_and_run(
                temporary, omit={"scripts/pump_fun_verify_offline.py"})
            self.assertNotEqual(result.returncode, 0, result.stdout[-500:])
            self.assertIn("pump_fun_verify_offline", result.stderr)
            self.assertFalse((root / "out").exists())

    def test_unlisted_program_manifest_fails(self):
        with tempfile.TemporaryDirectory(prefix="imported-lab-cov-") as temporary:
            root, result = self.build_and_run(
                temporary, omit={"analysis/pump_fun/program-manifest.json"})
            self.assertNotEqual(result.returncode, 0, result.stdout[-500:])
            self.assertIn("program-manifest", result.stderr)
            self.assertFalse((root / "out").exists())

    def test_extra_unlisted_file_fails(self):
        with tempfile.TemporaryDirectory(prefix="imported-lab-cov-") as temporary:
            root, result = self.build_and_run(
                temporary,
                extra={"scripts/json.py": b"# shadow\n"})
            self.assertNotEqual(result.returncode, 0, result.stdout[-500:])
            self.assertIn("json.py", result.stderr)
            self.assertFalse((root / "out").exists())

    def test_tampered_listed_script_still_fails(self):
        with tempfile.TemporaryDirectory(prefix="imported-lab-cov-") as temporary:
            root, result = self.build_and_run(
                temporary, tamper_listed_script=True)
            self.assertNotEqual(result.returncode, 0, result.stdout[-500:])
            self.assertFalse((root / "out").exists())


class SnapshotAdmissionControls(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='snapshot-admission-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.docs = build_tree(self.root)
        self.snapshot = self.root / 'research/imported-lab'
        self.manifest = self.root / 'research/import-manifest.json'
        self.marker = self.root / 'executed-marker'
        for name in VERIFIERS:
            (self.snapshot / 'scripts' / (name + '.py')).write_text(
                f'from pathlib import Path\nPath({str(self.marker)!r}).write_text("executed")\n')
        self.repin()

    def repin(self):
        document = json.loads(self.manifest.read_text())
        document['files'] = [
            {'path': path.relative_to(self.snapshot).as_posix(), 'sha256': sha(path.read_bytes())}
            for path in sorted(self.snapshot.rglob('*'))
            if path.is_file() and '__pycache__' not in path.parts]
        self.manifest.write_text(json.dumps(document))

    def refuse(self, message, flags=()):
        output = self.root / 'out'
        result = subprocess.run(
            [sys.executable, *flags, '-B', str(self.root / 'scripts' / SCRIPT),
             '--docs-checkout', str(self.docs), '--output', str(output)],
            capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(message, result.stderr)
        self.assertFalse(output.exists())
        self.assertFalse(self.marker.exists(), 'an unadmitted verifier executed')
        self.assertEqual(list(self.root.glob('.out.*')), [])

    def test_listed_file_missing_on_disk_is_rejected_before_execution(self):
        (self.snapshot / 'notes.txt').unlink()
        self.refuse('listed but absent')

    def test_listed_metadata_tamper_is_rejected_before_docs_checkout(self):
        (self.snapshot / 'analysis/pump_fun/program-manifest.json').write_text(
            json.dumps({'official_docs_commit': '0' * 40}))
        self.refuse('program-manifest.json')

    def test_duplicate_paths_cannot_inflate_import_count(self):
        document = json.loads(self.manifest.read_text())
        document['files'].append(document['files'][0])
        self.manifest.write_text(json.dumps(document))
        self.refuse('duplicate file paths')

    def test_invalid_file_metadata_is_rejected(self):
        document = json.loads(self.manifest.read_text())
        document['files'][0]['path'] = False
        self.manifest.write_text(json.dumps(document))
        self.refuse('file metadata is invalid')

    def test_unlisted_symlink_package_is_rejected(self):
        package = self.root / 'unlisted-package'
        package.mkdir()
        (package / '__init__.py').write_text('value = 1\n')
        (self.snapshot / 'scripts/unlisted_package').symlink_to(package, target_is_directory=True)
        for flags in ((), ('-O',), ('-OO',)):
            with self.subTest(flags=flags):
                self.refuse('snapshot contains a symlink', flags)

    def test_symlink_file_is_rejected_even_if_content_hash_matches(self):
        notes = self.snapshot / 'notes.txt'
        other = self.root / 'notes-copy'
        other.write_bytes(notes.read_bytes())
        notes.unlink()
        notes.symlink_to(other)
        self.refuse('snapshot contains a symlink')

    def test_valid_timestamp_bytecode_cannot_override_a_listed_source(self):
        helper = self.snapshot / 'scripts/checked_helper.py'
        payload = f'from pathlib import Path\nPath({str(self.marker)!r}).write_text("cache executed")\n'
        honest = 'value = 1\n'
        size = max(len(payload), len(honest)) + 20
        pad = lambda value: value + '#' * (size - len(value))
        helper.write_text(pad(payload))
        timestamp = helper.stat().st_mtime
        py_compile.compile(str(helper), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.TIMESTAMP)
        helper.write_text(pad(honest))
        os.utime(helper, (timestamp, timestamp))
        for name in VERIFIERS:
            (self.snapshot / 'scripts' / (name + '.py')).write_text('import checked_helper\n')
        self.repin()
        for flags in ((), ('-O',), ('-OO',)):
            with self.subTest(flags=flags):
                self.refuse('snapshot contains bytecode cache', flags)

    @unittest.skipUnless(hasattr(os, 'mkfifo'), 'FIFO unavailable')
    def test_non_regular_entry_is_rejected_without_reading_it(self):
        os.mkfifo(self.snapshot / 'fifo')
        self.refuse('snapshot contains a non-regular entry')

    def test_copied_snapshot_is_readmitted_before_execution(self):
        script = self.root / 'scripts' / SCRIPT
        spec = importlib.util.spec_from_file_location('snapshot_copy_gate', script)
        tool = importlib.util.module_from_spec(spec)
        with mock.patch.object(sys, 'path', list(sys.path)):
            spec.loader.exec_module(tool)
        real_copy = tool.shutil.copytree

        def mutate_copy(source, destination, *args, **kwargs):
            answer = real_copy(source, destination, *args, **kwargs)
            if Path(source).resolve() == self.snapshot.resolve():
                (Path(destination) / 'scripts/pump_fun_verify_offline.py').write_text('raise SystemExit(0)\n')
            return answer

        with mock.patch.object(tool.shutil, 'copytree', side_effect=mutate_copy), \
                mock.patch.object(sys, 'argv', [str(script), '--docs-checkout', str(self.docs),
                                              '--output', str(self.root / 'out')]):
            with self.assertRaisesRegex(AssertionError, 'pump_fun_verify_offline.py'):
                tool.main()
        self.assertFalse(self.marker.exists())
        self.assertFalse((self.root / 'out').exists())
        self.assertEqual(list(self.root.glob('.out.*')), [])


if __name__ == "__main__":
    unittest.main()
