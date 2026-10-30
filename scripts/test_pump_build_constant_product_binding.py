#!/usr/bin/env python3
"""Regression test: the constant-product build report must bind its inputs.

scripts/pump_build_constant_product.py compiles
programs/pump/recovered/constant_product.rs and publishes a comparison.json
carrying source_sha256 and rustc_sha256. The builder used to compute both
hashes only after the build, from fresh reads, so an input that changed
during compilation was certified with the hash of bytes the compiler never
saw. The original-side slice is pinned against its capture manifest before
use; the compiled side now gets the same discipline: hash the inputs before
the build, fail the run if either changed, and report the before-hashes.

The test stages a temporary tree: a synthetic deployed.so whose capture
manifest is generated for it (so the pinning check passes), a dummy source,
an embedded object carrying the expected .text.constant_product_output
section, and a fake rustc that either leaves the source alone or appends to
it mid-build.
"""

import base64
import hashlib
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "pump_build_constant_product.py"
SOURCE = b"pub fn constant_product_output() -> u64 { 7 }\n"
RANGE_END = 0x88908

# A minimal x86-64 relocatable object whose single section is named
# .text.constant_product_output, as the builder expects.
OBJECT_B64 = "f0VMRgIBAQAAAAAAAAAAAAEAPgABAAAAAAAAAAAAAAAAAAAAAAAAAOgBAAAAAAAAAAAAAEAAAAAAAEAADAALAPMPHvpVSInluCoAAABdwwBHQ0M6IChVYnVudHUgMTMuMy4wLTZ1YnVudHUyfjI0LjA0LjEpIDEzLjMuMAAAAAAEAAAAEAAAAAUAAABHTlUAAgAAwAQAAAADAAAAAAAAABQAAAAAAAAAAXpSAAF4EAEbDAcIkAEAABwAAAAcAAAAAAAAAA8AAAAARQ4QhgJDDQZGDAcIAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAQAAAAQA8f8AAAAAAAAAAAAAAAAAAAAAAAAAAAMAAQAAAAAAAAAAAAAAAAAAAAAABQAAABIAAQAAAAAAAAAAAA8AAAAAAAAAAHQuYwBzZWxlY3RfZmVlX3RpZXIAAAAAIAAAAAAAAAACAAAAAgAAAAAAAAAAAAAAAC5zeW10YWIALnN0cnRhYgAuc2hzdHJ0YWIALnRleHQuY29uc3RhbnRfcHJvZHVjdF9vdXRwdXQALmRhdGEALmJzcwAuY29tbWVudAAubm90ZS5HTlUtc3RhY2sALm5vdGUuZ251LnByb3BlcnR5AC5yZWxhLmVoX2ZyYW1lAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGwAAAAEAAAAGAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAPAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAADkAAAABAAAAAwAAAAAAAAAAAAAAAAAAAE8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAA/AAAACAAAAAMAAAAAAAAAAAAAAAAAAABPAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAARAAAAAEAAAAwAAAAAAAAAAAAAAAAAAAATwAAAAAAAAAuAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAABAAAAAAAAAE0AAAABAAAAAAAAAAAAAAAAAAAAAAAAAH0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAABdAAAABwAAAAIAAAAAAAAAAAAAAAAAAACAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAAdQAAAAEAAAACAAAAAAAAAAAAAAAAAAAAoAAAAAAAAAA4AAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAHAAAAAEAAAAQAAAAAAAAAAAAAAAAAAAAFABAAAAAAAAGAAAAAAAAAAJAAAABwAAAAgAAAAAAAAAGAAAAAAAAAABAAAAAgAAAAAAAAAAAAAAAAAAAAAAAADYAAAAAAAAAGAAAAAAAAAACgAAAAMAAAAIAAAAAAAAABgAAAAAAAAACQAAAAMAAAAAAAAAAAAAAAAAAAAAAAAAOAEAAAAAAAAVAAAAAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAABEAAAADAAAAAAAAAAAAAAAAAAAAAAAAAGgBAAAAAAAAfwAAAAAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAA="

FAKE_RUSTC = """#!/usr/bin/env python3
import pathlib, shutil, sys
argv = sys.argv[1:]
if '--version' in argv:
    print('rustc 1.44.0-fake (0000000 2026-01-01)')
    raise SystemExit(0)
source = pathlib.Path(next(a for a in argv if a.endswith('.rs')))
__MUTATE__
out = argv[argv.index('-o') + 1]
shutil.copy(__OBJ__, out)
"""

MUTATE = "source.write_bytes(source.read_bytes() + bytes([10]) + b'// changed during build' + bytes([10]))"


def stage(root: pathlib.Path, mutate: bool) -> pathlib.Path:
    (root / "scripts").mkdir(parents=True)
    (root / "scripts" / "pump_build_constant_product.py").write_bytes(BUILDER.read_bytes())
    src_dir = root / "programs" / "pump" / "recovered"
    src_dir.mkdir(parents=True)
    (src_dir / "constant_product.rs").write_bytes(SOURCE)
    capture_dir = root / "evidence" / "original" / "pump"
    capture_dir.mkdir(parents=True)
    deployed = bytes(RANGE_END)
    (capture_dir / "deployed.so").write_bytes(deployed)
    manifest = {"payload_sha256": hashlib.sha256(deployed).hexdigest()}
    (capture_dir / "capture.json").write_text(json.dumps(manifest))
    obj = root / "obj.o"
    obj.write_bytes(base64.b64decode(OBJECT_B64))
    toolchain = root / "toolchain" / "rust" / "bin"
    toolchain.mkdir(parents=True)
    rustc = toolchain / "rustc"
    rustc.write_text(
        FAKE_RUSTC.replace("__MUTATE__", MUTATE if mutate else "").replace("__OBJ__", repr(str(obj)))
    )
    rustc.chmod(0o755)
    return root / "toolchain"


class ConstantProductInputBindingTests(unittest.TestCase):
    def run_builder(self, mutate: bool):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = pathlib.Path(tmp.name) / "tree"
        root.mkdir()
        toolchain = stage(root, mutate)
        out = root / "out"
        proc = subprocess.run(
            [sys.executable, str(root / "scripts" / "pump_build_constant_product.py"),
             "--toolchain", str(toolchain), "--output", str(out)],
            capture_output=True, text=True,
        )
        return proc, out

    def test_report_binds_the_compiled_source(self):
        proc, out = self.run_builder(mutate=False)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        report = json.loads((out / "comparison.json").read_text())
        self.assertEqual(report["source_sha256"], hashlib.sha256(SOURCE).hexdigest())
        self.assertIn("rustc_sha256", report)

    def test_source_changed_during_build_is_rejected(self):
        proc, out = self.run_builder(mutate=True)
        self.assertNotEqual(proc.returncode, 0)
        self.assertFalse((out / "comparison.json").exists())


class SnapshotBindingTests(unittest.TestCase):
    def prepare(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name) / "tree"
        root.mkdir()
        return root, stage(root, mutate=False)

    def invoke(self, root, toolchain, *, optimized=False, env=None):
        command = [sys.executable, *(['-O'] if optimized else []),
                   str(root / 'scripts/pump_build_constant_product.py'),
                   '--toolchain', str(toolchain), '--output', str(root / 'out')]
        return subprocess.run(command, capture_output=True, text=True, env=env)

    def mutant_object(self, root):
        data = bytearray(base64.b64decode(OBJECT_B64))
        data[64] ^= 1
        path = root / 'mutant.o'
        path.write_bytes(data)
        return path

    def test_transient_source_mutation_compiles_the_frozen_bytes(self):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                root, toolchain = self.prepare()
                original = root / 'programs/pump/recovered/constant_product.rs'
                mutant = self.mutant_object(root)
                rustc = toolchain / 'rust/bin/rustc'
                rustc.write_text(
                    '#!/usr/bin/env python3\nimport pathlib,shutil,sys\n'
                    "if '--version' in sys.argv: print('frozen compiler');raise SystemExit(0)\n"
                    "source=pathlib.Path(next(x for x in sys.argv[1:] if x.endswith('.rs')))\n"
                    f'original=pathlib.Path({str(original)!r})\n'
                    f'original.write_bytes({SOURCE + b"// temporary change"!r})\n'
                    'observed=source.read_bytes()\n'
                    f'original.write_bytes({SOURCE!r})\n'
                    f'shutil.copy({str(root / "obj.o")!r} if observed=={SOURCE!r} else {str(mutant)!r},sys.argv[sys.argv.index("-o")+1])\n',
                    encoding='utf-8')
                result = self.invoke(root, toolchain, optimized=optimized)
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads((root / 'out/comparison.json').read_bytes())
                self.assertEqual(report['object_sha256'], hashlib.sha256((root / 'obj.o').read_bytes()).hexdigest())
                self.assertEqual(original.read_bytes(), SOURCE)
                self.assertFalse(list((root / 'out').glob('.compile-inputs-*')))

    def test_compiler_replacement_during_launch_uses_the_snapshot(self):
        import os
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                root, toolchain = self.prepare()
                rustc = toolchain / 'rust/bin/rustc'
                mutant = self.mutant_object(root)
                replacement = (
                    '#!/usr/bin/env python3\nimport shutil,sys\n'
                    f'shutil.copy({str(mutant)!r},sys.argv[sys.argv.index("-o")+1])\n').encode()
                injection = root / 'injection';injection.mkdir()
                (injection / 'sitecustomize.py').write_text(
                    'import subprocess,pathlib\nreal_run=subprocess.run\n'
                    f'compiler=pathlib.Path({str(rustc)!r})\n'
                    f'replacement={replacement!r}\n'
                    'def run(args,*a,**kw):\n'
                    "    if isinstance(args,list) and '--emit=obj' in args:\n"
                    '        saved=compiler.read_bytes();compiler.write_bytes(replacement)\n'
                    '        try: return real_run(args,*a,**kw)\n'
                    '        finally: compiler.write_bytes(saved)\n'
                    '    return real_run(args,*a,**kw)\n'
                    'subprocess.run=run\n', encoding='utf-8')
                result = self.invoke(root, toolchain, optimized=optimized,
                                     env={**os.environ, 'PYTHONPATH': str(injection)})
                self.assertEqual(result.returncode, 0, result.stderr)
                report = json.loads((root / 'out/comparison.json').read_bytes())
                self.assertEqual(report['object_sha256'], hashlib.sha256((root / 'obj.o').read_bytes()).hexdigest())
                self.assertEqual(report['rustc_sha256'], hashlib.sha256(rustc.read_bytes()).hexdigest())

    def test_version_probe_mutation_is_rejected_before_publication(self):
        for optimized in (False, True):
            with self.subTest(optimized=optimized):
                root, toolchain = self.prepare()
                rustc = toolchain / 'rust/bin/rustc'
                rustc.write_text(
                    '#!/usr/bin/env python3\nimport pathlib,shutil,sys\n'
                    "if '--version' in sys.argv:\n"
                    f'    pathlib.Path({str(rustc)!r}).write_text("changed compiler")\n'
                    "    print('changed version');raise SystemExit(0)\n"
                    f'shutil.copy({str(root / "obj.o")!r},sys.argv[sys.argv.index("-o")+1])\n',
                    encoding='utf-8')
                result = self.invoke(root, toolchain, optimized=optimized)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((root / 'out/comparison.json').exists())


if __name__ == "__main__":
    unittest.main()
