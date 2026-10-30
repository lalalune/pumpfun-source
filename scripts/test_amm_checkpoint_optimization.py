"""The AMM saved-checkpoint verifier must reject tampered evidence in every
optimization mode.

`python -O` / `-OO` strip `assert`, and the fallback (saved-checkpoint)
branch of scripts/verify_pump_amm_checkpoint.py expresses every acceptance
check as a bare assert — the candidate and manifest seals, the allocation and
upgradeable control reports, and the saved-verifier report — while the two
newer packet branches already use require(). A synthetic root whose status
report names a wrong candidate digest is rejected under plain python but
prints PASS under -O/-OO, because the fixture supplies every file the
verifier reads outside its asserts.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'verify_pump_amm_checkpoint.py'
CHECKPOINT = 'repro/pump_amm/v2-mint-clone-recovery-20261028'
ARTIFACT = CHECKPOINT + '/results/build/candidate.so'


def control_module(body):
    return 'def verify(root):\n    return ' + body + '\n'


def fixture(root):
    checkpoint = root / CHECKPOINT
    results = checkpoint / 'results'
    (results / 'build').mkdir(parents=True)
    (results / 'build' / 'candidate.so').write_bytes(b'tampered bytes\n')
    (results / 'manifest.json').write_bytes(b'tampered bytes\n')
    (root / 'repro' / 'status.json').write_text(json.dumps({'pump_amm': {
        'candidate_artifact': ARTIFACT,
        'candidate_sha256': '0' * 64,
        'loader_allocation_control': {
            'proof_path': 'repro/pump_amm/fake-alloc',
            'manifest_sha256': '0' * 64,
        },
        'upgradeable_loader_control': {
            'proof_path': 'repro/pump_amm/fake-upgrade',
            'manifest_sha256': '0' * 64,
        },
    }}), encoding='utf-8')
    for proof, body in (
        ('repro/pump_amm/fake-alloc',
         "{'candidate_sha256': '0' * 64, 'equal_allocation_control_cases': 0, "
         "'equal_allocation_control_mismatches': 999}"),
        ('repro/pump_amm/fake-upgrade',
         "{'candidate_sha256': '0' * 64, 'policy_cases': 0, 'policy_mismatches': 999}"),
    ):
        directory = root / proof
        directory.mkdir(parents=True)
        (directory / 'manifest.json').write_bytes(b'tampered bytes\n')
        (directory / 'verify.py').write_text(control_module(body), encoding='utf-8')
    (checkpoint / 'verify_saved.py').write_text(
        "import json\n"
        "print(json.dumps({'current_source_checked': False, "
        "'candidate_sha256': '0' * 64}))\n",
        encoding='utf-8')


class AmmCheckpointOptimizationTests(unittest.TestCase):
    def run_verifier(self, root, flags):
        return subprocess.run(
            [sys.executable, '-B', *flags, str(SCRIPT), '--repo', str(root)],
            capture_output=True, text=True, timeout=60)

    def test_tampered_status_is_rejected_in_every_mode(self):
        for flags in ([], ['-O'], ['-OO']):
            with self.subTest(flags=flags), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                fixture(root)
                result = self.run_verifier(root, flags)
                self.assertNotEqual(result.returncode, 0, result.stdout)
                self.assertNotIn("'status': 'PASS'", result.stdout)


if __name__ == '__main__':
    unittest.main()
