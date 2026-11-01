"""Native parser controls only; never import captured V2 or extension suites."""
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
V2 = dict(op='sell', amount=10**12, limit=0, partial=0, vtr=10**15, vqr=30_000_000_000,
          rtr=793_100_000_000_000, rqr=5_000_000_000, supply=10**15, complete=0, cashback=0,
          mayhem=0, creator=1, curve_creator_bps=0, curve_lamports=2_046_240, vault_lamports=0,
          table='flat', tf='-', epoch=5, mint_supply=10**15, buyback_bps=5000, configurable=0,
          whitelisted=0, fee_len=4104, flat='95:30', tiers='0:95:30', stable='0:20:5',
          exotic='0:0:0', user_base=10**13, curve_base=10**15, user_quote=10**14,
          curve_quote=5_000_000_000, fee_recipient_ok=1, buyback_ok=1, bad='none')
SWEEP = ['protocol', '0', 'quote', '3000000', '7000000', '2046240', 'fee_recipient', '1000000000',
         't22', 't22', '-', '0', 'none', 'none', '0', '0', '1', '1',
         '10000000000:0:0:1:0:0:0', '0:0:0:1:0:0:0']


def v2_line(**changes):
    return ' '.join(f'{key}={value}' for key, value in (V2 | changes).items())


def sweep_line(index=None, value=None):
    fields = SWEEP.copy()
    if index is not None:
        fields[index] = value
    return ','.join(fields)


class ExtraHostInputValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.hosts = {}
        for name in ('v2_token_quote', 'sweep_fees_token2022'):
            host = Path(cls.tmp.name) / name
            subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings',
                            str(ROOT / 'programs/pump/recovered' / f'{name}_host.rs'), '-o', str(host)],
                           check=True, timeout=30)
            cls.hosts[name] = host

    def rejects(self, name, lines):
        for line in lines:
            with self.subTest(line=line):
                run = subprocess.run([str(self.hosts[name])], input=line + '\n',
                                     capture_output=True, text=True, timeout=5)
                self.assertNotEqual(run.returncode, 0, run.stdout)
                self.assertEqual(run.stdout, '')

    def test_v2_unknown_bad_slot_is_rejected(self):
        self.rejects('v2_token_quote', [v2_line(bad='curve_kee')])

    def test_v2_keys_and_closed_tags_are_strict(self):
        self.rejects('v2_token_quote', [v2_line(op='typo'), v2_line(table='typo'),
                                       v2_line() + ' ignored=1', v2_line() + ' amount=1',
                                       ' '.join(v2_line().split(' ')[1:])])

    def test_v2_flags_and_vector_lengths_are_strict(self):
        lines = [v2_line(**{key: 2}) for key in ('partial', 'complete', 'cashback', 'mayhem', 'creator',
                                               'configurable', 'whitelisted', 'fee_recipient_ok', 'buyback_ok')]
        lines += [v2_line(flat='95:30:9'), v2_line(exotic='0:0:0:1'),
                  v2_line(tf='0:0:0:0:0:1'), v2_line(tiers='0:95:30:1'), v2_line(stable='0:20:5:1')]
        self.rejects('v2_token_quote', lines)

    def test_sweep_closed_tags_are_strict(self):
        self.rejects('sweep_fees_token2022', [sweep_line(index, 'typo') for index in (0, 2, 6, 8, 9, 12, 13)])

    def test_sweep_flags_lengths_and_fee_width_are_strict(self):
        lines = [sweep_line(index, '2') for index in (1, 14, 15, 16, 17)]
        for slot in (18, 19):
            for index in range(1, 7):
                fields = SWEEP[slot].split(':')
                fields[index] = '2'
                lines.append(sweep_line(slot, ':'.join(fields)))
            lines.append(sweep_line(slot, SWEEP[slot] + ':1'))
        lines += [sweep_line() + ',extra', ','.join(SWEEP[:-1]),
                  sweep_line(10, '0:0:0:0:0:1'), sweep_line(10, '65536:0:0:0:0'),
                  sweep_line(10, '0:0:0:65536:0')]
        self.rejects('sweep_fees_token2022', lines)

    def test_valid_requests_keep_native_answers(self):
        examples = {'v2_token_quote': [v2_line(), v2_line(op='buy', limit=10**15),
                                       v2_line(op='exact', amount=10**8, limit=1)],
                    'sweep_fees_token2022': [sweep_line()]}
        for name, lines in examples.items():
            run = subprocess.run([str(self.hosts[name])], input='\n'.join(lines) + '\n',
                                 capture_output=True, text=True, timeout=5)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(len(run.stdout.splitlines()), len(lines))
            self.assertTrue(all(line.startswith('ok') for line in run.stdout.splitlines()), run.stdout)


if __name__ == '__main__':
    unittest.main()
