"""Native parser controls; never import or run captured-program campaigns."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class LengthHostInputValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.hosts = {}
        for name in ('accumulator', 'config'):
            host = Path(cls.tmp.name) / name
            source = ROOT / 'programs/pump/recovered' / f'{name}_length_host.rs'
            subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(source), '-o', str(host)],
                           check=True, timeout=30)
            cls.hosts[name] = host

    def rejects(self, name, lines):
        for line in lines:
            with self.subTest(line=line):
                run = subprocess.run([str(self.hosts[name])], input=line + '\n',
                                     capture_output=True, text=True, timeout=5)
                self.assertNotEqual(run.returncode, 0, run.stdout)
                self.assertEqual(run.stdout, '')

    def answers(self, name, rows):
        run = subprocess.run([str(self.hosts[name])], input=''.join(line + '\n' for line, _ in rows),
                             capture_output=True, text=True, check=True, timeout=5)
        self.assertEqual(run.stdout.splitlines(), [answer for _, answer in rows])

    def test_accumulator_refuses_malformed_twin_and_unknown_read(self):
        self.rejects('accumulator', ['user,claim,137,1000000,not-a-code',
                                    'user,nonsense,137,1000000,-'])

    def test_accumulator_refuses_unknown_target_flags_and_column_counts(self):
        self.rejects('accumulator', ['', 'nonsense,claim,137,1000000,-',
                                    'global,2,544', 'global,-1,544', 'global,true,544',
                                    'global,1,544,extra', 'global,1',
                                    'user,claim,137,1000000,-,extra', 'user,claim,137,1000000',
                                    'user,claim,-1,1000000,-', 'user,claim,137,1000000,4294967296'])

    def test_accumulator_valid_reads_and_both_flags_still_answer(self):
        self.answers('accumulator', [('user,ignored,0,0,-', 'same'),
                                     ('user,load,8,0,-', 'error:3003'),
                                     ('user,init,138,0,-', 'error:2019'),
                                     ('user,claim,137,2000000,-', 'paid:155600'),
                                     ('user,claim,137,2000000,6024', 'same'),
                                     ('user,sell,0,0,-', 'error:0'),
                                     ('user,extend,7,0,-', 'error:6010'),
                                     ('global,0,7', 'same'), ('global,1,7', 'error:3001'),
                                     ('global,1,544', 'same')])

    def test_config_refuses_malformed_row_unknown_slot_and_request(self):
        self.rejects('config', ['scan,408,1,1,not-a-row', 'typed,nonsense,408,1,1,1,1',
                               'nonsense,0,100,5'])

    def test_config_refuses_invalid_flags_and_column_counts(self):
        self.rejects('config', ['', 'typed,control,408,2,1,1,1', 'typed,control,408,1,1,2,1',
                               'typed,control,408,1,1,1,2', 'scan,408,2,1,0', 'rewards,2,0,5',
                               'typed,control,408,1,1,1,1,extra', 'typed,control,408,1,1,1',
                               'scan,408,1,1,0,extra', 'scan,408,1,1',
                               'rewards,1,0,5,extra', 'rewards,1,0', 'scan,408,1,1,-1',
                               'scan,408,1,1,18446744073709551616'])

    def test_config_valid_slots_scan_and_rewards_still_answer(self):
        self.answers('config', [('typed,control,108,1,0,1,1', 'pass'),
                                ('typed,migrate,80,1,0,1,0', 'pass'),
                                ('typed,distribute,80,1,0,1,1', 'pass'),
                                ('typed,quote,80,1,0,1,1', 'pass'),
                                ('typed,control,108,0,0,1,1', 'error:3002'),
                                ('typed,migrate,80,1,0,0,1', 'error:3003'),
                                ('scan,148,1,1,0', 'found:0'), ('scan,148,1,1,-', 'missing'),
                                ('rewards,1,0,5', 'pass'), ('rewards,0,0,5', 'spend'),
                                ('rewards,1,1,5', 'argument'), ('rewards,0,100,0', 'pass')])


if __name__ == '__main__':
    unittest.main()
