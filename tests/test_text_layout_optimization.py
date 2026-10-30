"""Regression checks for link-receipt admission under optimized Python.

finish() is the verified builder's check over a saved link receipt: script,
linker, wrapper and helper hashes, bound input bytes, and the requirement
that forwarded file operands point at the bound copies. Before this fix
every check was a bare assert, so under -O a receipt with an unbound
forwarded operand or a mismatched script hash was still accepted and the
record claimed its bound inputs.
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
    "from pump_text_layout import finish\n"
    "root = Path(sys.argv[1])\n"
    "case = sys.argv[2]\n"
    "record = json.loads((root / 'record.json').read_text())\n"
    "if case == 'unbound':\n"
    "    inv = json.loads((root / 'inv.json').read_text())\n"
    "    inv['forwarded'] = ['/tmp/unbound.o']\n"
    "    (root / 'inv.json').write_text(json.dumps(inv))\n"
    "elif case == 'scripthash':\n"
    "    record['script_sha256'] = '0' * 64\n"
    "elif case == 'copybytes':\n"
    "    (root / 'copy.o').write_bytes(b'mutated')\n"
    "out = finish(record)\n"
    "print('OK', out['bound_inputs'])\n"
)

MODES = ([], ["-O"], ["-OO"])


class TextLayoutOptimizationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        script = self.root / "ordered.ld"
        script.write_bytes(b"script")
        linker = self.root / "rust-lld"
        linker.write_bytes(b"linker")
        wrapper = self.root / "wrapper"
        wrapper.write_bytes(b"wrapper")
        helper = self.root / "helper.py"
        helper.write_bytes(b"helper")
        copy = self.root / "copy.o"
        copy.write_bytes(b"object-bytes")
        self.copy = copy

        def sha(path):
            return hashlib.sha256(Path(path).read_bytes()).hexdigest()

        inv = {
            "incoming": ["a.o"],
            "forwarded": [str(copy)],
            "link_inputs": {
                "a.o": {
                    "kind": "object",
                    "copy": str(copy),
                    "bytes": len(b"object-bytes"),
                    "sha256": sha(copy),
                }
            },
            "replacement_script_sha256": sha(script),
            "real_linker_sha256": sha(linker),
        }
        (self.root / "inv.json").write_text(json.dumps(inv))
        record = {
            "script": str(script),
            "script_sha256": sha(script),
            "real_linker": str(linker),
            "real_linker_sha256": sha(linker),
            "external_wrapper": str(wrapper),
            "external_wrapper_sha256": sha(wrapper),
            "helper_sha256": {str(helper): sha(helper)},
            "link_receipt": str(self.root / "inv.json"),
        }
        (self.root / "record.json").write_text(json.dumps(record))

    def run_driver(self, optimization, case):
        env = dict(os.environ)
        env["PYTHONPATH"] = str(SCRIPTS) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [sys.executable, *optimization, "-c", DRIVER,
             str(self.root), case],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            check=False,
        )

    def test_unbound_forwarded_operand_rejected_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "unbound")
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn("forwarded operands must point at bound copies",
                              completed.stderr)

    def test_script_hash_mismatch_rejected_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "scripthash")
                self.assertNotEqual(completed.returncode, 0, completed.stdout)
                self.assertIn("link script hash mismatch", completed.stderr)

    def test_mutated_bound_copy_rejected_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "copybytes")
                self.assertNotEqual(completed.returncode, 0, completed.stdout)

    def test_valid_receipt_accepted_in_all_modes(self):
        for optimization in MODES:
            with self.subTest(optimization=optimization or "normal"):
                completed = self.run_driver(optimization, "valid")
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertIn("OK 1", completed.stdout)


if __name__ == "__main__":
    unittest.main()
