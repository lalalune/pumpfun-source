"""Fault-injection tests for dependency-cache publication; no compiler needed."""
import contextlib
import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bootstrap


class DependencyCacheTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / 'source'
        (self.source / 'deps').mkdir(parents=True)
        (self.source / 'deps/library.rlib').write_bytes(b'complete library')
        self.template = self.root / 'cache/template-target-sbpf'

    def copy(self, command, **kwargs):
        self.assertEqual(command[:2], ['cp', '-cRp'])
        self.assertTrue(kwargs['check'])
        self.assertFalse(self.template.exists())
        shutil.copytree(command[2], command[3])

    def fail_copy(self, command, **kwargs):
        target = Path(command[3])
        target.mkdir(parents=True)
        (target / 'partial').write_bytes(b'partial')
        raise subprocess.CalledProcessError(1, command)

    def assert_no_staging(self):
        self.assertEqual(list(self.template.parent.glob('*.stage.*')), [])

    def test_failed_copy_is_not_published_and_retry_succeeds(self):
        with patch.object(bootstrap.subprocess, 'run', side_effect=self.fail_copy):
            with self.assertRaises(subprocess.CalledProcessError):
                bootstrap.publish_dependency_cache(self.source, self.template)
        self.assertFalse(self.template.exists())
        self.assert_no_staging()
        with patch.object(bootstrap.subprocess, 'run', side_effect=self.copy):
            self.assertTrue(bootstrap.publish_dependency_cache(self.source, self.template))
        self.assertEqual((self.template / 'deps/library.rlib').read_bytes(), b'complete library')
        self.assert_no_staging()

    def test_existing_cache_is_preserved(self):
        self.template.mkdir(parents=True)
        (self.template / 'previous').write_bytes(b'previous')
        with patch.object(bootstrap.subprocess, 'run') as run:
            self.assertFalse(bootstrap.publish_dependency_cache(self.source, self.template))
            run.assert_not_called()
        self.assertEqual((self.template / 'previous').read_bytes(), b'previous')

    def test_dangling_symlink_is_not_replaced(self):
        self.template.parent.mkdir()
        self.template.symlink_to(self.root / 'missing')
        with patch.object(bootstrap.subprocess, 'run') as run:
            self.assertFalse(bootstrap.publish_dependency_cache(self.source, self.template))
            run.assert_not_called()
        self.assertTrue(self.template.is_symlink())

    def test_promotion_failure_cleans_up(self):
        with patch.object(bootstrap.subprocess, 'run', side_effect=self.copy), patch.object(Path, 'rename', side_effect=OSError('promotion failed')):
            with self.assertRaises(OSError):
                bootstrap.publish_dependency_cache(self.source, self.template)
        self.assertFalse(self.template.exists())
        self.assert_no_staging()

    def test_non_directory_copy_is_rejected(self):
        def copy_file(command, **kwargs):
            Path(command[3]).write_bytes(b'file')
        with patch.object(bootstrap.subprocess, 'run', side_effect=copy_file):
            with self.assertRaises(RuntimeError):
                bootstrap.publish_dependency_cache(self.source, self.template)
        self.assertFalse(self.template.exists())
        self.assert_no_staging()

    def test_warm_cli_does_not_leave_partial_cache(self):
        cache = self.template.parent
        hybrid = cache / 'toolchains/hybrid144'
        with contextlib.ExitStack() as stack:
            stack.enter_context(patch.object(bootstrap, 'HOME_CACHE', cache))
            stack.enter_context(patch.object(bootstrap, 'HYBRID', hybrid))
            stack.enter_context(patch.object(bootstrap, 'check_linux_libs', return_value=[]))
            stack.enter_context(patch.object(bootstrap, 'hybrid_ok', return_value=True))
            stack.enter_context(patch.object(bootstrap.subprocess, 'check_output', return_value=str(hybrid / 'rust')))
            stack.enter_context(patch.object(bootstrap.subprocess, 'run', side_effect=self.fail_copy))
            stack.enter_context(patch('sys.argv', ['bootstrap', '--sdk-check', 'skip', '--warm']))
            stack.enter_context(patch.dict('sys.modules', {'fastbuild': type('FakeBuild', (), {'build': staticmethod(lambda *a, **kw: {'ok': True})})}))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            with self.assertRaises(subprocess.CalledProcessError):
                bootstrap.main()
        self.assertFalse(self.template.exists())
        self.assert_no_staging()


if __name__ == '__main__':
    unittest.main()
