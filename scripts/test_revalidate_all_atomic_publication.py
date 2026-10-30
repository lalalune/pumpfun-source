"""Research revalidation reports are published as one complete packet."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
import revalidate_all as runner
import deep_disassembly as publisher


class RevalidateAllAtomicPublicationTests(unittest.TestCase):
    def invoke(self, repo, output):
        argv = [
            str(Path(runner.__file__)),
            '--output', str(output),
        ]
        with mock.patch.object(runner, 'REPO', repo), \
                mock.patch.object(sys, 'argv', argv):
            runner.main()

    def repository(self, root):
        repo = root / 'repo'
        (repo / 'research/first').mkdir(parents=True)
        return repo

    def test_late_report_failure_leaves_no_partial_audit(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.repository(root)
            output = root / 'audit'
            original_write = Path.write_text

            def fail_summary(path, *args, **kwargs):
                if path.name == 'summary.json':
                    raise OSError('injected summary write failure')
                return original_write(path, *args, **kwargs)

            with mock.patch.object(Path, 'write_text', fail_summary):
                with self.assertRaisesRegex(
                        OSError, 'injected summary write failure'):
                    self.invoke(repo, output)

            self.assertFalse(
                output.exists(),
                'failed revalidation published partial reports')
            self.assertEqual(list(root.glob('.audit.staging-*')), [])

    def test_complete_audit_publishes_manifest_and_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.repository(root)
            output = root / 'audit'

            self.invoke(repo, output)

            self.assertEqual(
                sorted(path.name for path in output.iterdir()),
                [
                    'README.md', 'failed.json', 'invocation-errors.json',
                    'manifest.json', 'passed.json', 'results.json',
                    'skipped.json', 'summary.json', 'verify.py',
                ],
            )
            self.assertEqual(
                json.loads((output / 'invocation-errors.json').read_text()), [])
            self.assertEqual(
                json.loads((output / 'results.json').read_text()),
                [{
                    'packet': 'first',
                    'has_verify': False,
                    'has_manifest': False,
                    'manifest_check': {'status': 'skipped'},
                    'verify_check': {'status': 'skipped'},
                    'overall': 'no_verification',
                }],
            )
            self.assertEqual(list(root.glob('.audit.staging-*')), [])

    def test_existing_audit_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.repository(root)
            output = root / 'audit'
            output.mkdir()
            marker = output / 'prior.txt'
            marker.write_text('prior complete audit')

            with self.assertRaises(FileExistsError):
                self.invoke(repo, output)

            self.assertEqual(marker.read_text(), 'prior complete audit')
            self.assertEqual(
                sorted(path.name for path in output.iterdir()), ['prior.txt'])

    def test_late_destination_is_not_replaced(self):
        for late_file in (False, True):
            with self.subTest(late_file=late_file), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                repo = self.repository(root)
                output = root / 'audit'
                rename = publisher.rename_directory

                def compete(source, destination, **kwargs):
                    output.mkdir()
                    if late_file:
                        (output / 'user-evidence').write_bytes(b'keep me')
                    return rename(source, destination, **kwargs)

                with mock.patch.object(publisher, 'rename_directory', compete):
                    with self.assertRaises(FileExistsError):
                        self.invoke(repo, output)
                self.assertEqual(list(root.glob('.audit.staging-*')), [])
                self.assertEqual(sorted(p.name for p in output.iterdir()),
                                 ['user-evidence'] if late_file else [])
                if late_file:
                    self.assertEqual((output / 'user-evidence').read_bytes(), b'keep me')

    @unittest.skipUnless(os.name == 'posix', 'POSIX permission check')
    def test_audit_preserves_umask_and_source_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.repository(root)
            source = repo / 'research/first/source.txt'
            source.write_bytes(b'original evidence')
            output = root / 'audit'
            previous = os.umask(0o027)
            try:
                self.invoke(repo, output)
            finally:
                os.umask(previous)
            self.assertEqual(source.read_bytes(), b'original evidence')
            self.assertEqual(output.stat().st_mode & 0o777, 0o750)
            for path in output.iterdir():
                self.assertEqual(path.stat().st_mode & 0o777, 0o640, path.name)

    def test_success_does_not_delete_a_recreated_staging_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = self.repository(root)
            output = root / 'audit'
            rename = publisher.rename_directory
            recreated = []

            def publish_then_recreate(source, destination, **kwargs):
                rename(source, destination, **kwargs)
                source.mkdir()
                (source / 'late-writer').write_bytes(b'keep me')
                recreated.append(source)

            with mock.patch.object(publisher, 'rename_directory', publish_then_recreate):
                self.invoke(repo, output)
            self.assertTrue((output / 'manifest.json').is_file())
            self.assertEqual((recreated[0] / 'late-writer').read_bytes(), b'keep me')


if __name__ == '__main__':
    unittest.main()
