#!/usr/bin/env python3
"""Real captured-program packets must accept valid long output basenames."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import deep_disassembly as tool


def packet_hashes(path):
    return {entry.name: hashlib.sha256(entry.read_bytes()).hexdigest()
            for entry in path.iterdir() if entry.is_file()}


class PacketTemporaryNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='packet-names-')
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        cls.capture = ROOT / 'evidence/original/mayhem/deployed.so'
        cls.capture_hash = hashlib.sha256(cls.capture.read_bytes()).hexdigest()
        cls.control = cls.root / 'control'
        completed = cls.run_cli(cls.control)
        if completed.returncode:
            raise AssertionError(completed.stdout + completed.stderr)
        cls.control_hashes = packet_hashes(cls.control)

    @classmethod
    def tearDownClass(cls):
        if hashlib.sha256(cls.capture.read_bytes()).hexdigest() != cls.capture_hash:
            raise AssertionError('captured input changed')

    @classmethod
    def run_cli(cls, output):
        return subprocess.run(
            [sys.executable, '-B', str(ROOT / 'scripts/deep_disassembly.py'),
             '--program', 'mayhem', '--output', str(output)],
            capture_output=True, text=True, timeout=60)

    def verify_packet(self, path):
        completed = subprocess.run(
            [sys.executable, '-B', str(path / 'verify.py')],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(packet_hashes(path), self.control_hashes)

    def admit_long_path(self, parent, name):
        output = parent / name
        try:
            output.mkdir()
            output.rmdir()
        except OSError as error:
            self.skipTest(f'filesystem does not accept the requested basename: {error}')
        return output

    def test_long_ascii_and_multibyte_outputs_match_short_control(self):
        for label, name in (('ascii', 'p' * 240), ('unicode', '측' * 80)):
            with self.subTest(label=label), tempfile.TemporaryDirectory(dir=self.root) as folder:
                parent = Path(folder)
                output = self.admit_long_path(parent, name)
                completed = self.run_cli(output)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.verify_packet(output)
                self.assertEqual(list(parent.iterdir()), [output])

    @unittest.skipUnless(sys.platform == 'darwin' or sys.platform.startswith('linux'),
                         'native atomic directory exchange requires Linux or macOS')
    def test_long_existing_packet_keeps_complete_previous_packet(self):
        with tempfile.TemporaryDirectory(dir=self.root) as folder:
            parent = Path(folder)
            output = self.admit_long_path(parent, 'r' * 240)
            shutil.copytree(self.control, output)
            previous_hashes = packet_hashes(output)
            completed = self.run_cli(output)
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.verify_packet(output)
            siblings = [path for path in parent.iterdir() if path != output]
            self.assertEqual(len(siblings), 1)
            self.assertIn('.previous-', siblings[0].name)
            self.assertEqual(packet_hashes(siblings[0]), previous_hashes)
            self.verify_packet(siblings[0])

    def test_multibyte_temporary_components_leave_suffix_room(self):
        with tempfile.TemporaryDirectory(dir=self.root) as folder:
            output = Path(folder) / ('측' * 80)
            for label in ('staging', 'previous'):
                with self.subTest(label=label):
                    sibling = tool.temporary_sibling(output, label)
                    self.assertEqual(sibling.parent, output.parent)
                    self.assertLessEqual(len(os.fsencode(sibling.name)), 255)
                    sibling.name.encode('utf-8', errors='strict')
                    sibling.rmdir()

    def test_standalone_audit_accepts_long_output(self):
        with tempfile.TemporaryDirectory(dir=self.root) as folder:
            repo = Path(folder)
            scripts = repo / 'scripts'
            scripts.mkdir()
            shutil.copyfile(ROOT / 'scripts/revalidate_all.py', scripts / 'revalidate_all.py')
            packet = repo / 'research/captured-bytes'
            packet.mkdir(parents=True)
            shutil.copyfile(self.capture, packet / 'mayhem.so')
            (packet / 'manifest.json').write_text(
                json.dumps({'mayhem.so': self.capture_hash}), encoding='utf-8')
            for name in ('short-audit', 'a' * 240):
                with self.subTest(name_length=len(name)):
                    output = self.admit_long_path(repo, name)
                    completed = subprocess.run(
                        [sys.executable, '-B', str(scripts / 'revalidate_all.py'),
                         '--output', str(output)], cwd=repo,
                        capture_output=True, text=True, timeout=30)
                    self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                    summary = json.loads((output / 'summary.json').read_text())
                    self.assertEqual(summary['pass'], 1)
                    self.assertEqual(summary['fail'], 0)
                    verified = subprocess.run(
                        [sys.executable, '-B', str(output / 'verify.py')], cwd=repo,
                        capture_output=True, text=True, timeout=30)
                    self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
            self.assertEqual(hashlib.sha256((packet / 'mayhem.so').read_bytes()).hexdigest(),
                             self.capture_hash)

    @unittest.skipIf(os.name == 'nt', 'POSIX umask semantics')
    def test_existing_collision_and_short_name_permissions_are_preserved(self):
        with tempfile.TemporaryDirectory(dir=self.root) as folder:
            parent = Path(folder)
            first = parent / f'.packet.staging-{os.getpid()}-{"a" * 32}'
            first.mkdir()
            (first / 'prior.txt').write_bytes(b'preserve me')
            values = [SimpleNamespace(hex='a' * 32), SimpleNamespace(hex='b' * 32)]
            old_umask = os.umask(0o027)
            try:
                with patch.object(tool.uuid, 'uuid4', side_effect=values):
                    sibling = tool.temporary_sibling(parent / 'packet', 'staging')
            finally:
                os.umask(old_umask)
            self.assertEqual(sibling.name, f'.packet.staging-{os.getpid()}-{"b" * 32}')
            self.assertEqual(sibling.stat().st_mode & 0o777, 0o750)
            self.assertEqual((first / 'prior.txt').read_bytes(), b'preserve me')


if __name__ == '__main__':
    unittest.main()
