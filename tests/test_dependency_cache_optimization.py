"""Regression checks for dependency-cache admission under optimized Python.

seed() and finish() in scripts/pump_dependency_cache.py are the cache
admission gates: seed() accepts a saved cache entry only if its manifest
context and key match and every listed file is an allowed, hash-matching
entry, and finish() publishes a fresh build only if the workspace manifests
did not change during the build. Before this fix every one of those checks
was a bare assert, so under -O/-OO a cache entry with a mismatched manifest
context, a file hash, or a disallowed path was still recorded as a cache hit,
and a build whose manifests changed mid-build was still published. The cache
object is built with the same object.__new__ fixture pattern as the existing
manifest-state test, so the driver exercises the admission logic without a
real SDK or Cargo build.
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
    "import sys, json, hashlib\n"
    "from pathlib import Path\n"
    "import pump_dependency_cache as m\n"
    "case = sys.argv[1]\n"
    "tamper = sys.argv[2]\n"
    "root = Path(sys.argv[3])\n"
    "def sha(path):\n"
    "    return hashlib.sha256(Path(path).read_bytes()).hexdigest()\n"
    "def make_cache(entry):\n"
    "    cache = object.__new__(m.DependencyCache)\n"
    "    cache.entry = entry\n"
    "    cache.root = root / 'cache-root'\n"
    "    cache.key = 'k'\n"
    "    cache.context = {'manifests': {}}\n"
    "    cache.sources = {}\n"
    "    cache.workspace = root / 'workspace'\n"
    "    cache.sdk = root / 'sdk'\n"
    "    cache.tools = {}\n"
    "    cache.configs = {}\n"
    "    cache.target = 'sbf-solana-solana'\n"
    "    cache.direct = True\n"
    "    cache.record = {'main_command': ['x'], 'main_freshly_compiled': True}\n"
    "    cache.crates = {'dependency'}\n"
    "    cache.packages = {'dependency'}\n"
    "    cache.main_names = {'pump'}\n"
    "    return cache\n"
    "REL = 'sbf-solana-solana/release/deps/libdependency-0123456789abcdef.rlib'\n"
    "if case == 'seed':\n"
    "    entry = root / 'entry'\n"
    "    (entry / 'files' / REL).parent.mkdir(parents=True, exist_ok=True)\n"
    "    (entry / 'files' / REL).write_bytes(b'artifact-bytes')\n"
    "    files = {REL: sha(entry / 'files' / REL)}\n"
    "    context = {'manifests': {}}\n"
    "    if tamper == 'hash':\n"
    "        files = {REL: '0' * 64}\n"
    "    if tamper == 'context':\n"
    "        context = {'manifests': {}, 'extra': 1}\n"
    "    if tamper == 'rel':\n"
    "        bad = 'sbf-solana-solana/release/deps/libpump-0123456789abcdef.rlib'\n"
    "        (entry / 'files' / bad).parent.mkdir(parents=True, exist_ok=True)\n"
    "        (entry / 'files' / bad).write_bytes(b'artifact-bytes')\n"
    "        files = {bad: sha(entry / 'files' / bad)}\n"
    "    (entry / 'MANIFEST.json').write_text(json.dumps(\n"
    "        {'context': context, 'key': 'k', 'files': files}))\n"
    "    cache = make_cache(entry)\n"
    "    cache.seed(root / 'seed-target')\n"
    "elif case == 'finish':\n"
    "    workspace = root / 'workspace'\n"
    "    workspace.mkdir(parents=True, exist_ok=True)\n"
    "    (workspace / 'Cargo.toml').write_text('[fixture]\\n')\n"
    "    target = root / 'build-target'\n"
    "    artifact = target / 'release' / 'deps' / 'libdependency-0123456789abcdef.rlib'\n"
    "    artifact.parent.mkdir(parents=True, exist_ok=True)\n"
    "    artifact.write_bytes(b'artifact-bytes')\n"
    "    report = root / 'build-report.json'\n"
    "    report.write_text(json.dumps({'returncode': 0}))\n"
    "    log = root / 'build.log'\n"
    "    log.write_text('')\n"
    "    cache = make_cache(root / 'noentry')\n"
    "    cache.context = {'manifests': {'Cargo.toml': '0' * 64 if tamper == 'manifest' else sha(workspace / 'Cargo.toml')}}\n"
    "    cache.finish(target, log, report)\n"
    "print('OK')\n"
)

MODES = ([], ["-O"], ["-OO"])


class DependencyCacheOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def run_driver(self, optimization, case, tamper):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, case, tamper, str(self.root)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_seed_tampers_rejected_in_all_modes(self):
        for tamper in ("context", "hash", "rel"):
            with self.subTest(tamper=tamper):
                for optimization in MODES:
                    with self.subTest(optimization=optimization or "normal"):
                        completed = self.run_driver(optimization, "seed", tamper)
                        self.assertNotEqual(completed.returncode, 0, completed.stdout)
                        self.assertNotIn("OK", completed.stdout)

    def test_finish_manifest_tamper_rejected_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "finish", "manifest")
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)

    def test_valid_seed_and_finish_accepted_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                for case in ("seed", "finish"):
                    completed = self.run_driver(optimization, case, "none")
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    self.assertIn("OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
