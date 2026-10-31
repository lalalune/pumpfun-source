"""Captured-program checks for several Pump instructions in one transaction.

Every other captured test sends one Pump instruction per transaction. Here each
case runs the same steps twice on the captured
`evidence/original/pump/deployed.so`, with the captured Pump Fees, SPL Token,
Associated Token and Token Metadata programs: one transaction per step on one
chain, then all steps in one transaction on a fresh chain. The separate run
gives each step's outcome, compute units and trace entries to
`programs/pump/recovered/same_tx_host.rs`, which answers how the joined
transaction ends. The joined run must agree on the error and its instruction
index, the fee, the units, the trace and the events, and must end on the
separate runs' state (plus the saved fees) or, on a failure, on the start state
less the fee. This shows matching behaviour on these inputs only; it is not a
byte-identity claim.
"""
from pathlib import Path
import hashlib
import json
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.system_program import TransferParams, transfer
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_legacy_buy_captured as base  # noqa: E402
import test_legacy_create_captured as cr  # noqa: E402
import test_migrate_captured as mg  # noqa: E402

HOST_SOURCE = base.ROOT / 'programs/pump/recovered/same_tx_host.rs'
USER = base.USER.pubkey()
START = 10**15
BIG = 10**9
MAX_LIMIT = 1_400_000
# Each separate step carries a limit, so a long step cannot run out by itself.
SEPARATE_LIMIT = MAX_LIMIT
LEAD_UNITS = 150
UPGRADEABLE = cr.UPGRADEABLE
NAMED = {'close': 'close_user_volume_accumulator', 'init': 'init_user_volume_accumulator',
         'sync': 'sync_user_volume_accumulator', 'claim': 'claim_cashback', 'collect': 'collect_creator_fee',
         'buy': 'buy', 'exact': 'buy_exact_sol_in', 'sell': 'sell'}
CREATED = cr.MINT.pubkey()

BUY = ('buy', 10**12, base.U64)
SELL = ('sell', 10**11, 0)
CASHBACK_SELL = ('sell', 10**11, 0, 'cashback')
TOO_MUCH = ('sell', 10**15, 0)
TOO_MUCH_CASHBACK = ('sell', 10**15, 0, 'cashback')
FILL = ('buy', 10**18, base.U64, 'fill')
COLLECT, CLOSE, INIT, SYNC, CLAIM, CREATE = ('collect',), ('close',), ('init',), ('sync',), ('claim',), ('create',)
FUND_VAULT = ('pay', 'creator_vault', 3_000_000)
FUND_CURVE = ('pay', 'bonding_curve', 5_000)
FUND_ACCUMULATOR = ('pay', 'user_volume_accumulator', 500_000)


def case(ops, limit=None, **setup):
    return dict(ops=ops, limit=limit, setup=setup)


def fixed_global():
    data = bytearray(base.global_data(0, False))
    data[8] = 1
    struct.pack_into('<QQQQ', data, 73, base.VT, base.VS, base.RT, base.SUPPLY)
    data[113:145] = bytes(mg.WITHDRAW)
    data[145] = 1
    struct.pack_into('<Q', data, 146, 15_000_001)
    data[450] = 1
    return bytes(data)


VM = []
TOUCHED = set()


def shared_vm():
    """One VM per run: loading five programs per case takes most of the time."""
    if not VM:
        vm = LiteSVM().with_sigverify(False).with_transaction_history(0)
        programdata = base.pda(bytes(base.PUMP), program=UPGRADEABLE)[0]
        vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32)
                                            + base.PUMP_ELF.read_bytes(), UPGRADEABLE, False))
        vm.set_account(base.PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
        for key, path in ((base.FEES, base.FEES_ELF), (base.TOKEN, base.TOKEN_ELF), (base.ATA, base.ATA_ELF),
                          (cr.METADATA, cr.METADATA_ELF)):
            vm.add_program_from_file(key, path)
        vm.add_program(mg.PUMP_AMM, mg.noop_program())
        VM.append(vm)
    vm = VM[0]
    for key in TOUCHED:
        account = vm.get_account(key)
        if account is not None and not account.executable and 'Sysvar1111' not in str(account.owner):
            vm.set_account(key, Account(0, b'', base.SYSTEM))
    return vm


class Chain:
    def __init__(self, cashback=False, created=False):
        self.vm = shared_vm()
        self.mint = CREATED if created else base.MINT
        self.vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
        self.curve = base.pda(b'bonding-curve', bytes(self.mint))[0]
        creator = cr.CREATOR if created else base.CREATOR
        self.vault = base.pda(b'creator-vault', bytes(creator))[0]
        names = {
            'global': base.GLOBAL, 'fee_recipient': base.FEE_RECIPIENT, 'mint': self.mint,
            'bonding_curve': self.curve, 'associated_bonding_curve': self.ata(self.curve),
            'associated_user': self.ata(USER), 'user': USER, 'payer': USER, 'system_program': base.SYSTEM,
            'token_program': base.TOKEN, 'creator_vault': self.vault, 'event_authority': base.EVENT_AUTHORITY,
            'program': base.PUMP, 'global_volume_accumulator': base.GLOBAL_VOLUME,
            'user_volume_accumulator': base.USER_VOLUME, 'fee_config': base.FEE_CONFIG, 'fee_program': base.FEES,
            'creator': creator,
        }
        self.names = names
        accounts = {
            USER: Account(START, b'', base.SYSTEM),
            base.GLOBAL: Account(BIG, fixed_global(), base.PUMP),
            base.FEE_CONFIG: Account(BIG, base.fee_config_data(((0, 95, 30),)), base.FEES),
            base.GLOBAL_VOLUME: Account(BIG, base.ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), base.PUMP),
            base.USER_VOLUME: Account(BIG, base.ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(USER) + bytes(97),
                                      base.PUMP),
            self.v2(): Account(10**7, b'', base.SYSTEM),
            names['associated_user']: Account(base.TOKEN_RENT, self.token_data(USER, 0), base.TOKEN),
            mg.WITHDRAW: Account(1_000_000, b'', base.SYSTEM),
            mg.WSOL: Account(1_461_600, mg.mint_data(9, 0), base.TOKEN),
        }
        lp_mint = self.mig()['lp_mint']
        accounts[lp_mint] = Account(1_461_600, mg.mint_data(9, 0), mg.TOKEN22)
        accounts[self.mig()['user_pool_token_account']] = Account(
            2_074_080, mg.token_data(lp_mint, self.mig()['pool_authority'], 0), mg.TOKEN22)
        if not created:
            item = dict(base.DEFAULTS, rs=0, vt=base.VT, vs=base.VS, rt=base.RT, supply=base.SUPPLY)
            curve = bytearray(base.curve_data(item))
            curve[82] = int(cashback)
            accounts[base.MINT] = Account(BIG, base.mint_data(base.SUPPLY), base.TOKEN)
            accounts[self.curve] = Account(base.CURVE_RENT, bytes(curve), base.PUMP)
            accounts[self.ata(self.curve)] = Account(base.TOKEN_RENT, self.token_data(self.curve, base.RT), base.TOKEN)
        for key, account in accounts.items():
            self.vm.set_account(key, account)
        TOUCHED.update(accounts)

    def ata(self, owner):
        return mg.ata(owner, self.mint)

    def v2(self):
        return base.pda(b'bonding-curve-v2', bytes(self.mint))[0]

    def token_data(self, owner, amount):
        return mg.token_data(self.mint, owner, amount)

    def mig(self):
        pa = mg.pda([b'pool-authority', bytes(self.mint)])
        pool = mg.pda([b'pool', struct.pack('<H', 0), bytes(pa), bytes(self.mint), bytes(mg.WSOL)], mg.PUMP_AMM)
        lp = mg.pda([b'pool_lp_mint', bytes(pool)], mg.PUMP_AMM)
        return dict(mg.ACCOUNTS, mint=self.mint, bonding_curve=self.curve,
                    associated_bonding_curve=self.ata(self.curve), user=USER, pool=pool, pool_authority=pa,
                    pool_authority_mint_account=mg.ata(pa, self.mint), pool_authority_wsol_account=mg.ata(pa, mg.WSOL),
                    lp_mint=lp, user_pool_token_account=mg.ata(pa, lp, mg.TOKEN22),
                    pool_base_token_account=mg.ata(pool, self.mint), pool_quote_token_account=mg.ata(pool, mg.WSOL))

    def ix(self, op):
        kind = op[0]
        if kind == 'pay':
            return transfer(TransferParams(from_pubkey=USER, to_pubkey=self.names[op[1]], lamports=op[2]))
        if kind == 'create':
            names = dict(cr.ACCOUNTS, user=USER, bonding_curve=self.curve)
            metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False))
                     for a in cr.CREATE['accounts']]
            data = (bytes(cr.CREATE['discriminator']) + cr.borsh_string('Coin') + cr.borsh_string('CN')
                    + cr.borsh_string('https://x') + bytes(cr.CREATOR))
            return Instruction(base.PUMP, data, metas)
        if kind == 'migrate':
            names = self.mig()
            metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False))
                     for a in mg.MIGRATE['accounts']]
            return Instruction(base.PUMP, bytes(mg.MIGRATE['discriminator']), metas)
        ix = base.IX[NAMED[kind]]
        metas = [AccountMeta(self.names[a['name']], a.get('signer', False), a.get('writable', False))
                 for a in ix['accounts']]
        data = bytes(ix['discriminator'])
        if kind in ('buy', 'exact', 'sell'):
            data += struct.pack('<QQ', op[1], op[2]) + (b'\x00\x01' if op[3:] == ('fill',) else b'')
            if kind == 'sell' and op[3:] == ('cashback',):
                metas += [AccountMeta(base.USER_VOLUME, False, True), AccountMeta(self.v2(), False, False),
                          AccountMeta(base.BUYBACK, False, True)]
            else:
                metas += [AccountMeta(self.v2(), False, False), AccountMeta(base.BUYBACK, False, True)]
        return Instruction(base.PUMP, data, metas)

    def send(self, ops, limit=None):
        self.vm.expire_blockhash()
        bh = self.vm.latest_blockhash()
        pre = [] if limit is None else [set_compute_unit_limit(limit)]
        instructions = [self.ix(o) for o in ops]
        TOUCHED.update(meta.pubkey for ix in instructions for meta in ix.accounts)
        msg = Message.new_with_blockhash(pre + instructions, USER, bh)
        tx = Transaction.new_unsigned(msg)
        signers = [base.USER] + ([cr.MINT] if any(o[0] == 'create' for o in ops) else [])
        tx.partial_sign(signers, bh)
        result = self.vm.send_transaction(tx)
        failed = isinstance(result, FailedTransactionMetadata)
        meta = result.meta() if failed else result
        groups = json.loads(meta.to_json())['inner_instructions'] or []
        return dict(err=str(result.err()) if failed else None, cu=meta.compute_units_consumed(),
                    trace=len(pre) + len(ops) + sum(len(g) for g in groups), logs=meta.logs())

    def snap(self):
        keys = [USER, base.GLOBAL, self.mint, self.curve, self.ata(self.curve), self.ata(USER), base.USER_VOLUME,
                base.GLOBAL_VOLUME, base.FEE_RECIPIENT, base.BUYBACK, self.vault, self.v2(), mg.WITHDRAW,
                self.mig()['pool_authority'], self.mig()['pool_authority_wsol_account'],
                self.mig()['pool_authority_mint_account']]
        out = {}
        for k in keys:
            a = self.vm.get_account(k)
            out[str(k)] = None if a is None or a.lamports == 0 else (a.lamports, str(a.owner), bytes(a.data))
        return out


def label(err):
    if err is None:
        return 'ok'
    custom = re.search(r'Custom\((\d+)\)', err)
    if custom:
        return f'c{custom.group(1)}'
    if 'MaxInstructionTraceLengthExceeded' in err:
        return 'trace'
    if 'ComputationalBudgetExceeded' in err or 'ProgramFailedToComplete' in err:
        return 'budget'
    return re.sub(r'\W', '', err)


def signatures(op):
    return 2 if op[0] == 'create' else 1


def names_mint(op):
    return int(op[0] in ('buy', 'exact', 'sell', 'migrate'))


def events(logs):
    return [line for line in logs if line.startswith('Program data: ')]


def run_case(item):
    """Run the steps one transaction each, then together, on two fresh chains."""
    apart = Chain(**item['setup'])
    before = apart.snap()
    steps, emitted = [], []
    for op in item['ops']:
        alone = apart.send([op], SEPARATE_LIMIT)
        steps.append(':'.join(map(str, (label(alone['err']), alone['cu'] - LEAD_UNITS, alone['trace'] - 1,
                                        signatures(op), int(op[0] == 'pay'), names_mint(op)))))
        if alone['err']:
            break
        emitted += events(alone['logs'])
    final = apart.snap()
    together = Chain(**item['setup'])
    limit = '-' if item['limit'] is None else item['limit']
    return dict(line=';'.join([str(limit), str(max(map(signatures, item['ops']))), *steps]), before=before, apart=final, emitted=emitted,
                joined=together.send(item['ops'], item['limit']), after=together.snap())


def fixed_cases():
    cases = [
        case([BUY, BUY]), case([BUY, SELL]), case([BUY, COLLECT]), case([BUY, SELL, SELL, SELL]),
        case([COLLECT, BUY, COLLECT]), case([SYNC, SYNC]), case([INIT, INIT]), case([BUY, CLAIM]),
        case([FUND_VAULT, COLLECT]), case([FUND_VAULT, BUY, COLLECT]), case([COLLECT, FUND_VAULT, COLLECT]),
        case([FUND_CURVE, BUY]), case([FUND_ACCUMULATOR, CLOSE]),
        # Reopen: the second instruction sees an account the first one closed.
        case([CLOSE, INIT]), case([CLOSE, BUY]), case([BUY, CLOSE]), case([CLOSE, INIT, CLOSE, INIT]),
        case([CLOSE, FUND_ACCUMULATOR, INIT]), case([CLOSE, FUND_ACCUMULATOR, BUY]),
        # Rollback: a later failure undoes the earlier steps.
        case([CLOSE, CLOSE]), case([CLOSE, SYNC]), case([CLOSE, SELL]), case([SELL, BUY]), case([BUY, TOO_MUCH]),
        case([BUY, BUY, TOO_MUCH]), case([FUND_VAULT, TOO_MUCH]), case([COLLECT, BUY, SELL, TOO_MUCH]),
        case([BUY, ('migrate',)]), case([FILL, BUY]), case([FILL, SELL]), case([FILL, ('exact', 1, 1)]),
        case([FILL, COLLECT]), case([FILL, COLLECT, COLLECT]),
        # Completing buy, then migrate.
        case([FILL, ('migrate',)]), case([FILL, FUND_CURVE, ('migrate',)]), case([FILL, ('migrate',), COLLECT]),
        case([FILL, ('migrate',), BUY]), case([FILL, ('migrate',), SELL]), case([FILL, ('migrate',), ('migrate',)]),
        case([BUY, ('buy', 10**18, base.U64, 'fill'), ('migrate',)]),
        # Create, then trade on the new curve.
        case([CREATE], created=True), case([CREATE, BUY], created=True), case([CREATE, BUY, SELL], created=True),
        case([CREATE, FILL], created=True), case([CREATE, FILL, ('migrate',)], created=True),
        case([CREATE, CREATE], created=True), case([CREATE, BUY, TOO_MUCH], created=True),
        case([FUND_VAULT, CREATE, BUY, COLLECT], created=True), case([BUY, CREATE], created=True),
        # Cashback: the sell credits the accumulator the claim pays out.
        case([BUY, CASHBACK_SELL], cashback=True), case([BUY, CASHBACK_SELL, CLAIM], cashback=True),
        case([BUY, CASHBACK_SELL, CLOSE], cashback=True), case([BUY, CLAIM, CASHBACK_SELL], cashback=True),
        case([BUY, CASHBACK_SELL, CLAIM, CASHBACK_SELL, CLAIM], cashback=True),
        case([CLOSE, BUY, CASHBACK_SELL, CLAIM], cashback=True),
        case([BUY, CASHBACK_SELL, CLAIM, TOO_MUCH_CASHBACK], cashback=True),
    ]
    # The trace: 9 buys reach exactly 64 entries, the tenth is refused.
    cases += [case([BUY] * n) for n in (8, 9, 10, 12)]
    cases += [case([BUY] * n, limit=MAX_LIMIT) for n in (8, 9, 10)]
    cases += [case([BUY] * 8 + [SELL] * n) for n in (1, 2, 3)]
    cases += [case([BUY] * 8 + [COLLECT] * n) for n in (1, 3, 4, 5, 6)]
    cases += [case([BUY] * 8 + [FUND_VAULT] * n) for n in (6, 7, 8, 9)]
    cases += [case([CREATE, BUY, *[SELL] * n], created=True) for n in (4, 5, 6, 7, 8, 9, 10)]
    cases += [case([FILL, ('migrate',), *[COLLECT] * n]) for n in (5, 6, 7, 8)]
    return cases


def budget_cases():
    """The limit sits around the sum of the steps; `-delta` is relative to that sum."""
    cases = []
    for ops, setup in (([BUY, SELL], {}), ([BUY, BUY, BUY], {}), ([CLOSE, INIT], {}), ([FILL, ('migrate',)], {}),
                       ([CREATE, BUY], dict(created=True)), ([FUND_VAULT, BUY, COLLECT], {}),
                       ([BUY, CASHBACK_SELL, CLAIM], dict(cashback=True))):
        for delta in (150, 149, 0, -1, -1_000):
            cases.append(dict(case(ops, **setup), delta=delta))
    for ops, setup in (([BUY, SELL], {}), ([CREATE, BUY], dict(created=True))):
        for fraction in (0.2, 0.5, 0.7, 0.9):
            cases.append(dict(case(ops, **setup), fraction=fraction))
    return cases


def random_cases(count=500, seed=20261031):
    rng = random.Random(seed)
    cases = []
    while len(cases) < count:
        created = rng.random() < 0.2
        cashback = not created and rng.random() < 0.3
        ops = [CREATE] if created else []
        held = 0
        for _ in range(rng.randrange(1, 7)):
            roll = rng.random()
            if roll < 0.3:
                amount = rng.choice((1, rng.randrange(1, 10**12), rng.randrange(1, 10**14)))
                held += amount
                ops.append(('buy', amount, base.U64))
            elif roll < 0.4:
                ops.append(('exact', rng.randrange(1, 10**10), 1))
            elif roll < 0.6:
                amount = rng.choice((1, rng.randrange(1, max(held, 2)), held + 1))
                ops.append(('sell', amount, 0, 'cashback') if cashback else ('sell', amount, 0))
            elif roll < 0.7:
                ops.append(rng.choice((FUND_VAULT, FUND_CURVE, FUND_ACCUMULATOR)))
            elif roll < 0.97:
                ops.append(rng.choice((COLLECT, CLOSE, INIT, SYNC, CLAIM)))
            else:
                ops.append(FILL)
        cases.append(case(ops, created=created, cashback=cashback))
    return cases


class SameTxCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for table in (base.ELF_SHA256, cr.ELF_SHA256):
            for path, digest in table.items():
                assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'same-tx-host'
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

    def wrong(self, item, ran, answer):
        """Why the joined run disagrees with the model's answer, or None."""
        joined = ran['joined']
        fields = answer.split(',')
        payer = str(USER)
        if fields[0] == 'ok':
            fee, saved, units, trace = map(int, fields[1:])
            if joined['err'] is not None:
                return f'expected a pass: {joined["err"]}'
            if (joined['cu'], joined['trace']) != (units, trace):
                return f'units or trace: {joined["cu"], joined["trace"]} != {units, trace}'
            expected = dict(ran['apart'])
            lamports, owner, data = expected[payer]
            expected[payer] = (lamports + saved, owner, data)
            if not any('Log truncated' in line for line in joined['logs']):
                if events(joined['logs']) != ran['emitted']:
                    return 'events differ'
        else:
            index, failure, fee = int(fields[1]), fields[2], int(fields[3])
            if joined['err'] is None:
                return f'expected {failure} at {index}'
            found = int(re.search(r'\((\d+), ', joined['err']).group(1))
            if (found, label(joined['err'])) != (index, failure):
                return f'{found, label(joined["err"])} != {index, failure}'
            expected = dict(ran['before'])
            lamports, owner, data = expected[payer]
            expected[payer] = (lamports - fee, owner, data)
        if ran['after'] != expected:
            return 'end state differs: ' + str([k[:6] for k in expected if expected[k] != ran['after'][k]])
        return None

    def run_cases(self, cases):
        results = [run_case(item) for item in cases]
        answers = self.host_answers([r['line'] for r in results])
        self.assertEqual(len(answers), len(results))
        wrong = [(cases[i]['ops'], w) for i in range(len(cases))
                 for w in [self.wrong(cases[i], results[i], answers[i])] if w]
        self.assertEqual(wrong[:3], [], f'{len(wrong)} of {len(cases)} differ')
        return answers

    def test_fixed_cases_match_captured_program(self):
        answers = self.run_cases(fixed_cases())
        kinds = {a.split(',')[2] for a in answers if a.startswith('fail')}
        self.assertTrue({'trace', 'c3012', 'c6005', 'c6023', 'c11'} <= kinds, kinds)

    def test_budget_is_shared(self):
        cases = []
        for item in budget_cases():
            whole = run_case(dict(item, limit=SEPARATE_LIMIT))['joined']['cu'] - LEAD_UNITS
            limit = int(whole * item['fraction']) if 'fraction' in item else whole + item['delta']
            cases.append(dict(item, limit=limit))
        answers = self.run_cases(cases)
        self.assertEqual(sum(a.startswith('ok') for a in answers), 7)
        self.assertEqual({a.split(',')[2] for a in answers if a.startswith('fail')}, {'budget'})
        # A budget that holds the first step but not the second stops at the second step.
        self.assertIn(1, {int(a.split(',')[1]) for a in answers if a.startswith('fail')})
        self.assertIn(2, {int(a.split(',')[1]) for a in answers if a.startswith('fail')})

    def test_seeded_random_cases_match_captured_program(self):
        answers = self.run_cases(random_cases())
        self.assertGreater(sum(a.startswith('ok') for a in answers), 20)
        self.assertGreater(sum(a.startswith('fail') for a in answers), 20)

    def test_reopened_accumulator_is_new(self):
        chain = Chain()
        data = bytearray(chain.vm.get_account(base.USER_VOLUME).data)
        struct.pack_into('<Q', data, 41, 7)
        account = chain.vm.get_account(base.USER_VOLUME)
        chain.vm.set_account(base.USER_VOLUME, Account(account.lamports, bytes(data), base.PUMP))
        self.assertIsNone(chain.send([CLOSE, INIT])['err'])
        fresh = chain.vm.get_account(base.USER_VOLUME)
        self.assertEqual(bytes(fresh.data), base.ACCOUNT_DISC['UserVolumeAccumulator'] + bytes(USER) + bytes(97))
        self.assertEqual(fresh.lamports, 1_844_400)

    def test_failed_create_leaves_no_mint(self):
        chain = Chain(created=True)
        self.assertIsNotNone(chain.send([CREATE, FILL, ('migrate',)], MAX_LIMIT)['err'])
        self.assertIsNone(chain.snap()[str(CREATED)])
        self.assertIsNone(chain.snap()[str(chain.curve)])


if __name__ == '__main__':
    unittest.main()
