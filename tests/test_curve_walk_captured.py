"""Captured-program checks for one bonding curve carried across many calls.

The single-call tests build a fresh VM per case, so nothing shows that what a
call stores is what the next call reads. Here each walk runs `buy`,
`buy_exact_sol_in`, `sell` and `collect_creator_fee` from the captured
`evidence/original/pump/deployed.so` on one LiteSVM VM, while
`programs/pump/recovered/curve_walk_host.rs` carries its own state from the
same start and never sees the VM again. After every step the outcome, the
curve, both token balances, every lamport balance and the TradeEvent amounts
must agree, past the buy that completes the curve. The market cap moves during
a walk, so fee tiers change under it. This is matching behaviour on these
inputs only, not a byte-identity claim.
"""
from pathlib import Path
import base64
import hashlib
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_legacy_buy_captured as base  # noqa: E402

HOST_SOURCE = base.ROOT / 'programs/pump/recovered/curve_walk_host.rs'
SELL_TOKENS = base.pda(b'bonding-curve', bytes(base.MINT))[0]
COLLECT = base.IX['collect_creator_fee']
USER = base.USER.pubkey()
START_USER = 10**15
BIG = 10**9


def plan(rng):
    """One walk: the setup and its operations."""
    mcap = base.MCAP
    tiers = rng.choice((((0, 95, 30),), ((0, 95, 30), (mcap * 2, 50, 20)),
                        ((0, 95, 30), (mcap + 1, 70, 25), (mcap * 3, 50, 20), (mcap * 10, 10, 5)),
                        ((0, 0, 0), (mcap * 2, 200, 100))))
    setup = dict(creator=rng.random() < 0.8, creator_bps=rng.choice((0, 0, 500)), configurable=rng.random() < 0.5,
                 buyback=rng.choice((0, 0, 2_500, 10_000)), tiers=tiers, supply=base.SUPPLY, vt=base.VT, vs=base.VS,
                 rt=base.RT, rs=0, complete=False)
    ops = []
    held = 0
    for _ in range(rng.choice((12, 40, 80))):
        roll = rng.random()
        trailing = rng.choice((b'', b'', b'\x01', b'\x00\x01', b'\x01\x01', b'\x01\x00'))
        if roll < 0.35:
            amount = rng.choice((rng.randrange(1, 10**6), rng.randrange(1, 10**14), rng.randrange(10**13, 3 * 10**14)))
            held += amount
            ops.append(('buy', amount, rng.choice((base.U64, base.U64, rng.randrange(0, 10**11))), trailing))
        elif roll < 0.6:
            ops.append(('exact', rng.choice((rng.randrange(1, 1_000), rng.randrange(1, 40 * BIG))),
                        rng.choice((1, 1, rng.randrange(1, 10**14))), trailing))
        elif roll < 0.85:
            amount = rng.choice((0, 1, rng.randrange(1, max(held, 2)), rng.randrange(1, 10**14), held + 1))
            ops.append(('sell', amount, rng.choice((0, 0, rng.randrange(0, 10**10)))))
        else:
            ops.append(('collect',))
    return setup, ops


def start_state(setup):
    return [setup['vt'], setup['vs'], setup['rt'], 0, 0, 0, setup['rt'], START_USER, base.CURVE_RENT, 0, 0, 0, 0]


def start_line(setup):
    fields = ['start', int(setup['creator']), setup['creator_bps'], setup['supply'], int(setup['configurable']),
              setup['buyback'], ';'.join(f'{t}:{p}:{c}' for t, p, c in setup['tiers']), *start_state(setup)]
    return ','.join(map(str, fields))


def op_line(op):
    if op[0] == 'collect':
        return 'collect'
    if op[0] == 'sell':
        return f'sell,{op[1]},{op[2]}'
    return f'{op[0]},{op[1]},{op[2]},{op[3].hex()}'


class Walk:
    def __init__(self, setup):
        self.vm = LiteSVM().with_sigverify(False).with_transaction_history(0)
        for key, path in ((base.PUMP, base.PUMP_ELF), (base.FEES, base.FEES_ELF), (base.TOKEN, base.TOKEN_ELF),
                          (base.ATA, base.ATA_ELF)):
            self.vm.add_program_from_file(key, path)
        self.vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
        self.creator = base.CREATOR if setup['creator'] else base.SYSTEM
        self.vault = base.VAULT if setup['creator'] else base.DEFAULT_VAULT
        item = dict(base.DEFAULTS, **setup)
        accounts = {
            USER: Account(START_USER, b'', base.SYSTEM),
            base.GLOBAL: Account(BIG, base.global_data(setup['buyback'], setup['configurable']), base.PUMP),
            base.MINT: Account(BIG, base.mint_data(setup['supply']), base.TOKEN),
            base.CURVE: Account(base.CURVE_RENT, base.curve_data(item), base.PUMP),
            base.ata(base.CURVE): Account(base.TOKEN_RENT, base.token_data(base.CURVE, setup['rt']), base.TOKEN),
            base.ata(USER): Account(base.TOKEN_RENT, base.token_data(USER, 0), base.TOKEN),
            base.FEE_CONFIG: Account(BIG, base.fee_config_data(setup['tiers']), base.FEES),
            base.GLOBAL_VOLUME: Account(BIG, base.ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), base.PUMP),
            base.USER_VOLUME: Account(BIG, base.ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(USER) + bytes(97),
                                      base.PUMP),
            base.CURVE_V2: Account(10**7, b'', base.SYSTEM),
        }
        for key, account in accounts.items():
            self.vm.set_account(key, account)
        self.names = {
            'global': base.GLOBAL, 'fee_recipient': base.FEE_RECIPIENT, 'mint': base.MINT,
            'bonding_curve': base.CURVE, 'associated_bonding_curve': base.ata(base.CURVE),
            'associated_user': base.ata(USER), 'user': USER, 'system_program': base.SYSTEM,
            'token_program': base.TOKEN, 'creator_vault': self.vault, 'event_authority': base.EVENT_AUTHORITY,
            'program': base.PUMP, 'global_volume_accumulator': base.GLOBAL_VOLUME,
            'user_volume_accumulator': base.USER_VOLUME, 'fee_config': base.FEE_CONFIG, 'fee_program': base.FEES,
            'creator': self.creator,
        }

    def lamports(self, key):
        account = self.vm.get_account(key)
        return account.lamports if account else 0

    def tokens(self, owner):
        return struct.unpack_from('<Q', self.vm.get_account(base.ata(owner)).data, 64)[0]

    def state(self):
        stored = self.vm.get_account(base.CURVE).data
        fields = [*struct.unpack_from('<QQQQ', stored, 8), stored[48], self.tokens(USER), self.tokens(base.CURVE)]
        fields += [self.lamports(k) for k in (USER, base.CURVE, base.FEE_RECIPIENT, base.BUYBACK, self.vault,
                                              self.creator if self.creator != base.SYSTEM else base.OTHER_NONE)]
        return ','.join(map(str, fields))

    def instruction(self, op):
        if op[0] == 'collect':
            metas = [AccountMeta(self.names[a['name']], False, a.get('writable', False)) for a in COLLECT['accounts']]
            return Instruction(base.PUMP, bytes(COLLECT['discriminator']), metas)
        if op[0] == 'sell':
            ix = base.IX['sell']
            data = struct.pack('<QQ', op[1], op[2])
            tail = [AccountMeta(base.CURVE_V2, False, False), AccountMeta(base.BUYBACK, False, True)]
        else:
            ix = base.IX['buy' if op[0] == 'buy' else 'buy_exact_sol_in']
            data = struct.pack('<QQ', op[1], op[2]) + op[3]
            tail = [AccountMeta(base.CURVE_V2, False, False), AccountMeta(base.BUYBACK, False, True)]
        metas = [AccountMeta(self.names[a['name']], a.get('signer', False), a.get('writable', False))
                 for a in ix['accounts']]
        return Instruction(base.PUMP, bytes(ix['discriminator']) + data, metas + tail)

    def run(self, op):
        self.vm.expire_blockhash()
        blockhash = self.vm.latest_blockhash()
        message = Message.new_with_blockhash([self.instruction(op)], USER, blockhash)
        tx = Transaction.new_unsigned(message)
        tx.partial_sign([base.USER], blockhash)
        result = self.vm.send_transaction(tx)
        trade = ''
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            outcome = f'error:{code.group(1)}' if code else 'panic' if 'ProgramFailedToComplete' in text else text
        else:
            outcome = 'ok'
            events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
            found = [e for e in events if e[:8] == base.TRADE_EVENT]
            if found:
                t = base.decode_trade(found[0])
                is_buy = found[0][8 + 32 + 16]
                trade = ','.join(map(str, (t['sol_amount'], t['token_amount'], is_buy, t['fee_bps'], t['fee'],
                                           t['creator_bps'], t['creator_fee'], t['track_volume'],
                                           t['buyback_fee'])))
        return f'{outcome}|{self.state()}|{trade}'


base.OTHER_NONE = base.pda(b'walk-no-creator')[0]


class CurveWalkCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in base.ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'curve-walk-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, lines):
        out = subprocess.run([str(self.host)], input='\n'.join(lines) + '\n', capture_output=True, text=True,
                             check=True).stdout
        return out.splitlines()

    def compare(self, lines, captured):
        hosted = [a for a in self.host_answers(lines) if a != 'started']
        steps = [line for line in lines if not line.startswith('start')]
        self.assertEqual(len(hosted), len(captured))
        wrong = [(steps[i], h, c) for i, (h, c) in enumerate(zip(hosted, captured)) if h != c]
        self.assertEqual(wrong[:3], [], f'{len(wrong)} of {len(captured)} differ')

    def walk(self, setup, ops):
        lines, answers = [start_line(setup)], []
        vm = Walk(setup)
        for op in ops:
            lines.append(op_line(op))
            answers.append(vm.run(op))
        return lines, answers

    def walks(self, count, seed):
        rng = random.Random(seed)
        lines, answers = [], []
        for _ in range(count):
            more_lines, more_answers = self.walk(*plan(rng))
            lines += more_lines
            answers += more_answers
        return lines, answers

    def test_random_walks(self):
        lines, answers = self.walks(40, 20261031)
        self.compare(lines, answers)
        outcomes = {a.split('|')[0] for a in answers}
        self.assertGreater(len(answers), 1_000)
        self.assertIn('error:6005', outcomes)
        self.assertIn('error:6023', outcomes)

    def test_complete_then_every_trade_stops(self):
        setup = plan(random.Random(1))[0] | dict(creator=True, buyback=0, tiers=((0, 95, 30),), creator_bps=0)
        ops = [('buy', 10**14, base.U64, b''), ('buy', 10**18, base.U64, b'\x00\x01'), ('sell', 1, 0),
               ('buy', 1, base.U64, b''), ('exact', 10**9, 1, b''), ('collect',), ('collect',)]
        lines, answers = self.walk(setup, ops)
        self.compare(lines, answers)
        self.assertEqual([a.split('|')[0] for a in answers],
                         ['ok', 'ok', 'error:6005', 'error:6005', 'error:6005', 'ok', 'ok'])

    def test_an_unknown_operation_is_refused(self):
        # The driver's catchall read any token as `collect` and answered a real
        # walk, so a misspelt or shifted operation column still looked checked.
        setup = plan(random.Random(1))[0] | dict(creator=True, buyback=0, tiers=((0, 95, 30),), creator_bps=0)
        run = subprocess.run([str(self.host)], input=f'{start_line(setup)}\nplanet,1,2\n',
                             capture_output=True, text=True)
        self.assertNotEqual(run.returncode, 0, run.stdout)

    def test_full_sell_back_leaves_one_lamport_of_rounding(self):
        setup = plan(random.Random(2))[0] | dict(creator=True, buyback=0, tiers=((0, 95, 30),), creator_bps=0)
        ops = [('buy', 10**13, base.U64, b''), ('collect',), ('sell', 10**13, 0), ('collect',), ('sell', 1, 0)]
        lines, answers = self.walk(setup, ops)
        self.compare(lines, answers)
        self.assertEqual(answers[2].split('|')[1].split(',')[:4],
                         [str(base.VT), str(base.VS + 1), str(base.RT), '1'])


if __name__ == '__main__':
    unittest.main()
