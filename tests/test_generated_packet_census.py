"""Generated capture-analysis verifiers must account for the packet directory."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
GENERATORS = {
    'analyze_program': ['--program', 'mayhem'],
    'deep_disassembly': ['--program', 'mayhem'],
    'deep_section_analysis': ['--program', 'mayhem'],
    'bytecode_signatures': [],
}


class GeneratedPacketCensusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name)
        for tool, arguments in GENERATORS.items():
            result = subprocess.run(
                [sys.executable, '-B', str(ROOT / 'scripts' / (tool + '.py')),
                 *arguments, '--output', str(cls.root / tool)],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)

    def verify(self, packet):
        return subprocess.run([sys.executable, '-I', '-B', str(packet / 'verify.py')],
                              capture_output=True, text=True, timeout=10)

    def packets(self):
        for tool in GENERATORS:
            with tempfile.TemporaryDirectory() as temporary:
                packet = Path(temporary) / 'packet'
                shutil.copytree(self.root / tool, packet)
                yield tool, packet

    def assert_census_failure(self, packet):
        result = self.verify(packet)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('packet directory entry set mismatch', result.stdout)

    def test_unmodified_captured_packets_verify(self):
        for tool, packet in self.packets():
            with self.subTest(tool=tool):
                result = self.verify(packet)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn('All checks passed.', result.stdout)

    def test_extra_files_and_directories_are_rejected_without_deletion(self):
        for tool, packet in self.packets():
            for directory in (False, True):
                with self.subTest(tool=tool, directory=directory):
                    extra = packet / 'unlisted-analysis'
                    manifest = (packet / 'manifest.json').read_bytes()
                    if directory:
                        extra.mkdir()
                    else:
                        extra.write_bytes(b'unreviewed analysis')
                    try:
                        self.assert_census_failure(packet)
                        self.assertTrue(extra.exists())
                        self.assertEqual((packet / 'manifest.json').read_bytes(), manifest)
                    finally:
                        extra.rmdir() if directory else extra.unlink()

    def test_extra_symlink_is_rejected_without_following_it(self):
        for tool, packet in self.packets():
            with self.subTest(tool=tool):
                extra = packet / 'unlisted-link'
                try:
                    extra.symlink_to('absent-target')
                except (OSError, NotImplementedError) as error:
                    self.skipTest(f'symlinks unavailable: {error}')
                self.assert_census_failure(packet)
                self.assertTrue(extra.is_symlink())

    def test_missing_expected_file_is_rejected(self):
        for tool, packet in self.packets():
            with self.subTest(tool=tool):
                (packet / 'README.md').unlink()
                result = self.verify(packet)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('FAIL:', result.stdout)

    def test_existing_hash_checks_still_reject_changed_bytes(self):
        for tool, packet in self.packets():
            with self.subTest(tool=tool):
                with (packet / 'README.md').open('ab') as stream:
                    stream.write(b'\nchanged\n')
                result = self.verify(packet)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('README.md hash mismatch', result.stdout)

    def test_manifest_membership_is_checked_independently(self):
        for tool, packet in self.packets():
            with self.subTest(tool=tool):
                path = packet / 'manifest.json'
                manifest = json.loads(path.read_text())
                del manifest['README.md']
                path.write_text(json.dumps(manifest))
                result = self.verify(packet)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('manifest artifact set mismatch', result.stdout)


if __name__ == '__main__':
    unittest.main()
