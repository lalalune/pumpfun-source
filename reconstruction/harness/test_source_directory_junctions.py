import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import source_inputs


def load_runner():
    spec = importlib.util.spec_from_file_location('junction_runner', Path(__file__).with_name('experiment_runner.py'))
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'fcntl': types.ModuleType('fcntl')}): spec.loader.exec_module(module)
    return module


class SourceDirectoryLinkTests(unittest.TestCase):
    def test_directory_links_are_rejected_before_reading_target_bytes(self):
        runner = load_runner()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, outside = root / 'source', root / 'outside'
            source.mkdir()
            outside.mkdir()
            (outside / 'input.rs').write_bytes(b'synthetic external input')
            link = source / 'nested'
            if os.name == 'nt':
                subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(outside)],
                               check=True, capture_output=True)
            else:
                link.symlink_to(outside, target_is_directory=True)
            try:
                for read in (runner.manifest, source_inputs.snapshot):
                    with self.subTest(reader=read.__module__), \
                         patch.object(Path, 'read_bytes', side_effect=AssertionError('outside read')), \
                         patch.object(Path, 'open', side_effect=AssertionError('outside open')):
                        with self.assertRaises(ValueError): read(source)
            finally:
                if os.name == 'nt': os.rmdir(link)
                else: link.unlink()
            self.assertEqual(runner.manifest(source), {})
            self.assertEqual(source_inputs.snapshot(source)['files'], [])


if __name__ == '__main__': unittest.main()
