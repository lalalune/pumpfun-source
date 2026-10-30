#!/usr/bin/env python3
"""Compare CLI publication using captured bytes and real filesystem failures."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

try:
    import resource
except ImportError:
    resource = None

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import analyze
import compare
import deep_disassembly


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ComparePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='compare-publication-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.original_path = ROOT / 'evidence/dependencies/donation_relay/deployed.so'
        self.original = self.original_path.read_bytes()
        self.candidate = self.root / 'candidate.so'
        self.candidate.write_bytes(self.original)

    def tearDown(self):
        self.assertEqual(self.original_path.read_bytes(), self.original)

    def run_cli(self, output, *, padded=False, file_limit=None, umask=None):
        arguments = [str(ROOT / 'scripts/compare.py'), 'donation_relay',
                     str(self.candidate), '--output', str(output)]
        if padded:
            arguments.append('--pad-zero-to-allocation')
        if file_limit is not None:
            launcher = (
                'import os,resource,runpy,signal,sys; '
                'resource.setrlimit(resource.RLIMIT_FSIZE, '
                f'({file_limit}, {file_limit})); '
                'signal.signal(signal.SIGXFSZ, signal.SIG_IGN); '
                'sys.argv=sys.argv[1:]; '
                'sys.path.insert(0, os.path.dirname(sys.argv[0])); '
                'runpy.run_path(sys.argv[0], run_name="__main__")'
            )
            command = [sys.executable, '-B', '-c', launcher, *arguments]
        elif umask is not None:
            launcher = (
                'import os,runpy,sys; '
                f'os.umask({umask}); '
                'sys.argv=sys.argv[1:]; '
                'sys.path.insert(0, os.path.dirname(sys.argv[0])); '
                'runpy.run_path(sys.argv[0], run_name="__main__")'
            )
            command = [sys.executable, '-B', '-c', launcher, *arguments]
        else:
            command = [sys.executable, '-B', *arguments]
        return subprocess.run(command, capture_output=True, text=True, timeout=30)

    def read_report(self, output):
        return json.loads((output / 'comparison.json').read_text())

    def test_unpadded_equal_and_mismatch_publish_reports(self):
        for equal in (True, False):
            with self.subTest(equal=equal):
                candidate = self.original if equal else b'changed' + self.original[7:]
                self.candidate.write_bytes(candidate)
                output = self.root / ('equal' if equal else 'mismatch')
                completed = self.run_cli(output)
                self.assertEqual(completed.returncode, 0 if equal else 1, completed.stderr)
                report = self.read_report(output)
                self.assertEqual(report['full_byte_equality'], equal)
                self.assertEqual(report['candidate_sha256'], sha(candidate))
                self.assertEqual(json.loads(completed.stdout), report)
                self.assertEqual({p.name for p in output.iterdir()}, {'comparison.json'})
                self.assertEqual(self.candidate.read_bytes(), candidate)

    def test_padding_publishes_complete_artifact_matching_receipt(self):
        extent = analyze.elf_layout(self.original)['elf_extent']
        candidate = self.original[:extent]
        self.candidate.write_bytes(candidate)
        output = self.root / 'nested' / 'padded'
        completed = self.run_cli(output, padded=True)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = self.read_report(output)
        artifact = (output / 'candidate.deployed.so').read_bytes()
        self.assertEqual(artifact, self.original)
        self.assertEqual(len(artifact), report['candidate_bytes'])
        self.assertEqual(sha(artifact), report['candidate_sha256'])
        self.assertEqual(sha(candidate), report['candidate_input_sha256'])
        self.assertFalse(report['source_provenance_verified'])
        self.assertEqual(self.candidate.read_bytes(), candidate)
        self.assertEqual(list(output.parent.iterdir()), [output])

    @unittest.skipUnless(resource is not None and hasattr(resource, 'RLIMIT_FSIZE')
                         and hasattr(signal, 'SIGXFSZ'), 'requires Unix file size limits')
    def test_real_write_failures_leave_no_output_and_allow_retry(self):
        for padded, limit in ((False, 64), (True, 4096)):
            with self.subTest(padded=padded, limit=limit):
                parent = self.root / f'limited-{limit}'
                parent.mkdir()
                output = parent / 'comparison'
                failed = self.run_cli(output, padded=padded, file_limit=limit)
                self.assertNotEqual(failed.returncode, 0)
                self.assertIn('File too large', failed.stderr)
                self.assertFalse(output.exists(), 'failed write exposed a partial output')
                self.assertEqual(list(parent.iterdir()), [], 'temporary stage leaked')
                self.assertEqual(self.candidate.read_bytes(), self.original)
                retried = self.run_cli(output, padded=padded)
                self.assertEqual(retried.returncode, 0, retried.stderr)
                self.assertTrue(self.read_report(output)['full_byte_equality'])
                if padded:
                    self.assertEqual((output / 'candidate.deployed.so').read_bytes(), self.original)

    def test_existing_outputs_are_preserved(self):
        for kind in ('empty-directory', 'nonempty-directory', 'file', 'dangling-link'):
            with self.subTest(kind=kind):
                output = self.root / kind
                if kind.endswith('directory'):
                    output.mkdir()
                    if kind == 'nonempty-directory':
                        (output / 'prior.txt').write_bytes(b'prior receipt')
                elif kind == 'file':
                    output.write_bytes(b'prior file')
                else:
                    try:
                        output.symlink_to('absent-target', target_is_directory=True)
                    except OSError as error:
                        if os.name == 'nt':
                            continue
                        raise error
                before = output.lstat()
                completed = self.run_cli(output, padded=True)
                self.assertNotEqual(completed.returncode, 0)
                after = output.lstat()
                self.assertEqual((after.st_dev, after.st_ino), (before.st_dev, before.st_ino))
                if kind == 'nonempty-directory':
                    self.assertEqual((output / 'prior.txt').read_bytes(), b'prior receipt')
                elif kind == 'file':
                    self.assertEqual(output.read_bytes(), b'prior file')
                elif kind == 'dangling-link':
                    self.assertEqual(os.readlink(output), 'absent-target')
                else:
                    self.assertEqual(list(output.iterdir()), [])

    def test_concurrent_empty_destination_is_not_replaced(self):
        output = self.root / 'racing-output'
        native_rename = deep_disassembly.rename_directory
        identity = []

        def create_competing_directory(staged, destination):
            destination.mkdir()
            identity.append(destination.stat().st_ino)
            native_rename(staged, destination)

        arguments = ['compare.py', 'donation_relay', str(self.candidate),
                     '--output', str(output), '--pad-zero-to-allocation']
        with patch.object(sys, 'argv', arguments), contextlib.redirect_stdout(io.StringIO()):
            with patch.object(deep_disassembly, 'rename_directory', create_competing_directory):
                with self.assertRaises(FileExistsError):
                    compare.main()
        self.assertEqual(output.stat().st_ino, identity[0])
        self.assertEqual(list(output.iterdir()), [])
        self.assertEqual({p.name for p in self.root.iterdir()}, {'candidate.so', 'racing-output'})

    @unittest.skipIf(os.name == 'nt', 'POSIX umask semantics')
    def test_published_directory_and_files_keep_normal_umask(self):
        output = self.root / 'permissions'
        completed = self.run_cli(output, padded=True, umask=0o027)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(output.stat().st_mode & 0o777, 0o750)
        for path in output.iterdir():
            self.assertEqual(path.stat().st_mode & 0o777, 0o640)


if __name__ == '__main__':
    unittest.main()
