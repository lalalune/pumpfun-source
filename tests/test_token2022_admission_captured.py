"""Captured-program checks for Token-2022 bodies in the trades' account admission.

Every case runs a legacy, v2 or v3 trade from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured Pump Fees,
SPL Token, Token-2022 and Associated Token programs, on a Token-2022 base mint
and, on v2 and v3, a Token-2022 quote mint. A case holds one account fault, one
Token-2022 account body, or both.

`programs/pump/recovered/token2022_admission_host.rs` gets the body, the fault
and two twin runs: the fault on valid accounts, and the fault with a wrong owner
on the body's slot. It names the ending. Plain Token-2022 accounts are also run
against the same fault on SPL Token accounts. This shows matching behavior on
these inputs only; it is not a byte-identity claim.
"""
from pathlib import Path
import hashlib
import itertools
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
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_legacy_buy_captured as legacy_base  # noqa: E402
import test_v2_token_quote_captured as v2_base  # noqa: E402
import test_v3_trade_accounting_captured as v3_base  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
ELF_SHA256 = {
    ROOT / 'evidence/original/pump/deployed.so': '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    ROOT / 'evidence/original/pump_fees/deployed.so': legacy_base.ELF_SHA256[legacy_base.FEES_ELF],
    ROOT / 'evidence/dependencies/spl_token/deployed.so': '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ROOT / 'evidence/dependencies/spl_token_2022/deployed.so': '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ROOT / 'evidence/dependencies/associated_token/deployed.so': '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/token2022_admission_host.rs'

PAYER = Keypair.from_seed(bytes([239]) * 32)
ALIEN = Pubkey.from_bytes(bytes([62]) * 32)
OTHER_MINT = Pubkey.from_bytes(bytes([63]) * 32)
SYSTEM = legacy_base.SYSTEM
TOKEN = v3_base.TOKEN
TOKEN22 = v3_base.TOKEN22
ATA = v3_base.ATA
RENT_REFUSAL = 'InsufficientFundsForRent'

BUYBACK_LIST = 741  # eight keys in Global, the last at entry 7
FEE_LIST = 162  # seven more fee recipients

LEGACY_ARGS = {'sell': (10**12, 0), 'buy': (10**12, 10**15), 'buy_exact_sol_in': (10**8, 1)}
V2_ARGS = {'sell_v2': (10**12, 0), 'buy_v2': (10**12, 10**15), 'buy_exact_quote_in_v2': (10**8, 1)}
V3_ARGS = {'sell_v3': (10**12, 0), 'buy_v3': (10**12, 10**15), 'buy_exact_quote_in_v3': (10**9, 1)}
V2_ROUTE = {'sol': (v2_base.WSOL, TOKEN, 9), 't22': (v2_base.T22_QUOTE, TOKEN22, 6)}


def t22_ata(owner, mint):
    return Pubkey.find_program_address([bytes(owner), bytes(TOKEN22), bytes(mint)], ATA)[0]


class Fixture:
    """The expected accounts of one trade; faults edit them before the run."""

    base_mint, base_program, curve_base, user_base = 'base_mint', 'base_token_program', 'associated_base_bonding_curve', 'associated_base_user'
    trailing = ()

    def __init__(self, family, ix, quote):
        self.family, self.ix, self.quote = family, ix, quote
        self.read_only, self.unsigned = set(), False

    def to_token2022(self):
        """Move the base mint and its two accounts to Token-2022, in place."""
        mint = self.names[self.base_mint]
        held = self.accounts[mint]
        self.accounts[mint] = Account(held.lamports, bytes(held.data), TOKEN22)
        for slot, owner in ((self.curve_base, self.curve), (self.user_base, self.signer.pubkey())):
            old = self.accounts.pop(self.names[slot])
            self.names[slot] = t22_ata(owner, mint)
            self.accounts[self.names[slot]] = Account(old.lamports, bytes(old.data), TOKEN22)
        self.names[self.base_program] = TOKEN22
        return self

    def held(self, slot):
        return self.accounts.get(self.names[slot])

    def put(self, slot, data=None, owner=None):
        account = self.held(slot)
        self.accounts[self.names[slot]] = Account(account.lamports, bytes(account.data) if data is None else data,
                                                  account.owner if owner is None else owner)

    def token_field(self, slot, offset, key):
        data = bytearray(self.held(slot).data)
        data[offset:offset + 32] = bytes(key)
        self.put(slot, data=bytes(data))


def accumulator_bytes(disc, user):
    data = bytearray(137)
    data[:8] = disc
    data[8:40] = bytes(user)
    return bytes(data)


class LegacyFixture(Fixture):
    base_mint, base_program, curve_base, user_base = 'mint', 'token_program', 'associated_bonding_curve', 'associated_user'

    def __init__(self, ix, quote, **over):
        super().__init__('legacy', ix, quote)
        base = legacy_base
        USER = base.USER.pubkey()
        self.signer = base.USER
        c = dict(base.DEFAULTS, op='buy', rs=5 * 10**9, **over)
        user_tokens = over.get('user_base', 10**13)
        c.pop('user_base', None)
        curve = bytearray(base.curve_data(c))
        curve[81] = c.get('mayhem', 0)
        self.curve = base.CURVE
        self.accounts = {
            base.GLOBAL: Account(10**9, base.global_data(5_000, False), base.PUMP),
            base.FEE_CONFIG: Account(10**9, base.fee_config_data(c['tiers']), base.FEES),
            base.GLOBAL_VOLUME: Account(10**9, base.ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), base.PUMP),
            USER: Account(10**13, b'', SYSTEM),
            PAYER.pubkey(): Account(10**12, b'', SYSTEM),
            base.MINT: Account(10**9, base.mint_data(c['supply']), TOKEN),
            base.CURVE: Account(base.CURVE_RENT + c['rs'] + 10**10, bytes(curve), base.PUMP),
            base.ata(base.CURVE): Account(base.TOKEN_RENT, base.token_data(base.CURVE, c['rt']), TOKEN),
            base.ata(USER): Account(base.TOKEN_RENT, base.token_data(USER, user_tokens), TOKEN),
            base.CURVE_V2: Account(10**7, b'', SYSTEM),
            base.FEE_RECIPIENT: Account(10**9, b'', SYSTEM),
            base.BUYBACK: Account(10**9, b'', SYSTEM),
            base.VAULT: Account(10**9, b'', SYSTEM),
            base.USER_VOLUME: Account(10**9, accumulator_bytes(base.ACCOUNT_DISC['UserVolumeAccumulator'], USER), base.PUMP),
        }
        self.names = {
            'global': base.GLOBAL, 'fee_recipient': base.FEE_RECIPIENT, 'mint': base.MINT, 'bonding_curve': base.CURVE,
            'associated_bonding_curve': base.ata(base.CURVE), 'associated_user': base.ata(USER), 'user': USER,
            'system_program': SYSTEM, 'token_program': TOKEN, 'creator_vault': base.VAULT,
            'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP, 'global_volume_accumulator': base.GLOBAL_VOLUME,
            'user_volume_accumulator': base.USER_VOLUME, 'fee_config': base.FEE_CONFIG, 'fee_program': base.FEES,
            'curve': base.CURVE_V2, 'buyback': base.BUYBACK,
        }
        self.trailing = ['curve', 'buyback']
        self.args = LEGACY_ARGS[ix]


class V2Fixture(Fixture):
    def __init__(self, ix, quote, **over):
        super().__init__('v2', ix, quote)
        base = v2_base
        USER = base.USER.pubkey()
        self.signer = base.USER
        op = {'sell_v2': 'sell', 'buy_v2': 'buy', 'buy_exact_quote_in_v2': 'exact'}[ix]
        c = base.default_case(op=op, quote='spl' if quote == 'sol' else quote, **over)
        mint, program, decimals = V2_ROUTE[quote]
        native = quote == 'sol'
        q = lambda owner: base.ata(owner, mint, program)
        vault = base.pda(base.PUMP, b'creator-vault', bytes(base.CREATOR))
        self.roles = dict(native=native, quote_mint=mint, program=program)
        self.curve = base.CURVE
        recipient = base.RESERVED if c['mayhem'] else base.FEE_RECIPIENT
        lamports = c['curve_lamports'] + (c['rqr'] if native else 0)
        self.accounts = {
            base.GLOBAL: Account(10**9, base.global_bytes(c), base.PUMP),
            base.FEE_CONFIG: Account(10**9, base.fee_config_bytes(c), base.FEES),
            base.GLOBAL_VOLUME: Account(10**9, base.ACCOUNT_DISC['GlobalVolumeAccumulator'] + bytes(536), base.PUMP),
            USER: Account(10**13, b'', SYSTEM),
            PAYER.pubkey(): Account(10**12, b'', SYSTEM),
            base.BASE: Account(10**9, base.mint_bytes(c['mint_supply'], 6), TOKEN),
            mint: Account(10**9, base.mint_bytes(10**18, decimals), program),
            base.CURVE: Account(lamports, base.curve_bytes(c, SYSTEM if native else mint), base.PUMP),
            base.ata(base.CURVE, base.BASE): Account(base.TOKEN_RENT, base.token_bytes(base.BASE, base.CURVE, c['curve_base']), TOKEN),
            base.ata(USER, base.BASE): Account(base.TOKEN_RENT, base.token_bytes(base.BASE, USER, c['user_base']), TOKEN),
            base.USER_VOLUME: Account(base.rent(137), accumulator_bytes(base.ACCOUNT_DISC['UserVolumeAccumulator'], USER), base.PUMP),
        }
        for key in (recipient, base.BUYBACK, vault):
            self.accounts[key] = Account(10**9, b'', SYSTEM)
        if not native:
            amounts = {base.CURVE: c['curve_quote'], USER: c['user_quote']}
            for owner in (base.CURVE, USER, vault, base.USER_VOLUME, recipient, base.BUYBACK):
                self.accounts[q(owner)] = Account(base.TOKEN_RENT, base.token_bytes(mint, owner, amounts.get(owner, 0)), program)
        self.names = {
            'global': base.GLOBAL, 'base_mint': base.BASE, 'quote_mint': mint, 'base_token_program': TOKEN,
            'quote_token_program': program, 'associated_token_program': ATA, 'fee_recipient': recipient,
            'associated_quote_fee_recipient': q(recipient), 'buyback_fee_recipient': base.BUYBACK,
            'associated_quote_buyback_fee_recipient': q(base.BUYBACK), 'bonding_curve': base.CURVE,
            'associated_base_bonding_curve': base.ata(base.CURVE, base.BASE), 'associated_quote_bonding_curve': q(base.CURVE),
            'user': USER, 'associated_base_user': base.ata(USER, base.BASE), 'associated_quote_user': q(USER),
            'creator_vault': vault, 'associated_creator_vault': q(vault), 'sharing_config': base.SHARING,
            'global_volume_accumulator': base.GLOBAL_VOLUME, 'user_volume_accumulator': base.USER_VOLUME,
            'associated_user_volume_accumulator': q(base.USER_VOLUME), 'fee_config': base.FEE_CONFIG,
            'fee_program': base.FEES, 'system_program': SYSTEM, 'event_authority': base.EVENT_AUTHORITY, 'program': base.PUMP,
        }
        self.args = V2_ARGS[ix]


class V3Fixture(Fixture):
    def __init__(self, ix, quote, **over):
        super().__init__('v3', ix, quote)
        base = v3_base
        USER = base.USER.pubkey()
        self.signer = base.USER
        c = base.default_case(quote=quote, buy=int(ix != 'sell_v3'), **over)
        r = self.roles = base.roles(c)
        self.curve = base.CURVE
        self.accounts = {
            base.GLOBAL: Account(10**9, base.global_bytes(c), base.PUMP),
            base.FEE_CONFIG: Account(10**9, base.fee_config_bytes(c), base.FEES),
            USER: Account(10**12, b'', SYSTEM),
            PAYER.pubkey(): Account(10**12, b'', SYSTEM),
            base.BUYBACK: Account(10**9, b'', SYSTEM),
            base.BASE: Account(10**9, base.mint_bytes(c['mint_supply'], 6), TOKEN),
            r['quote_mint']: Account(10**9, base.mint_bytes(10**18, 9 if r['native'] else 6, c['tf']), r['program']),
            base.CURVE: Account(c['curve_lamports'], base.curve_bytes(c, r['curve_field']), base.PUMP),
            r['curve_base']: Account(base.TOKEN_RENT, base.token_bytes(base.BASE, base.CURVE, c['curve_base']), TOKEN),
            r['user_base']: Account(base.TOKEN_RENT, base.token_bytes(base.BASE, USER, c['user_base']), TOKEN),
            base.USER_VOLUME: Account(base.rent(137), accumulator_bytes(base.ACCOUNT_DISC['UserVolumeAccumulator'], USER), base.PUMP),
        }
        if not r['native']:
            for key, owner, amount in ((r['curve_quote'], base.CURVE, c['rqr']), (r['user_quote'], USER, c['user_quote']),
                                       (r['recipient'], base.BUYBACK, 0)):
                self.accounts[key] = Account(base.TOKEN_RENT, base.token_bytes(r['quote_mint'], owner, amount), r['program'])
        self.names = {
            'global': base.GLOBAL, 'base_mint': base.BASE, 'quote_mint': r['quote_mint'], 'base_token_program': TOKEN,
            'quote_token_program': r['program'], 'bonding_curve': base.CURVE,
            'associated_base_bonding_curve': r['curve_base'], 'associated_quote_bonding_curve': r['curve_quote'],
            'user': USER, 'associated_base_user': r['user_base'], 'associated_quote_user': r['user_quote'],
            'user_volume_accumulator': base.USER_VOLUME, 'fee_config': base.FEE_CONFIG,
            'buyback_fee_recipient': r['recipient'], 'system_program': SYSTEM, 'event_authority': base.EVENT_AUTHORITY,
            'program': base.PUMP,
        }
        self.args = V3_ARGS[ix]


def wrong(fx, slot):
    return Pubkey.from_bytes(bytes([100 + sorted(fx.names).index(slot)]) * 32)


def slot_fault(slot, kind):
    def apply(fx):
        if kind == 'readonly':
            fx.read_only.add(slot)
        elif fx.held(slot) is None and kind != 'key':
            return  # a native quote account does not exist to fault
        elif kind == 'key':
            fx.accounts[wrong(fx, slot)] = fx.held(slot) or Account(10**9, b'', SYSTEM)
            fx.names[slot] = wrong(fx, slot)
        elif kind == 'owner':
            fx.put(slot, owner=ALIEN)
        elif kind == 'missing':
            del fx.accounts[fx.names[slot]]
        elif kind == 'disc':
            fx.put(slot, data=bytes([fx.held(slot).data[0] ^ 0xff]) + bytes(fx.held(slot).data)[1:])
        elif kind == 'short':
            fx.put(slot, data=bytes(fx.held(slot).data)[:4])
        elif kind == 'mint':
            fx.token_field(slot, 0, OTHER_MINT)
        elif kind == 'auth':
            fx.token_field(slot, 32, ALIEN)
    return apply


def resize(slot, size):
    def apply(fx):
        fx.put(slot, data=bytes(fx.held(slot).data)[:size].ljust(size, b'\0'))
    return apply


def absent_accumulator(lamports, data=b''):
    def apply(fx):
        fx.accounts[fx.names['user_volume_accumulator']] = Account(lamports, data, SYSTEM)
    return apply


def fee_config_bump(fx):
    data = bytearray(fx.held('fee_config').data)
    data[8] ^= 1
    fx.put('fee_config', data=bytes(data))


def program_key(slot, key):
    def apply(fx):
        fx.names[slot] = key
    return apply


def other_base_program(fx):
    fx.names[fx.base_program] = TOKEN if fx.names[fx.base_program] == TOKEN22 else TOKEN22


def plain_account(slot):
    def apply(fx):
        fx.accounts[wrong(fx, slot)] = Account(10**9, b'', SYSTEM)
        fx.names[slot] = wrong(fx, slot)
    return apply


def unsigned(fx):
    fx.unsigned = True


def payee(slot, owner, entry=None, offset=None):
    def apply(fx):
        if entry is not None and fx.held('global') and len(fx.held('global').data) > 997:
            data = bytearray(fx.held('global').data)
            data[offset + 32 * entry:offset + 32 * (entry + 1)] = bytes(owner)
            fx.put('global', data=bytes(data))
        fx.names[slot] = owner
        if owner != SYSTEM:
            fx.accounts.setdefault(owner, Account(10**9, b'', SYSTEM))
    return apply


def drop_trailing(count):
    def apply(fx):
        fx.trailing = fx.trailing[:count]
    return apply


def swap_trailing(fx):
    fx.trailing = fx.trailing[::-1]


def trade_args(ixs, sell, buy, exact):
    def apply(fx):
        fx.args = dict(zip(ixs, (sell, buy, exact)))[fx.ix]
    return apply


def no_change(fx):
    pass


def shared_faults(faults, args, slots):
    """Faults that read the same on all three families. `args` is in sell, buy, exact order."""
    names = list(args)

    def fault(name, edit=no_change, **over):
        faults[name] = (over, edit)

    for slot, kinds in slots.items():
        for kind in kinds.split():
            fault(f'{slot}.{kind}', slot_fault(slot, kind))
    fault('user.unsigned', unsigned)
    fault('uva.len8', resize('user_volume_accumulator', 8))
    fault('uva.len136', resize('user_volume_accumulator', 136))
    fault('uva.absent', absent_accumulator(0))
    fault('uva.sysdata', absent_accumulator(10**9, b'\1\2'))
    fault('fee_config.bump', fee_config_bump)
    fault('fee_config.len100', resize('fee_config', 100))
    fault('system_program.ata', program_key('system_program', ATA))
    fault('system_program.plain', plain_account('system_program'))
    fault('event_authority.key', slot_fault('event_authority', 'key'))
    fault('program.token', program_key('program', TOKEN))
    fault('program.plain', plain_account('program'))
    fault('h.complete', complete=1)
    sell, buy, exact = args[names[0]], args[names[1]], args[names[2]]
    fault('h.zero', trade_args(names, (0, 0), (0, 10**15), (exact[0], 0)))
    fault('h.zero_quote', trade_args(names, sell, buy, (0, 1)))
    fault('h.over', trade_args(names, (10**14, 0), buy, exact), user_base=1)
    fault('h.limit', trade_args(names, (10**12, 10**15), (10**12, 0), (exact[0], 10**15)))


def legacy_faults():
    faults = {}
    shared_faults(faults, LEGACY_ARGS, {
        'global': 'key owner missing disc short',
        'fee_recipient': 'readonly',
        'mint': 'key owner missing short',
        'bonding_curve': 'key owner missing disc short readonly',
        'associated_bonding_curve': 'key owner missing short readonly mint auth',
        'associated_user': 'key owner missing short readonly mint auth',
        'creator_vault': 'key readonly',
        'global_volume_accumulator': 'key owner missing disc short',
        'user_volume_accumulator': 'key owner disc readonly',
        'fee_config': 'key owner missing disc short',
        'buyback': 'readonly',
    })
    faults['token_program.other'] = ({}, other_base_program)
    faults['token_program.ata'] = ({}, program_key('token_program', ATA))
    faults['token_program.plain'] = ({}, plain_account('token_program'))
    faults['fee_recipient.unlisted'] = ({}, payee('fee_recipient', ALIEN))
    faults['fee_recipient.listed'] = ({}, payee('fee_recipient', ALIEN, 6, FEE_LIST))
    faults['fee_recipient.zero'] = ({}, payee('fee_recipient', SYSTEM))
    faults['buyback.unlisted'] = ({}, payee('buyback', ALIEN))
    faults['buyback.listed'] = ({}, payee('buyback', ALIEN, 7, BUYBACK_LIST))
    faults['buyback.zero'] = ({}, payee('buyback', SYSTEM))
    faults['buyback.absent'] = ({}, drop_trailing(1))
    faults['curve_v2.absent'] = ({}, drop_trailing(0))
    faults['curve_v2.key'] = ({}, slot_fault('curve', 'key'))
    faults['curve_v2.swapped'] = ({}, swap_trailing)
    return faults


def v2_faults():
    faults = {}
    shared_faults(faults, V2_ARGS, {
        'global': 'key owner missing disc short',
        'base_mint': 'key owner missing short',
        'quote_mint': 'key owner missing short',
        'fee_recipient': 'key readonly',
        'associated_quote_fee_recipient': 'key owner missing short readonly mint auth',
        'associated_quote_buyback_fee_recipient': 'key missing mint',
        'bonding_curve': 'key owner missing disc short readonly',
        'associated_base_bonding_curve': 'key owner missing short readonly mint auth',
        'associated_quote_bonding_curve': 'key owner missing short readonly mint auth',
        'associated_base_user': 'key owner missing short readonly mint auth',
        'associated_quote_user': 'key owner missing short readonly mint auth',
        'creator_vault': 'key readonly',
        'associated_creator_vault': 'key missing mint',
        'global_volume_accumulator': 'key owner missing disc short',
        'user_volume_accumulator': 'key owner disc readonly',
        'associated_user_volume_accumulator': 'key missing',
        'fee_config': 'key owner missing disc short',
    })
    faults['base_token_program.other'] = ({}, other_base_program)
    faults['base_token_program.ata'] = ({}, program_key('base_token_program', ATA))
    faults['associated_token_program.plain'] = ({}, plain_account('associated_token_program'))
    faults['fee_program.plain'] = ({}, plain_account('fee_program'))
    return faults


def v3_faults():
    faults = {}
    shared_faults(faults, V3_ARGS, {
        'global': 'key owner missing disc short',
        'base_mint': 'key owner missing short',
        'quote_mint': 'key owner missing short',
        'bonding_curve': 'key owner missing disc short readonly',
        'associated_base_bonding_curve': 'key owner missing short readonly mint auth',
        'associated_quote_bonding_curve': 'key owner missing short readonly mint auth',
        'associated_base_user': 'key owner missing short readonly mint auth',
        'associated_quote_user': 'key owner missing short readonly mint auth',
        'user_volume_accumulator': 'key owner disc readonly',
        'fee_config': 'key owner missing disc short',
        'buyback_fee_recipient': 'key owner missing short readonly mint auth',
    })
    faults['base_token_program.other'] = ({}, other_base_program)
    faults['base_token_program.ata'] = ({}, program_key('base_token_program', ATA))
    faults['fee_config.len2511'] = ({}, resize('fee_config', 2511))
    faults['h.overflow'] = (dict(rqr=2**64 - 1, protocol_fees=1, curve_lamports=10**10), no_change)
    return faults


FAMILIES = {
    'legacy': (LegacyFixture, legacy_base, tuple(LEGACY_ARGS), ('sol',), legacy_faults()),
    'v2': (V2Fixture, v2_base, tuple(V2_ARGS), ('sol', 't22'), v2_faults()),
    'v3': (V3Fixture, v3_base, tuple(V3_ARGS), ('sol', 't22'), v3_faults()),
}
MINT_SLOTS = {'mint': 'base_mint', 'base_mint': 'base_mint', 'quote_mint': 'quote_mint'}
TOKEN_ROLE = {
    'associated_bonding_curve': 'curve_base', 'associated_base_bonding_curve': 'curve_base',
    'associated_user': 'user_base', 'associated_base_user': 'user_base',
    'associated_quote_bonding_curve': 'curve_quote', 'associated_quote_user': 'user_quote',
    'buyback_fee_recipient': 'payee', 'associated_quote_fee_recipient': 'payee',
    'associated_quote_buyback_fee_recipient': 'payee', 'associated_creator_vault': 'payee',
}


def tlv(kind, body=b''):
    return struct.pack('<HH', kind, len(body)) + body


def mint_with(data, kind=1, exts=b''):
    return bytes(data[:82]).ljust(165, b'\0') + bytes([kind]) + exts


def token_with(data, kind=2, exts=b''):
    return bytes(data[:165]) + bytes([kind]) + exts


MINT_BODIES = {
    'meta': ('extended', lambda d: mint_with(d, 1, tlv(18, bytes(64)))),
    'nontransfer': ('extended', lambda d: mint_with(d, 1, tlv(9))),
    'pause_off': ('extended', lambda d: mint_with(d, 1, tlv(26, bytes(33)))),
    'tlv_stub': ('extended', lambda d: mint_with(d, 1, b'\x01')),
    'overrun': ('bad_tlv', lambda d: mint_with(d, 1, struct.pack('<HH', 18, 200))),
    'len83': ('bad_length', lambda d: bytes(d[:82]) + b'\0'),
    'len165': ('bad_length', lambda d: bytes(d[:82]).ljust(165, b'\0')),
    'len355': ('bad_length', lambda d: bytes(d[:82]).ljust(355, b'\0')),
    'len166': ('wrong_type', lambda d: mint_with(d)),
    'type0': ('wrong_type', lambda d: mint_with(d, 0)),
    'type2': ('wrong_type', lambda d: mint_with(d, 2)),
    'uninit': ('uninitialized', lambda d: bytes(45) + b'\0' + bytes(d[46:82])),
    'pause_on': ('paused', lambda d: mint_with(d, 1, tlv(26, bytes(32) + b'\1'))),
    'hook': ('hook_set', lambda d: mint_with(d, 1, tlv(14, bytes(32) + bytes([7]) * 32))),
}
TOKEN_BODIES = {
    'immutable': ('extended', lambda d: token_with(d, 2, tlv(7))),
    'hook_account': ('extended', lambda d: token_with(d, 2, tlv(7) + tlv(15, b'\0'))),
    'pausable': ('extended', lambda d: token_with(d, 2, tlv(7) + tlv(27))),
    'overrun': ('extended', lambda d: token_with(d, 2, struct.pack('<HH', 7, 200))),
    'len164': ('bad_length', lambda d: bytes(d[:164])),
    'len200': ('bad_length', lambda d: bytes(d[:165]).ljust(200, b'\0')),
    'len355': ('bad_length', lambda d: bytes(d[:165]).ljust(355, b'\0')),
    'len166': ('wrong_type', lambda d: token_with(d)),
    'type0': ('wrong_type', lambda d: token_with(d, 0)),
    'type1': ('wrong_type', lambda d: token_with(d, 1)),
    'uninit': ('uninitialized', lambda d: bytes(d[:108]) + b'\0' + bytes(d[109:])),
    'frozen': ('frozen', lambda d: bytes(d[:108]) + b'\2' + bytes(d[109:])),
    'cpi_guard': ('cpi_guard', lambda d: token_with(d, 2, tlv(7) + tlv(11, b'\1'))),
    'memo': ('memo_required', lambda d: token_with(d, 2, tlv(7) + tlv(8, b'\1'))),
}
PAIR_MINT_BODIES = ('overrun', 'len83', 'type2', 'uninit', 'pause_on', 'hook')
PAIR_TOKEN_BODIES = ('len200', 'type1', 'uninit', 'frozen', 'cpi_guard', 'memo')
# Every fault on these, on these routes, stays within one test run's reach.
PAIR_ROUTES = {
    'legacy': (('sell', 'sol'), ('buy', 'sol'), ('buy_exact_sol_in', 'sol')),
    'v2': (('sell_v2', 't22'), ('buy_v2', 'sol'), ('buy_exact_quote_in_v2', 't22')),
    'v3': (('sell_v3', 't22'), ('sell_v3', 'sol'), ('buy_v3', 't22'), ('buy_exact_quote_in_v3', 'sol')),
}
SKIPPED_KINDS = {'owner', 'disc', 'plain'}


def slots_of(family, quote):
    """The body slots of a route, as (slot, bodies)."""
    fixture = FAMILIES[family][0]
    base = [(fixture.base_mint, MINT_BODIES), (fixture.curve_base, TOKEN_BODIES), (fixture.user_base, TOKEN_BODIES)]
    if quote == 'sol':
        return base
    rest = ['associated_quote_bonding_curve', 'associated_quote_user']
    rest += ['buyback_fee_recipient'] if family == 'v3' else ['associated_quote_fee_recipient',
                                                              'associated_quote_buyback_fee_recipient',
                                                              'associated_creator_vault']
    return base + [('quote_mint', MINT_BODIES)] + [(slot, TOKEN_BODIES) for slot in rest]


class Program:
    """One LiteSVM per family, kept across cases."""

    def __init__(self, family):
        base = FAMILIES[family][1]
        self.family, self.base = family, base
        self.vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
        for key, path in ((base.PUMP, ROOT / 'evidence/original/pump/deployed.so'),
                          (base.FEES, ROOT / 'evidence/original/pump_fees/deployed.so'),
                          (TOKEN, ROOT / 'evidence/dependencies/spl_token/deployed.so'),
                          (TOKEN22, ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'),
                          (ATA, ROOT / 'evidence/dependencies/associated_token/deployed.so')):
            self.vm.add_program_from_file(key, path)
        stamp = getattr(base, 'TIMESTAMP', 1_700_000_000)
        epoch = getattr(base, 'EPOCH', 0)
        self.vm.set_clock(Clock(100, stamp, epoch, epoch, stamp))
        self.seen = set()

    def run(self, fx):
        vm, base = self.vm, self.base
        for key in self.seen - set(fx.accounts):
            vm.set_account(key, Account(0, b'', SYSTEM))
        for key, account in fx.accounts.items():
            vm.set_account(key, account)
        self.seen |= set(fx.accounts)
        ix = base.IX[fx.ix]
        metas = [AccountMeta(fx.names[a['name']], bool(a.get('signer')) and not (a['name'] == 'user' and fx.unsigned),
                             bool(a.get('writable')) and a['name'] not in fx.read_only) for a in ix['accounts']]
        metas += [AccountMeta(fx.names[slot], False, slot != 'curve' and slot not in fx.read_only) for slot in fx.trailing]
        data = bytes(ix['discriminator']) + struct.pack('<QQ', *fx.args)
        if not fx.ix.startswith('sell'):
            data += bytes(2) if self.family == 'legacy' else bytes([0])
        payer = PAYER if fx.unsigned else fx.signer
        vm.expire_blockhash()
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), Instruction(base.PUMP, data, metas)],
                                               payer.pubkey(), [payer], vm.latest_blockhash())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            if code:
                return int(code.group(1))
            words = re.sub(r'[^A-Za-z]+', ' ', text).split()
            return RENT_REFUSAL if RENT_REFUSAL in text else words[-1] if words else text
        return 'ok'


def build(family, ix, quote, name=None, t22=True):
    fixture, _, _, _, faults = FAMILIES[family]
    over, edit = faults[name] if name else ({}, no_change)
    fx = fixture(ix, quote, **over)
    if t22:
        fx.to_token2022()
    edit(fx)
    return fx


def model_fault(name):
    slot, kind = name.split('.')
    role = TOKEN_ROLE.get(slot, slot)
    return f"{slot if role == 'payee' else role}.{kind}"


class Token2022AdmissionCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        cls.host = Path(cls.tmp.name) / 'token2022-admission-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(cls.host)], check=True)
        cls.programs = {family: Program(family) for family in FAMILIES}
        cls.plain, cls.probe = {}, {}

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def run_body(self, family, ix, quote, name, slot, make):
        fx = build(family, ix, quote, name)
        held = fx.held(slot)
        if held is None:
            return None
        fx.put(slot, data=make(bytes(held.data)))
        return self.programs[family].run(fx)

    def plain_run(self, family, ix, quote, name):
        key = (family, ix, quote, name)
        if key not in self.plain:
            self.plain[key] = self.programs[family].run(build(family, ix, quote, name))
        return self.plain[key]

    def probe_run(self, family, ix, quote, name, slot):
        key = (family, ix, quote, name, slot)
        if key not in self.probe:
            fx = build(family, ix, quote, name)
            fx.put(slot, owner=ALIEN)
            self.probe[key] = self.programs[family].run(fx)
        return self.probe[key]

    def line(self, family, ix, quote, name, slot, kind):
        role = MINT_SLOTS.get(slot) or TOKEN_ROLE[slot]
        side = 'sell' if ix.startswith('sell') else 'buy'
        return ' '.join(str(x) for x in (family, side, role, kind, model_fault(name) if name else '-',
                                         self.plain_run(family, ix, quote, name), self.probe_run(family, ix, quote, name, slot)))

    def answers(self, lines):
        text = ''.join(line + '\n' for line in lines)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
        self.assertEqual(len(out), len(lines))
        return out

    def compare(self, cases):
        """`cases` holds (family, ix, quote, fault, slot, body name, bodies)."""
        lines, got, kept = [], [], []
        for family, ix, quote, name, slot, label, bodies in cases:
            kind, make = bodies[label]
            captured = self.run_body(family, ix, quote, name, slot, make)
            if captured is None:
                continue
            lines.append(self.line(family, ix, quote, name, slot, kind))
            got.append(str(captured))
            kept.append((family, ix, quote, name, slot, label))
        answers = self.answers(lines)
        wrong_cases = [(case, line, answer, seen) for case, line, answer, seen in zip(kept, lines, answers, got) if answer != seen]
        self.assertEqual(wrong_cases[:15], [], f'{len(wrong_cases)} of {len(kept)} differ')
        return kept, answers

    def test_plain_token2022_accounts_admit_like_spl_token(self):
        for family, (_, _, ixs, quotes, faults) in FAMILIES.items():
            program = self.programs[family]
            for ix, quote, name in itertools.product(ixs, quotes, faults):
                spl = program.run(build(family, ix, quote, name, t22=False))
                self.assertEqual(self.plain_run(family, ix, quote, name), spl, (family, ix, quote, name))

    def body_cases(self):
        return [(family, ix, quote, None, slot, label, bodies)
                for family, (_, _, ixs, quotes, _) in FAMILIES.items() for ix in ixs for quote in quotes
                for slot, bodies in slots_of(family, quote) for label in bodies]

    def pair_cases(self):
        cases = []
        for family, routes in PAIR_ROUTES.items():
            faults = [n for n in FAMILIES[family][4] if n.split('.')[1] not in SKIPPED_KINDS]
            for ix, quote in routes:
                for slot, bodies in slots_of(family, quote):
                    for label in (PAIR_MINT_BODIES if bodies is MINT_BODIES else PAIR_TOKEN_BODIES):
                        cases += [(family, ix, quote, name, slot, label, bodies) for name in faults if name.split('.')[0] != slot]
        return cases

    def test_a_body_alone_matches_captured_program(self):
        kept, answers = self.compare(self.body_cases())
        self.assertEqual(set(answers), {'ok', 'InvalidAccountData', 'UninitializedAccount', '17', '36', '42', '67', '6063'})

    def test_a_body_with_a_fault_matches_captured_program(self):
        kept, answers = self.compare(self.pair_cases())
        self.assertGreater(len(kept), 5000)

    def test_a_body_loses_or_wins_on_both_sides_of_the_transfer(self):
        # A frozen user account loses to an earlier gate and beats a later buyback check.
        fixture = TOKEN_BODIES['frozen'][1]
        self.assertEqual(self.run_body('legacy', 'sell', 'sol', 'h.complete', 'associated_user', fixture), 6005)
        self.assertEqual(self.run_body('legacy', 'sell', 'sol', 'buyback.unlisted', 'associated_user', fixture), 17)
        self.assertEqual(self.plain_run('legacy', 'sell', 'sol', 'buyback.unlisted'), 6057)

    def test_checker_rejects_a_different_outcome(self):
        # Negative control: the same inputs with another body give another answer.
        line = 'legacy sell user_base {} buyback.unlisted 6057 6057'
        self.assertEqual(self.answers([line.format('frozen'), line.format('extended')]), ['17', '6057'])
        self.assertEqual(self.answers(['legacy sell user_base frozen h.complete 6005 6005']), ['6005'])


if __name__ == '__main__':
    unittest.main()
