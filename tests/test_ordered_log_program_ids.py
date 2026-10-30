"""Compute-meter lines are excluded only when the program id is a pubkey."""
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pump_strict_ordered_logs as gate

PROGRAM = '1' * 32


def report(original_logs, candidate_logs):
    return {
        'original_sha256': gate.ORIGINAL,
        'candidate_sha256': 'abc',
        'case_count': 1,
        'suites': {'case': [{
            'original': {'logs': original_logs},
            'candidate': {'logs': candidate_logs},
        }]},
    }


class OrderedLogProgramIdTests(unittest.TestCase):
    def test_short_program_id_is_a_real_log(self):
        result = gate.audit(
            report(['Program 1 consumed 1 of 2 compute units', 'kept'], ['kept']),
            'abc',
            1,
        )
        self.assertEqual(result['strict_ordered_log_mismatch_cases'], 1)

    def test_pubkey_meter_line_is_still_excluded(self):
        meter = f'Program {PROGRAM} consumed 17 of 99 compute units'
        result = gate.audit(report(['kept', meter], ['kept']), 'abc', 1)
        self.assertEqual(result['strict_ordered_log_mismatch_cases'], 0)

    def test_meter_lookalike_with_a_prefix_is_kept(self):
        line = f'Program log: Program {PROGRAM} consumed 17 of 99 compute units'
        result = gate.audit(report(['kept', line], ['kept']), 'abc', 1)
        self.assertEqual(result['strict_ordered_log_mismatch_cases'], 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
