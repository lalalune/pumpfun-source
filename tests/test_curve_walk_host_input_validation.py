"""Native line-protocol checks; no captured campaign or VM imports."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
START = ('start,1,0,1000000000000000,0,0,0:95:30,'
         '1073000000000000,30000000000,793100000000000,0,0,0,'
         '793100000000000,1000000000000000,2046960,0,0,0,0')


class CurveWalkHostInputValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.host = Path(cls.tmp.name) / 'curve-walk-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings',
                        str(ROOT / 'programs/pump/recovered/curve_walk_host.rs'), '-o', str(cls.host)],
                       check=True, timeout=30)

    def run_host(self, lines):
        return subprocess.run([str(self.host)], input='\n'.join(lines) + '\n',
                              capture_output=True, text=True, timeout=5)

    def test_unknown_operation_has_no_step_answer(self):
        result = self.run_host([START, 'planet,1,2'])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, 'started\n')

    def test_operation_column_counts_are_exact(self):
        for line in ('buy,1,18446744073709551615,,extra', 'exact,1000,0,,extra',
                     'sell,0,0,extra', 'collect,extra', 'buy,1,2', 'exact,1,2', 'sell,1'):
            with self.subTest(line=line):
                result = self.run_host([START, line])
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, 'started\n')

    def test_start_flags_tiers_and_column_counts_are_exact(self):
        bad = [START + ',extra', ','.join(START.split(',')[:-1])]
        for index in (1, 4, 11):
            for flag in ('2', '-1', 'true'):
                fields = START.split(',')
                fields[index] = flag
                bad.append(','.join(fields))
        for tier in ('0:95:30:999', '0:95', '0:95:30;1:2:3:4'):
            fields = START.split(',')
            fields[6] = tier
            bad.append(','.join(fields))
        for line in bad:
            with self.subTest(line=line):
                result = self.run_host([line])
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, '')

    def test_all_four_valid_operations_keep_stateful_answers(self):
        result = self.run_host([START, 'buy,1000000,18446744073709551615,',
                                'exact,1000,1,', 'sell,1,0', 'collect'])
        self.assertEqual(result.returncode, 0, result.stderr)
        answers = result.stdout.splitlines()
        self.assertEqual(answers[0], 'started')
        self.assertEqual(len(answers), 5)
        for answer in answers[1:]:
            outcome, state, _ = answer.split('|')
            self.assertEqual(outcome, 'ok')
            self.assertEqual(len(state.split(',')), 13)
        self.assertEqual([answer.split('|')[2].split(',')[2] for answer in answers[1:4]], ['1', '1', '0'])
        self.assertEqual(answers[4].split('|')[2], '')

    def test_start_resets_the_walk(self):
        result = self.run_host([START, 'collect', START, 'collect'])
        self.assertEqual(result.returncode, 0, result.stderr)
        answers = result.stdout.splitlines()
        self.assertEqual(answers[::2], ['started', 'started'])
        self.assertEqual(answers[1], answers[3])


if __name__ == '__main__':
    unittest.main()
