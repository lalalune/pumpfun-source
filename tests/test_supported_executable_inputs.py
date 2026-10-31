"""Admitted build-script helpers keep the source permissions needed by Cargo."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUST = (Path(os.environ['PUMP_TEST_RUST_BIN']) if os.environ.get('PUMP_TEST_RUST_BIN') else
        Path(shutil.which('rustc')).parent if shutil.which('rustc') else None)
RESEARCH = ROOT/'research/supported-build-executable-inputs-20261101'


class SupportedExecutableInputTests(unittest.TestCase):
    @unittest.skipUnless(os.name == 'posix' and RUST and (RUST/'cargo').is_file(),
                         'requires a POSIX host Cargo/rustc toolchain')
    def test_actual_staging_loop_preserves_the_executable_cargo_input(self):
        result = subprocess.run([sys.executable, '-B', str(RESEARCH/'staging_probe.py'), str(ROOT), str(RUST)],
                                capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads(result.stdout)
        self.assertEqual(record['original']['returncode'], 0, record)
        self.assertEqual(record['staged']['returncode'], 0, record)
        self.assertEqual(record['original']['output'], '37')
        self.assertEqual(record['staged']['output'], '37')
        self.assertEqual(record['original_helper_mode'], '0o755')
        self.assertEqual(record['staged_helper_mode'], record['original_helper_mode'])

    @unittest.skipUnless(sys.platform == 'darwin' and os.environ.get('PUMP_SUPPORTED_TEST_TOOLS'),
                         'requires authenticated v1.53 SDK and pinned v1.52 objcopy')
    def test_full_supported_plan_and_execute_match_the_direct_sbf_build(self):
        result = subprocess.run([sys.executable, '-B', str(RESEARCH/'probe.py'), str(ROOT),
                                 os.environ['PUMP_SUPPORTED_TEST_TOOLS']], capture_output=True, text=True, timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr)
        rows = json.loads(result.stdout)['rows']
        executable = rows['executable']
        self.assertEqual(executable['control_returncode'], 0, executable)
        self.assertEqual(executable['adapter_returncode'], 0, executable)
        self.assertEqual(executable['adapter_stage'], 'complete')
        self.assertEqual(executable['adapter_candidate_sha256'], executable['control_candidate_sha256'])
        self.assertEqual(executable['staged_helper_mode'], '0o755')
        self.assertTrue(executable['source_unchanged'])
        nonexecutable = rows['nonexecutable']
        self.assertEqual(nonexecutable['control_returncode'], 101, nonexecutable)
        self.assertEqual(nonexecutable['adapter_returncode'], 101, nonexecutable)
        self.assertEqual(nonexecutable['adapter_stage'], 'compile_failed')
        self.assertEqual(nonexecutable['staged_helper_mode'], '0o644')
        self.assertNotIn('adapter_candidate_sha256', nonexecutable)


if __name__ == '__main__':
    unittest.main()
