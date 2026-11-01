"""Captured-program checks for Pump `migrate_v2` into a real PumpSwap pool.

`tests/test_migrate_v2_captured.py` replaces pump_amm with a no-op, so it never
runs a migration with tokens in the curve to its end. Here every case runs
`evidence/original/pump/deployed.so` with `evidence/original/pump_amm/deployed.so`
and the captured SPL Token, Token-2022 and Associated Token programs on LiteSVM,
for native, SPL and Token-2022 quotes. The same inputs go to
`programs/pump/recovered/migrate_v2_pool_host.rs`, and the error, the stored pool,
every balance and lamport movement, the LP mint, the closed accounts and the
events must agree. This shows matching behavior on these inputs only; it is not
a byte-identity claim.
"""
from pathlib import Path
import hashlib
import json
import random
import re
import struct
import subprocess
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

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
AMM_ELF = ROOT / 'evidence/original/pump_amm/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    AMM_ELF: '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/migrate_v2_pool_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
AMM_IDL = json.loads((ROOT / 'programs/pump/idls/pump_amm.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
PUMP_AMM = Pubkey.from_string(AMM_IDL['address'])
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
RENT = Pubkey.from_string('SysvarRent111111111111111111111111111111111')
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
SYSTEM = Pubkey.default()
MIGRATE = next(i for i in IDL['instructions'] if i['name'] == 'migrate_v2')
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
CONFIG_DISC = bytes(next(a['discriminator'] for a in AMM_IDL['accounts'] if a['name'] == 'GlobalConfig'))
POOL_DISC = bytes(next(a['discriminator'] for a in AMM_IDL['accounts'] if a['name'] == 'Pool'))
disc = lambda idl, name: bytes(next(e['discriminator'] for e in idl['events'] if e['name'] == name))
MIGRATION_EVENT = disc(IDL, 'CompletePumpAmmMigrationEvent')
CREATE_POOL_EVENT = disc(AMM_IDL, 'CreatePoolEvent')
BOOST_EVENT = disc(AMM_IDL, 'InitBoostEvent')

EMIT_CPI_TAG = bytes.fromhex('e445a52e51cb9a1d')

USER = Keypair.from_seed(bytes([223]) * 32)
MINT = Pubkey.from_bytes(bytes([73]) * 32)
QUOTE = Pubkey.from_bytes(bytes([74]) * 32)
CREATOR = Pubkey.from_bytes(bytes([60]) * 32)
WITHDRAW = Pubkey.from_bytes(bytes([61]) * 32)
TS = 1_800_000_000
TX_FEE = 5000
TOKEN_RENT = 2_039_280
WITHDRAW_START = 1_000_000
U64 = 2**64 - 1


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(seeds, program)[0]


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA)


GLOBAL = pda([b'global'])
CURVE = pda([b'bonding-curve', bytes(MINT)])
AUTHORITY = pda([b'pool-authority', bytes(MINT)])
AMM_CONFIG = pda([b'global_config'], PUMP_AMM)


def names(item):
    token = TOKEN22 if item['t22'] else TOKEN
    quote, program = (WSOL, TOKEN) if item['quote'] == 'sol' else (QUOTE, TOKEN if item['quote'] == 'spl' else TOKEN22)
    pool = pda([b'pool', struct.pack('<H', 0), bytes(AUTHORITY), bytes(MINT), bytes(quote)], PUMP_AMM)
    lp_mint = pda([b'pool_lp_mint', bytes(pool)], PUMP_AMM)
    boost_authority = pda([b'boost_vault', bytes(pool)], PUMP_AMM)
    return {
        'global': GLOBAL, 'withdraw_authority': WITHDRAW, 'base_mint': MINT, 'quote_mint': quote,
        'bonding_curve': CURVE, 'associated_base_bonding_curve': ata(CURVE, MINT, token),
        'associated_quote_bonding_curve': ata(CURVE, quote, program), 'user': USER.pubkey(), 'system_program': SYSTEM,
        'pump_amm': PUMP_AMM, 'pool': pool, 'pool_authority': AUTHORITY,
        'pool_authority_mint_account': ata(AUTHORITY, MINT, token),
        'pool_authority_quote_account': ata(AUTHORITY, quote, program), 'amm_global_config': AMM_CONFIG,
        'lp_mint': lp_mint, 'user_pool_token_account': ata(AUTHORITY, lp_mint, TOKEN22),
        'pool_base_token_account': ata(pool, MINT, token), 'pool_quote_token_account': ata(pool, quote, program),
        'base_token_program': token, 'quote_token_program': program, 'token_2022_program': TOKEN22,
        'associated_token_program': ATA, 'pump_amm_event_authority': pda([b'__event_authority'], PUMP_AMM),
        'rent': RENT, 'event_authority': pda([b'__event_authority']), 'program': PUMP,
        'boost_authority': boost_authority, 'boost_vault': ata(boost_authority, quote, program),
    }


def mint_data(decimals=6, supply=10**18, fee_bps=0):
    data = struct.pack('<I32sQBBI32s', 0, bytes(32), supply, decimals, 1, 0, bytes(32))
    if not fee_bps:
        return data
    rate = struct.pack('<QQH', 0, U64, fee_bps)
    extension = bytes(64) + bytes(8) + rate + rate
    return data + bytes(165 - len(data)) + bytes([1]) + struct.pack('<HH', 1, len(extension)) + extension


def token_data(mint, owner, amount, native=None, extra=b''):
    option = struct.pack('<IQ', 1, native) if native is not None else struct.pack('<IQ', 0, 0)
    return struct.pack('<32s32sQI32sB', bytes(mint), bytes(owner), amount, 0, bytes(32), 1) + option + struct.pack('<QI32s', 0, 0, bytes(32)) + extra


def global_data(fee):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    struct.pack_into('<QQQQQ', data, 73, 1_073_000_000_000_000, 30_000_000_000, 793_100_000_000_000, 10**15, 95)
    data[113:145] = bytes(WITHDRAW)
    data[145] = 1
    struct.pack_into('<QQ', data, 146, fee, 30)
    data[450] = 1
    struct.pack_into('<Q', data, 1005, 4_000_000_000)
    return bytes(data)


def curve_data(item):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, 279_900_000_000_000, 115_005_359_056, 0, item['rqr'], 10**15)
    data[48] = 1
    data[49:81] = bytes(CREATOR)
    data[81], data[82] = item['mayhem'], item['cashback']
    if item['quote'] != 'sol':
        data[83:115] = bytes(QUOTE)
    struct.pack_into('<Q', data, 115, item['cfb'])
    data[123], data[124] = item['can_edit'], item['holder']
    struct.pack_into('<QQ', data, 150, 0, item['pcqi'])
    return bytes(data)


def config_data(item):
    data = bytearray(1200)
    data[:8] = CONFIG_DISC
    struct.pack_into('<QQB', data, 40, 25, 5, item['flags'])
    data[417], data[642], data[939] = item['may_on'], item['cb_on'], item['boost']
    return bytes(data)


DEFAULTS = dict(tokens=206_900_000_000_000, rqr=85_005_359_056, pcqi=0, fee=15_000_001, mayhem=0, cashback=0, cfb=0,
                can_edit=0, holder=0, pa_mint=None, pa_wsol=None, pool_base=None, pool_quote=None, user_lp=0,
                pa_lamports=0, pool_lamports=0, lp_lamports=0, taken='', flags=0, may_on=0, cb_on=0, boost=0, remaining=0,
                vault=0, t22=0, tfee=0, slack=10_000_000, quote='sol', qfee=0)


def case(**changes):
    unknown = set(changes) - set(DEFAULTS)
    assert not unknown, unknown
    return dict(DEFAULTS, **changes)


def host_line(item):
    dash = lambda v: '-' if v is None else v
    return ','.join(map(str, [item['quote'], item['qfee'], item['tokens'], item['rqr'], item['pcqi'], item['fee'], item['mayhem'], item['cashback'],
                              dash(item['pa_mint']), dash(item['pa_wsol']), dash(item['pool_base']),
                              dash(item['pool_quote']), item['user_lp'], item['pa_lamports'], item['pool_lamports'],
                              item['lp_lamports'], int('pool' in item['taken']), int('lp' in item['taken']), int(item['flags'] & 1), item['may_on'],
                              item['cb_on'], item['boost'], item['remaining'], item['vault'], item['t22'],
                              item['tfee']]))


class Bench:
    """One VM for all cases: the programs stay, each key is cleared after a run."""

    def __init__(self):
        self.vm = LiteSVM().with_transaction_history(0)
        programdata = pda([bytes(PUMP)], UPGRADEABLE)
        self.vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + PUMP_ELF.read_bytes(),
                                                 UPGRADEABLE, False))
        self.vm.set_account(PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
        self.vm.add_program_from_file(PUMP_AMM, AMM_ELF)
        self.vm.add_program_from_file(TOKEN22, TOKEN22_ELF)
        self.vm.add_program_from_file(TOKEN, TOKEN_ELF)
        self.vm.add_program_from_file(ATA, ATA_ELF)
        self.vm.set_clock(Clock(1000, 0, 0, 0, TS))
        self.stale = set()

    def run(self, item):
        vm = self.vm
        for key in self.stale:
            vm.set_account(key, Account(0, b'', SYSTEM))
        vm.expire_blockhash()
        keys = names(item)
        token, quote_key = keys['base_token_program'], keys['quote_mint']
        program = keys['quote_token_program']
        pool_key, lp_key, vault_key = keys['pool'], keys['lp_mint'], keys['boost_vault']
        native = item['quote'] == 'sol'
        extension = lambda bps: bytes([2]) + struct.pack('<HHQ', 2, 8, 0) if bps else b''
        fee_account, quote_extra = extension(item['tfee']), extension(item['qfee'])
        wrapped = lambda: TOKEN_RENT if native else None
        quote_rent = 2_157_600 if item['qfee'] else TOKEN_RENT
        quote_lamports = lambda amount: TOKEN_RENT + amount if native else quote_rent
        reserves = item['rqr'] + item['pcqi']
        state = {GLOBAL: (10**9, PUMP, global_data(item['fee'])), USER.pubkey(): (10**15, SYSTEM, b''),
                 WITHDRAW: (WITHDRAW_START, SYSTEM, b''), MINT: (1_461_600, token, mint_data(fee_bps=item['tfee'])),
                 quote_key: (1_461_600, program, mint_data(9 if native else 6, 0 if native else 10**18, item['qfee'])),
                 CURVE: ((reserves if native else 0) + item['slack'], PUMP, curve_data(item)),
                 keys['associated_base_bonding_curve']: (TOKEN_RENT, token, token_data(MINT, CURVE, item['tokens'], extra=fee_account)),
                 AMM_CONFIG: (10**7, PUMP_AMM, config_data(item))}
        if not native:
            state[keys['associated_quote_bonding_curve']] = (quote_rent, program, token_data(quote_key, CURVE, reserves, extra=quote_extra))
        if item['pa_lamports']:
            state[AUTHORITY] = (item['pa_lamports'], SYSTEM, b'')
        if item['pool_lamports']:
            state[pool_key] = (item['pool_lamports'], SYSTEM, b'')
        if item['lp_lamports']:
            state[lp_key] = (item['lp_lamports'], SYSTEM, b'')
        if 'pool' in item['taken']:
            state[pool_key] = (2_888_400, PUMP_AMM, bytes(287))
        if 'lp' in item['taken']:
            state[lp_key] = (1_461_600, TOKEN22, mint_data(9, 0))
        if item['pa_mint'] is not None:
            state[keys['pool_authority_mint_account']] = (TOKEN_RENT, token, token_data(MINT, AUTHORITY, item['pa_mint'], extra=fee_account))
        if item['pa_wsol'] is not None:
            state[keys['pool_authority_quote_account']] = (quote_lamports(item['pa_wsol']), program,
                                                           token_data(quote_key, AUTHORITY, item['pa_wsol'], wrapped(), quote_extra))
        if item['pool_base'] is not None:
            state[keys['pool_base_token_account']] = (TOKEN_RENT, token, token_data(MINT, pool_key, item['pool_base'], extra=fee_account))
        if item['pool_quote'] is not None:
            state[keys['pool_quote_token_account']] = (quote_lamports(item['pool_quote']), program,
                                                       token_data(quote_key, pool_key, item['pool_quote'], wrapped(), quote_extra))
        if item['user_lp']:
            state[keys['user_pool_token_account']] = (2_074_080, TOKEN22, token_data(lp_key, AUTHORITY, 0, None, bytes([2]) + struct.pack('<HH', 7, 0)))
        if item['vault']:
            state[vault_key] = (quote_rent, program, token_data(quote_key, keys['boost_authority'], 0, wrapped(), quote_extra))
        for key, (lamports, owner, data) in state.items():
            vm.set_account(key, Account(lamports, data, owner))
        self.stale = set(keys.values()) | set(state)
        self.stale -= {SYSTEM, TOKEN, TOKEN22, ATA, PUMP, PUMP_AMM, RENT, GLOBAL, USER.pubkey(), AMM_CONFIG}
        metas = [AccountMeta(keys[a['name']], a.get('signer', False), a.get('writable', False) or a['name'] == 'quote_mint' and item['qfee'] > 0)
                 for a in MIGRATE['accounts']]
        metas += [AccountMeta(k, False, True) for k in (keys['boost_authority'], vault_key)[:item['remaining']]]
        ix = Instruction(PUMP, bytes(MIGRATE['discriminator']), metas)
        tx = Transaction.new_signed_with_payer([set_compute_unit_limit(1_400_000), ix], USER.pubkey(), [USER],
                                               vm.latest_blockhash())
        lamports = lambda key: vm.get_account(key).lamports if vm.get_account(key) else 0
        user_before = lamports(USER.pubkey())
        result = vm.send_transaction(tx)
        if isinstance(result, FailedTransactionMetadata):
            text = str(result.err())
            code = re.search(r'Custom\((\d+)\)', text)
            return {'error': int(code.group(1)) if code else text}
        amount = lambda key: struct.unpack_from('<Q', vm.get_account(key).data, 64)[0] if vm.get_account(key) else None
        pool = vm.get_account(pool_key)
        lp = vm.get_account(lp_key)
        return {'error': None, 'pool': bytes(pool.data), 'pool_lamports': pool.lamports,
                'user': user_before - lamports(USER.pubkey()), 'withdraw': lamports(WITHDRAW) - WITHDRAW_START,
                'curve': (lamports(CURVE), bytes(vm.get_account(CURVE).data)),
                'lp': (struct.unpack_from('<Q', lp.data, 36)[0], lp.lamports),
                'pool_base': amount(keys['pool_base_token_account']), 'pool_quote': amount(keys['pool_quote_token_account']),
                'wsol': amount(keys['pool_authority_quote_account']), 'vault': amount(vault_key),
                'authority': (lamports(AUTHORITY), vm.get_account(keys['pool_authority_mint_account']) is None,
                              vm.get_account(keys['user_pool_token_account']) is None),
                'curve_tokens': amount(keys['associated_base_bonding_curve']),
                'events': [bytes(ix.instruction().data)[8:] for group in result.inner_instructions() for ix in group
                           if bytes(ix.instruction().data)[:8] == EMIT_CPI_TAG]}


def fixed_cases():
    return native_cases() + [dict(item, quote=quote) for item in native_cases() for quote in ('spl', 't22')] + token_cases()


def token_cases():
    cases = []
    add = lambda **k: cases.append(case(**k))
    for quote in ('spl', 't22'):
        for tokens, reserves in ((1, 1), (1, 9_999), (1, 10_000), (9, 1_111), (9, 1_112), (99, 99), (99, 102), (100, 99),
                                 (100, 100), (10_000, 1), (10_000, 2), (101, 101), (2, 5_000)):
            add(quote=quote, tokens=tokens, rqr=reserves)
        add(quote=quote, rqr=0)
        add(quote=quote, rqr=0, pcqi=1)
        add(quote=quote, rqr=1, pcqi=0)
        add(quote=quote, fee=0)
        add(quote=quote, fee=6_424_080)
        add(quote=quote, fee=6_424_079)
        add(quote=quote, fee=6_424_079, pa_lamports=1)
        add(quote=quote, fee=4_000_000)
        add(quote=quote, fee=1, flags=1)
    add(quote='t22', qfee=100)
    add(quote='t22', qfee=10_000)
    add(quote='t22', qfee=1, rqr=1)
    add(quote='t22', qfee=100, flags=1)
    add(quote='t22', qfee=100, tokens=0)
    add(quote='t22', qfee=100, t22=1, tfee=100)
    add(quote='t22', qfee=100, fee=6_424_079)
    add(quote='t22', qfee=250, boost=1, remaining=2)
    add(quote='t22', qfee=250, boost=0, remaining=2)
    add(quote='t22', qfee=250, boost=1, remaining=2, vault=1)
    add(quote='t22', qfee=250, pa_wsol=5)
    add(quote='t22', qfee=250, pool_quote=5)
    add(quote='t22', qfee=250, pool_base=5, pa_mint=7)
    add(quote='t22', qfee=250, mayhem=1, may_on=1)
    add(quote='t22', qfee=1)
    add(quote='t22', qfee=5_000, rqr=2)
    add(quote='t22', qfee=5_000, rqr=3, tokens=10**6)
    return cases


def native_cases():
    cases = [case()]
    add = lambda **k: cases.append(case(**k))
    # Liquidity: zero sides, and the floor of the root around the minimum.
    add(tokens=0)
    add(rqr=15_000_001)
    add(tokens=0, rqr=15_000_001)
    add(rqr=15_000_000)
    add(rqr=15_000_000, pcqi=1)
    add(rqr=15_000_000, pcqi=2)
    for tokens, quote in ((1, 1), (1, 9_999), (1, 10_000), (9, 1_111), (9, 1_112), (99, 99), (99, 102), (100, 99), (100, 100),
                          (10_000, 1), (10_000, 2), (101, 101), (4, 2_500), (3, 3_333), (3, 3_334), (2, 5_000)):
        add(tokens=tokens, rqr=15_000_001 + quote)
    add(tokens=U64, rqr=2**63)
    add(tokens=U64, rqr=U64 - 10_000_000 - 15_000_001)
    # post_complete_quote_in joins the quote.
    add(pcqi=1)
    add(pcqi=99, rqr=15_000_000)
    add(pcqi=15_000_001, rqr=0)
    add(pcqi=10**10)
    # Fee boundaries: four Pump accounts, then the pool, LP mint and LP account.
    for fee in (0, 1, 8_157_119, 8_157_120, 8_157_121, 11_045_519, 11_045_520, 11_045_521, 12_507_119, 12_507_120,
                12_507_121, 14_581_199, 14_581_200, 14_581_201, 10**9):
        add(fee=fee)
    add(fee=14_581_199, pa_lamports=1)
    add(fee=14_581_199, pool_lamports=1)
    add(fee=14_581_199, lp_lamports=1)
    add(fee=10**6, pa_lamports=14_000_000)
    add(fee=14_581_200, pa_lamports=5)
    add(pa_lamports=123_456)
    # Rent paid only for what is missing.
    for key in ('pool_lamports', 'lp_lamports'):
        for lamports in (1, 777, 1_461_599, 1_461_600, 1_461_601, 2_888_399, 2_888_400, 2_888_401, 5 * 10**6):
            add(**{key: lamports})
    # Rent failures come before every pump_amm handler check.
    for fault in (dict(flags=1), dict(tokens=0), dict(mayhem=1), dict(cashback=1)):
        add(fee=11_000_000, **fault)
        add(fee=14_581_200, **fault)
        add(fee=14_581_199, **fault)
    # pump_amm handler order.
    add(mayhem=1, cashback=1)
    add(mayhem=1, cashback=1, may_on=1)
    add(mayhem=1, flags=1)
    add(cashback=1, flags=1)
    add(flags=1, tokens=0)
    add(tokens=0, rqr=15_000_001, flags=1)
    add(tokens=1, rqr=15_000_002, flags=1)
    for flags in (2, 4, 8, 16, 32, 64, 128, 3, 255, 254):
        add(flags=flags)
    # Flags stored on the pool.
    add(mayhem=1, may_on=1)
    add(cashback=1, cb_on=1)
    add(may_on=1, cb_on=1)
    add(mayhem=1, may_on=1, cashback=1, cb_on=1, cfb=5, can_edit=1, holder=1)
    add(cfb=20_000)
    add(cfb=U64)
    add(can_edit=1)
    add(holder=1)
    # Accounts already there.
    add(pa_mint=0)
    add(pa_mint=5)
    add(pa_mint=5, tokens=0)
    add(pa_mint=10**6, pcqi=99)
    add(pa_wsol=0)
    add(pa_wsol=7_777)
    add(pool_base=0)
    add(pool_base=9)
    add(pool_quote=0)
    add(pool_quote=9)
    add(pool_base=9, pool_quote=9, pa_mint=9, pa_wsol=9)
    add(tokens=99, rqr=15_000_000 + 100, pool_base=10**6, pool_quote=10**6)
    add(user_lp=1)
    add(user_lp=1, fee=12_507_120)
    add(taken='pool')
    add(taken='lp')
    add(taken='pool', flags=1)
    add(taken='lp', fee=1)
    add(pool_base=0, pool_quote=0, pa_mint=0, pa_wsol=0, fee=6_424_080)
    add(pool_base=0, pool_quote=0, pa_mint=0, pa_wsol=0, fee=6_424_079)
    # Boost: the gate, the vault's rent, and the amount.
    add(boost=1)
    add(boost=1, remaining=1)
    add(boost=0, remaining=1)
    add(boost=1, remaining=2)
    add(boost=0, remaining=2)
    add(boost=1, remaining=2, vault=1)
    add(boost=0, remaining=2, vault=1)
    add(boost=1, remaining=2, mayhem=1, may_on=1)
    add(boost=1, remaining=0, mayhem=1, may_on=1)
    add(boost=1, remaining=1, mayhem=1, may_on=1)
    add(boost=1, remaining=2, cashback=1, cb_on=1)
    add(boost=1, remaining=2, pcqi=1_000)
    add(boost=1, remaining=2, tokens=10**15)
    add(boost=1, remaining=2, tokens=10**15 - 1)
    add(boost=1, remaining=2, tokens=10**15 + 1)
    add(boost=1, remaining=2, tokens=2 * 10**15)
    add(boost=1, remaining=2, tokens=10**6)
    add(boost=1, remaining=2, tokens=10**15 // 84_990_359_055)
    add(boost=1, remaining=2, tokens=10**15 // 84_990_359_055 + 1)
    add(boost=1, remaining=2, tokens=U64, rqr=2**63)
    add(boost=1, remaining=2, tokens=U64, rqr=2**40)
    add(boost=1, remaining=2, pool_base=10**14, pool_quote=10**9)
    add(boost=1, remaining=2, fee=14_581_200)
    add(boost=1, remaining=2, fee=14_581_199)
    add(boost=1, remaining=2, flags=1)
    add(boost=1, remaining=2, tokens=0)
    # Token-2022 base mint.
    add(t22=1)
    add(t22=1, boost=1, remaining=2)
    add(t22=1, tokens=0)
    add(t22=1, pa_mint=5, pool_base=9)
    add(t22=1, tfee=100)
    add(t22=1, tfee=10_000)
    add(t22=1, tfee=1, tokens=1)
    add(t22=1, tfee=100, flags=1)
    add(t22=1, tfee=100, tokens=0)
    add(t22=1, tfee=100, mayhem=1)
    add(t22=1, tfee=100, fee=11_000_000)
    return cases


def random_cases(count=200, seed=8170):
    rng = random.Random(seed)
    cases = []
    maybe = lambda p, value: value if rng.random() < p else None
    for _ in range(count):
        cases.append(case(quote=rng.choice(('sol', 'spl', 't22')), tokens=rng.choice((0, rng.randrange(1, 500), rng.randrange(1, 10**12), rng.randrange(1, 10**16))),
                          rqr=rng.randrange(15_000_001, 10**12) if rng.random() < 0.8 else 15_000_001 + rng.randrange(0, 2_000),
                          pcqi=rng.choice((0, 0, rng.randrange(1, 10**10))),
                          fee=rng.choice((15_000_001, rng.randrange(14_000_000, 15_000_000), 14_581_200)),
                          mayhem=int(rng.random() < 0.2), cashback=int(rng.random() < 0.2), cfb=rng.randrange(0, 20_000),
                          can_edit=rng.randrange(2), holder=rng.randrange(2), pa_mint=maybe(0.2, rng.randrange(0, 10**6)),
                          pa_wsol=maybe(0.2, rng.randrange(0, 10**6)), pool_base=maybe(0.2, rng.randrange(0, 10**6)),
                          pool_quote=maybe(0.2, rng.randrange(0, 10**6)), pa_lamports=rng.choice((0, 0, rng.randrange(1, 10**6))),
                          pool_lamports=rng.choice((0, 0, rng.randrange(1, 4 * 10**6))),
                          lp_lamports=rng.choice((0, 0, rng.randrange(1, 2 * 10**6))), flags=rng.choice((0, 0, 0, 1, 14)),
                          may_on=int(rng.random() < 0.8), cb_on=int(rng.random() < 0.8), boost=rng.randrange(2),
                          remaining=rng.choice((0, 2, 2, 1)), vault=rng.randrange(2), t22=int(rng.random() < 0.2)))
        if cases[-1]['quote'] == 't22':
            cases[-1]['qfee'] = rng.choice((0, 1, 100, 2_500))
    return cases


class MigrateV2PoolCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'migrate-v2-pool-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)], check=True)
        cls.host = host
        cls.bench = Bench()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_matches(self, item, answer, captured):
        if answer == 'error:-1':
            self.assertIn('IllegalOwner', str(captured['error']))
            return
        if answer.startswith('error:'):
            self.assertEqual(captured['error'], int(answer[6:]))
            return
        self.assertIsNone(captured['error'])
        fields = answer.split(',')[1:]
        wsol_left = None if fields[10] == '-' else int(fields[10])
        base, quote, initial, lp_out, pool_base, pool_quote, boosted, vault, user_paid, gain = map(int, fields[:10])
        self.assertEqual(captured['pool_base'], pool_base)
        self.assertEqual(captured['pool_quote'], pool_quote)
        self.assertEqual(captured['vault'], vault if item['vault'] or (item['remaining'] == 2 and not item['mayhem']) else None)
        self.assertEqual(captured['lp'], (0, max(1_461_600, item['lp_lamports'])))
        self.assertEqual(captured['authority'], (0, True, True))
        self.assertEqual(captured['wsol'], wsol_left)
        self.assertEqual(captured['user'], TX_FEE + user_paid)
        self.assertEqual(captured['withdraw'], gain)
        self.assertEqual(captured['curve_tokens'], 0)
        after = bytearray(curve_data(item))
        struct.pack_into('<QQQQ', after, 8, 0, 0, 0, 0)
        self.assertEqual(captured['curve'], (item['slack'], bytes(after)))
        self.assertEqual(captured['pool_lamports'], max(2_888_400, item['pool_lamports']))
        self.assertEqual(captured['pool'], self.pool_bytes(item, initial, boosted))
        expected = [self.create_event(item, base, quote, pool_base, pool_quote + boosted, initial, lp_out)]
        self.assertEqual(captured['events'][0][:len(expected[0])], expected[0])
        self.assertEqual(len(captured['events']), 2 + int(boosted > 0))
        tail = [e for e in captured['events'][1:] if e[:8] == BOOST_EVENT]
        self.assertEqual(len(tail), int(boosted > 0))
        migrated = [e for e in captured['events'] if e[:8] == MIGRATION_EVENT]
        self.assertEqual(len(migrated), 1)
        self.assertEqual(migrated[0][:72], MIGRATION_EVENT + bytes(USER.pubkey()) + bytes(MINT))
        self.assertEqual(struct.unpack_from('<QQQ', migrated[0], 72), (base, quote, item['fee']))

    def pool_bytes(self, item, initial, boosted):
        keys = names(item)
        _, pool_bump = Pubkey.find_program_address(
            [b'pool', struct.pack('<H', 0), bytes(AUTHORITY), bytes(MINT), bytes(keys['quote_mint'])], PUMP_AMM)
        # The Pool account stores its canonical bump at byte 8. Reading that
        # byte back from the account made the expectation agree with whatever
        # the program wrote, so a non-canonical bump went unnoticed.
        return (POOL_DISC + bytes([pool_bump]) + struct.pack('<H', 0) + bytes(AUTHORITY) + bytes(MINT) + bytes(keys['quote_mint'])
                + bytes(keys['lp_mint']) + bytes(keys['pool_base_token_account']) + bytes(keys['pool_quote_token_account'])
                + struct.pack('<Q', initial) + bytes(CREATOR) + bytes([item['mayhem'], item['cashback']])
                + boosted.to_bytes(16, 'little') + struct.pack('<QBB', item['cfb'], item['can_edit'], item['holder'])
                + bytes(16))

    def create_event(self, item, base, quote, pool_base, pool_quote, initial, lp_out):
        keys = names(item)
        return (CREATE_POOL_EVENT + struct.pack('<qH', TS, 0) + bytes(AUTHORITY) + bytes(MINT) + bytes(keys['quote_mint'])
                + struct.pack('<BBQQQQQQQ', 6, 9 if item['quote'] == 'sol' else 6, base, quote, pool_base, pool_quote, 100,
                              initial, lp_out))

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), t22=item['t22'], host=answer):
                self.assert_matches(item, answer, self.bench.run(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_changed_pool(self):
        # Negative control: a passing boosted run must fail once the pool, the
        # refund or the boost amount moves.
        item = case(boost=1, remaining=2)
        answer = self.host_answers([item])[0]
        captured = self.bench.run(item)
        self.assert_matches(item, answer, captured)
        changed = [dict(captured, pool=captured['pool'][:-1] + b'\x01'), dict(captured, withdraw=captured['withdraw'] + 1),
                   dict(captured, vault=captured['vault'] - 1), dict(captured, events=captured['events'][1:])]
        for other in changed:
            with self.assertRaises(AssertionError):
                self.assert_matches(item, answer, other)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'error:-1', 'error:0', 'error:1', 'error:6001', 'error:6002', 'error:6003',
                                    'error:6006', 'error:6017', 'error:6024', 'error:6027', 'error:6041',
                                    'error:6049'})


if __name__ == '__main__':
    unittest.main()
