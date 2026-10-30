"""Check the research wrapper preserves experiments and frozen-helper integrity."""
import hashlib
from pathlib import Path
import unittest
from build_reconstruction_candidate import ROOT, command


class ResearchSelectionTests(unittest.TestCase):
    def test_default_does_not_select_header_incompatible_older_family(self):
        for name in ('pump', 'pump_amm', 'pump_fees'):
            argv=command(['--program',name,'--manifest','sample/Cargo.toml','--output','work/build'])
            self.assertEqual(argv[argv.index('--tools-version')+1], 'v1.44')
            self.assertIn('sample/Cargo.toml', argv)
        argv=command(['--program','mayhem'])
        self.assertEqual(argv[argv.index('--tools-version')+1], 'v1.52')

    def test_explicit_experiment_and_argument_boundaries_are_preserved(self):
        tail=['--program','pump','--tools-version=v1.43','--output','work/path with spaces']
        argv=command(tail)
        self.assertEqual(argv[2:],tail)
        self.assertNotIn('--tools-version',argv)

    def test_current_helper_matches_accepted_historical_helper(self):
        # The accepted copy at d75184ea323be8a83ebe11fe5f26a13f3dcbe052
        # has Git blob 85fa552fd8c1556876715d089dbaf4f45857128d.
        # It is absent from current checkouts; retain its exact byte check.
        frozen_sha256='bb683621ffc4297c58f030cb03da54484b7370b786fd8eda965a37f4b3198ee9'
        current=(ROOT/'scripts/build_partial_candidate.py').read_bytes()
        self.assertEqual(hashlib.sha256(current).hexdigest(), frozen_sha256)


if __name__ == '__main__':
    unittest.main()
