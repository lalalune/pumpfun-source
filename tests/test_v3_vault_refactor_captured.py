"""Regression harness for the `trade_v3` buy payment and curve-hop vault admission.

PR #1554 inlines `admit_vaults` in `multi_hop_curve_swap.rs` and splits the
`match` that picks the user quote payment in `trade_v3::v3_execute_buy`. This
file runs the same cases through:

* the captured `evidence/original/pump/deployed.so` (always),
* `programs/pump/recovered/v3_vault_refactor_host.rs`, a native model of the
  two paths (always), and
* any rebuilt Pump candidates listed in `PUMP_CANDIDATE_ELFS`
  (`os.pathsep`-separated). Without that variable the candidate test skips.

Cases cover `buy_v3` and `buy_exact_quote_in_v3` with SOL and SPL Token
quotes, buyback 0/50%/100%, fills that cross into the post-complete pool, the
`max_sol_cost` boundary, insufficient funds and wrong quote / buyback
accounts, plus single curve-hop routes through the captured Pump AMM
`multi_hop_swap` (the only signer of `multi_hop_curve_swap`) with correct,
wrong, missing, never-created and doubly wrong vaults. State is the captured
mainnet Pump Global and Pump AMM GlobalConfig with synthetic curves, mints and
fee configs.

For every case a candidate must give the captured program's error, the same
AnchorError source site, the same bytes, owner and signed lamport delta for
every non-executable account, and the same event and return-data log lines.
Compute units are not compared. Passing shows matching behaviour on these
inputs only; it is not a byte-identity claim.

Build a candidate with platform-tools v1.44 (the repo's pinned toolchain)
and `RUSTC_WRAPPER=scripts/pump_rustc_source_path_wrapper.sh`, so AnchorError
sites read `programs/pump/src/...` like the captured program:
    cargo build --release --target sbf-solana-solana --locked
in `programs/pump`, then run, for example,
    PUMP_CANDIDATE_ELFS=main.so:pr1554.so python -m unittest tests/test_v3_vault_refactor_captured.py
"""
from pathlib import Path
import base64
import hashlib
import json
import os
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
FEES_ELF = ROOT / 'evidence/original/pump_fees/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    AMM_ELF: '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7',
    FEES_ELF: '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/v3_vault_refactor_host.rs'


def fixture(name):
    row = json.loads((ROOT / 'tests/fixtures' / name).read_text())
    data = base64.b64decode(row['data_base64'])
    assert hashlib.sha256(data).hexdigest() == row['data_sha256'], name
    return row, data


GLOBAL_ROW, GLOBAL_BYTES = fixture('pump_global_slot_461019957.json')
AMM_CONFIG_ROW, AMM_CONFIG_BYTES = fixture('pump_amm_global_config_slot_461019958.json')

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
AMM_IDL = json.loads((ROOT / 'evidence/upstream/pump_amm.json').read_text())
IX = {ix['name']: ix for ix in IDL['instructions']}
MULTI_HOP = next(ix for ix in AMM_IDL['instructions'] if ix['name'] == 'multi_hop_swap')
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
EVENT_DISC = {e['name']: bytes(e['discriminator']) for e in IDL['events']}

PUMP = Pubkey.from_string(IDL['address'])
AMM = Pubkey.from_string(AMM_IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
GLOBAL = Pubkey.from_string(GLOBAL_ROW['address'])
AMM_CONFIG = Pubkey.from_string(AMM_CONFIG_ROW['address'])
EXECUTABLE = {PUMP, AMM, FEES, TOKEN, TOKEN22, ATA, SYSTEM}

USER = Keypair.from_seed(bytes([221]) * 32)
CREATOR = Pubkey.from_bytes(bytes([222]) * 32)
BASE = Pubkey.from_bytes(bytes([223]) * 32)
QUOTE = Pubkey.from_bytes(bytes([224]) * 32)
OTHER = Pubkey.from_bytes(bytes([225]) * 32)
STRAY = Pubkey.from_bytes(bytes([226]) * 32)
STRAY2 = Pubkey.from_bytes(bytes([227]) * 32)
BUYBACK = Pubkey.from_bytes(GLOBAL_BYTES[741:773])  # first Global buyback fee recipient

pda = lambda program, *seeds: Pubkey.find_program_address(list(seeds), program)[0]
ata = lambda owner, mint, program=TOKEN: pda(ATA, bytes(owner), bytes(program), bytes(mint))
CURVE = pda(PUMP, b'bonding-curve', bytes(BASE))
EVENT_AUTHORITY = pda(PUMP, b'__event_authority')
USER_VOLUME = pda(PUMP, b'user_volume_accumulator', bytes(USER.pubkey()))
FEE_CONFIG, FEE_BUMP = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], FEES)
AMM_FEE_CONFIG, AMM_FEE_BUMP = Pubkey.find_program_address([b'fee_config', bytes(AMM)], FEES)
AMM_EVENT_AUTHORITY = pda(AMM, b'__event_authority')
AMM_USER_VOLUME = pda(AMM, b'user_volume_accumulator', bytes(USER.pubkey()))

TX_FEE = 5_000
CURVE_TOKENS = 10**15            # base tokens in the curve vault, incl. the migration reserve
REAL_TOKENS = 793_100_000_000_000
VIRTUAL_TOKENS = 1_073_000_000_000_000
VIRTUAL_QUOTE = 30_000_000_000
U64 = 2**64 - 1


def mint(supply, decimals):
    return struct.pack('<I', 0) + bytes(32) + struct.pack('<Q', supply) + bytes([decimals, 1]) + struct.pack('<I', 0) + bytes(32)


def token(mint_key, owner, amount, native=None):
    is_native = struct.pack('<IQ', 1, native) if native is not None else struct.pack('<I', 0) + bytes(8)
    return (bytes(mint_key) + bytes(owner) + struct.pack('<Q', amount) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + is_native + struct.pack('<Q', 0) + struct.pack('<I', 0) + bytes(32))


def token_amount(row):
    return struct.unpack_from('<Q', row[1], 64)[0] if row and row[2] in (str(TOKEN), str(TOKEN22)) and len(row[1]) >= 72 else 0


def fee_config(bump, protocol_bps=95, creator_bps=30):
    tier = (0).to_bytes(16, 'little') + struct.pack('<QQQ', 0, protocol_bps, creator_bps)
    data = (ACCOUNT_DISC['FeeConfig'] + bytes([bump]) + bytes(32) + struct.pack('<QQQ', 0, protocol_bps, creator_bps)
            + struct.pack('<I', 1) + tier + struct.pack('<I', 1) + tier + struct.pack('<QQQ', 0, protocol_bps, creator_bps))
    return data.ljust(4104, b'\0')


def u64(data, offset):
    return struct.unpack_from('<Q', data, offset)[0]


def decode_trade(data):
    """Quote amounts of a TradeEvent: (quote_amount, fee, creator_fee, buyback_fee, token_amount)."""
    o = 8 + 32
    token_amount_ = u64(data, o + 8)
    o += 8 + 8 + 1 + 32 + 8 + 8 * 4 + 32 + 8
    fee = u64(data, o); o += 8 + 32 + 8
    creator_fee = u64(data, o); o += 8 + 1 + 8 * 4
    o += 4 + struct.unpack_from('<I', data, o)[0] + 1 + 8 + 8 + 8
    buyback = u64(data, o); o += 8
    o += 4 + 40 * struct.unpack_from('<I', data, o)[0] + 32
    return (u64(data, o), fee, creator_fee, buyback, token_amount_)


def decode_post(data):
    """PostCompleteBuyEvent: (quote_in, fee, creator_fee, buyback_fee, base_out)."""
    o = 8 + 32 * 4 + 8
    base_out, quote_in, _, fee, _, creator_fee, buyback = struct.unpack_from('<7Q', data, o)
    return (quote_in, fee, creator_fee, buyback, base_out)


def new_vm(pump_elf, amm=False):
    vm = LiteSVM().with_sigverify(True).with_transaction_history(0)
    vm.add_program_from_file(PUMP, pump_elf)
    vm.add_program_from_file(FEES, FEES_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(TOKEN22, TOKEN22_ELF)
    vm.add_program_from_file(ATA, ATA_ELF)
    if amm:
        vm.add_program_from_file(AMM, AMM_ELF)
    vm.set_clock(Clock(100, 1_700_000_000, 0, 0, 1_700_000_000))
    return vm


def common_state(vm, case):
    native = case['quote'] == 'sol'
    quote_mint = WSOL if native else QUOTE
    global_data = bytearray(GLOBAL_BYTES)
    struct.pack_into('<Q', global_data, 997, case.get('buyback', 5_000))
    global_data[1013:1045] = bytes(QUOTE)  # whitelisted quote mint
    vm.set_account(GLOBAL, Account(GLOBAL_ROW['lamports'], bytes(global_data), PUMP))
    vm.set_account(USER.pubkey(), Account(case.get('user_lamports', 10**13), b'', SYSTEM))
    vm.set_account(BASE, Account(10**9, mint(10**15, 6), TOKEN))
    vm.set_account(quote_mint, Account(10**9, mint(10**18, 9 if native else 6), TOKEN))
    curve = bytearray(166)
    curve[:8] = ACCOUNT_DISC['BondingCurve']
    real_quote = case.get('real_quote', 0)
    struct.pack_into('<5Q', curve, 8, VIRTUAL_TOKENS, VIRTUAL_QUOTE, REAL_TOKENS, real_quote, 10**15)
    curve[49:81] = bytes(CREATOR)
    curve[83:115] = bytes(SYSTEM if native else QUOTE)
    rent = vm.minimum_balance_for_rent_exemption(166)
    vm.set_account(CURVE, Account(rent + real_quote * native, bytes(curve), PUMP))
    vm.set_account(ata(CURVE, BASE), Account(2_039_280, token(BASE, CURVE, CURVE_TOKENS), TOKEN))
    if not native:
        vm.set_account(ata(CURVE, QUOTE), Account(2_039_280, token(QUOTE, CURVE, real_quote), TOKEN))
    vm.set_account(FEE_CONFIG, Account(10**9, fee_config(FEE_BUMP), FEES))
    return native, quote_mint


def execute(vm, program, data, metas):
    tx = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1_400_000), Instruction(program, data, metas)], USER.pubkey(), [USER], vm.latest_blockhash())
    keys = sorted({m.pubkey for m in metas} - EXECUTABLE, key=bytes)

    def snap():
        out = {}
        for key in keys:
            acct = vm.get_account(key)
            out[key] = None if acct is None else (acct.lamports, bytes(acct.data), str(acct.owner))
        return out

    before = snap()
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    logs = meta.logs()
    error = None
    if failed:
        text = str(result.err())
        code = re.search(r'Custom\((\d+)\)', text)
        error = int(code.group(1)) if code else text
    site = next((m.group(1) for line in logs for m in [re.search(r'AnchorError thrown in (\S+?)\. Error Code', line)] if m), None)
    after = snap()
    delta = {k: (after[k][0] if after[k] else 0) - (before[k][0] if before[k] else 0) for k in keys}
    return {
        'error': error, 'site': site, 'before': before, 'after': after, 'delta': delta,
        'events': [line for line in logs if line.startswith('Program data: ')],
        'returns': [line for line in logs if line.startswith('Program return: ')],
    }


def run_v3(pump_elf, case):
    vm = new_vm(pump_elf)
    native, quote_mint = common_state(vm, case)
    user = USER.pubkey()
    volume = bytearray(137)
    volume[:8] = ACCOUNT_DISC['UserVolumeAccumulator']
    volume[8:40] = bytes(user)
    vm.set_account(USER_VOLUME, Account(vm.minimum_balance_for_rent_exemption(137), bytes(volume), PUMP))
    vm.set_account(ata(user, BASE), Account(2_039_280, token(BASE, user, 0), TOKEN))
    if native:
        recipient = BUYBACK
    else:
        vm.set_account(ata(user, QUOTE), Account(2_039_280, token(QUOTE, user, case.get('user_quote', 10**15)), TOKEN))
        recipient = ata(BUYBACK, QUOTE)
        vm.set_account(recipient, Account(2_039_280, token(QUOTE, BUYBACK, 0), TOKEN))
    names = {
        'global': GLOBAL, 'base_mint': BASE, 'quote_mint': quote_mint, 'base_token_program': TOKEN,
        'quote_token_program': TOKEN, 'bonding_curve': CURVE, 'associated_base_bonding_curve': ata(CURVE, BASE),
        'associated_quote_bonding_curve': ata(CURVE, quote_mint), 'user': user, 'associated_base_user': ata(user, BASE),
        'associated_quote_user': ata(user, quote_mint), 'user_volume_accumulator': USER_VOLUME, 'fee_config': FEE_CONFIG,
        'buyback_fee_recipient': recipient, 'system_program': SYSTEM, 'event_authority': EVENT_AUTHORITY, 'program': PUMP,
    }
    names.update(case.get('names', {}))
    for key, acct in case.get('accounts', {}).items():
        vm.set_account(key, acct)
    ix = IX[case['ix']]
    metas = [AccountMeta(names[a['name']], a.get('signer', False), a.get('writable', False)) for a in ix['accounts']]
    data = bytes(ix['discriminator']) + struct.pack('<QQ', *case['args']) + bytes([case.get('partial', 0)])
    out = execute(vm, PUMP, data, metas)
    out['roles'] = {'user': user, 'curve': CURVE, 'recipient': recipient, 'user_quote': names['associated_quote_user'],
                    'curve_quote': names['associated_quote_bonding_curve'], 'user_base': ata(user, BASE)}
    return out


def run_hop(pump_elf, case):
    vm = new_vm(pump_elf, amm=True)
    native, quote_mint = common_state(vm, case)
    user = USER.pubkey()
    vm.set_account(AMM_CONFIG, Account(AMM_CONFIG_ROW['lamports'], AMM_CONFIG_BYTES, AMM))
    vm.set_account(AMM_FEE_CONFIG, Account(10**9, fee_config(AMM_FEE_BUMP), FEES))
    source, destination = ata(user, quote_mint), ata(user, BASE)
    vm.set_account(source, Account(2_039_280 + 10**12 * native, token(quote_mint, user, 10**12, 2_039_280 if native else None), TOKEN))
    vm.set_account(destination, Account(2_039_280, token(BASE, user, 0), TOKEN))
    recipient = ata(BUYBACK, quote_mint)
    vm.set_account(recipient, Account(2_039_280, token(quote_mint, BUYBACK, 0, 2_039_280 if native else None), TOKEN))
    hop = {'base': BASE, 'quote': quote_mint, 'curve': CURVE, 'curve_base': ata(CURVE, BASE), 'curve_quote': ata(CURVE, quote_mint)}
    hop.update(case.get('hop', {}))
    for key, acct in case.get('accounts', {}).items():
        vm.set_account(key, acct)
    keys = [user, source, destination, AMM_CONFIG, AMM_FEE_CONFIG, AMM_USER_VOLUME, recipient, TOKEN, TOKEN22, SYSTEM,
            AMM_EVENT_AUTHORITY, AMM, PUMP, GLOBAL, FEE_CONFIG, EVENT_AUTHORITY]
    metas = [AccountMeta(k, bool(a.get('signer')), bool(a.get('writable'))) for k, a in zip(keys, MULTI_HOP['accounts'])]
    metas += [AccountMeta(hop['base'], False, False), AccountMeta(hop['quote'], False, False), AccountMeta(hop['curve'], False, True),
              AccountMeta(hop['curve_base'], False, True), AccountMeta(hop['curve_quote'], False, True)]
    data = bytes(MULTI_HOP['discriminator']) + struct.pack('<QQ', case.get('amount', 10**9), 1)
    return execute(vm, AMM, data, metas)


def run_case(pump_elf, case):
    return (run_hop if case['kind'] == 'hop' else run_v3)(pump_elf, case)


def vault(mint_key, owner, amount=0):
    return Account(2_039_280, token(mint_key, owner, amount), TOKEN)


def v3_cases():
    cases = []
    add = lambda label, **k: cases.append(dict(kind='v3', label=label, **k))
    for quote in ('sol', 'token'):
        for buyback in (0, 5_000, 10_000):
            add(f'{quote}-buy-small-bb{buyback}', quote=quote, ix='buy_v3', args=(10**9, 10**15), buyback=buyback)
            add(f'{quote}-exact-in-bb{buyback}', quote=quote, ix='buy_exact_quote_in_v3', args=(10**9, 1), buyback=buyback)
            # Crossing the curve end adds a post-complete fill and its buyback.
            add(f'{quote}-buy-cross-bb{buyback}', quote=quote, ix='buy_v3', args=(800 * 10**12, 10**15), buyback=buyback)
            add(f'{quote}-exact-in-cross-bb{buyback}', quote=quote, ix='buy_exact_quote_in_v3', args=(10**11, 1), buyback=buyback)
        add(f'{quote}-buy-all-real', quote=quote, ix='buy_v3', args=(REAL_TOKENS, 10**15))
        add(f'{quote}-buy-real-quote', quote=quote, ix='buy_v3', args=(10**12, 10**15), real_quote=5 * 10**9)
        add(f'{quote}-buy-partial', quote=quote, ix='buy_v3', args=(10**9, 10**15), partial=1)
        # max_sol_cost compares against pool_quote + total_buyback, the SOL path's payment.
        add(f'{quote}-max-cost-exact', quote=quote, ix='buy_v3', args=(10**9, 28_310))
        add(f'{quote}-max-cost-short', quote=quote, ix='buy_v3', args=(10**9, 28_309))
        add(f'{quote}-cross-max-cost-short', quote=quote, ix='buy_v3', args=(800 * 10**12, 1))
        add(f'{quote}-zero', quote=quote, ix='buy_v3', args=(0, 10**15))
        add(f'{quote}-too-many', quote=quote, ix='buy_v3', args=(10**16, 10**15))
    add('sol-user-short', quote='sol', ix='buy_v3', args=(10**12, 10**15), user_lamports=10**7)
    add('sol-recipient-unlisted', quote='sol', ix='buy_v3', args=(10**9, 10**15), names={'buyback_fee_recipient': OTHER})
    add('token-user-short', quote='token', ix='buy_v3', args=(10**12, 10**15), user_quote=10**6)
    add('token-user-quote-wrong-owner', quote='token', ix='buy_v3', args=(10**9, 10**15),
        names={'associated_quote_user': STRAY}, accounts={STRAY: vault(QUOTE, OTHER, 10**15)})
    add('token-user-quote-wrong-mint', quote='token', ix='buy_v3', args=(10**9, 10**15),
        names={'associated_quote_user': STRAY}, accounts={STRAY: vault(BASE, USER.pubkey(), 10**15)})
    add('token-curve-quote-missing', quote='token', ix='buy_v3', args=(10**9, 10**15), accounts={ata(CURVE, QUOTE): Account(0, b'', SYSTEM)})
    add('token-recipient-unlisted-owner', quote='token', ix='buy_v3', args=(10**9, 10**15),
        names={'buyback_fee_recipient': ata(OTHER, QUOTE)}, accounts={ata(OTHER, QUOTE): vault(QUOTE, OTHER)})
    add('token-recipient-not-ata', quote='token', ix='buy_v3', args=(10**9, 10**15),
        names={'buyback_fee_recipient': STRAY}, accounts={STRAY: vault(QUOTE, BUYBACK)})
    add('token-recipient-wrong-mint', quote='token', ix='buy_v3', args=(10**9, 10**15),
        names={'buyback_fee_recipient': STRAY}, accounts={STRAY: vault(BASE, BUYBACK)})
    return cases


def hop_cases():
    cases = []
    add = lambda label, base_ok, quote_ok, **k: cases.append(dict(kind='hop', label=label, base_ok=base_ok, quote_ok=quote_ok, **k))
    for quote, quote_mint in (('sol', WSOL), ('token', QUOTE)):
        stray_base = {STRAY: vault(BASE, CURVE, CURVE_TOKENS)}
        add(f'{quote}-ok', True, True, quote=quote)
        add(f'{quote}-ok-bb0', True, True, quote=quote, buyback=0)
        add(f'{quote}-ok-cross', True, True, quote=quote, amount=10**11)
        add(f'{quote}-base-not-ata', False, True, quote=quote, hop={'curve_base': STRAY}, accounts=stray_base)
        add(f'{quote}-base-other-curve-ata', False, True, quote=quote, hop={'curve_base': ata(OTHER, BASE)},
            accounts={ata(OTHER, BASE): vault(BASE, OTHER, CURVE_TOKENS)})
        add(f'{quote}-quote-not-ata', True, False, quote=quote, hop={'curve_quote': STRAY2}, accounts={STRAY2: vault(quote_mint, CURVE)})
        add(f'{quote}-quote-missing', True, False, quote=quote, hop={'curve_quote': STRAY2})
        add(f'{quote}-quote-token22-address', True, False, quote=quote, hop={'curve_quote': ata(CURVE, quote_mint, TOKEN22)})
        add(f'{quote}-both-wrong', False, False, quote=quote, hop={'curve_base': STRAY, 'curve_quote': STRAY2},
            accounts={**stray_base, STRAY2: vault(quote_mint, CURVE)})
        # quote_ok=2: the right vault address, never created. Creation is off
        # for the hop, so a token quote stops here; a native one passes.
        absent = {ata(CURVE, quote_mint): Account(0, b'', SYSTEM)}
        add(f'{quote}-quote-ata-absent', True, 2, quote=quote, accounts=absent)
        add(f'{quote}-base-wrong-quote-absent', False, 2, quote=quote, hop={'curve_base': STRAY}, accounts={**stray_base, **absent})
    return cases


def random_cases(count, seed):
    rng = random.Random(seed)
    cases = []
    for i in range(count):
        quote = rng.choice(('sol', 'token'))
        buyback = rng.choice((0, 1, 3_333, 5_000, 9_999, 10_000, rng.randrange(10_001)))
        if rng.random() < 0.5:
            amount = rng.choice((1, rng.randrange(1, 10**12), rng.randrange(10**12, REAL_TOKENS), rng.randrange(REAL_TOKENS, 10**15)))
            case = dict(ix='buy_v3', args=(amount, rng.choice((10**15, rng.randrange(1, 10**11)))))
        else:
            case = dict(ix='buy_exact_quote_in_v3', args=(rng.choice((1, rng.randrange(1, 10**9), rng.randrange(10**9, 2 * 10**11))), 1))
        cases.append(dict(kind='v3', label=f'random-{i}', quote=quote, buyback=buyback, partial=rng.randrange(2),
                          real_quote=rng.choice((0, rng.randrange(10**10))), **case))
    return cases


class Host:
    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.binary = Path(self.tmp.name) / 'v3-vault-refactor-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(self.binary)], check=True)

    def ask(self, lines):
        out = subprocess.run([str(self.binary)], input=''.join(l + '\n' for l in lines), capture_output=True, text=True, check=True)
        return out.stdout.splitlines()


def model_line(case, run):
    if case['kind'] == 'hop':
        return f"admit,{int(case['quote'] == 'sol')},{int(case['base_ok'])},{int(case['quote_ok'])}"
    trades = [decode_trade(base64.b64decode(e[14:])) for e in run['events'] if base64.b64decode(e[14:])[:8] == EVENT_DISC['TradeEvent']]
    posts = [decode_post(base64.b64decode(e[14:])) for e in run['events'] if base64.b64decode(e[14:])[:8] == EVENT_DISC['PostCompleteBuyEvent']]
    assert len(trades) == 1 and len(posts) <= 1, case['label']
    fills = [trades[0][:4]] + [p[:4] for p in posts]
    return 'pay,' + ','.join(str(v) for fill in fills for v in fill)


class V3VaultRefactorCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.host = Host()
        cls.cases = v3_cases() + hop_cases() + random_cases(60, 1554)
        cls.captured = [run_case(PUMP_ELF, case) for case in cls.cases]

    @classmethod
    def tearDownClass(cls):
        cls.host.tmp.cleanup()

    def check_model(self, case, run, answer):
        """The captured outcome must match the model's answer for this case."""
        label = case['label']
        if case['kind'] == 'hop':
            if answer == 'ok':
                self.assertIsNone(run['error'], label)
            else:
                _, code, site = answer.split(',')
                self.assertEqual((run['error'], run['site']), (int(code), site), label)
                self.assertEqual(run['events'], [], label)
            return
        if run['error'] is not None:
            return  # rejections are pinned by the candidate comparison, not the model
        status, user_out, curve_in, recipient_in = answer.split(',')
        self.assertEqual(status, 'ok', label)
        user_out, curve_in, recipient_in = int(user_out), int(curve_in), int(recipient_in)
        r, d = run['roles'], run['delta']
        trade = decode_trade(base64.b64decode(next(e for e in run['events'] if base64.b64decode(e[14:])[:8] == EVENT_DISC['TradeEvent'])[14:]))
        posts = [decode_post(base64.b64decode(e[14:])) for e in run['events'] if base64.b64decode(e[14:])[:8] == EVENT_DISC['PostCompleteBuyEvent']]
        tokens = lambda key: token_amount(run['after'][key]) - token_amount(run['before'][key])
        self.assertEqual(tokens(r['user_base']), trade[4] + sum(p[4] for p in posts), label)
        if case['quote'] == 'sol':
            self.assertEqual(d[r['user']], -user_out - TX_FEE, label)
            self.assertEqual(d[r['curve']], curve_in, label)
            self.assertEqual(d[r['recipient']], recipient_in, label)
        else:
            self.assertEqual(d[r['user']], -TX_FEE, label)
            self.assertEqual(d[r['curve']], 0, label)
            self.assertEqual(tokens(r['user_quote']), -user_out, label)
            self.assertEqual(tokens(r['curve_quote']), curve_in, label)
            self.assertEqual(tokens(r['recipient']), recipient_in, label)
        moved = {r['user'], r['curve'], r['recipient']}
        self.assertTrue(all(v == 0 for k, v in d.items() if k not in moved), label)

    def answers(self, runs):
        lines = [model_line(c, r) if c['kind'] == 'hop' or r['error'] is None else 'admit,0,1,1' for c, r in zip(self.cases, runs)]
        return self.host.ask(lines)

    def test_captured_matches_model(self):
        answers = self.answers(self.captured)
        for case, run, answer in zip(self.cases, self.captured, answers):
            with self.subTest(case=case['label']):
                self.check_model(case, run, answer)
        outcomes = {(c['kind'], c['quote'], 'ok' if r['error'] is None else r['error']) for c, r in zip(self.cases, self.captured)}
        needed = {('v3', q, e) for q in ('sol', 'token') for e in ('ok', 1, 6002, 6020, 6021, 6057)}
        needed |= {('v3', 'token', e) for e in (2006, 3012, 6004, 6010)}
        needed |= {('hop', q, e) for q in ('sol', 'token') for e in ('ok', 2006)} | {('hop', 'token', 3012)}
        self.assertLessEqual(needed, outcomes)
        sites = {r['site'] for c, r in zip(self.cases, self.captured) if c['kind'] == 'hop' and r['error']}
        self.assertEqual(sites, {'programs/pump/src/multi_hop_curve_swap.rs:369', 'programs/pump/src/buy_v2.rs:55',
                                 'programs/pump/src/buy_v2.rs:60'})
        crossed = [c['label'] for c, r in zip(self.cases, self.captured)
                   if c['kind'] == 'v3' and any(base64.b64decode(e[14:])[:8] == EVENT_DISC['PostCompleteBuyEvent'] for e in r['events'])]
        self.assertGreaterEqual(len(crossed), 8)

    def outcome(self, run):
        return {k: run[k] for k in ('error', 'site', 'after', 'delta', 'events', 'returns')}

    def assert_same(self, label, expected, got):
        e, g = self.outcome(expected), self.outcome(got)
        for key in e:
            self.assertEqual(g[key], e[key], f'{label}: {key}')

    def test_candidates_match_captured(self):
        raw = os.environ.get('PUMP_CANDIDATE_ELFS', '')
        candidates = [Path(p).resolve() for p in raw.split(os.pathsep) if p]
        if not candidates:
            self.skipTest('set PUMP_CANDIDATE_ELFS to rebuilt pump_recovered.so paths')
        for elf in candidates:
            for case, expected in zip(self.cases, self.captured):
                with self.subTest(candidate=elf.name, case=case['label']):
                    self.assert_same(f"{elf}:{case['label']}", expected, run_case(elf, case))

    def test_checker_rejects_tampered_outcomes(self):
        """Negative control: the same checks must fail on altered results."""
        answers = self.answers(self.captured)
        index = {c['label']: i for i, c in enumerate(self.cases)}
        tampered = 0
        for label, change in [
            ('sol-buy-small-bb5000', lambda r: r['delta'].__setitem__(r['roles']['recipient'], r['delta'][r['roles']['recipient']] + 1)),
            ('sol-buy-cross-bb5000', lambda r: r['delta'].__setitem__(r['roles']['curve'], r['delta'][r['roles']['curve']] - 1)),
            ('token-buy-small-bb5000', lambda r: r['delta'].__setitem__(r['roles']['user'], r['delta'][r['roles']['user']] - 1)),
            ('token-both-wrong', lambda r: r.__setitem__('site', 'programs/pump/src/buy_v2.rs:55')),
            ('sol-quote-missing', lambda r: r.__setitem__('error', None)),
        ]:
            i = index[label]
            run = dict(self.captured[i], delta=dict(self.captured[i]['delta']))
            change(run)
            with self.assertRaises(AssertionError, msg=label):
                self.check_model(self.cases[i], run, answers[i])
            tampered += 1
        # The candidate comparison must notice a single-byte or single-lamport change.
        i = index['token-buy-cross-bb5000']
        run = self.captured[i]
        key = run['roles']['curve_quote']
        lamports, data, owner = run['after'][key]
        changed = dict(run, after={**run['after'], key: (lamports, data[:64] + bytes([data[64] ^ 1]) + data[65:], owner)})
        with self.assertRaises(AssertionError):
            self.assert_same('tampered-bytes', run, changed)
        changed = dict(run, delta={**run['delta'], key: run['delta'][key] + 1})
        with self.assertRaises(AssertionError):
            self.assert_same('tampered-delta', run, changed)
        changed = dict(run, events=run['events'][:-1])
        with self.assertRaises(AssertionError):
            self.assert_same('tampered-events', run, changed)
        self.assertEqual(tampered, 5)


if __name__ == '__main__':
    unittest.main()
