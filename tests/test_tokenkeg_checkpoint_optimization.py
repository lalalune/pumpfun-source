"""Regression checks for tokenkeg portable-binding verification under optimized Python.

portable_binding() in scripts/pump_tokenkeg_checkpoint_differential.py
authenticates a portable source binding: the package manifest seal, the
binding kind and origin record, the origin build record and checkpoint
hashes, the candidate hash chain, and the report source map against the
checkpoint primary sources. Before this fix every one of those 12 checks was
a bare assert, so under -O/-OO a binding with a mismatched manifest seal, a
wrong binding kind, or a candidate that differs from the checkpoint candidate
was still accepted as authenticated. The differential, checkpoint and
manifest modules are stubbed here (the real ones need the sealed packages),
so the driver exercises the binding admission logic, not the differential.
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
    "import sys, json, hashlib, types\n"
    "from pathlib import Path\n"
    "tamper = sys.argv[1]\n"
    "root = Path(sys.argv[2])\n"
    "pkg = root / 'pkg'\n"
    "pkg.mkdir(parents=True, exist_ok=True)\n"
    "def fsha(p):\n"
    "    return hashlib.sha256(Path(p).read_bytes()).hexdigest()\n"
    "orig_cand = b'candidate-bytes'\n"
    "cand_sha = hashlib.sha256(orig_cand).hexdigest()\n"
    "candidate = root / 'candidate.so'\n"
    "candidate.write_bytes(b'tampered-bytes' if tamper == 'candidate' else orig_cand)\n"
    "origin = {'returncode': 0, 'source_unchanged': True,\n"
    "          'source_sha256': {'a.rs': 'h1', 'b.rs': 'h2'},\n"
    "          'comparison': {'candidate_sha256': cand_sha, 'other': 1}}\n"
    "origin_path = pkg / 'canonical-build.json'\n"
    "origin_path.write_text(json.dumps(origin))\n"
    "checkpoint = {'candidate_sha256': cand_sha,\n"
    "              'primary_source_sha256': {'a.rs': 'h1', 'b.rs': 'h2'}}\n"
    "checkpoint_path = pkg / 'CHECKPOINT.json'\n"
    "checkpoint_path.write_text(json.dumps(checkpoint))\n"
    "manifest = {'canonical-build.json': fsha(origin_path),\n"
    "            'CHECKPOINT.json': fsha(checkpoint_path)}\n"
    "manifest_path = pkg / 'MANIFEST.json'\n"
    "manifest_path.write_text(json.dumps(manifest))\n"
    "expected = {'programs/pump/a.rs': 'h1', 'programs/pump/b.rs': 'h2'}\n"
    "binding = {'kind': 'other-kind' if tamper == 'kind' else 'verified-equal-canonical-primary-source',\n"
    "           'origin_build_record': 'pkg/canonical-build.json',\n"
    "           'origin_build_record_sha256': fsha(origin_path),\n"
    "           'original_compiled_source_sha256': origin['source_sha256']}\n"
    "report = {'portable_source_binding': binding,\n"
    "          'comparison': origin['comparison'], 'source_sha256': expected}\n"
    "report_path = root / 'report.json'\n"
    "report_path.write_text(json.dumps(report))\n"
    "chk = types.ModuleType('verify_pump_main_checkpoint')\n"
    "chk.MANIFEST_SHA256 = '0' * 64 if tamper == 'seal' else fsha(manifest_path)\n"
    "chk.PACKAGE = 'pkg'\n"
    "chk.ROOT = root\n"
    "chk.sha = fsha\n"
    "sys.modules['verify_pump_main_checkpoint'] = chk\n"
    "man = types.ModuleType('build_source_manifest')\n"
    "def source_manifest(*args, **kwargs):\n"
    "    cp = json.loads(checkpoint_path.read_text())\n"
    "    return {'programs/pump/' + n: d for n, d in cp['primary_source_sha256'].items()}\n"
    "man.source_manifest = source_manifest\n"
    "sys.modules['build_source_manifest'] = man\n"
    "base = types.ModuleType('pump_tokenkeg_two_curve_differential')\n"
    "base.compiled_binding = lambda *args: {'orig': True}\n"
    "base.fixture = types.SimpleNamespace()\n"
    "base.bindings = lambda *args: {'repository_inputs': {}}\n"
    "base.SOURCE_DIRECTORY = root / 'programs/pump'\n"
    "sys.modules['pump_tokenkeg_two_curve_differential'] = base\n"
    "import pump_tokenkeg_checkpoint_differential as v\n"
    "v.portable_binding(candidate, report_path)\n"
    "print('OK')\n"
)

MODES = ([], ["-O"], ["-OO"])


class TokenkegCheckpointOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def run_driver(self, optimization, tamper):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, tamper, str(self.root)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_binding_tampers_rejected_in_all_modes(self):
        for tamper in ("seal", "kind", "candidate"):
            with self.subTest(tamper=tamper):
                for optimization in MODES:
                    with self.subTest(optimization=optimization or "normal"):
                        completed = self.run_driver(optimization, tamper)
                        self.assertNotEqual(completed.returncode, 0, completed.stdout)
                        self.assertNotIn("OK", completed.stdout)

    def test_valid_binding_accepted_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "none")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
