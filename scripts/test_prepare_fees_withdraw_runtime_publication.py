"""The focused Fees runtime is published only after complete preparation."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


class FeesRuntimePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='fees-runtime-publication-')
        self.root = Path(self.temporary.name)
        self.package = self.root / 'repro/pump_fees/sharing-second-pump-cpi-v144'
        (self.package / 'source').mkdir(parents=True)
        source_map = {}
        for index in range(26):
            name = f'source-{index}.rs'
            data = f'// source {index}\n'.encode()
            (self.package / 'source' / name).write_bytes(data)
            source_map[name] = sha(data)

        archive = self.package / 'runtime-repository.tar.gz'
        corrected = json.dumps(source_map).encode()
        with tarfile.open(archive, 'w:gz') as output:
            for name, data in [
                ('validation-layer/harness/fees_donation_business_differential.py',
                 b'# sealed focused harness\n'),
                ('validation-layer/corrected-source-sha256.json', corrected),
            ]:
                member = tarfile.TarInfo(name)
                member.size = len(data)
                output.addfile(member, io.BytesIO(data))
        manifest = {'runtime-repository.tar.gz': sha(archive.read_bytes())}
        (self.package / 'manifest.json').write_text(json.dumps(manifest))
        (self.package / 'manifest.sha256').write_text(
            sha((self.package / 'manifest.json').read_bytes()) + '  manifest.json\n')

        spec = importlib.util.spec_from_file_location(
            'fees_runtime_under_test',
            SCRIPTS / 'prepare_fees_withdraw_runtime.py',
        )
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        tool.ROOT = self.root
        tool.PACKAGE = self.package
        tool.HISTORICAL_SEAL = sha((self.package / 'manifest.json').read_bytes())
        tool.current_binding = lambda: (
            {'current.rs': sha(b'current')},
            {'candidate_sha256': 'c' * 64},
        )
        self.tool = tool

    def tearDown(self):
        self.temporary.cleanup()

    def test_late_witness_failure_leaves_no_partial_output(self):
        output = self.root / 'runtime'
        real_write_text = Path.write_text

        def fail_witness(path, *args, **kwargs):
            if path.name == 'source-binding-witness.json':
                raise OSError('injected witness write failure')
            return real_write_text(path, *args, **kwargs)

        with mock.patch.object(Path, 'write_text', fail_witness):
            with self.assertRaisesRegex(OSError, 'injected witness write failure'):
                self.tool.prepare(output)

        self.assertFalse(output.exists(), 'failed preparation published a partial runtime')
        self.assertEqual(list(output.parent.glob('.runtime.*')), [])

    def test_successful_preparation_publishes_complete_runtime(self):
        output = self.root / 'runtime'
        result = self.tool.prepare(output)
        self.assertEqual(result['status'], 'PASS')
        self.assertEqual(result['source_inputs'], 26)
        self.assertTrue((output / 'source-binding-witness.json').is_file())
        self.assertTrue((output / 'historical-corrected-source-sha256.json').is_file())
        self.assertEqual(list(output.parent.glob('.runtime.*')), [])

    def test_late_destination_is_preserved(self):
        output = self.root / 'runtime'
        real_write = Path.write_text

        def create_competitor(path, *args, **kwargs):
            result = real_write(path, *args, **kwargs)
            if path.name == 'source-binding-witness.json':
                output.mkdir()
            return result

        with mock.patch.object(Path, 'write_text', create_competitor):
            with self.assertRaises(FileExistsError):
                self.tool.prepare(output)
        self.assertTrue(output.is_dir())
        self.assertEqual(list(output.iterdir()), [])
        self.assertEqual(list(output.parent.glob('.runtime.*')), [])

    def test_published_directory_uses_normal_umask(self):
        output = self.root / 'runtime'
        previous = os.umask(0o027)
        try:
            self.tool.prepare(output)
        finally:
            os.umask(previous)
        self.assertEqual(output.stat().st_mode & 0o777, 0o750)


if __name__ == '__main__':
    unittest.main()
