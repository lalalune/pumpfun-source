import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


def runner_module():
    spec = importlib.util.spec_from_file_location('output_runner', Path(__file__).with_name('experiment_runner.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'fcntl': types.ModuleType('fcntl')}): spec.loader.exec_module(module)
    return module


class OutputBoundaryTests(unittest.TestCase):
    def fixture(self, root):
        attempt = root / 'attempt'
        (attempt / 'output').mkdir(parents=True)
        for name in ('stdout.log', 'stderr.log'): (attempt / name).write_bytes(b'')
        return attempt

    def test_root_and_nested_directory_links_are_rejected_before_target_read(self):
        runner = runner_module()
        for nested in (False, True):
            with self.subTest(nested=nested), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                attempt = self.fixture(root)
                outside = root / 'outside'
                outside.mkdir()
                (outside / 'result').write_bytes(b'owned synthetic target')
                link = attempt / 'output' / 'nested' if nested else attempt / 'output'
                if not nested: link.rmdir()
                if os.name == 'nt':
                    subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)], check=True, capture_output=True)
                else: link.symlink_to(outside, target_is_directory=True)
                read = Path.read_bytes
                def guarded_read(path):
                    if path.is_relative_to(link): raise AssertionError('target bytes read')
                    return read(path)
                try:
                    with patch.object(Path, 'read_bytes', guarded_read):
                        with self.assertRaises(ValueError): runner.artifacts(attempt)
                finally:
                    if os.name == 'nt': os.rmdir(link)
                    else: link.unlink()

    def test_disappearing_output_directory_is_not_a_partial_manifest(self):
        runner = runner_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            attempt = self.fixture(root)
            nested = attempt / 'output/nested'
            nested.mkdir()
            (nested / 'result').write_bytes(b'result')
            expected = runner.artifacts(attempt)
            moved = root / 'moved'
            scandir = os.scandir
            def disappear(path):
                if Path(path) == nested: nested.rename(moved)
                return scandir(path)
            try:
                with patch.object(os, 'scandir', side_effect=disappear):
                    with self.assertRaises((OSError, ValueError)): runner.artifacts(attempt)
            finally:
                if moved.exists(): moved.rename(nested)
            self.assertEqual(runner.artifacts(attempt), expected)


if __name__ == '__main__': unittest.main()
