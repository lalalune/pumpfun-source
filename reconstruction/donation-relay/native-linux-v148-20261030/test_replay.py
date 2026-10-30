"""Finite no-compiler packet, path-preservation and real process-guard checks."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replay
import verify

parser = argparse.ArgumentParser()
parser.add_argument('--repo', type=Path, required=True)
args, rest = parser.parse_known_args()
REPO = args.repo.resolve()


class ReplayChecks(unittest.TestCase):
    def test_actual_packet_and_source_capture(self):
        result = verify.verify(REPO)
        self.assertEqual(result['meaningfulBytesLiteralEqual'], 818280)
        self.assertFalse(result['wholeCapturedAllocationEqualsCompilerFile'])
        self.assertFalse(result['newPublicLauncherColdBuildTested'])

    def test_real_source_byte_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / 'source'
            shutil.copytree(REPO / 'programs/donation-relay', clone)
            p = clone / 'src/lib.rs'; p.write_bytes(p.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'source hash/type mismatch'):
                replay.check_source(clone, modes=False)

    def test_consumed_layout_byte_mutation_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            clone = Path(tmp) / 'config'; shutil.copytree(HERE / 'layout', clone)
            p = clone / 'ordered.ld'; p.write_bytes(p.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'configuration hash mismatch'):
                replay.check_config(clone)

    def test_existing_output_is_preserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'previous result'; work.mkdir()
            sentinel = work / 'keep'; sentinel.write_bytes(b'preserve prior attempt')
            with self.assertRaisesRegex(ValueError, 'work path already exists'):
                replay.stage(REPO, '/not-needed/sdk', '/not-needed/registry', work)
            self.assertEqual(sentinel.read_bytes(), b'preserve prior attempt')
            self.assertEqual(list(work.iterdir()), [sentinel])

    def test_input_overlap_rejected_before_any_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); repo = root / 'repo'; source = repo / 'programs/donation-relay'
            sdk, registry = root / 'sdk', root / 'registry'
            for p in [source, sdk, registry]:
                p.mkdir(parents=True); (p / 'keep').write_bytes(b'unchanged')
            for p in [source, sdk, registry]:
                with self.subTest(root=p), self.assertRaisesRegex(ValueError, 'overlaps an authenticated input root'):
                    replay.stage(repo, sdk, registry, p / 'new replay')
                self.assertEqual(sorted(x.name for x in p.iterdir()), ['keep'])
                self.assertEqual((p / 'keep').read_bytes(), b'unchanged')

    def test_wrong_archive_fails_before_output_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); archive = root / 'wrong.tar.bz2'; archive.write_bytes(b'not the SDK')
            out = root / 'new-sdk'
            with self.assertRaisesRegex(ValueError, 'SDK archive differs'):
                replay.extract_sdk(archive, out)
            self.assertFalse(out.exists())

    def test_wrong_locked_archive_fails_before_registry_creation(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp); archives = root / 'archives'; archives.mkdir()
            name = replay.load('registry-inputs.json')['packages'][0]['name']
            (archives / (name + '.crate')).write_bytes(b'checksum mismatch')
            out = root / 'new-registry'
            with self.assertRaisesRegex(ValueError, 'locked archive mismatch'):
                replay.prepare_registry(archives, out)
            self.assertFalse(out.exists())

    def test_real_process_disk_guard_stops_owned_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = replay.monitored([sys.executable, '-c', 'import time; time.sleep(30)'],
                                      Path(tmp), 'disk', 5, 1 << 63)
            self.assertEqual(result['guardFired'], 'HOST_DISK_FLOOR_128_MIB')
            self.assertNotEqual(result['returncode'], 0)
            self.assertFalse(result['groupRemained'])

    def test_real_process_timeout_stops_owned_group(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = replay.monitored([sys.executable, '-c', 'import time; time.sleep(30)'],
                                      Path(tmp), 'timeout', .02, 0)
            self.assertEqual(result['guardFired'], 'TIMEOUT')
            self.assertNotEqual(result['returncode'], 0)
            self.assertFalse(result['groupRemained'])

    def test_statvfs_uses_supplied_filesystem(self):
        root = Path('/dev/shm')
        if not root.is_dir():
            self.skipTest('no second temporary filesystem')
        with tempfile.TemporaryDirectory(dir=root) as tmp:
            p = Path(tmp)
            if p.stat().st_dev == HERE.stat().st_dev:
                self.skipTest('temporary root shares the package filesystem')
            before = os.statvfs(p); actual = replay.free_bytes(p); after = os.statvfs(p)
            low = min(before.f_bavail * before.f_frsize, after.f_bavail * after.f_frsize)
            high = max(before.f_bavail * before.f_frsize, after.f_bavail * after.f_frsize)
            self.assertGreaterEqual(actual, low)
            self.assertLessEqual(actual, high)


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]] + rest)
