"""Check generated roadmap membership using all three captured program analyses."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
SOURCE_PACKET = None
RUNS = []


class RoadmapManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.generated = tempfile.TemporaryDirectory(prefix='roadmap-members-')
        cls.addClassCleanup(cls.generated.cleanup)
        cls.packet = Path(cls.generated.name) / 'packet'
        if SOURCE_PACKET:
            shutil.copytree(SOURCE_PACKET, cls.packet)
        else:
            generated = subprocess.run([
                sys.executable, '-B', str(ROOT / 'scripts/reconstruction_roadmap.py'),
                '--output', str(cls.packet),
            ], capture_output=True, text=True, timeout=60)
            if generated.returncode:
                raise RuntimeError(generated.stdout + generated.stderr)
        cls.members = json.loads((cls.packet / 'manifest.json').read_text())
        if set(cls.members) != {'README.md', 'summary.json', 'reconstruction-plan.json',
                                'verify.py', 'pump-details.json', 'pump_amm-details.json',
                                'mayhem-details.json'}:
            raise RuntimeError('expected the actual three-program roadmap packet')

    def verify(self, folder, case):
        result = subprocess.run([sys.executable, '-I', '-B', str(folder / 'verify.py')],
                                capture_output=True, text=True, timeout=30)
        RUNS.append({'case': case, 'returncode': result.returncode,
                     'last_line': result.stdout.strip().splitlines()[-1:]})
        return result

    def test_unmodified_generated_packet_passes(self):
        result = self.verify(self.packet, 'intact')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_omitted_members_cannot_pass_even_when_removed_from_manifest(self):
        for name in self.members:
            for remove_file in (False, True):
                if name == 'verify.py' and remove_file:
                    continue  # The verifier must exist to execute the admission check.
                with self.subTest(member=name, remove_file=remove_file), tempfile.TemporaryDirectory() as temporary:
                    packet = Path(temporary) / 'packet'
                    shutil.copytree(self.packet, packet)
                    manifest = dict(self.members)
                    manifest.pop(name)
                    (packet / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
                    if remove_file:
                        (packet / name).unlink()
                    result = self.verify(packet, f'omit:{name}:delete={remove_file}')
                    self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                    self.assertIn('manifest omits required roadmap artifacts', result.stdout)

    def test_empty_or_nonmapping_manifest_fails_explicitly(self):
        for value in ({}, [], None):
            with self.subTest(manifest=value), tempfile.TemporaryDirectory() as temporary:
                packet = Path(temporary) / 'packet'
                shutil.copytree(self.packet, packet)
                (packet / 'manifest.json').write_text(json.dumps(value), encoding='utf-8')
                result = self.verify(packet, f'manifest:{value!r}')
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn('manifest omits required roadmap artifacts', result.stdout)

    def test_adapter_extension_is_accepted_only_with_matching_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            packet = Path(temporary) / 'packet'
            shutil.copytree(self.packet, packet)
            extra = packet / 'adapter-inputs.json'
            extra.write_text('{"scope":"extension control"}\n', encoding='utf-8')
            manifest = dict(self.members)
            manifest[extra.name] = hashlib.sha256(extra.read_bytes()).hexdigest()
            (packet / 'manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
            result = self.verify(packet, 'bound-extension')
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            extra.write_text('changed\n', encoding='utf-8')
            result = self.verify(packet, 'changed-extension')
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn('adapter-inputs.json hash mismatch', result.stdout)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--packet', type=Path, help='Use an already generated before packet')
    parser.add_argument('--report', type=Path)
    options, remaining = parser.parse_known_args()
    SOURCE_PACKET = options.packet
    result = unittest.main(argv=[sys.argv[0], *remaining], exit=False)
    # A renamed, emptied or silently skipped case still exits 0 through
    # wasSuccessful(); the package is checked for exactly four passing tests.
    passed = (result.result.wasSuccessful() and result.result.testsRun == 4
              and not result.result.skipped)
    if options.report:
        with options.report.open('x', encoding='utf-8') as stream:
            json.dump({'python': sys.version, 'passed': passed,
                       'tests_run': result.result.testsRun,
                       'skipped': [case.id() for case, _ in result.result.skipped],
                       'runs': RUNS}, stream, indent=2)
            stream.write('\n')
    sys.exit(0 if passed else 1)
