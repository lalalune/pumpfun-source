"""Captured-program checks for the recovered Pump `create_v2`.

Every case runs Pump `create_v2` from the captured
`evidence/original/pump/deployed.so` on LiteSVM, with the captured SPL Token,
Token-2022, Associated Token and Mayhem programs, against a synthetic Global
built from the IDL layout. Mayhem's `global_params` is created by Mayhem's own
initializer. The same inputs go to `programs/pump/recovered/create_v2_host.rs`,
and the error, the whole new bonding curve, the Token-2022 mint and supply, the
curve's and Mayhem's token balances, the curve's quote ATA, and the CreateEvent
must agree. A rejected create must leave every account it named unchanged.
This shows matching behavior on these inputs only; it is not a byte-identity
claim.
"""
from pathlib import Path
import base64
import hashlib
import json
import random
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
MAYHEM_ELF = ROOT / 'evidence/original/mayhem/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
TOKEN22_ELF = ROOT / 'evidence/dependencies/spl_token_2022/deployed.so'
ATA_ELF = ROOT / 'evidence/dependencies/associated_token/deployed.so'
ELF_SHA256 = {
    PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
    MAYHEM_ELF: 'a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb',
    TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697',
    TOKEN22_ELF: '15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d',
    ATA_ELF: '6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d',
}
HOST_SOURCE = ROOT / 'programs/pump/recovered/create_v2_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text())
PUMP = Pubkey.from_string(IDL['address'])
CREATE_V2 = next(i for i in IDL['instructions'] if i['name'] == 'create_v2')
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}
CREATE_EVENT = bytes(next(e['discriminator'] for e in IDL['events'] if e['name'] == 'CreateEvent'))
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
MAYHEM = Pubkey.from_string('MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e')
NATIVE = Pubkey.from_string('So11111111111111111111111111111111111111112')
BLOCKED = Pubkey.from_string('9pan9bMn5HatX4EJdBwg9VgCa7Uz5HL8N1m5D3NdXejP')
SYSTEM = Pubkey.default()

USER = Keypair.from_seed(bytes([231]) * 32)
MINT = Keypair.from_seed(bytes([232]) * 32)
ADMIN = Keypair.from_seed(bytes([233]) * 32)
WHITELISTED = Pubkey.from_bytes(bytes([70]) * 32)
CONTROLLED = Pubkey.from_bytes(bytes([71]) * 32)
ROOT_QUOTE = Pubkey.from_bytes(bytes([72]) * 32)
CREATOR = Pubkey.from_bytes(bytes([60]) * 32)
STRANGER = Pubkey.from_bytes(bytes([200]) * 32)
TS = 1_800_000_000
U64 = 2**64 - 1
TX_FEE = 2 * 5_000  # payer and mint signatures
REJECTIONS = {'missing': 'MissingAccount', 'illegal_owner': 'IllegalOwner'}


def pda(*seeds, program=PUMP):
    return Pubkey.find_program_address(list(seeds), program)[0]


def ata(owner, program, mint):
    return pda(bytes(owner), bytes(program), bytes(mint), program=ATA)


GLOBAL = pda(b'global')
CURVE = pda(b'bonding-curve', bytes(MINT.pubkey()))
CURVE_ATA = ata(CURVE, TOKEN22, MINT.pubkey())
QUOTE_CONTROL = pda(b'quote-control')
SOL_VAULT = pda(b'sol-vault', program=MAYHEM)
MAYHEM_VAULT = ata(SOL_VAULT, TOKEN22, MINT.pubkey())
HOLDER_PDA = pda(b'holder-rewards', bytes(MINT.pubkey()))
ACCOUNTS = {
    'mint': MINT.pubkey(), 'mint_authority': pda(b'mint-authority'), 'bonding_curve': CURVE,
    'associated_bonding_curve': CURVE_ATA, 'global': GLOBAL, 'user': USER.pubkey(), 'system_program': SYSTEM,
    'token_program': TOKEN22, 'associated_token_program': ATA, 'mayhem_program_id': MAYHEM,
    'global_params': pda(b'global-params', program=MAYHEM), 'sol_vault': SOL_VAULT,
    'mayhem_state': pda(b'mayhem-state', bytes(MINT.pubkey()), program=MAYHEM), 'mayhem_token_vault': MAYHEM_VAULT,
    'event_authority': pda(b'__event_authority'), 'program': PUMP,
}
# Host fault letter -> account passed as a stranger (`g`, `B`, `U`, `R` change
# account state or flags instead).
WRONG = {'A': 'mint_authority', 'C': 'bonding_curve', 'T': 'associated_bonding_curve', 'P': 'token_program',
         'I': 'associated_token_program', 'Y': 'mayhem_program_id', 'Q': 'global_params', 'V': 'sol_vault',
         'S': 'mayhem_state', 'E': 'event_authority', 'X': 'system_program'}
# Account fault letters in the order the model checks them.
FAULT_ORDER = 'gBXPIUCTAYQVSE'

DEFAULT_CURVE = dict(depth=0, mayhem=0, complete=0, vt=10**15, vq=3 * 10**10, rt=8 * 10**14, rq=0, supply=10**15,
                     root='sol')
DEFAULTS = dict(faults='', name='Coin', symbol='CN', uri='https://x', creator_zero=0, mayhem=0, cashback=0, fee=0,
                holder=0, tail=None, create_v2=1, mayhem_on=1, holder_on=1, configurable=1, max_bps=300, max_depth=2,
                vtr=1_073_000_000_000_000, vsr=30_000_000_000, rtr=793_100_000_000_000, supply=10**15,
                ivqr=4_000_000_000, migration_fee=15_000_000, quote='none', reserves=5_555, program=TOKEN,
                owner_wrong=0, ata_wrong=0, ata_exists=0, params=1, curve=None, curve_flaw=None)


def case(**changes):
    unknown = set(changes) - set(DEFAULTS)
    assert not unknown, unknown
    return dict(DEFAULTS, **changes)


def quoted(**changes):
    return case(quote='curve', curve=dict(DEFAULT_CURVE, **changes))


def tail_bytes(item):
    if item['tail'] is not None:
        return item['tail']
    return bytes([item['cashback']]) + struct.pack('<Q', item['fee']) + bytes([item['holder']])


def host_quote(item):
    kind = item['quote']
    if kind == 'listed':
        return f"listed:{item['reserves']}"
    if kind in ('zero', 'native'):
        return 'native'
    if kind == 'short1':
        return 'short'
    if kind == 'curve':
        q = item['curve']
        if item['curve_flaw']:
            return 'curve_invalid'
        return (f"curve:{q['depth']}:{q['mayhem']}:{q['complete']}:{q['vt']}:{q['vq']}:{q['rt']}:{q['rq']}:"
                f"{q['supply']}:{q['root']}")
    return kind


def host_line(item):
    return ','.join(map(str, [
        item['faults'] or '-', item['mayhem'], tail_bytes(item).hex() or '-', item['creator_zero'],
        len(item['name'].encode()), len(item['symbol'].encode()), len(item['uri'].encode()), host_quote(item),
        item['owner_wrong'], item['ata_wrong'], item['ata_exists'], item['params'], item['create_v2'],
        item['mayhem_on'], item['holder_on'], item['configurable'], item['max_bps'], item['max_depth'], item['vtr'],
        item['vsr'], item['rtr'], item['supply'], item['ivqr'], item['migration_fee']]))


def global_data(item):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 2 if 'B' in item['faults'] else 1
    struct.pack_into('<QQQQQ', data, 73, item['vtr'], item['vsr'], item['rtr'], item['supply'], 95)
    struct.pack_into('<Q', data, 146, item['migration_fee'])
    data[450] = item['create_v2']
    data[515] = item['mayhem_on']
    struct.pack_into('<Q', data, 1005, item['ivqr'])
    data[1013:1045] = bytes(WHITELISTED)
    data[1045] = item['configurable']
    struct.pack_into('<Q', data, 1046, item['max_bps'])
    data[1086] = item['holder_on']
    data[1087] = item['max_depth']
    return bytes(data)


def string(text):
    raw = text.encode()
    return struct.pack('<I', len(raw)) + raw


def mint_data():
    return struct.pack('<I', 1) + bytes(USER.pubkey()) + struct.pack('<Q', 10**15) + bytes([6, 1]) + bytes(36)


def token_data(mint, owner):
    return (bytes(mint) + bytes(owner) + bytes(8) + struct.pack('<I', 0) + bytes(32)
            + bytes([1]) + struct.pack('<I', 0) + bytes(16) + struct.pack('<I', 0) + bytes(32))


def control_data(entries):
    return (ACCOUNT_DISC['QuoteControl'] + bytes(USER.pubkey()) * 2 + bytes(32) + struct.pack('<I', len(entries))
            + b''.join(bytes(k) + struct.pack('<Q', r) for k, r in entries))


def quote_curve_data(q):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, q['vt'], q['vq'], q['rt'], q['rq'], q['supply'])
    data[48] = q['complete']
    data[49:81] = bytes(CREATOR)
    data[81] = q['mayhem']
    if q['root'] != 'sol':
        key = WHITELISTED if q['root'] == 'whitelisted' else ROOT_QUOTE
        data[83:115] = bytes(key)
    data[141] = q['depth']
    return bytes(data)


def quote_mint_key(item):
    kind = item['quote']
    if kind in ('whitelisted', 'noexec', 'short', 'short1', 'badprogram'):
        return WHITELISTED
    return {'native': NATIVE, 'zero': SYSTEM, 'blocked': BLOCKED}.get(kind, CONTROLLED)


def quote_setup(vm, item):
    """The remaining accounts of a case, with their accounts set on the VM."""
    kind = item['quote']
    if kind == 'none':
        return []
    mint = quote_mint_key(item)
    program = STRANGER if kind == 'badprogram' else item['program']
    owner = SYSTEM if item['owner_wrong'] else (TOKEN if kind == 'badprogram' else item['program'])
    if mint != SYSTEM:
        vm.set_account(mint, Account(10**7, mint_data(), owner))
    if kind == 'noexec':
        vm.set_account(TOKEN, Account(10**9, b'', SYSTEM))
    quote_ata = STRANGER if item['ata_wrong'] else ata(CURVE, program, mint)
    if item['ata_exists']:
        vm.set_account(quote_ata, Account(10**7, token_data(mint, CURVE), program))
    metas = [AccountMeta(mint, False, False), AccountMeta(quote_ata, False, True), AccountMeta(program, False, False)]
    if kind == 'short':
        return metas[:2]
    if kind == 'short1':
        return metas[:1]
    if kind in ('whitelisted', 'native', 'zero', 'blocked', 'badprogram', 'noexec', 'ctl_absent'):
        return metas
    if kind == 'ctl_key':
        return metas + [AccountMeta(STRANGER, False, False)]
    entries = [(CONTROLLED, item['reserves'])] if kind == 'listed' else []
    if kind == 'curve' and item['curve']['root'] not in ('sol', 'whitelisted', 'unlisted'):
        entries = [(ROOT_QUOTE, item['curve']['root'])]
    vm.set_account(QUOTE_CONTROL, Account(10**9, control_data(entries), STRANGER if kind == 'ctl_owner' else PUMP))
    metas.append(AccountMeta(QUOTE_CONTROL, False, False))
    if kind == 'curve':
        key = pda(b'bonding-curve', bytes(mint))
        if item['curve_flaw'] == 'key':
            return metas + [AccountMeta(STRANGER, False, False)]
        data = quote_curve_data(item['curve'])
        if item['curve_flaw'] == 'data':
            data = bytes(8) + data[8:]
        vm.set_account(key, Account(10**7, data, STRANGER if item['curve_flaw'] == 'owner' else PUMP))
        metas.append(AccountMeta(key, False, False))
    return metas


def new_vm(item):
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PUMP, PUMP_ELF)
    vm.add_program_from_file(MAYHEM, MAYHEM_ELF)
    vm.add_program_from_file(TOKEN, TOKEN_ELF)
    vm.add_program_from_file(TOKEN22, TOKEN22_ELF)
    vm.add_program_from_file(ATA, ATA_ELF)
    vm.set_clock(Clock(1000, 0, 0, 0, TS))
    vm.set_account(USER.pubkey(), Account(10**12, b'', SYSTEM))
    vm.set_account(ADMIN.pubkey(), Account(10**12, b'', SYSTEM))
    if item['params']:
        metas = [AccountMeta(ADMIN.pubkey(), True, True), AccountMeta(ACCOUNTS['global_params'], False, True),
                 AccountMeta(SYSTEM, False, False)]
        disc = hashlib.sha256(b'global:initialize_global_params').digest()[:8]
        tx = Transaction.new_signed_with_payer([Instruction(MAYHEM, disc, metas)], ADMIN.pubkey(), [ADMIN],
                                               vm.latest_blockhash())
        assert not isinstance(vm.send_transaction(tx), FailedTransactionMetadata)
    if 'g' not in item['faults']:
        vm.set_account(GLOBAL, Account(10**9, global_data(item), PUMP))
    if 'U' in item['faults']:
        vm.set_account(MINT.pubkey(), Account(10**7, bytes(82), TOKEN22))
    return vm


def run_captured(item):
    vm = new_vm(item)
    wrong = {WRONG[f] for f in item['faults'] if f in WRONG}
    read_only = {'mayhem_state'} if 'R' in item['faults'] else set()
    metas = [AccountMeta(STRANGER if a['name'] in wrong else ACCOUNTS[a['name']], a.get('signer', False),
                         a.get('writable', False) and a['name'] not in read_only) for a in CREATE_V2['accounts']]
    quote_metas = quote_setup(vm, item)
    creator = SYSTEM if item['creator_zero'] else CREATOR
    data = (bytes(CREATE_V2['discriminator']) + string(item['name']) + string(item['symbol']) + string(item['uri'])
            + bytes(creator) + bytes([item['mayhem']]) + tail_bytes(item))
    tx = Transaction.new_signed_with_payer(
        [set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas + quote_metas)],
        USER.pubkey(), [USER, MINT], vm.latest_blockhash())
    watched = sorted({m.pubkey for m in metas + quote_metas if m.pubkey not in (PUMP, MAYHEM, TOKEN, TOKEN22, ATA, SYSTEM)},
                     key=bytes)

    def snapshot():
        out = {}
        for key in watched:
            account = vm.get_account(key)
            out[key] = None if account is None else (account.lamports, bytes(account.data), account.owner)
        return out

    before = snapshot()
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    get = lambda key: vm.get_account(key)
    return {'error': str(result.err()) if failed else None, 'before': before, 'after': snapshot(),
            'events': [base64.b64decode(line[14:]) for line in meta.logs() if line.startswith('Program data: ')],
            'curve': get(CURVE), 'ata': get(CURVE_ATA), 'mint': get(MINT.pubkey()), 'vault': get(MAYHEM_VAULT),
            'state': get(ACCOUNTS['mayhem_state']), 'quote_ata': quote_ata_account(vm, item)}


def quote_ata_account(vm, item):
    if item['quote'] == 'none' or item['ata_wrong'] or item['quote'] == 'badprogram':
        return None
    return vm.get_account(ata(CURVE, item['program'], quote_mint_key(item)))


def fixed_cases():
    cases = [case()]
    add = lambda **k: cases.append(case(**k))
    add_curve = lambda **k: cases.append(quoted(**k))
    # Optional arguments: missing bytes read as off; a short fee reads as 0
    # and leaves its bytes for the holder flag.
    for tail in (b'', b'\0', b'\1', b'\2', b'\0\1', b'\0\2', b'\0\1\0\0', b'\0\0\0\0', bytes(9), bytes(9) + b'\1',
                 bytes(9) + b'\2', bytes(10) + b'\7'):
        add(tail=tail)
    add(mayhem=2)
    add(tail=b'\2', faults='A')
    add(mayhem=2, faults='g')
    # Accounts, alone and in pairs across each neighbouring check.
    for fault in FAULT_ORDER + 'R':
        add(faults=fault)
    for first, second in zip(FAULT_ORDER, FAULT_ORDER[1:]):
        add(faults=first + second)
    for pair in ('gE', 'BE', 'PU', 'UE', 'UA', 'TY', 'CY', 'YE'):
        add(faults=pair)
    add(faults='A', create_v2=0, creator_zero=1, mayhem=1, mayhem_on=0)
    # Argument gates and their order.
    add(mayhem=1)
    add(mayhem=1, mayhem_on=0)
    add(cashback=1)
    add(holder=1)
    add(holder=1, holder_on=0)
    add(holder=1, creator_zero=1)
    add(holder=1, mayhem=1)
    add(creator_zero=1)
    add(create_v2=0)
    add(mayhem=1, mayhem_on=0, cashback=1)
    add(cashback=1, holder=1, holder_on=0)
    add(cashback=1, creator_zero=1)
    add(holder=1, holder_on=0, creator_zero=1)
    add(creator_zero=1, create_v2=0)
    add(create_v2=0, quote='short')
    add(create_v2=0, name='x' * 33)
    add(quote='short', name='x' * 33)
    # Quote admission.
    for kind in ('short', 'short1', 'badprogram', 'noexec', 'native', 'zero', 'blocked', 'whitelisted', 'listed', 'ctl_absent',
                 'ctl_key', 'ctl_owner', 'unlisted'):
        add(quote=kind)
        add(quote=kind, mayhem=1)
        add(quote=kind, fee=301)
        add(quote=kind, owner_wrong=1)
        add(quote=kind, ata_wrong=1)
    for kind in ('whitelisted', 'listed'):
        add(quote=kind, program=TOKEN22)
        add(quote=kind, ata_exists=1)
    add(quote='native', ata_exists=1)
    add(quote='listed', ata_exists=1, mayhem=1)
    add(quote='listed', ata_exists=1, fee=301)
    add(quote='listed', reserves=0)
    add(quote='listed', reserves=U64)
    add(quote='listed', mayhem=1, fee=301)
    add(quote='listed', fee=301, name='x' * 33)
    add(quote='listed', fee=301, ata_wrong=1)
    add(quote='listed', fee=301, owner_wrong=1)
    add(quote='listed', owner_wrong=1, ata_wrong=1)
    add(quote='listed', fee=1, configurable=0)
    add(quote='listed', fee=0, configurable=0)
    add(quote='listed', fee=1, max_bps=0)
    add(quote='listed', fee=300)
    add(quote='whitelisted', ata_exists=1, mayhem=1)
    # One quote curve.
    add_curve()
    for flaw in ('key', 'owner', 'data'):
        cases.append(dict(quoted(), curve_flaw=flaw))
    add_curve(mayhem=1)
    add_curve(depth=2)
    add_curve(depth=255)
    add_curve(depth=1)
    add_curve(depth=1, vt=0, vq=0, rt=0)
    add_curve(depth=1, complete=1)
    add_curve(depth=1, supply=1)
    add_curve(depth=2, mayhem=1)
    add_curve(mayhem=1, root='unlisted')
    add_curve(root='unlisted')
    add_curve(root='unlisted', complete=1)
    add_curve(root='unlisted', vt=0, vq=0, rt=0)
    add_curve(root='whitelisted')
    add_curve(root=7_000_000_000)
    add_curve(root=0)
    add_curve(complete=1)
    add_curve(vt=0, vq=0, rt=0)
    add_curve(vt=0, vq=0, rt=0, rq=1)
    add_curve(vq=0)
    add_curve(vt=0, rt=0)
    add_curve(supply=1)
    add_curve(rt=0)
    add_curve(rt=1)
    add_curve(rt=10**15)
    add_curve(rt=10**15 + 1)
    add_curve(rq=10**12, rt=1)
    add_curve(rt=10**14, supply=2 * 10**15)
    add_curve(rt=10**14, rq=0, vq=1)
    cases.append(dict(quoted(), mayhem=1))
    cases.append(dict(quoted(), fee=300))
    cases.append(dict(quoted(), fee=301))
    cases.append(dict(quoted(), fee=1, configurable=0))
    cases.append(dict(quoted(), max_depth=0))
    cases.append(dict(quoted(), max_depth=1))
    cases.append(dict(quoted(), max_depth=255))
    cases.append(dict(quoted(), owner_wrong=1))
    cases.append(dict(quoted(), ata_wrong=1))
    cases.append(dict(quoted(), rtr=0))
    cases.append(dict(quoted(), vtr=793_100_000_000_000))
    cases.append(dict(quoted(), vtr=1))
    cases.append(dict(quoted(root=0), vsr=0))
    # Metadata limits (UTF-8 bytes), after the quote gates.
    add(name='x' * 32)
    add(name='x' * 33)
    add(name='é' * 16)
    add(name='é' * 16 + 'x')
    add(symbol='x' * 13)
    add(symbol='x' * 14)
    add(uri='x' * 200)
    add(uri='x' * 201)
    add(name='x' * 33, symbol='x' * 14)
    add(symbol='x' * 14, uri='x' * 201)
    add(name='', symbol='', uri='')
    # Global is copied as is; a mayhem coin mints the supply twice.
    add(supply=0)
    add(supply=U64)
    add(supply=2**63, mayhem=1)
    add(supply=2**63 - 1, mayhem=1)
    add(supply=0, mayhem=1)
    add(vtr=0, vsr=0, rtr=0)
    add(rtr=2 * 10**15)
    add(vtr=U64, vsr=U64, rtr=U64)
    add(quote='whitelisted', ivqr=0)
    add(quote='whitelisted', ivqr=U64)
    add(params=0)
    add(params=0, mayhem=1)
    add(mayhem=1, name='x' * 33, params=0)
    return cases


def random_cases(count=80, seed=807):
    rng = random.Random(seed)
    cases = []
    for _ in range(count):
        kind = rng.choice(('none', 'native', 'whitelisted', 'listed', 'curve', 'curve', 'unlisted', 'blocked'))
        item = dict(
            faults=rng.choice(('',) * 18 + ('A', 'Y')), creator_zero=int(rng.random() < 0.05),
            mayhem=int(rng.random() < 0.2), cashback=int(rng.random() < 0.02), holder=int(rng.random() < 0.2),
            fee=rng.choice((0, 1, 300, 301, rng.randrange(0, 301))), configurable=int(rng.random() > 0.1),
            mayhem_on=int(rng.random() > 0.05), holder_on=int(rng.random() > 0.05), create_v2=int(rng.random() > 0.02),
            name='n' * rng.randrange(26, 34), symbol='s' * rng.randrange(8, 15), uri='u' * rng.randrange(190, 202),
            vtr=rng.randrange(10**14, 2 * 10**15), vsr=rng.randrange(1, 10**11), rtr=rng.randrange(10**13, 10**14),
            supply=rng.randrange(0, 2**63), ivqr=rng.randrange(U64), migration_fee=rng.randrange(0, 10**9),
            quote=kind, reserves=rng.randrange(U64), owner_wrong=int(rng.random() < 0.02))
        if kind == 'curve':
            vt = rng.randrange(1, 2 * 10**15)
            item['curve'] = dict(depth=int(rng.random() < 0.05), mayhem=int(rng.random() < 0.05),
                                 complete=int(rng.random() < 0.05), vt=vt, vq=rng.randrange(1, 10**13),
                                 rt=rng.randrange(0, vt + 1), rq=rng.randrange(0, 10**12),
                                 supply=rng.randrange(10**14, 2 * 10**15),
                                 root=rng.choice(('sol', 'whitelisted', 'unlisted', rng.randrange(0, 10**12))))
        cases.append(case(**item))
    return cases


class CreateV2CapturedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for path, digest in ELF_SHA256.items():
            assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, path
        cls.tmp = tempfile.TemporaryDirectory()
        host = Path(cls.tmp.name) / 'create-v2-host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(host)],
                       check=True)
        cls.host = host

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def host_answers(self, cases):
        text = ''.join(host_line(item) + '\n' for item in cases)
        out = subprocess.run([str(self.host)], input=text, capture_output=True, text=True, check=True).stdout
        return out.splitlines()

    def assert_rejected(self, item, answer, captured):
        if answer in REJECTIONS:
            self.assertIn(REJECTIONS[answer], str(captured['error']))
        else:
            self.assertIn(f'InstructionErrorCustom({answer[6:]})', str(captured['error']))
        # A rejected create only charges the two signature fees.
        payer = USER.pubkey()
        for key, after in captured['after'].items():
            before = captured['before'][key]
            if key == payer:
                self.assertEqual(after[0], before[0] - TX_FEE)
                self.assertEqual(after[1:], before[1:])
            else:
                self.assertEqual(after, before, str(key))

    def assert_matches(self, item, answer, captured):
        if answer in REJECTIONS or answer.startswith('error:'):
            self.assert_rejected(item, answer, captured)
            return
        self.assertIsNone(captured['error'])
        fields = list(map(int, answer.split(',')[1:]))
        vtr, vqr, rtr, supply, initial_vqr, passed, fee, depth, mayhem, holder, minted, quote_ata = fields
        creator = HOLDER_PDA if holder else CREATOR
        quote = quote_mint_key(item) if passed else SYSTEM
        curve = bytearray(166)
        curve[:8] = ACCOUNT_DISC['BondingCurve']
        struct.pack_into('<QQQQQ', curve, 8, vtr, vqr, rtr, 0, supply)
        curve[49:81] = bytes(creator)
        curve[81] = mayhem
        curve[83:115] = bytes(quote)
        struct.pack_into('<Q', curve, 115, fee)
        curve[124] = holder
        curve[141] = depth
        struct.pack_into('<Q', curve, 142, initial_vqr)
        self.assertEqual(bytes(captured['curve'].data), bytes(curve))
        self.assertEqual(captured['curve'].owner, PUMP)
        # Supply minted, decimals 6, mint authority revoked (COption::None).
        mint = bytes(captured['mint'].data)
        self.assertEqual(captured['mint'].owner, TOKEN22)
        self.assertEqual(mint[:4] + mint[36:45], bytes(4) + struct.pack('<QB', minted, 6))
        self.assertEqual(struct.unpack_from('<Q', captured['ata'].data, 64)[0], supply)
        # The name, symbol and uri live in the mint's metadata extension.
        self.assertIn(string(item['name']) + string(item['symbol']) + string(item['uri']), mint)
        if mayhem:
            self.assertEqual(struct.unpack_from('<Q', captured['vault'].data, 64)[0], supply)
            self.assertIsNotNone(captured['state'])
        else:
            self.assertIsNone(captured['vault'])
            self.assertIsNone(captured['state'])
        if quote_ata:
            self.assertEqual(bytes(captured['quote_ata'].data)[:64], bytes(quote) + bytes(CURVE))
            self.assertEqual(captured['quote_ata'].owner, item['program'])
        elif item['quote'] != 'none' and not item['ata_exists']:
            self.assertIsNone(captured['quote_ata'])
        event = (CREATE_EVENT + string(item['name']) + string(item['symbol']) + string(item['uri'])
                 + bytes(MINT.pubkey()) + bytes(CURVE) + bytes(USER.pubkey()) + bytes(creator)
                 + struct.pack('<qQQQQ', TS, vtr, vqr, rtr, supply) + bytes(TOKEN22) + bytes([mayhem, 0]) + bytes(quote)
                 + struct.pack('<QQBB', vqr, fee, holder, depth))
        self.assertEqual(captured['events'], [event])

    def run_cases(self, cases):
        answers = self.host_answers(cases)
        self.assertEqual(len(answers), len(cases))
        for item, answer in zip(cases, answers):
            with self.subTest(case=host_line(item), host=answer):
                self.assert_matches(item, answer, run_captured(item))

    def test_fixed_cases_match_captured_program(self):
        self.run_cases(fixed_cases())

    def test_seeded_random_cases_match_captured_program(self):
        self.run_cases(random_cases())

    def test_checker_rejects_tampered_outcomes(self):
        # Negative control: a passing create must fail once the host's reserves,
        # fee or minted total is off, or an error is claimed instead.
        item = dict(quoted(), fee=100)
        answer = self.host_answers([item])[0]
        captured = run_captured(item)
        self.assert_matches(item, answer, captured)
        fields = answer.split(',')
        for index in (2, 5, 7, 8, 11):
            with self.subTest(field=index):
                changed = list(fields)
                changed[index] = str(int(changed[index]) + 1)
                with self.assertRaises(AssertionError):
                    self.assert_matches(item, ','.join(changed), captured)
        with self.assertRaises(AssertionError):
            self.assert_matches(item, 'error:6078', captured)

    def test_fixed_cases_cover_every_outcome(self):
        outcomes = {a.split(',')[0] for a in self.host_answers(fixed_cases())}
        self.assertEqual(outcomes, {'ok', 'missing', 'illegal_owner', *(f'error:{code}' for code in (
            0, 14, 102, 2000, 2006, 2012, 3003, 3008, 3012, 6024, 6026, 6027, 6030, 6043, 6044, 6045, 6046, 6048,
            6063, 6064, 6065, 6071, 6075, 6077, 6078, 6082, 6084, 6099, 6100, 6101, 6104, 6105, 6107, 6109))})


if __name__ == '__main__':
    unittest.main()
