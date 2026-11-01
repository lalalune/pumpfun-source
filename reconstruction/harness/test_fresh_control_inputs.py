"""Actual executable-cache and private-source admission controls."""
import importlib.util
import importlib._bootstrap_external as bytecode
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest

H = Path(__file__).resolve().parent
sys.path.insert(0, str(H))
import fresh_control_inputs


class SourceAdmissionTests(unittest.TestCase):
    def private_context(self, root):
        for name in (*fresh_control_inputs.MODULES, 'fresh_control_inputs'):
            shutil.copyfile(H / (name + '.py'), root / (name + '.py'))
        path = root / 'fresh_control_inputs.py'
        raw = path.read_bytes()
        module = types.ModuleType('_private_fresh_admission')
        module.__file__ = str(path)
        module.__dict__['_ADMITTED_SOURCE_BYTES'] = raw
        exec(compile(raw, str(path), 'exec', dont_inherit=True), module.__dict__)
        return module.load_context()

    def test_executable_timestamp_caches_never_substitute_admitted_source(self):
        for name in ('fresh_control', 'fastbuild', 'score', 'verify_fresh_control'):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                context = self.private_context(root)
                source = root / (name + '.py')
                raw = source.read_bytes()
                marker = root / 'cached-code-executed'
                # Keep future imports legal while injecting real executable code.
                injected = raw.replace(b'from __future__ import annotations\n', b'')
                injected = ('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("executed")\n').encode() + injected
                code = compile(injected, str(source), 'exec')
                metadata = source.stat()
                cache = Path(importlib.util.cache_from_source(str(source)))
                cache.parent.mkdir(exist_ok=True)
                cache.write_bytes(bytecode._code_to_timestamp_pyc(code, int(metadata.st_mtime), metadata.st_size))
                spec = importlib.util.spec_from_file_location('_private_cached_' + name, source)
                cached = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(cached)
                self.assertTrue(marker.exists(), 'timestamp cache was not executable')
                marker.unlink()
                canonical = sys.modules.get(name)
                loaded = context.load(name)
                self.assertFalse(marker.exists())
                self.assertEqual(loaded.__dict__['_ADMITTED_SOURCE_BYTES'], raw)
                self.assertIs(sys.modules.get(name), canonical)
                context.recheck()

    def test_changed_private_source_fails_before_build(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary).resolve()
            context = self.private_context(root)
            producer = context.load('fresh_control')
            source = root / 'score.py'
            source.write_bytes(source.read_bytes() + b'\n# changed after admission\n')
            with self.assertRaisesRegex(ValueError, 'executed source input changed'):
                producer.run_pair(root / 'missing-base', root / 'missing-candidate', root / 'out')
            self.assertFalse((root / 'out').exists())


if __name__ == '__main__':
    unittest.main()
