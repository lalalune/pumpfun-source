"""Actual POSIX process exclusion, with an optional genuine SBF compiler probe."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/amm_sell/native_build.py'
spec = importlib.util.spec_from_file_location('amm_native_lane_lock', SCRIPT)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


@unittest.skipUnless(os.name == 'posix', 'native AMM builds require POSIX lane locks')
class NativeLaneLockTests(unittest.TestCase):
    def test_busy_lane_is_rejected_before_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lane = root / 'lane'
            with native.lane_lock(lane):
                result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--lane', str(lane), '--id', 'second'],
                                        env=dict(os.environ, AMM_SELL_SWARM=str(root)),
                                        capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('native build lane already in use', result.stderr)
                self.assertEqual([p.name for p in lane.iterdir()], ['.native-build.lock'])

    def test_distinct_lanes_can_be_owned_by_distinct_processes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            code = ('import importlib.util,sys;from pathlib import Path;'
                    's=importlib.util.spec_from_file_location("native",sys.argv[1]);'
                    'm=importlib.util.module_from_spec(s);s.loader.exec_module(m);'
                    '\nwith m.lane_lock(Path(sys.argv[2])): print("independent lane acquired",flush=True)\n')
            with native.lane_lock(root / 'first'):
                result = subprocess.run([sys.executable, '-B', '-c', code, str(SCRIPT), str(root / 'second')],
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('independent lane acquired', result.stdout)

    def test_real_build_setup_failure_releases_the_retained_lock(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            lane = root / 'lane'
            result = subprocess.run([sys.executable, '-B', str(SCRIPT), '--lane', str(lane), '--id', 'missing-baseline'],
                                    env=dict(os.environ, AMM_SELL_SWARM=str(root)),
                                    capture_output=True, text=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('Lane needs --source-root', result.stderr)
            inode = (lane / '.native-build.lock').stat().st_ino
            with native.lane_lock(lane):
                self.assertEqual((lane / '.native-build.lock').stat().st_ino, inode)


@unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('PUMP_BUILD_TEST_SDK'),
                     'set PUMP_BUILD_TEST_SDK to the authenticated v1.44 macOS SDK')
class NativeCompilerLaneTests(unittest.TestCase):
    def test_same_lane_cannot_replace_the_compiling_source(self):
        probe = ROOT / 'research/amm-native-lane-exclusion-20261101/probe.py'
        result = subprocess.run([sys.executable, '-B', str(probe), str(ROOT), os.environ['PUMP_BUILD_TEST_SDK']],
                                capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertFalse(record['workspace_overwritten_during_first_compile'])
        self.assertEqual(record['first_returncode'], 0)
        self.assertNotEqual(record['second_returncode'], 0)
        self.assertEqual(record['independent_lane_returncode'], 0)
        self.assertTrue(record['first_matches_a'])
        self.assertFalse(record['first_matches_b'])
        self.assertEqual(record['first_declared_source_sha256'], record['source_a_sha256'])


if __name__ == '__main__':
    unittest.main()
