"""Native creator-fee credit limits compared with signed captured-program runs."""
import hashlib
import copy
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

import test_creator_fee_distribution_captured as ordinary
import test_distribution_alias_captured as alias


def ordinary_cases():
    b = ordinary
    rows = [b.case(vault=b.ZERO_RENT + amount, holders=[b.holder(10000, lamports=balance)], op=op)
            for op in ('distribute', 'minimum') for amount in (0, 1, 2, 10000)
            for balance in (b.U64, b.U64 - 1, b.U64 - 2, 10**9)]
    # Check recipient order and precedence against admission/amount errors.
    for first in (True, False):
        for other in (b.holder(5000), b.holder(0), b.holder(5000, key='other'),
                      b.holder(5000, key='program')):
            holders = [b.holder(5000, lamports=b.U64), other]
            if not first:
                holders.reverse()
            rows.append(b.case(vault=b.ZERO_RENT + 4, holders=holders))
    rows.extend([
        b.case(vault=b.ZERO_RENT + 4, holders=[b.holder(10000, lamports=b.U64)], active=False),
        b.case(vault=b.ZERO_RENT + 4, holders=[b.holder(10000, lamports=b.U64)], creator_fee=1),
        b.case(vault=b.ZERO_RENT + 1, holders=[b.holder(65535, lamports=b.U64)]),
        b.case(vault=b.ZERO_RENT + 10**9, holders=[b.holder(65535, lamports=b.U64)]),
    ])
    return rows


def alias_cases():
    b = alias
    rows = []
    for amount in (0, 1, 2, 4):
        for balance in (b.U64, b.U64 - 1, b.U64 - 2, 10**9):
            for repeated in (True, False):
                slots = [b.slot('h0', 5000), b.slot('h0' if repeated else 'h1', 5000)]
                rows.append(b.v1(slots, vault=b.ZERO_RENT + amount, h0=balance, h1=balance))
    rows.extend([
        b.v1([b.slot('h0', 10000, False)], vault=b.ZERO_RENT + 2, h0=b.U64),
        b.v1([b.slot('h0', 5000), b.slot('h0', 5000, False)], vault=b.ZERO_RENT + 2, h0=b.U64),
        b.v1([b.slot('h0', 10000), b.slot('pump', 1)], vault=b.ZERO_RENT + 2, h0=b.U64),
        b.v1([b.slot('vault', 1)], vault=b.U64),
    ])
    return rows


def records():
    for path, digest in ordinary.ELF_SHA256.items():
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError('captured image hash changed')
    output = []
    with tempfile.TemporaryDirectory(prefix='distribution-credit-') as temporary:
        for name, base, cases in (('ordinary', ordinary, ordinary_cases()), ('aliases', alias, alias_cases())):
            host = Path(temporary) / name
            subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(base.HOST_SOURCE),
                            '-o', str(host)], check=True)
            answers = subprocess.run([str(host)], input='\n'.join(base.host_line(c) for c in cases) + '\n',
                                     capture_output=True, text=True, check=True).stdout.splitlines()
            if len(answers) != len(cases):
                raise ValueError('host case count differs')
            checker = (ordinary.CreatorFeeDistributionCapturedTests() if name == 'ordinary'
                       else alias.DistributionAliasCapturedTests())
            vm = alias.Vm() if name == 'aliases' else None
            for case, answer in zip(cases, answers):
                captured = ordinary.run_captured(case, include_failed_state=True) if vm is None else vm.run(case)
                try:
                    if name == 'ordinary' and answer == 'ArithmeticOverflow':
                        checker.assertIn('ArithmeticOverflow', str(captured['error']))
                        expected = copy.deepcopy(captured['before'])
                        expected[str(ordinary.PAYER.pubkey())]['lamports'] -= 5000
                        checker.assertEqual(captured['after'], expected)
                        checker.assertEqual(captured['events'], [])
                    else:
                        checker.assert_matches(case, answer, captured)
                except AssertionError:
                    matches = False
                else:
                    matches = True
                output.append(dict(family=name, case=case, host=answer, captured=captured, matches=matches))
    return output


class CreatorDistributionCreditTests(unittest.TestCase):
    def test_credits_match_captured_runtime(self):
        rows = records()
        wrong = [row for row in rows if not row['matches']]
        self.assertEqual(wrong, [])


if __name__ == '__main__':
    import sys
    if sys.argv[1:] == ['--probe']:
        print(json.dumps(records(), indent=2, default=lambda value: value.hex() if isinstance(value, bytes) else str(value)))
    else:
        unittest.main()
