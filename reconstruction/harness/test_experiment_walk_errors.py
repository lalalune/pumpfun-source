import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


def load_runner():
    spec = importlib.util.spec_from_file_location('walk_error_runner', Path(__file__).with_name('experiment_runner.py'))
    module = importlib.util.module_from_spec(spec)
    # These tests exercise only manifest(), not POSIX locking or processes.
    if sys.platform == 'win32':
        with patch.dict(sys.modules, {'fcntl': types.ModuleType('fcntl')}): spec.loader.exec_module(module)
    else:
        spec.loader.exec_module(module)
    return module


class WalkErrorTests(unittest.TestCase):
    def test_unreadable_subtree_cannot_be_omitted_from_source_identity(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / 'nested'
            nested.mkdir()
            (nested / 'lib.rs').write_bytes(b'synthetic source')
            original_scandir = runner.os.scandir
            def scandir(path):
                if Path(path) == nested:
                    raise PermissionError('synthetic read denial')
                return original_scandir(path)
            with patch.object(runner.os, 'scandir', side_effect=scandir):
                with self.assertRaisesRegex(PermissionError, 'synthetic read denial'):
                    runner.manifest(root)
            self.assertEqual(set(runner.manifest(root)), {'nested/lib.rs'})


if __name__ == '__main__': unittest.main()
