"""Captured-program checks for Token-2022 bodies outside the trades.

Every case runs an instruction from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022 and Associated Token programs. The expected accounts come from the
base tests' fixtures, moved to one Token-2022 mint. A case rewrites the bytes of
the mint and of up to two token accounts: length, type byte, state, option tags,
stored mint and authority, or the owning program.

The final bytes go to `programs/pump/recovered/token2022_nontrade_admission_host.rs`,
which names the ending. A passing body must also move the same tokens as a plain
one. This shows matching behavior on these inputs only; it is not a
byte-identity claim.
"""
from pathlib import Path
import hashlib
import itertools
import random
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from solders.account import Account
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_claim_cashback_v2_captured as cashback  # noqa: E402
import test_creator_fee_collect_captured as collect  # noqa: E402
import test_creator_fee_distribution_quote_captured as dist  # noqa: E402
import test_holder_distribution_token_captured as holder  # noqa: E402
import test_sweep_fees_captured as sweep  # noqa: E402
import test_token_incentives_captured as incentives  # noqa: E402
import test_token_schedule_captured as schedule  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEPS = ROOT / 'evidence/dependencies'
TOKEN22_ELF = DEPS / 'spl_token_2022/deployed.so'
ELF_SHA256 = {
    ROOT / 'evidence/original/pump/deployed.so': '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    DEPS / 'spl_token/deployed.so': '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    DEPS / 'associated_token/deployed.so': '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/token2022_nontrade_admission_host.rs'

PUMP, SYSTEM = sweep.PUMP, sweep.SYSTEM
TOKEN, ATA = sweep.TOKEN, sweep.ATA
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
FEE_PAYER = Keypair.from_seed(bytes([240]) * 32)
RENT = 10**8
OTHER = bytes([9]) * 32
RUNTIME = {'InvalidAccountData': 'invalid_account_data', 'UninitializedAccount': 'uninitialized_account',
           'IncorrectProgramId': 'incorrect_program_id'}


def t22(owner, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN22), bytes(mint)], ATA)[0]


def mint_bytes():
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', 10**18) + bytes([6, 1]) + struct.pack('<I', 0) + bytes(32)


def token_bytes(mint, owner, amount):
    return (bytes(mint) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def tacc(mint, owner, amount):
    return Account(RENT, token_bytes(mint, owner, amount), TOKEN22)


class Route:
    def __init__(self, name, ix, keys, accounts, signers, data=b'', tail=(), mints=(), tokens=(), budget=False):
        self.name, self.ix, self.keys, self.accounts, self.signers = name, ix, keys, accounts, signers
        self.data, self.tail, self.mints, self.tokens, self.budget = data, tail, mints, tokens, budget


def r_sweep(bucket):
    item = sweep.case(bucket=bucket, native=False)
    mint, curve = sweep.QUOTE_MINT, sweep.CURVE
    recipient = sweep.VAULT if bucket == 'creator' else sweep.FEE_RECIPIENT
    keys = dict(payer=sweep.PAYER.pubkey(), base_mint=sweep.BASE_MINT, quote_mint=mint, quote_token_program=TOKEN22,
                associated_token_program=ATA, system_program=SYSTEM, bonding_curve=curve,
                associated_quote_bonding_curve=t22(curve, mint), recipient=recipient,
                associated_quote_recipient=t22(recipient, mint), event_authority=sweep.EVENT_AUTHORITY, program=PUMP)
    keys['global'] = sweep.GLOBAL
    accounts = {
        sweep.PAYER.pubkey(): Account(10**12, b'', SYSTEM),
        sweep.GLOBAL: Account(10**9, sweep.global_data(), PUMP),
        sweep.BASE_MINT: Account(10**9, sweep.mint_data(), TOKEN),
        mint: Account(10**9, mint_bytes(), TOKEN22),
        curve: Account(sweep.curve_lamports(item), sweep.curve_data(item), PUMP),
        recipient: Account(10**9, b'', SYSTEM),
        keys['associated_quote_bonding_curve']: tacc(mint, curve, 10**10),
        keys['associated_quote_recipient']: tacc(mint, recipient, 0),
    }
    ix = sweep.IX['sweep_creator_fee' if bucket == 'creator' else 'sweep_protocol_fee']
    return Route(f'sweep_{bucket}', ix, keys, accounts, [sweep.PAYER], mints=('quote_mint',),
                 tokens=('associated_quote_bonding_curve', 'associated_quote_recipient'))


def r_collect():
    b = collect
    vault = b.pda([b'creator-vault', bytes(b.CREATOR)])
    q = b.QUOTE
    keys = dict(creator=b.CREATOR, creator_vault=vault, system_program=SYSTEM, event_authority=b.EVENT_AUTHORITY, program=PUMP,
                creator_token_account=t22(b.CREATOR, q), creator_vault_token_account=t22(vault, q), quote_mint=q,
                quote_token_program=TOKEN22, associated_token_program=ATA)
    accounts = {
        vault: Account(10**8, b'', SYSTEM), b.CREATOR: Account(10**9, b'', SYSTEM),
        q: Account(10**9, mint_bytes(), TOKEN22),
        keys['creator_vault_token_account']: tacc(q, vault, 10**6),
        keys['creator_token_account']: tacc(q, b.CREATOR, 0),
    }
    return Route('collect_v2', b.IX['collect_creator_fee_v2'], keys, accounts, [], mints=('quote_mint',),
                 tokens=('creator_vault_token_account', 'creator_token_account'))


def r_cashback():
    b = cashback
    item = b.case(native=False)
    q = b.QUOTE_MINT
    keys = dict(user=b.USER, user_volume_accumulator=b.UVA, quote_mint=q, quote_token_program=TOKEN22,
                associated_token_program=ATA, associated_user_volume_accumulator=t22(b.UVA, q),
                associated_quote_user=t22(b.USER, q), system_program=SYSTEM, event_authority=b.EVENT_AUTHORITY, program=PUMP)
    accounts = {
        b.USER: Account(10**9, b'', SYSTEM),
        b.UVA: Account(b.rent(b.UVA_LEN) + item['extra'], b.uva_data(item), PUMP),
        q: Account(10**9, mint_bytes(), TOKEN22),
        keys['associated_user_volume_accumulator']: tacc(q, b.UVA, 500_000),
        keys['associated_quote_user']: tacc(q, b.USER, 3),
    }
    return Route('cashback_v2', b.IX, keys, accounts, [], mints=('quote_mint',),
                 tokens=('associated_user_volume_accumulator', 'associated_quote_user'))


def r_schedule():
    b = schedule
    item = b.case()
    gata = t22(b.GVA, b.MINT)
    keys = dict(authority=b.AUTHORITY.pubkey(), global_volume_accumulator=b.GVA, mint=b.MINT,
                global_incentive_token_account=gata, associated_token_program=ATA, system_program=SYSTEM,
                token_program=TOKEN22, event_authority=b.EVENT_AUTHORITY, program=PUMP)
    keys['global'] = b.GLOBAL
    accounts = {
        b.AUTHORITY.pubkey(): Account(10**12, b'', SYSTEM),
        b.GLOBAL: Account(10**9, b.global_data(), PUMP),
        b.GVA: Account(10**9, b.gva_data(item), PUMP),
        b.MINT: Account(10**9, mint_bytes(), TOKEN22),
        gata: tacc(b.MINT, b.GVA, 0),
    }
    return Route('schedule', b.IX, keys, accounts, [b.AUTHORITY], data=b.args(item), mints=('mint',),
                 tokens=('global_incentive_token_account',))


def r_claim():
    b = incentives
    item = b.case()
    gata, uata = t22(b.GLOBAL_VOLUME, b.MINT), t22(b.USER, b.MINT)
    keys = dict(user=b.USER, user_ata=uata, global_volume_accumulator=b.GLOBAL_VOLUME, global_incentive_token_account=gata,
                user_volume_accumulator=b.USER_VOLUME, mint=b.MINT, token_program=TOKEN22, system_program=SYSTEM,
                associated_token_program=ATA, event_authority=b.EVENT_AUTHORITY, program=PUMP, payer=b.PAYER.pubkey())
    accounts = {
        b.PAYER.pubkey(): Account(10**12, b'', SYSTEM),
        b.MINT: Account(10**9, mint_bytes(), TOKEN22),
        b.GLOBAL_VOLUME: Account(10**9, b.global_volume_data(item), PUMP),
        gata: tacc(b.MINT, b.GLOBAL_VOLUME, item['vault']),
        b.USER_VOLUME: Account(10**9, b.user_volume_data(item), PUMP),
        uata: tacc(b.MINT, b.USER, 0),
    }
    return Route('claim_incentives', b.IX['claim_token_incentives'], keys, accounts, [b.PAYER], mints=('mint',),
                 tokens=('user_ata', 'global_incentive_token_account'))


def r_dist():
    b = dist
    item = b.case()
    vault_ata = t22(b.VAULT, b.QUOTE)
    IX = next(i for i in b.IDL['instructions'] if i['name'] == 'distribute_creator_fees_v2')
    keys = dict(payer=b.PAYER.pubkey(), mint=b.MINT, bonding_curve=b.CURVE, sharing_config=b.SHARING, creator_vault=b.VAULT,
                system_program=SYSTEM, event_authority=b.EVENT_AUTHORITY, program=PUMP,
                creator_vault_quote_token_account=vault_ata, quote_mint=b.QUOTE, quote_token_program=TOKEN22,
                associated_token_program=ATA)
    accounts = {
        b.PAYER.pubkey(): Account(10**12, b'', SYSTEM),
        b.MINT: Account(10**9, b.mint_data(6), TOKEN),
        b.QUOTE: Account(10**9, mint_bytes(), TOKEN22),
        b.CURVE: Account(10**9, b.curve_data(item), PUMP),
        b.SHARING: Account(10**9, b.sharing_data(item), b.FEES),
        b.VAULT: Account(b.VAULT_LAMPORTS, b'', SYSTEM),
        vault_ata: tacc(b.QUOTE, b.VAULT, item['vault_tokens']),
    }
    wallets, atas = [], []
    for i, h in enumerate(item['holders']):
        a = b.holder_address(i, h)
        wallets.append(a)
        atas.append(t22(a, b.QUOTE))
        accounts[a] = Account(10**9, b'', SYSTEM)
        accounts[atas[-1]] = tacc(b.QUOTE, a, 0)
    tail = (wallets + atas)[:item['remaining']]
    keys['share_0'] = atas[0]
    return Route('distribute_v2', IX, keys, accounts, [b.PAYER], data=bytes([0]), tail=tail, mints=('quote_mint',),
                 tokens=('creator_vault_quote_token_account', 'share_0'), budget=True)


def r_holder(amount=500):
    b = holder
    q, w = b.STABLE, b.WALLETS[0]
    source, target = t22(b.REWARDS, q), t22(w, q)
    keys = dict(holder_reward_claim_authority=b.AUTHORITY.pubkey(), mint=b.MINT, holder_rewards=b.REWARDS,
                holder_rewards_token_account=source, quote_mint=q, quote_token_program=TOKEN22,
                associated_token_program=ATA, system_program=SYSTEM, event_authority=b.EVENT_AUTHORITY, program=PUMP)
    keys['global'] = b.GLOBAL
    keys['share_0'] = target
    g = bytearray(1088)
    g[:8] = b.GLOBAL_DISC
    g[8] = 1
    g[1054:1086] = bytes(b.AUTHORITY.pubkey())
    g[1086] = 1
    accounts = {
        b.AUTHORITY.pubkey(): Account(10**10, b'', SYSTEM),
        b.GLOBAL: Account(10**9, bytes(g), PUMP),
        b.MINT: Account(1_461_600, b.mint_data(), TOKEN),
        q: Account(1_461_600, mint_bytes(), TOKEN22),
        b.REWARDS: Account(10**9, b'', SYSTEM),
        w: Account(b.WALLET_LAMPORTS, b'', SYSTEM),
        source: tacc(q, b.REWARDS, 10**6),
        target: tacc(q, w, 0),
    }
    data = (1).to_bytes(4, 'little') + struct.pack('<Q', amount)
    return Route('holder', b.IX, keys, accounts, [b.AUTHORITY], data=data, tail=[w, target], mints=('quote_mint',),
                 tokens=('holder_rewards_token_account', 'share_0'), budget=True)


def r_collect_empty():
    r = r_collect()
    k = r.keys['creator_vault_token_account']
    a = r.accounts[k]
    r.accounts[k] = Account(a.lamports, token_bytes(r.keys['quote_mint'], r.keys['creator_vault'], 0), TOKEN22)
    r.name = 'collect_empty'
    return r


def r_sweep_empty():
    item = sweep.case(bucket='protocol', native=False, protocol_fees=0)
    r = r_sweep('protocol')
    r.accounts[sweep.CURVE] = Account(sweep.curve_lamports(item), sweep.curve_data(item), PUMP)
    r.name = 'sweep_empty'
    return r


def r_cashback_empty():
    r = r_cashback()
    k = r.keys['associated_user_volume_accumulator']
    r.accounts[k] = Account(RENT, token_bytes(r.keys['quote_mint'], cashback.UVA, 0), TOKEN22)
    a = r.accounts[cashback.UVA]
    r.accounts[cashback.UVA] = Account(cashback.rent(cashback.UVA_LEN), bytes(a.data), PUMP)
    r.name = 'cashback_empty'
    return r


def r_holder_zero():
    r = r_holder(0)
    r.name = 'holder_zero'
    return r


BUILD = {'sweep_protocol': lambda: r_sweep('protocol'), 'sweep_creator': lambda: r_sweep('creator'), 'collect_v2': r_collect,
         'cashback_v2': r_cashback, 'schedule': r_schedule, 'claim_incentives': r_claim, 'distribute_v2': r_dist, 'holder': r_holder,
         'collect_empty': r_collect_empty, 'sweep_empty': r_sweep_empty, 'cashback_empty': r_cashback_empty, 'holder_zero': r_holder_zero}


def error_name(result):
    text = str(result.err())
    code = re.search(r'Custom\((\d+)\)', text)
    if code:
        return f'error:{code.group(1)}'
    for name, short in RUNTIME.items():
        if name in text:
            return f'error:{short}'
    return f'error:{text}'


def setb(at, value):
    return lambda d: d[:at] + bytes([value]) + d[at + 1:]


def chain(*edits):
    def apply(data):
        for edit in edits:
            data = edit(data)
        return data
    return apply


def sized(length, kind):
    """A body of this length, its type byte set when it has one."""
    def apply(d):
        grown = d[:length] + bytes(max(0, length - len(d)))
        return grown[:165] + bytes([kind]) + grown[166:] if length > 165 else grown
    return apply


def typed_tail(base, kind, payload=b''):
    return lambda d: d + bytes(165 - base) + bytes([kind]) + payload


ENTRY = struct.pack('<HH', 7, 0)
OVERRUN = struct.pack('<HH', 7, 1000)
TOKEN_KINDS = {f'len{n}': sized(n, 2) for n in (160, 164, 166, 167, 168, 169, 170, 171, 200, 354, 355, 356, 400)}
TOKEN_KINDS.update({
    'type0': typed_tail(165, 0, ENTRY), 'type1': typed_tail(165, 1, ENTRY), 'type3': typed_tail(165, 3, ENTRY),
    'entry': typed_tail(165, 2, ENTRY), 'overrun': typed_tail(165, 2, OVERRUN), 'bare1': typed_tail(165, 1),
    'state0': setb(108, 0), 'state2': setb(108, 2), 'state3': setb(108, 3), 'state9': setb(108, 9),
    'delegate1': setb(72, 1), 'delegate2': setb(72, 2), 'delegatehigh': setb(73, 1),
    'native2': setb(109, 2), 'nativehigh': setb(111, 1), 'close1': setb(129, 1), 'close2': setb(129, 2),
    'closehigh': setb(132, 1), 'mint': lambda d: OTHER + d[32:], 'auth': lambda d: d[:32] + OTHER + d[64:],
    'mintbody': lambda d: mint_bytes(), 'mintext': lambda d: mint_bytes() + bytes(83) + b'\x01' + ENTRY,
    'state0len166': chain(sized(166, 2), setb(108, 0)), 'state0type1': chain(typed_tail(165, 1, ENTRY), setb(108, 0)),
    'state0len164': chain(sized(164, 2), setb(108, 0)), 'close2len166': chain(sized(166, 2), setb(129, 2)),
    'state0len355': chain(sized(355, 2), setb(108, 0)), 'state0close2': chain(setb(108, 0), setb(129, 2)),
    'state9close2': chain(setb(108, 9), setb(129, 2)), 'frozenext': chain(typed_tail(165, 2, ENTRY), setb(108, 2)),
    'frozentype1': chain(typed_tail(165, 1, ENTRY), setb(108, 2)), 'frozenlen166': chain(sized(166, 2), setb(108, 2)),
    'mintext2': chain(typed_tail(165, 2, ENTRY), lambda d: OTHER + d[32:]),
    'authext': chain(typed_tail(165, 2, OVERRUN), lambda d: d[:32] + OTHER + d[64:]),
})
MINT_KINDS = {f'len{n}': sized(n, 1) for n in (79, 81, 83, 100, 164, 165, 166, 167, 168, 170, 200, 354, 355, 356)}
MINT_KINDS.update({
    'type0': typed_tail(82, 0, ENTRY), 'type2': typed_tail(82, 2, ENTRY), 'type3': typed_tail(82, 3, ENTRY),
    'entry': typed_tail(82, 1, ENTRY), 'overrun': typed_tail(82, 1, OVERRUN),
    'pad': lambda d: d + b'\x07' + bytes(82) + b'\x01' + ENTRY, 'padlate': lambda d: d + bytes(82) + b'\x07\x01' + ENTRY,
    'init0': setb(45, 0), 'init2': setb(45, 2), 'authority1': setb(0, 1), 'authority2': setb(0, 2), 'authorityhigh': setb(1, 1),
    'freeze1': setb(46, 1), 'freeze2': setb(46, 2), 'tokenbody': lambda d: token_bytes(PUMP, PUMP, 0),
    'tokenext': lambda d: token_bytes(PUMP, PUMP, 0) + b'\x02' + ENTRY,
    'init0len83': chain(sized(83, 1), setb(45, 0)), 'init0type2': chain(typed_tail(82, 2, ENTRY), setb(45, 0)),
    'init0pad': chain(lambda d: d + b'\x07' + bytes(82) + b'\x01' + ENTRY, setb(45, 0)),
    'init0len166': chain(sized(166, 1), setb(45, 0)), 'init0len355': chain(sized(355, 1), setb(45, 0)),
    'init0len200': chain(sized(200, 2), setb(45, 0)), 'badtaglen83': chain(sized(83, 1), setb(0, 2)),
    'init0tag': chain(setb(45, 0), setb(46, 2)), 'init2type2': chain(typed_tail(82, 2, ENTRY), setb(45, 2)),
})
PAIR_KINDS = ('len166', 'close2', 'state0', 'mint', 'auth', 'state2', 'spl')
MINT_PAIR_KINDS = ('len83', 'init0', 'spl')


def slots_of(route):
    return (route.mints[0],) + route.tokens


def plain_faults(route):
    slots = slots_of(route)
    faults = [f'0.{k}' for k in MINT_KINDS] + ['0.spl']
    for index in range(1, len(slots)):
        faults += [f'{index}.{k}' for k in TOKEN_KINDS] + [f'{index}.spl']
    return faults


def pair_faults(route):
    faults = [f'0.{k}' for k in MINT_PAIR_KINDS]
    for index in range(1, len(slots_of(route))):
        faults += [f'{index}.{k}' for k in PAIR_KINDS]
    return faults


def expected(route, index):
    """The mint and authority a token account should hold, from the fixture."""
    if index == 0:
        return b'', b''
    data = bytes(route.accounts[route.keys[slots_of(route)[index]]].data)
    return data[:32], data[32:64]


class Case:
    def __init__(self, route, faults):
        self.route, self.faults = route, faults
        self.accounts = dict(route.accounts)
        slots = slots_of(route)
        for fault in faults:
            index, kind = fault.split('.')
            key = route.keys[slots[int(index)]]
            held = self.accounts[key]
            if kind == 'spl':
                self.accounts[key] = Account(held.lamports, bytes(held.data), TOKEN)
            else:
                table = MINT_KINDS if index == '0' else TOKEN_KINDS
                self.accounts[key] = Account(held.lamports, table[kind](bytes(held.data)), held.owner)

    def host_line(self):
        fields = [self.route.name]
        for index, slot in enumerate(slots_of(self.route)):
            held = self.accounts[self.route.keys[slot]]
            mint, authority = expected(self.route, index)
            fields.append(':'.join(('t' if held.owner == TOKEN22 else 's', bytes(held.data).hex(), mint.hex(), authority.hex())))
        return ' '.join(fields)


class Harness:
    """One VM. Each run clears the last run's accounts and writes its own."""

    def __init__(self):
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        self.vm.add_program_from_file(PUMP, sweep.PUMP_ELF)
        self.vm.add_program_from_file(TOKEN, sweep.TOKEN_ELF)
        self.vm.add_program_from_file(TOKEN22, TOKEN22_ELF)
        self.vm.add_program_from_file(ATA, sweep.ATA_ELF)
        self.stale = []

    def put(self, key, account):
        self.vm.set_account(key, account)
        self.stale.append(key)

    def tokens(self, route, index):
        account = self.vm.get_account(route.keys[slots_of(route)[index]])
        return int.from_bytes(bytes(account.data)[64:72], 'little') if account and len(account.data) >= 72 else 0

    def run(self, case):
        route = case.route
        for key in self.stale:
            self.vm.set_account(key, Account(0, b'', SYSTEM))
        self.stale.clear()
        self.vm.expire_blockhash()
        now = incentives.DEFAULTS['now'] if route.name == 'claim_incentives' else 1_700_000_000
        self.vm.set_clock(sweep.Clock(100, now, 0, 0, now))
        self.put(FEE_PAYER.pubkey(), Account(10**12, b'', SYSTEM))
        for key, account in case.accounts.items():
            self.put(key, account)
        metas = [AccountMeta(route.keys[a['name']], a.get('signer', False), a.get('writable', False)) for a in route.ix['accounts']]
        metas += [AccountMeta(key, False, True) for key in route.tail]
        instructions = [set_compute_unit_limit(1_400_000)] if route.budget else []
        instructions.append(Instruction(PUMP, bytes(route.ix['discriminator']) + route.data, metas))
        tx = Transaction.new_signed_with_payer(instructions, FEE_PAYER.pubkey(), [FEE_PAYER] + route.signers,
                                               self.vm.latest_blockhash())
        before = [self.tokens(route, i) for i in range(1, len(slots_of(route)))]
        result = self.vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            return error_name(result), None
        return 'ok', [self.tokens(route, i + 1) - held for i, held in enumerate(before)]


def single_cases():
    return [Case(r, (f,)) for r in ROUTES.values() for f in plain_faults(r)]


def pair_cases():
    cases = []
    for route in ROUTES.values():
        faults = pair_faults(route)
        cases += [Case(route, pair) for pair in itertools.combinations(faults, 2)]
    return cases


def triple_cases(count=900, seed=31225):
    rng = random.Random(seed)
    routes = list(ROUTES.values())
    cases = []
    for _ in range(count):
        route = rng.choice(routes)
        faults = pair_faults(route) + rng.sample(plain_faults(route), 12)
        cases.append(Case(route, tuple(rng.sample(faults, 3))))
    return cases


ROUTES = {name: build() for name, build in BUILD.items()}


class Token2022NontradeAdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'token2022-nontrade-admission-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.harness = Harness()
        cls.plain = {name: cls.harness.run(Case(route, ())) for name, route in ROUTES.items()}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(case.host_line() + '\n' for case in cases)
        return subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        wrong = []
        for case, answer in zip(cases, answers):
            captured, moved = self.harness.run(case)
            if captured != answer or (moved is not None and moved != self.plain[case.route.name][1]):
                wrong.append((case.route.name, case.faults, answer, captured))
        self.assertEqual(wrong[:40], [], f'{len(wrong)} of {len(cases)} differ')

    def test_plain_accounts_pass_and_move_tokens(self):
        self.assertEqual({v[0] for v in self.plain.values()}, {'ok'})
        moved = {name: any(v[1]) for name, v in self.plain.items()}
        self.assertEqual({name for name, m in moved.items() if not m},
                         {'schedule', 'sweep_empty', 'collect_empty', 'cashback_empty', 'holder_zero'})

    def test_single_bodies_match_captured_program(self):
        self.run_cases(single_cases())

    def test_fault_pairs_match_captured_program(self):
        self.run_cases(pair_cases())

    def test_seeded_triples_match_captured_program(self):
        self.run_cases(triple_cases())

    def test_checker_rejects_a_changed_answer(self):
        # Negative control: run_cases must fail when the host's answer changes.
        case = Case(ROUTES['sweep_protocol'], ())
        for changed in ('error:2000', 'error:invalid_account_data'):
            with mock.patch.object(self, 'host_answers', lambda cases: [changed] * len(cases)):
                with self.assertRaises(AssertionError):
                    self.run_cases([case])

    def test_cases_reach_every_stop(self):
        answers = set(self.host_answers(single_cases()))
        self.assertEqual({a for a in answers if a.startswith('error:')},
                         {f'error:{c}' for c in (3, 4, 17, 2014, 2015, 2021, 2023, 6004, 6010, 6054, 6076)}
                         | {'error:invalid_account_data', 'error:uninitialized_account', 'error:incorrect_program_id'})


if __name__ == '__main__':
    unittest.main()
