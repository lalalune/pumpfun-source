"""Actual product CLIs and retained ELF/IDL inputs; no runtime loader patches."""
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("PUMP_DISPATCH_TEST_REPO", HERE.parent)).resolve()
SOURCES = ("scripts/deep_disassembly.py", "scripts/recover_dispatch.py",
           "scripts/analyze.py", "scripts/window_elf_reader.py")


def copy_inputs(root):
    paths = list(SOURCES)
    paths += [f"evidence/original/{name}/deployed.so" for name in ("pump", "pump_amm", "pump_fees", "mayhem")]
    paths += [f"evidence/upstream/{name}.json" for name in ("pump", "pump_amm", "pump_fees")]
    for relative in paths:
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)


def command(root, script, args=(), cp936=False):
    argv = [sys.executable, "-B", "-X", "utf8=0" if cp936 else "utf8=1"]
    if cp936:
        argv.append(str(HERE / "dispatch_encoding_cli.py"))
    argv += [str(root / script), *map(str, args)]
    return subprocess.run(argv, env=dict(os.environ, PYTHONHASHSEED="0", PYTHONIOENCODING="utf-8"),
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=45)


class DispatchIdlEncodingTests(unittest.TestCase):
    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stdout.decode("utf-8", "replace"))

    def deep(self, root, program, output, cp936):
        result = command(root, "scripts/deep_disassembly.py", ("--program", program, "--output", output), cp936)
        self.assert_success(result)
        self.assertEqual(len(list(output.iterdir())), 12)
        verifier = subprocess.run([sys.executable, "-B", str(output / "verify.py")], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=20)
        self.assert_success(verifier)
        return json.loads((output / "dispatch-table.json").read_text(encoding="utf-8"))

    def test_pump_deep_cli_recovers_the_actual_idl_in_cp936_and_utf8(self):
        with tempfile.TemporaryDirectory(prefix="dispatch-encoding-deep-") as temporary:
            work = Path(temporary);root = work / "inputs";copy_inputs(root)
            control = work / "utf8";candidate = work / "cp936"
            expected = {hex(int.from_bytes(bytes(item["discriminator"]), "little")) for item in json.loads((root / "evidence/upstream/pump.json").read_text(encoding="utf-8"))["instructions"]}
            self.assertEqual(len(expected), 56)
            self.assertEqual(set(self.deep(root, "pump", control, False)), expected)
            self.assertEqual(set(self.deep(root, "pump", candidate, True)), expected)
            for path in control.iterdir():
                self.assertEqual((candidate / path.name).read_bytes(), path.read_bytes(), path.name)

    def test_four_program_dispatch_map_cli_matches_utf8_under_cp936(self):
        with tempfile.TemporaryDirectory(prefix="dispatch-encoding-map-") as temporary:
            root = Path(temporary);copy_inputs(root)
            self.assert_success(command(root, "scripts/analyze.py"))
            self.assert_success(command(root, "scripts/recover_dispatch.py"))
            path = root / "evidence/dispatch-map.json"
            control = path.read_bytes()
            self.assert_success(command(root, "scripts/recover_dispatch.py", cp936=True))
            self.assertEqual(path.read_bytes(), control)
            report = json.loads(control)
            self.assertEqual(set(report), {"pump", "pump_amm", "pump_fees", "mayhem"})
            for name, count in (("pump", 56), ("pump_amm", 38), ("pump_fees", 31)):
                self.assertEqual(len(report[name]["instructions"]), count)
                self.assertEqual(sum(bool(row["matches"]) for row in report[name]["instructions"].values()), count)

    def test_real_no_idl_mayhem_deep_cli_keeps_its_existing_fallback(self):
        with tempfile.TemporaryDirectory(prefix="dispatch-encoding-no-idl-") as temporary:
            work = Path(temporary);root = work / "inputs";copy_inputs(root)
            self.assertFalse((root / "evidence/upstream/mayhem.json").exists())
            control = work / "utf8";candidate = work / "cp936"
            self.assertEqual(self.deep(root, "mayhem", candidate, True), self.deep(root, "mayhem", control, False))
            for path in control.iterdir():
                self.assertEqual((candidate / path.name).read_bytes(), path.read_bytes(), path.name)

    def test_reviewed_transition_preserves_complete_loader_algorithms(self):
        transition = json.loads((ROOT / "reconstruction/diagnostics/dispatch-idl-utf8/transition.json").read_text(encoding="utf-8"))
        self.assertEqual(transition["rootScriptSetBefore"], transition["rootScriptSetAfter"])
        for path, row in transition["reviewedAssetTransition"].items():
            source = (ROOT / path).read_text(encoding="utf-8")
            node = next(item for item in ast.parse(source).body if isinstance(item, ast.FunctionDef) and item.name == row["loader"])
            # Only the two existing IDL receiver calls have their new encoding
            # removed for the before/after AST comparison; no algorithm is run.
            for call in ast.walk(node):
                if (isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute)
                        and call.func.attr == "read_text" and isinstance(call.func.value, ast.Name)
                        and call.func.value.id in ("idl", "idl_path")):
                    call.keywords = [item for item in call.keywords if item.arg != "encoding"]
            # ast.unparse is stable across Python 3.11-3.14; the beforeLoaderUnparseSha256 values were
            # computed from the sourceBase files whose sha256 equals beforeSha256.
            self.assertEqual(hashlib.sha256(ast.unparse(node).encode()).hexdigest(),
                             row["beforeLoaderUnparseSha256"], path)
            # The recorded ast.dump digests were produced by Python <= 3.11; ast.dump output
            # changed in 3.12, so they are only comparable there.
            if sys.version_info < (3, 12):
                digest = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
                self.assertEqual(digest, row["beforeLoaderAstSha256"], path)
                self.assertEqual(digest, row["afterLoaderAstWithoutEncodingSha256"], path)


if __name__ == "__main__":
    unittest.main()
