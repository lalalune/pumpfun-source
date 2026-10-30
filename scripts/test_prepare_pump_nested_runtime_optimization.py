#!/usr/bin/env python3
"""Regression checks for nested-runtime preparation under optimized Python.

Sibling of the verified-build / text-layout optimization fixes, which
converted the asserts of the tools they touched but could not reach this
module: scripts/prepare_pump_nested_runtime.py expressed every binding
check as an assert, so under -O / -OO a tampered harness file, a
mismatched candidate, or changed staged source still produced a PASS
binding record. The test builds an isolated tree (module copy with its
script imports, a stub checkpoint verifier, and synthetic sealed inputs)
because the real repro/ evidence tree and sealed harness are not present
here.
"""

from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


SCRIPTS = Path(__file__).resolve().parent
PREFIX = "runtime-layer/nested-harness/"

SNIPPET = r"""
import sys, hashlib, json
from pathlib import Path
sys.path.insert(0, r'{scripts}')
import prepare_pump_nested_runtime as m
pkg = Path(r'{root}') / 'repro/pump/buy-mode-order-fortyeight'
m.HARNESS_SEAL = hashlib.sha256((pkg / 'manifest.json').read_bytes()).hexdigest()
record = m.prepare(Path(sys.argv[1]))
print(record['status'])
"""


def sha(data):
    return hashlib.sha256(data).hexdigest()


class NestedRuntimeOptimizationTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="nested-runtime-opt-")
        self.root = Path(self._tmp.name)
        (self.root / "scripts").mkdir()
        shutil.copy(SCRIPTS / "prepare_pump_nested_runtime.py",
                    self.root / "scripts" / "prepare_pump_nested_runtime.py")
        for dependency in ("deep_disassembly.py", "window_elf_reader.py"):
            shutil.copy(SCRIPTS / dependency, self.root / "scripts" / dependency)
        (self.root / "scripts" / "verify_current_checkpoint.py").write_text(
            "import hashlib, json\n"
            "from pathlib import Path\n"
            "def verify(name, root):\n"
            "    root = Path(root)\n"
            "    status = json.loads((root / 'repro/status.json').read_text())[name]\n"
            "    cand = root / status['candidate_artifact']\n"
            "    return {'candidate_sha256': hashlib.sha256(cand.read_bytes()).hexdigest()}\n"
        )
        sources = {}
        for i in range(37):
            p = self.root / f"programs/pump/src/f{i}.rs"
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(f"// source {i}\n".encode())
            sources[f"programs/pump/src/f{i}.rs"] = sha(p.read_bytes())
        cand = self.root / "repro/pump/pkg1/main/candidate.so"
        cand.parent.mkdir(parents=True, exist_ok=True)
        cand.write_bytes(b"candidate-bytes")
        (self.root / "repro/pump/pkg1/main/build-comparison.json").write_text(
            json.dumps({"source_sha256": sources,
                        "comparison": {"candidate_sha256": sha(cand.read_bytes())}}))
        attempt = {"returncode": 0, "source_unchanged": True,
                   "source_sha256": sources, "source_after_sha256": sources}
        (self.root / "repro/pump/pkg1/main/build-attempt.json").write_text(json.dumps(attempt))
        status = {"pump": {"candidate_artifact": "repro/pump/pkg1/main/candidate.so",
                           "comparison_report": "repro/pump/pkg1/main/build-comparison.json"}}
        (self.root / "repro/status.json").write_text(json.dumps(status))
        pkg = self.root / "repro/pump/buy-mode-order-fortyeight"
        harness = pkg / PREFIX
        harness.mkdir(parents=True)
        manifest = {}
        for i in range(5):
            f = harness / f"h{i}.py"
            f.write_bytes(f"# harness {i}\n".encode())
            manifest[f"{PREFIX}h{i}.py"] = {"sha256": sha(f.read_bytes())}
        esm = harness / "expected-source-map.json"
        esm.write_bytes(b"{}\n")
        manifest[f"{PREFIX}expected-source-map.json"] = {"sha256": sha(esm.read_bytes())}
        (pkg / "manifest.json").write_text(json.dumps(manifest, indent=2))
        self.harness = harness

    def tearDown(self):
        self._tmp.cleanup()

    def run_prepare(self, flag, tamper):
        if tamper:
            (self.harness / "h0.py").write_bytes(b"# TAMPERED\n")
        out = self.root / ("out-" + (flag or "normal"))
        code = SNIPPET.format(scripts=self.root / "scripts", root=self.root)
        argv = [sys.executable] + ([flag] if flag else []) + ["-c", code, str(out)]
        return subprocess.run(
            argv,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
        )

    def test_tampered_harness_rejected_under_optimization(self):
        for flag in ("-O", "-OO"):
            with self.subTest(flag=flag):
                completed = self.run_prepare(flag, tamper=True)
                self.assertNotEqual(completed.returncode, 0)
                self.assertIn("AssertionError", completed.stderr)

    def test_tampered_harness_rejected_normally(self):
        completed = self.run_prepare("", tamper=True)
        self.assertNotEqual(completed.returncode, 0)
        self.assertIn("AssertionError", completed.stderr)

    def test_untampered_preparation_still_passes(self):
        for flag in ("", "-O"):
            with self.subTest(flag=flag):
                completed = self.run_prepare(flag, tamper=False)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("PASS", completed.stdout)


if __name__ == "__main__":
    unittest.main()
