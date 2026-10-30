"""Regression checks for current-bindings verification under optimized Python.

current_pump_groups() and verify_pump_body() in scripts/verify_current_bindings.py
gate the "verified" current binding: the bound input counts (36 source files, 94
harness files, 28 runtime snapshots, 2 canonical harness files, 3 build helpers)
are the only guard against a dropped entry, because verify_maps() only checks the
entries a map lists, and the body checks bind the candidate to the sealed
original bytes. Before this fix every one of those checks was a bare assert, so
under -O/-OO a dropped source file was accepted as a complete binding and a
candidate whose relocated literal differed from the sealed bytes passed silently.
"""

from pathlib import Path
import hashlib
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

DRIVER = (
    "import sys, hashlib\n"
    "from pathlib import Path\n"
    "import verify_current_bindings as v\n"
    "case = sys.argv[1]\n"
    "v.ROOT = Path(sys.argv[2])\n"
    "if case == 'groups':\n"
    "    v.current_pump_groups(Path(sys.argv[3]))\n"
    "elif case == 'body':\n"
    "    def fake_sha(data):\n"
    "        b = bytes(data)\n"
    "        if len(b) == 3000 and b[2900:2901] == b'\\x01':\n"
    "            return '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d'\n"
    "        if len(b) == 3000 and b[2900:2901] == b'\\x02':\n"
    "            return '92575cd082bf76b332044a7d09371a9764db8b2cc40180bf1418f261945bbd6a'\n"
    "        return hashlib.sha256(b).hexdigest()\n"
    "    v.sha = fake_sha\n"
    "    v.verify_pump_body(Path(sys.argv[2]), Path(sys.argv[3]))\n"
    "print('OK')\n"
)

ELF_STUB = '''
import struct


def _bytes(marker, tamper):
    data = bytearray(3000)
    data[2900] = marker
    struct.pack_into("<I", data, 252, 2000)
    struct.pack_into("<I", data, 260, 0)
    data[2000:2008] = bytes.fromhex("17b7f83760d8ac60")
    if tamper and marker == 2:
        data[2000:2008] = bytes(8)
    return bytes(data)


class Elf:
    def __init__(self, path):
        name = str(path)
        if name.endswith("deployed.so"):
            self.b = _bytes(1, __TAMPER__)
        elif name.endswith("candidate.so"):
            self.b = _bytes(2, __TAMPER__)
        else:
            self.b = _bytes(2, False)
        self.lo = 0
        self.hi = 1840
        self.normalized = bytes(3000)
        self.funcs = [{"start": k * 100, "size": 100} for k in range(25)]
        self.entries = [k * 100 for k in range(27)]
        self.calls = {k: k * 100 for k in range(25)}

    def pattern(self, at, size):
        return [{"offset": 248, "type": 8, "symbol": ""}]

    def callsites(self, start, size):
        return [{"offset": k, "target": k * 100} for k in range(25)]
'''

MODES = ([], ["-O"], ["-OO"])

VALID = {"source": 36, "harness": 94, "runtime": 28, "canonical": 2, "helpers": 3}


class CurrentBindingsOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.package = self.root / "pkg"
        self.package.mkdir()

    def run_driver(self, optimization, case):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER, case, str(self.root), str(self.package)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def write_groups_package(self, counts, map_match=True):
        def mapping(prefix, count):
            return {f"{prefix}/{i}": "a" * 64 for i in range(count)}

        source = mapping("src", counts["source"])
        (self.package / "source-harness-sha256.json").write_text(json.dumps({
            "source": source,
            "canonical_harness": mapping("canon", counts["canonical"]),
            "static_and_saved_verifiers": {},
            "owned_documentation": {},
        }))
        (self.package / "source-sha256.json").write_text(json.dumps(
            source if map_match else mapping("src", counts["source"] + 1)))
        (self.package / "scratch-inputs-before.json").write_text(json.dumps({
            "harness_sha256": mapping("h", counts["harness"]),
            "repository_fixture_snapshot_sha256": mapping("r", counts["runtime"]),
        }))
        (self.package / "build-helper-sha256.json").write_text(json.dumps(
            mapping("b", counts["helpers"])))
        (self.package / "manifest-sha256.json").write_text(json.dumps(
            {"candidate.so": {"sha256": "a" * 64}}))

    def write_body_package(self, tamper):
        (self.package / "elf_reader.py").write_text(
            ELF_STUB.replace("__TAMPER__", "True" if tamper else "False"))
        (self.package / "function-match.json").write_text(json.dumps({
            "candidate_body": {"start": 0}, "original_body": {"start": 0}}))

    def test_groups_count_tampers_rejected_in_all_modes(self):
        variants = {
            "dropped source": {**VALID, "source": 35},
            "dropped harness": {**VALID, "harness": 93},
            "dropped runtime": {**VALID, "runtime": 27},
            "dropped canonical": {**VALID, "canonical": 1},
            "dropped helper": {**VALID, "helpers": 2},
        }
        for name, counts in variants.items():
            with self.subTest(variant=name):
                self.write_groups_package(counts)
                for optimization in MODES:
                    with self.subTest(optimization=optimization or "normal"):
                        completed = self.run_driver(optimization, "groups")
                        self.assertNotEqual(completed.returncode, 0, completed.stdout)
                        self.assertNotIn("OK", completed.stdout)

    def test_groups_map_mismatch_rejected_in_all_modes(self):
        self.write_groups_package(VALID, map_match=False)
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "groups")
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)

    def test_groups_valid_accepted_in_all_modes(self):
        self.write_groups_package(VALID)
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "groups")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK", completed.stdout)

    def test_body_pointer_tamper_rejected_in_all_modes(self):
        self.write_body_package(tamper=True)
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "body")
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertNotIn("OK", completed.stdout)

    def test_body_valid_accepted_in_all_modes(self):
        self.write_body_package(tamper=False)
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "body")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK", completed.stdout)


if __name__ == "__main__":
    unittest.main()
