"""The main-checkpoint verifier must reject tampered evidence in every
optimization mode.

`python -O` / `-OO` strip `assert`, and every acceptance check in the
generic fallback branch of scripts/verify_pump_main_checkpoint.py is an
assert, so a synthetic root whose manifest seal does not match the frozen
round47 seal is rejected under plain python but prints PASS under -O/-OO.
The fixture supplies every file the verifier reads outside its asserts,
including a stub package verify.py, so the only difference between the
modes is whether the checks run. The four sealed branches already use
require(); this test pins the fallback branch to the same rule.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'verify_pump_main_checkpoint.py'
PACKAGE = 'repro/pump/main-contract-round47-20261027'


def fixture(root):
    package = root / PACKAGE
    package.mkdir(parents=True)
    (package / 'MANIFEST.json').write_text('{}', encoding='utf-8')
    (package / 'CHECKPOINT.json').write_text(json.dumps({
        'candidate_sha256': '0' * 64,
        'unstripped_sha256': '1' * 64,
        'goal_complete': False,
        'primary_source_sha256': {},
        'normalized_windows': 0,
        'original_windows': 0,
    }), encoding='utf-8')
    (package / 'verify.py').write_text('', encoding='utf-8')
    (root / 'repro' / 'status.json').parent.mkdir(parents=True, exist_ok=True)
    (root / 'repro' / 'status.json').write_text(json.dumps({'pump': {
        'candidate_artifact': PACKAGE + '/candidate.so',
        'candidate_sha256': '0' * 64,
        'symbols_sha256': '1' * 64,
        'full_byte_equality': False,
    }}), encoding='utf-8')
    (root / 'programs' / 'pump').mkdir(parents=True)


class MainCheckpointOptimizationTests(unittest.TestCase):
    def run_verifier(self, root, flags):
        return subprocess.run(
            [sys.executable, '-B', *flags, str(SCRIPT), '--repo', str(root)],
            capture_output=True, text=True, timeout=60)

    def test_tampered_manifest_is_rejected_in_every_mode(self):
        for flags in ([], ['-O'], ['-OO']):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                result = self.run_verifier(root, flags)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertNotIn('"status": "PASS"', result.stdout)


if __name__ == '__main__':
    unittest.main()
