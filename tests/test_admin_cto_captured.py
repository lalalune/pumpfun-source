"""Captured-program checks for the recovered Pump `admin_cto` model.

Every case runs `admin_cto` from `evidence/original/pump/deployed.so` on LiteSVM,
with the captured Pump Fees and PumpSwap programs loaded for the two conditional
CPIs. The same inputs go to `programs/pump/recovered/admin_cto_host.rs`. The
error, or on success the curve bytes, the AdminCtoEvent, and the lamports added
to the curve, must agree. This is behaviour on these inputs, not a byte-identity
claim.

Nonzero creator-vault sweeps and a sharing-config body the fees program rejects
are not generated here.
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
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey
from solders.litesvm import LiteSVM
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from fees_donation_create_differential import (  # noqa: E402
    AMM, AUTH, CURVE, EVENT as FEES_EVENT, MINT, OTHER, PAYER, POOL_AUTH, PROGRAM, PUMP, QUOTE, SHARING)
import pump_amm_admin_differential as amm  # noqa: E402
import pump_validate_admin as pump  # noqa: E402

PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    ROOT / 'evidence/original/pump_amm/deployed.so': '6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7',
    ROOT / 'evidence/original/pump_fees/deployed.so': '4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e',
    ROOT / 'evidence/dependencies/spl_token/deployed.so': '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    ROOT / 'evidence/dependencies/spl_token_2022/deployed.so': '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ROOT / 'evidence/dependencies/associated_token/deployed.so': '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/admin_cto_host.rs'
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN_2022 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
WRONG = Pubkey.from_bytes(bytes([9]) * 32)
CUSTOM = Pubkey.from_bytes(bytes([88]) * 32)
CURVE_DISC = hashlib.sha256(b'account:BondingCurve').digest()[:8]
EVENT_DISC = bytes([110, 124, 226, 98, 170, 255, 17, 120])
IX = next(item for item in pump.IDL['instructions'] if item['name'] == 'admin_cto')
TIMESTAMP = 1_700_000_000
U64_MAX = 2**64 - 1


def pda(seeds, program):
    return Pubkey.find_program_address(list(seeds), program)[0]


def ata_of(owner, token_program, quote):
    return pda([bytes(owner), bytes(token_program), bytes(quote)], ATA)


HOLDER = pda([b'holder-rewards', bytes(MINT)], PUMP)


def u64(value):
    return struct.pack('<Q', value)


def default_case(**changes):
    item = dict(
        holder=None, fee=None, new=OTHER.pubkey(), new_none=False, raw=None, trailing='',
        curve_len=200, creator=PUMP, mayhem=0, cashback=0, holder_flag=0, can_edit=0,
        quote_field=None, fee_bps=0, creator_fee=0, protocol_fee=0, real_quote=0,
        curve_lamports=10**9, admin_lamports=10**12, global_len=1088, global_patches=(),
        global_bool=None, global_disc=False, quote=QUOTE, token_program=TOKEN,
        sharing_len=1024, sharing_owner=PROGRAM, pool='canonical', fault=None,
        present=26, unsigned=False, readonly=(), current_writable=False, quote_owner=None)
    item.update(changes)
    return item


def payload_of(case):
    if case['raw'] is not None:
        return case['raw']
    if case['holder'] is None:
        holder = b'\x00'
    else:
        holder = bytes([1, int(case['holder'])])
    fee = b'\x00' if case['fee'] is None else b'\x01' + u64(case['fee'])
    new = b'\x00' if case['new_none'] else b'\x01' + bytes(case['new'])
    return holder + fee + new + bytes.fromhex(case['trailing'])


def curve_bytes(case):
    length = case['curve_len']
    raw = bytearray(max(length, 8))
    raw[:8] = CURVE_DISC
    if case.get('curve_disc'):
        raw[0] ^= 0xFF
    if length > 32:
        raw[32:40] = u64(case['real_quote'])
    creator = bytes(case['creator'])
    raw[49:49 + min(32, max(0, length - 49))] = creator[:max(0, length - 49)]
    def put(at, value):
        if at < length:
            raw[at] = value
    put(81, case['mayhem'])
    put(82, case['cashback'])
    if case['quote_field'] is not None:
        field = bytes(case['quote_field'])
        raw[83:83 + min(32, max(0, length - 83))] = field[:max(0, length - 83)]
    if length > 115:
        raw[115:min(123, length)] = u64(case['fee_bps'])[:max(0, min(123, length) - 115)]
    put(123, case['can_edit'])
    put(124, case['holder_flag'])
    if length > 125:
        raw[125:min(133, length)] = u64(case['creator_fee'])[:max(0, min(133, length) - 125)]
    if length > 133:
        raw[133:min(141, length)] = u64(case['protocol_fee'])[:max(0, min(141, length) - 133)]
    return bytes(raw[:length])


def global_bytes(case):
    raw = bytearray(pump.DATA)
    raw[418:450] = bytes(AUTH.pubkey())
    for offset, value in case['global_patches']:
        raw[offset:offset + len(value)] = value
    if case['global_bool'] is not None and case['global_bool'] < len(raw):
        raw[case['global_bool']] = 2
    if case['global_disc'] and len(raw) >= 1:
        raw[0] ^= 0xFF
    return bytes(raw[:case['global_len']])


def classify(err):
    if err is None:
        return None
    text = str(err)
    found = re.search(r'Custom\((\d+)\)', text)
    if found:
        return f'error:{int(found.group(1))}'
    if 'InvalidAccountData' in text:
        return 'error:InvalidAccountData'
    if 'BorshIo' in text:
        return 'error:BorshIoError'
    if 'MissingAccount' in text:
        return 'error:MissingAccount'
    return f'error:UNPARSED:{text}'


def assemble(case):
    """Build the accounts, run the captured program, and return the host line plus its answer."""
    quote = case['quote']
    token_program = case['token_program']
    current = case['creator']
    if case['fault'] == 'creator_mismatch':
        current = WRONG
    curve = curve_bytes(case)
    glob = global_bytes(case)
    body = payload_of(case)
    holder_vault = pda([b'creator-vault', bytes(HOLDER)], PUMP)
    if case['fault'] == 'holder_vault_dest':
        holder_vault = WRONG
    pool_auth = pda([b'pool-authority', bytes(MINT)], PUMP)
    pool, pool_bump = Pubkey.find_program_address(
        [b'pool', (0).to_bytes(2, 'little'), bytes(pool_auth), bytes(MINT), bytes(quote)], AMM)
    names = {
        'admin_set_creator_authority': AUTH.pubkey(),
        'global': pump.GLOBAL,
        'mint': MINT,
        'quote_mint': quote,
        'quote_token_program': token_program,
        'associated_token_program': ATA,
        'system_program': SYSTEM,
        'bonding_curve': CURVE,
        'current_creator': current,
        'current_creator_quote_token_account': ata_of(current, token_program, quote),
        'creator_vault': pda([b'creator-vault', bytes(current)], PUMP),
        'creator_vault_quote_token_account': ata_of(pda([b'creator-vault', bytes(current)], PUMP), token_program, quote),
        'holder_creator_vault': holder_vault,
        'holder_creator_vault_quote_token_account': ata_of(holder_vault, token_program, quote),
        'pump_amm': AMM,
        'amm_global_config': amm.CONFIG_KEY,
        'pool_authority': pool_auth,
        'pool': pool,
        'pump_amm_event_authority': amm.EVENT,
        'coin_creator_vault_authority': pda([b'creator_vault', bytes(current)], AMM),
        'coin_creator_vault_ata': ata_of(pda([b'creator_vault', bytes(current)], AMM), token_program, quote),
        'sharing_config': SHARING,
        'pump_fees': PROGRAM,
        'pump_fees_event_authority': FEES_EVENT,
        'event_authority': pump.EVENT,
        'program': PUMP,
    }
    fault = case['fault']
    replacements = {
        'quote_owner': 'quote_mint', 'token_program': 'quote_token_program', 'ata_program': 'associated_token_program',
        'system': 'system_program', 'curve_owner': 'bonding_curve', 'creator_ata': 'current_creator_quote_token_account',
        'vault': 'creator_vault', 'holder_ata': 'holder_creator_vault_quote_token_account', 'amm': 'pump_amm',
        'amm_config': 'amm_global_config', 'pool_auth': 'pool_authority', 'pool_seeds': 'pool', 'amm_event': 'pump_amm_event_authority',
        'coin_auth': 'coin_creator_vault_authority', 'sharing_seeds': 'sharing_config', 'fees': 'pump_fees',
        'fees_event': 'pump_fees_event_authority', 'event': 'event_authority', 'program': 'program',
    }
    if fault in replacements:
        names[replacements[fault]] = WRONG
    if fault == 'global_seeds':
        names['global'] = WRONG
    if fault in ('curve_seeds', 'seeds_and_readonly'):
        names['bonding_curve'] = WRONG
    readonly = set(case['readonly'])
    if fault == 'admin_readonly':
        readonly.add('admin_set_creator_authority')
    if fault == 'curve_readonly':
        readonly.add('bonding_curve')
    if fault == 'vault_readonly':
        readonly.add('creator_vault')
    if fault == 'holder_vault_readonly':
        readonly.add('holder_creator_vault')
    if fault == 'pool_readonly':
        readonly.add('pool')
    if fault == 'seeds_and_readonly':
        readonly.add('bonding_curve')
    present = case['present']
    if fault == 'missing_program':
        present = 25
    unsigned = case['unsigned'] or fault == 'unsigned'
    metas = []
    for index, account in enumerate(IX['accounts']):
        if index >= present:
            break
        key = names[account['name']]
        signer = account.get('signer', False) and not unsigned
        writable = account.get('writable', False) and account['name'] not in readonly
        if account['name'] == 'current_creator' and case['current_writable']:
            writable = True
        metas.append(AccountMeta(key, signer, writable))

    vm = LiteSVM().with_transaction_history(0)
    vm.set_clock(Clock(1000, TIMESTAMP, 0, 0, TIMESTAMP))
    for name, key, path in (
            ('pump', PUMP, PUMP_ELF),
            ('pump_amm', AMM, ROOT / 'evidence/original/pump_amm/deployed.so'),
            ('pump_fees', PROGRAM, ROOT / 'evidence/original/pump_fees/deployed.so'),
            ('spl_token', TOKEN, ROOT / 'evidence/dependencies/spl_token/deployed.so'),
            ('spl_token_2022', TOKEN_2022, ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'),
            ('associated_token', ATA, ROOT / 'evidence/dependencies/associated_token/deployed.so')):
        vm.add_program_from_file(key, path)
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(AUTH.pubkey(), Account(case['admin_lamports'], b'', SYSTEM))
    vm.set_account(OTHER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(WRONG, Account(10**9, b'', SYSTEM))
    global_owner = SYSTEM if fault == 'global_owner' else PUMP
    vm.set_account(names['global'], Account(10**9, glob, global_owner))
    curve_owner = SYSTEM if fault == 'curve_owner' else PUMP
    vm.set_account(names['bonding_curve'], Account(case['curve_lamports'], curve, curve_owner))
    quote_owner = case['quote_owner'] or (SYSTEM if fault == 'quote_owner' else TOKEN)
    for mint in {MINT, quote}:
        mint_data = bytearray(82)
        mint_data[44] = 9
        mint_data[45] = 1
        owner = quote_owner if mint == quote else TOKEN
        vm.set_account(mint, Account(10**9, bytes(mint_data), owner))
    sharing_bump = Pubkey.find_program_address([b'sharing-config', bytes(MINT)], PROGRAM)[1]
    sharing = bytearray(hashlib.sha256(b'account:SharingConfig').digest()[:8])
    sharing += bytes([sharing_bump, 2, 1]) + bytes(MINT) + bytes(AUTH.pubkey()) + bytes([0])
    sharing += (1).to_bytes(4, 'little') + bytes(AUTH.pubkey()) + (10000).to_bytes(2, 'little')
    sharing = sharing.ljust(1024, b'\0')[:case['sharing_len']]
    sharing_owner = SYSTEM if fault == 'sharing_owner' else case['sharing_owner']
    vm.set_account(SHARING, Account(10**9, bytes(sharing), sharing_owner))
    vm.set_account(amm.CONFIG_KEY, Account(10**9, bytes(amm.RAW), AMM))
    if case['pool'] == 'canonical' and fault != 'pool_empty':
        pool_data = hashlib.sha256(b'account:Pool').digest()[:8] + bytes([pool_bump]) + (0).to_bytes(2, 'little')
        pool_data += bytes(pool_auth) + bytes(MINT) + bytes(quote) + bytes(96) + bytes(8) + bytes(SHARING) + bytes(2) + bytes(16)
        pool_owner = SYSTEM if fault == 'pool_system' or case['pool'] == 'system' else AMM
        vm.set_account(pool, Account(10**9, pool_data.ljust(301, b'\0'), pool_owner))
    else:
        vm.set_account(pool, Account(0, b'', SYSTEM))
    loaded = {PUMP, AMM, PROGRAM, TOKEN, TOKEN_2022, ATA, SYSTEM}
    for key in (
            names['current_creator'], names['creator_vault'], names['holder_creator_vault'],
            names['coin_creator_vault_authority'], names['current_creator_quote_token_account'],
            names['creator_vault_quote_token_account'], names['holder_creator_vault_quote_token_account'],
            names['coin_creator_vault_ata'], names['pool_authority']):
        if key in loaded:
            continue
        existing = vm.get_account(key)
        if existing is None or (existing.lamports == 0 and len(existing.data) == 0):
            vm.set_account(key, Account(0, b'', SYSTEM))
    # The creator account may be the sharing account, which was given real data above.
    if current == SHARING and fault == 'sharing_owner':
        pass

    def owned(key):
        account = vm.get_account(key)
        return account.owner if account is not None else SYSTEM

    def executable(key):
        account = vm.get_account(key)
        return bool(account and account.executable)

    def nonempty(key):
        account = vm.get_account(key)
        return bool(account and len(account.data) > 0)

    def marked(key, want_signer):
        return any(meta.pubkey == key and (meta.is_signer if want_signer else meta.is_writable) for meta in metas)

    mint_key = names['mint']
    quote_key = names['quote_mint']
    token_key = names['quote_token_program']
    current_key = names['current_creator']
    passed_pool_auth = names['pool_authority']
    expected_pool = pda([b'pool', (0).to_bytes(2, 'little'), bytes(passed_pool_auth), bytes(mint_key), bytes(quote_key)], AMM)
    flags = [
        marked(names['admin_set_creator_authority'], True),
        marked(names['admin_set_creator_authority'], False),
        owned(names['global']) == PUMP,
        names['global'] == pda([b'global'], PUMP),
        owned(quote_key) in (TOKEN, TOKEN_2022),
        token_key in (TOKEN, TOKEN_2022),
        owned(quote_key) == token_key,
        names['associated_token_program'] == ATA,
        names['system_program'] == SYSTEM,
        owned(names['bonding_curve']) == PUMP,
        names['bonding_curve'] == pda([b'bonding-curve', bytes(mint_key)], PUMP),
        marked(names['bonding_curve'], False),
        names['current_creator_quote_token_account'] == ata_of(current_key, token_key, quote_key),
        marked(names['current_creator_quote_token_account'], False),
        names['creator_vault'] == pda([b'creator-vault', bytes(current_key)], PUMP),
        marked(names['creator_vault'], False),
        names['creator_vault_quote_token_account'] == ata_of(names['creator_vault'], token_key, quote_key),
        marked(names['creator_vault_quote_token_account'], False),
        marked(names['holder_creator_vault'], False),
        names['holder_creator_vault'] == pda([b'creator-vault', bytes(HOLDER)], PUMP),
        names['holder_creator_vault_quote_token_account'] == ata_of(names['holder_creator_vault'], token_key, quote_key),
        marked(names['holder_creator_vault_quote_token_account'], False),
        names['pump_amm'] == AMM,
        names['amm_global_config'] == amm.CONFIG_KEY,
        names['pool_authority'] == pda([b'pool-authority', bytes(mint_key)], PUMP),
        names['pool'] == expected_pool,
        marked(names['pool'], False),
        names['pump_amm_event_authority'] == amm.EVENT,
        names['coin_creator_vault_authority'] == pda([b'creator_vault', bytes(current_key)], AMM),
        marked(names['coin_creator_vault_authority'], False),
        names['coin_creator_vault_ata'] == ata_of(names['coin_creator_vault_authority'], token_key, quote_key),
        marked(names['coin_creator_vault_ata'], False),
        names['sharing_config'] == pda([b'sharing-config', bytes(mint_key)], PROGRAM),
        marked(names['sharing_config'], False),
        names['pump_fees'] == PROGRAM,
        names['pump_fees_event_authority'] == FEES_EVENT,
        names['event_authority'] == pump.EVENT,
        any(meta.pubkey == PUMP for meta in metas),
        executable(current_key),
        owned(current_key) == SYSTEM,
        marked(current_key, False),
        owned(names['sharing_config']) == PROGRAM,
        nonempty(names['sharing_config']),
        owned(names['pool']) == AMM,
        nonempty(names['pool']),
    ]
    if len(flags) != 45:
        raise AssertionError(len(flags))
    line = ','.join([
        str(len(metas)),
        ''.join('1' if bit else '0' for bit in flags),
        body.hex(),
        curve.hex(),
        glob.hex(),
        bytes(names['admin_set_creator_authority']).hex(),
        bytes(quote_key).hex(),
        bytes(current_key).hex(),
        bytes(mint_key).hex(),
        bytes(names['bonding_curve']).hex(),
        bytes(names['sharing_config']).hex(),
        bytes(HOLDER).hex(),
        str(case['curve_lamports']),
        str(case['admin_lamports']),
        str(TIMESTAMP),
    ])
    signers = [PAYER]
    if any(meta.is_signer and meta.pubkey == AUTH.pubkey() for meta in metas):
        signers.append(AUTH)
    instruction = Instruction(PUMP, bytes(IX['discriminator']) + body, metas)
    transaction = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1_400_000), instruction], PAYER.pubkey(), signers, vm.latest_blockhash())
    before = vm.get_account(names['bonding_curve'])
    result = vm.send_transaction(transaction)
    if isinstance(result, FailedTransactionMetadata):
        return line, classify(result.err()), result.meta().logs()
    after = vm.get_account(names['bonding_curve'])
    events = [base64.b64decode(line[14:]) for line in result.logs() if line.startswith('Program data: ')]
    admin_events = [item for item in events if item[:8] == EVENT_DISC]
    if len(admin_events) != 1:
        return line, f'error:EVENT_COUNT:{len(admin_events)}', result.logs()
    rent = after.lamports - before.lamports
    answer = f'ok,{bytes(after.data).hex()},{admin_events[0].hex()},{rent}'
    return line, answer, result.logs()


def fixed_cases():
    cases = []
    add = cases.append
    add(default_case(name='success-exec', can_edit=1))
    add(default_case(name='success-zero', creator=SYSTEM))
    add(default_case(name='success-wallet', creator=OTHER.pubkey(), current_writable=True))
    add(default_case(name='success-shared', creator=SHARING))
    add(default_case(name='success-holder', creator=SHARING, holder=True, new_none=True, cashback=1, can_edit=1))
    add(default_case(name='success-fee', creator=SHARING, quote=CUSTOM, quote_field=CUSTOM, fee=1))
    add(default_case(name='success-fee-max', creator=SHARING, quote=CUSTOM, quote_field=CUSTOM, fee=300))
    add(default_case(name='success-grow', creator=SYSTEM, curve_len=124))
    add(default_case(name='success-rent', creator=SYSTEM, curve_len=124, curve_lamports=1))
    add(default_case(name='success-reserved', creator=PUMP, curve_len=166, protocol_fee=1_000_000, curve_lamports=3_046_239))
    add(default_case(name='success-no-pool', pool='empty'))
    add(default_case(name='success-pool-system', pool='system'))
    add(default_case(name='pool-data-other-owner', fault='pool_system'))
    add(default_case(name='success-sharing-empty', creator=SHARING, sharing_len=0))
    add(default_case(name='success-sharing-system-owner', creator=SHARING, fault='sharing_owner', current_writable=True))
    add(default_case(name='success-trailing', trailing='abcd'))
    add(default_case(name='success-holder-false', holder=False))
    add(default_case(name='success-holder-fee', creator=SYSTEM, holder=True, new_none=True, cashback=1, can_edit=1,
                      quote=CUSTOM, quote_field=CUSTOM, fee=10))
    add(default_case(name='decode-empty', raw=b''))
    add(default_case(name='decode-bad-tag', raw=b'\x02' + payload_of(default_case())[1:]))
    add(default_case(name='decode-short-fee', raw=b'\x00\x01' + b'\x01' * 7))
    add(default_case(name='decode-bool-2', raw=b'\x01\x02\x00\x00'))
    add(default_case(name='decode-before-accounts', raw=b'', present=0))
    add(default_case(name='no-accounts', present=0))
    add(default_case(name='unsigned', fault='unsigned'))
    add(default_case(name='unsigned-readonly', fault='unsigned', readonly=('admin_set_creator_authority',)))
    add(default_case(name='admin-readonly', fault='admin_readonly'))
    add(default_case(name='global-owner', fault='global_owner'))
    add(default_case(name='global-empty', global_len=0))
    add(default_case(name='global-7', global_len=7))
    add(default_case(name='global-bad-disc', global_len=8, global_disc=True))
    add(default_case(name='global-short', global_len=400))
    add(default_case(name='global-bool', global_bool=8))
    add(default_case(name='global-authority', global_patches=((418, bytes(WRONG)),)))
    add(default_case(name='global-seeds', fault='global_seeds'))
    add(default_case(name='authority-before-seeds', fault='global_seeds', global_patches=((418, bytes(WRONG)),)))
    add(default_case(name='disc-before-seeds', fault='global_seeds', global_disc=True))
    add(default_case(name='global-short-and-authority', global_len=400, global_patches=((418, bytes(WRONG)),)))
    add(default_case(name='quote-owner', fault='quote_owner'))
    add(default_case(name='quote-mismatch', quote_field=CUSTOM))
    add(default_case(name='token-program', fault='token_program'))
    add(default_case(name='token-program-mismatch', token_program=TOKEN_2022))
    add(default_case(name='ata-program', fault='ata_program'))
    add(default_case(name='system', fault='system'))
    add(default_case(name='curve-owner', fault='curve_owner'))
    add(default_case(name='curve-disc', curve_disc=True))
    add(default_case(name='curve-8', curve_len=8))
    add(default_case(name='curve-48', curve_len=48))
    add(default_case(name='curve-bool', mayhem=2))
    add(default_case(name='curve-seeds', fault='curve_seeds'))
    add(default_case(name='curve-readonly', fault='curve_readonly'))
    add(default_case(name='seeds-before-mut', fault='seeds_and_readonly'))
    add(default_case(name='creator-mismatch', fault='creator_mismatch'))
    add(default_case(name='creator-ata', fault='creator_ata'))
    add(default_case(name='vault', fault='vault'))
    add(default_case(name='vault-readonly', fault='vault_readonly'))
    add(default_case(name='holder-ata', fault='holder_ata'))
    add(default_case(name='holder-vault-readonly', fault='holder_vault_readonly'))
    add(default_case(name='amm', fault='amm'))
    add(default_case(name='amm-config', fault='amm_config'))
    add(default_case(name='pool-auth', fault='pool_auth'))
    add(default_case(name='pool-seeds', fault='pool_seeds'))
    add(default_case(name='pool-readonly', fault='pool_readonly'))
    add(default_case(name='amm-event', fault='amm_event'))
    add(default_case(name='fees', fault='fees'))
    add(default_case(name='event', fault='event'))
    add(default_case(name='program', fault='program', creator=SYSTEM))
    add(default_case(name='program-via-creator', fault='program'))
    add(default_case(name='program-after-mayhem', fault='program', creator=SYSTEM, mayhem=1))
    add(default_case(name='missing-token-program', present=4))
    add(default_case(name='missing-program', fault='missing_program'))
    add(default_case(name='mayhem', mayhem=1))
    add(default_case(name='mayhem-before-holder', mayhem=1, holder_flag=1))
    add(default_case(name='mayhem-before-unswept', mayhem=1, creator_fee=5))
    add(default_case(name='holder-immutable', holder_flag=1))
    add(default_case(name='holder-disabled', holder=True, new_none=True, global_patches=((1086, b'\x00'),)))
    add(default_case(name='holder-and-new', holder=True))
    add(default_case(name='new-required', new_none=True))
    add(default_case(name='new-zero', new=SYSTEM))
    add(default_case(name='new-sharing', new=SHARING))
    add(default_case(name='new-holder', new=HOLDER))
    add(default_case(name='fee-locked', fee=10))
    add(default_case(name='fee-wsol-field', fee=10, quote_field=QUOTE))
    add(default_case(name='fee-whitelist', fee=10))  # quote field filled in below
    add(default_case(name='fee-cashback', fee=10, quote=CUSTOM, quote_field=CUSTOM, cashback=1))
    add(default_case(name='fee-off', fee=10, quote=CUSTOM, quote_field=CUSTOM, global_patches=((1045, b'\x00'),)))
    add(default_case(name='fee-zero', fee=0, quote=CUSTOM, quote_field=CUSTOM))
    add(default_case(name='fee-over', fee=301, quote=CUSTOM, quote_field=CUSTOM))
    add(default_case(name='fee-locked-before-off', fee=10, global_patches=((1045, b'\x00'),)))
    add(default_case(name='unswept', creator_fee=5))
    add(default_case(name='unswept-before-writable', creator_fee=5, creator=OTHER.pubkey()))
    add(default_case(name='not-writable', creator=OTHER.pubkey()))
    add(default_case(name='overflow', creator_fee=U64_MAX, protocol_fee=1))
    add(default_case(name='mayhem-before-overflow', mayhem=1, creator_fee=U64_MAX, protocol_fee=1))
    add(default_case(name='overflow-real-quote', real_quote=U64_MAX, protocol_fee=1))
    add(default_case(name='rent-broke', creator=SYSTEM, curve_len=124, curve_lamports=1, admin_lamports=0))
    add(default_case(name='rent-before-unswept', creator_fee=5, curve_len=166, curve_lamports=1, admin_lamports=0))
    add(default_case(name='holder-vault-dest', creator=SHARING, holder=True, new_none=True, fault='holder_vault_dest'))
    add(default_case(name='holder-vault-not-swept', creator=SHARING, fault='holder_vault_dest'))
    add(default_case(name='disc-before-bool', curve_disc=True, mayhem=2))
    whitelist = bytes(pump.DATA)[1013:1045]
    for item in cases:
        if item['name'] == 'fee-whitelist':
            item['quote'] = Pubkey.from_bytes(whitelist)
            item['quote_field'] = Pubkey.from_bytes(whitelist)
    for item in cases:
        item.setdefault('name', item.get('fault') or 'case')
    return cases


def random_cases(count=48, seed=20261030):
    rng = random.Random(seed)
    cases = []
    for index in range(count):
        kind = rng.choice(('pump', 'zero', 'wallet', 'sharing'))
        creator = {'pump': PUMP, 'zero': SYSTEM, 'wallet': OTHER.pubkey(), 'sharing': SHARING}[kind]
        quote_custom = rng.random() < 0.4
        quote = CUSTOM if quote_custom else QUOTE
        fee = None if rng.random() < 0.5 else rng.choice((0, 1, 10, 300, 301, 10_000))
        holder = rng.choice((None, False, True))
        cases.append(default_case(
            name=f'random-{index}',
            creator=creator,
            current_writable=kind == 'wallet',
            holder=holder,
            new_none=holder is True or rng.random() < 0.15,
            new=rng.choice((OTHER.pubkey(), SYSTEM, SHARING, HOLDER, WRONG)),
            fee=fee,
            quote=quote,
            quote_field=quote if quote_custom else None,
            mayhem=rng.choice((0, 0, 0, 1)),
            cashback=rng.choice((0, 0, 1)),
            holder_flag=rng.choice((0, 0, 1)),
            can_edit=rng.choice((0, 1)),
            curve_len=rng.choice((81, 124, 166, 200, 210)),
            creator_fee=rng.choice((0, 0, 0, 1, 5)),
            protocol_fee=rng.choice((0, 0, 7)),
            real_quote=rng.choice((0, 0, 100)),
            curve_lamports=rng.choice((10**9, 10**9, 1, 3_000_000)),
            global_patches=() if rng.random() < 0.7 else ((1086, bytes([rng.choice((0, 1))])),),
        ))
    return cases


class AdminCtoCapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            actual = hashlib.sha256(path.read_bytes()).hexdigest()
            if actual != digest:
                raise AssertionError(f'{path} sha256 {actual}')
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'admin-cto-host'
        subprocess.run(
            ['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
            check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, lines):
        completed = subprocess.run(
            [str(self.host)], input=''.join(line + '\n' for line in lines),
            capture_output=True, text=True, check=True)
        return completed.stdout.splitlines()

    def run_cases(self, cases):
        prepared = []
        for case in cases:
            line, captured, logs = assemble(case)
            prepared.append((case['name'], line, captured, logs))
        answers = self.host_answers([item[1] for item in prepared])
        self.assertEqual(len(answers), len(prepared))
        for (name, line, captured, logs), answer in zip(prepared, answers):
            with self.subTest(name=name):
                self.assertEqual(answer, captured, '\n'.join(logs[-12:]))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        case = default_case(name='tamper', can_edit=1)
        line, captured, _logs = assemble(case)
        answer = self.host_answers([line])[0]
        self.assertEqual(answer, captured)
        kind, curve, event, rent = answer.split(',')
        self.assertEqual(kind, 'ok')
        flipped = bytearray.fromhex(curve)
        flipped[49] ^= 0xFF
        tampered_curve = f'ok,{bytes(flipped).hex()},{event},{rent}'
        tampered_event = f'ok,{curve},{event[:-2]}00,{rent}'
        tampered_rent = f'ok,{curve},{event},{int(rent) + 1}'
        for tampered in (tampered_curve, tampered_event, tampered_rent):
            self.assertNotEqual(tampered, captured)

    def test_fixed_cases_cover_every_outcome(self):
        prepared = [assemble(case) for case in fixed_cases()]
        answers = self.host_answers([item[0] for item in prepared])
        outcomes = set()
        for answer in answers:
            if answer.startswith('ok,'):
                outcomes.add('ok')
            else:
                outcomes.add(answer)
        expected = {
            'ok', 'error:102', 'error:1', 'error:2000', 'error:2006', 'error:2022', 'error:3001', 'error:3002',
            'error:3003', 'error:3005', 'error:3007', 'error:3008', 'error:3010', 'error:6000', 'error:6004',
            'error:6019', 'error:6024', 'error:6030', 'error:6077', 'error:6078', 'error:6080', 'error:6083',
            'error:6084', 'error:6088', 'error:6089', 'error:6090', 'error:6091', 'error:6092', 'error:6095',
            'error:InvalidAccountData', 'error:BorshIoError', 'error:MissingAccount',
        }
        self.assertEqual(outcomes, expected)


if __name__ == '__main__':
    unittest.main()
