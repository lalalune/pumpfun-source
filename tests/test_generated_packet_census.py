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

    def verify(self, packet, mode=()):
        return subprocess.run([sys.executable, '-I', '-B', *mode, str(packet / 'verify.py')],
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

    def test_duplicate_decoded_manifest_names_are_rejected_in_all_modes(self):
        for tool, packet in self.packets():
            path = packet / 'manifest.json'
            original = path.read_text(encoding='utf-8')
            digest = json.loads(original)['summary.json']
            for key, value in (('"summary.json"', '0' * 64),
                               ('"summary.json"', digest),
                               ('"\\u0073ummary.json"', '0' * 64)):
                repeated = '{' + key + ': ' + json.dumps(value) + ',' + original.lstrip()[1:]
                path.write_text(repeated, encoding='utf-8')
                for mode in ((), ('-O',), ('-OO',)):
                    with self.subTest(tool=tool, key=key, value=value, mode=mode):
                        result = self.verify(packet, mode)
                        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                        self.assertIn('duplicate manifest key: summary.json', result.stdout)
                        self.assertNotIn('All checks passed.', result.stdout)
                        self.assertEqual(path.read_text(encoding='utf-8'), repeated)


class GeneratedAuditManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temporary.cleanup)
        cls.root = Path(cls.temporary.name).resolve()
        cohort = cls.root / 'source'
        names = [f'scripts/{name}.py' for name in (
            'analyze_program', 'deep_disassembly', 'analyze', 'window_elf_reader',
            'reconstruction_roadmap', 'revalidate_all')]
        names += ['reconstruction/tooling/revalidation-qualification/audit.py']
        for name in names:
            path = cohort / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, path)
        shutil.copytree(ROOT / 'evidence', cohort / 'evidence')

        def generate(script, output, arguments=()):
            result = subprocess.run([
                sys.executable, '-I', '-B', str(cohort / script), *arguments,
                '--output', str(output)], cwd=cohort, capture_output=True,
                text=True, timeout=60)
            if result.returncode:
                raise AssertionError(result.stdout + result.stderr)

        # Auditors see only a fresh static capture packet whose verifier hashes
        # files. Never run the repository's unrelated archived/program checks.
        generate('scripts/analyze_program.py', cohort / 'research/static-mayhem',
                 ('--program', 'mayhem'))
        assert sorted(p.name for p in (cohort / 'research').iterdir()) == ['static-mayhem']
        for label, script, arguments in (
            ('roadmap', 'scripts/reconstruction_roadmap.py', ()),
            ('root-audit', 'scripts/revalidate_all.py', ()),
            ('qualified-audit', 'reconstruction/tooling/revalidation-qualification/audit.py',
             ('--repo', str(cohort))),
        ):
            generate(script, cls.root / label, arguments)

    def test_generated_audit_manifests_reject_duplicates_in_all_modes(self):
        for label in ('roadmap', 'root-audit', 'qualified-audit'):
            packet = self.root / label
            path = packet / 'manifest.json'
            original = path.read_text(encoding='utf-8')
            manifest = json.loads(original)
            variants = [(original, True),
                        (original.replace('"summary.json"', '"\\u0073ummary.json"', 1), True),
                        (json.dumps({**manifest, 'summary.json': '0' * 64}), False),
                        ('{', False)]
            for key, value in (('"summary.json"', '0' * 64),
                               ('"summary.json"', manifest['summary.json']),
                               ('"\\u0073ummary.json"', '0' * 64)):
                variants.append(('{' + key + ':' + json.dumps(value) + ','
                                 + original.lstrip()[1:], False))
            for index, (raw, valid) in enumerate(variants):
                path.write_text(raw, encoding='utf-8')
                for mode in ((), ('-O',), ('-OO',)):
                    with self.subTest(producer=label, case=index, mode=mode):
                        result = subprocess.run([
                            sys.executable, '-I', '-B', *mode, str(packet / 'verify.py')],
                            capture_output=True, text=True, timeout=10)
                        self.assertEqual(result.returncode == 0, valid,
                                         result.stdout + result.stderr)
                        if index >= 4:
                            self.assertIn('duplicate manifest key: summary.json', result.stdout)
                        self.assertEqual(path.read_text(encoding='utf-8'), raw)
            path.write_text(original, encoding='utf-8')


if __name__ == '__main__':
    unittest.main()
