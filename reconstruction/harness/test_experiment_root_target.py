"""Only a root target directory is generated; a file named target is source."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


def runner_module():
    spec = importlib.util.spec_from_file_location('root_target_runner', Path(__file__).with_name('experiment_runner.py'))
    module = importlib.util.module_from_spec(spec)
    if os.name == 'nt':
        # Staging uses real filesystem operations; these portable tests never
        # acquire a lock or execute a trial. POSIX trial tests below use fcntl.
        with patch.dict(sys.modules, {'fcntl': types.ModuleType('fcntl')}):
            spec.loader.exec_module(module)
    else:
        spec.loader.exec_module(module)
    return module


class RootTargetStagingTests(unittest.TestCase):
    def test_root_target_file_is_preserved_in_the_real_staged_tree(self):
        runner = runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source'
            source.mkdir()
            payload = b'input data\x00\xff\r\n'
            (source / 'target').write_bytes(payload)
            before = runner.manifest(source)
            staged = Path(temporary) / 'staged'
            shutil.copytree(source, staged, ignore=runner.stage_ignore(source))
            self.assertEqual(runner.manifest(staged), before)
            self.assertEqual((staged / 'target').read_bytes(), payload)

    def test_root_target_directory_is_omitted_but_nested_target_inputs_remain(self):
        runner = runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source'
            for name in ('target/generated', 'nested/target/input', 'other/target'):
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(name.encode())
            staged = Path(temporary) / 'staged'
            shutil.copytree(source, staged, ignore=runner.stage_ignore(source))
            self.assertEqual(runner.manifest(staged), runner.manifest(source))
            self.assertFalse((staged / 'target').exists())
            self.assertEqual((staged / 'nested/target/input').read_bytes(), b'nested/target/input')
            self.assertEqual((staged / 'other/target').read_bytes(), b'other/target')


@unittest.skipIf(os.name == 'nt', 'complete experiment trials require POSIX locks and process groups')
class RootTargetTrialTests(unittest.TestCase):
    def test_trial_reads_root_target_and_resumes_until_its_bytes_change(self):
        runner = runner_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / 'source'
            source.mkdir()
            (source / 'target').write_bytes(b'first')
            destination = root / 'trial'
            command = [sys.executable, '-c',
                       'from pathlib import Path; import sys; '
                       'Path(sys.argv[2], "result").write_bytes(Path(sys.argv[1], "target").read_bytes())',
                       '{source}', '{out}']
            first = runner.run_trial(source, command, destination)
            self.assertEqual(first['status'], 'pass')
            self.assertEqual((destination / first['attempt'] / 'output/result').read_bytes(), b'first')
            self.assertTrue(runner.run_trial(source, command, destination)['reused'])
            (source / 'target').write_bytes(b'second')
            second = runner.run_trial(source, command, destination)
            self.assertEqual(second['status'], 'pass')
            self.assertFalse(second['reused'])
            self.assertNotEqual(second['attempt'], first['attempt'])
            self.assertEqual((destination / second['attempt'] / 'output/result').read_bytes(), b'second')
            self.assertTrue((destination / first['attempt']).is_dir())
            receipt = json.loads((destination / 'latest.json').read_text())
            self.assertEqual(receipt['attempt'], second['attempt'])


if __name__ == '__main__':
    unittest.main()
