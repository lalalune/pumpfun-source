"""Captured-program checks for whole `multi_hop_curve_swap` routes.

Every case runs Pump `multi_hop_curve_swap` from the captured
`evidence/original/pump/deployed.so` (upgradeable loader) on LiteSVM over one or
more curve hops: sell one curve into another's quote, buy a curve quoted in
another curve's base, go round the same curve twice, in native SOL and in SPL
tokens, and buys that cross into the post-complete fill. On mainnet only
pump_amm calls the instruction, signing for its `global_config` PDA; here
signature verification is off so that PDA can sit in a signer slot, and every
other check runs unchanged. Account state is synthetic (IDL layouts). The same
inputs go to `programs/pump/recovered/multi_hop_route_host.rs`, and the error,
the bytes of every curve, every vault, the user's source and destination, the
user's lamports, the buyback recipient and the returned `CurveRunResult` must
agree. Events are not compared. This shows matching behavior on these inputs
only; it is not a byte-identity claim.
"""
from pathlib import Path
import copy
import hashlib
import json
import random
import re
import struct
from types import SimpleNamespace
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

ROOT = Path(__file__).resolve().parents[1]
PUMP_ELF = ROOT / 'evidence/original/pump/deployed.so'
TOKEN_ELF = ROOT / 'evidence/dependencies/spl_token/deployed.so'
ELF_SHA256 = {PUMP_ELF: '7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d',
              TOKEN_ELF: '8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697'}
HOST_SOURCE = ROOT / 'programs/pump/recovered/multi_hop_route_host.rs'

IDL = json.loads((ROOT / 'evidence/upstream/pump.json').read_text(encoding='utf-8'))
PUMP = Pubkey.from_string(IDL['address'])
FEES = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
PUMP_AMM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')
SYSTEM = Pubkey.default()
SWAP = next(i for i in IDL['instructions'] if i['name'] == 'multi_hop_curve_swap')
ACCOUNT_DISC = {a['name']: bytes(a['discriminator']) for a in IDL['accounts']}

USER = Keypair.from_seed(bytes([211]) * 32)
CREATOR = Pubkey.from_bytes(bytes([212]) * 32)
BUYBACK = Pubkey.from_bytes(bytes([213]) * 32)
# Mint ids of the model: 0 is WSOL, 1 an SPL quote, 2.. curve base mints.
MINTS = [WSOL] + [Pubkey.from_bytes(bytes([214 + i]) * 32) for i in range(4)]
TS = 1_800_000_000
CURVE_RENT = 2_046_240
TOKEN_RENT = 2_039_280
USER_LAMPORTS = 10**13
TX_FEE = 10_000                  # two signers: the user and the AMM config slot
SUPPLY = 10**15
TIER_BPS = (95, 30)
FLAT_BPS = (90, 20)
U64 = 2**64 - 1


def pda(seeds, program=PUMP):
    return Pubkey.find_program_address(seeds, program)[0]


def ata(owner, mint):
    return pda([bytes(owner), bytes(TOKEN), bytes(mint)], ATA)


GLOBAL = pda([b'global'])
FEE_CONFIG = pda([b'fee_config', bytes(PUMP)], FEES)
AMM_CONFIG = pda([b'global_config'], PUMP_AMM)
curve_key = lambda c: pda([b'bonding-curve', bytes(MINTS[c['base']])])


def mint_data(supply=SUPPLY, decimals=6):
    return struct.pack('<I32sQBBI32s', 0, bytes(32), supply, decimals, 1, 0, bytes(32))


def token_data(mint, owner, amount, native=None):
    tag, value = (0, 0) if native is None else (1, native)
    return struct.pack('<32s32sQI32sBIQQI32s', bytes(mint), bytes(owner), amount, 0, bytes(32), 1, tag, value,
                       0, 0, bytes(32))


def global_data(route):
    data = bytearray(1088)
    data[:8] = ACCOUNT_DISC['Global']
    data[8] = 1
    struct.pack_into('<QQQQQ', data, 73, 1_073_000_000_000_000, 30_000_000_000, 793_100_000_000_000, SUPPLY, 95)
    struct.pack_into('<Q', data, 146, route['pool_fee'])
    struct.pack_into('<Q', data, 154, 30)
    data[450] = 1
    data[451:483] = bytes([92]) * 32   # whitelist_pda
    data[515] = 1
    data[741:773] = bytes(BUYBACK)
    struct.pack_into('<QQ', data, 997, route['buyback_bps'], 30_000_000_000)
    return bytes(data)


def fee_config_data():
    bump = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], FEES)[1]
    data = (bytes([143, 52, 146, 187, 219, 123, 76, 155]) + bytes([bump]) + bytes([93]) * 32
            + struct.pack('<QQQ', 0, *FLAT_BPS) + struct.pack('<I', 1)
            + (0).to_bytes(16, 'little') + struct.pack('<QQQ', 0, *TIER_BPS)
            + struct.pack('<I', 0) + struct.pack('<QQQ', 0, 0, 0))
    return data.ljust(2512, b'\0')


def curve_data(c):
    data = bytearray(166)
    data[:8] = ACCOUNT_DISC['BondingCurve']
    struct.pack_into('<QQQQQ', data, 8, c['vtr'], c['vqr'], c['rtr'], c['rqr'], SUPPLY)
    data[48] = c['complete']
    data[49:81] = bytes(CREATOR) if c['creator'] else bytes(32)
    data[81], data[82] = c['mayhem'], c['cashback']
    if c['quote'] != 0:
        data[83:115] = bytes(MINTS[c['quote']])
    struct.pack_into('<QQ', data, 125, c['cf'], c['pf'])
    return bytes(data)


def curve(base, quote, **over):
    c = dict(base=base, quote=quote, vtr=10**15, vqr=30_000_000_000, rtr=793_100_000_000_000, rqr=100_000_000_000, cf=0, pf=0,
             creator=1, cashback=0, complete=0, mayhem=0, base_vault=10**15, quote_vault=None)
    c.update(over)
    if c['quote_vault'] is None:
        c['quote_vault'] = 0 if quote == 0 else c['rqr'] + c['cf'] + c['pf']
    return c


def route(curves, hops, amount=10**9, flags=None, source=None, destination=None, **over):
    r = dict(curves=curves, hops=hops, amount=amount, flags=flags if flags is not None else tuple(0 for _ in hops),
             remaining=5 * len(hops), source=source, destination=destination, source_balance=10**14, recipient=None,
             pool_fee=0, buyback_bps=5_000)
    r.update(over)
    if r['recipient'] is None:
        r['recipient'] = curves[hops[0]]['quote'] if hops else 1
    return r


def host_line(r):
    join = lambda v: ':'.join(map(str, v)) or '-'
    head = [r['amount'], join(r['flags']), r['remaining'], r['source'], r['destination'], r['source_balance'], r['recipient'],
            r['pool_fee'], r['buyback_bps'], TIER_BPS[0], TIER_BPS[1], FLAT_BPS[0], FLAT_BPS[1], join(r['hops'])]
    blocks = [','.join(map(str, [c['vtr'], c['vqr'], c['rtr'], c['rqr'], c['cf'], c['pf'], c['creator'], c['cashback'], c['complete'],
                                 c['mayhem'], c['base'], c['quote'], c['base_vault'], c['quote_vault']])) for c in r['curves']]
    return '|'.join([','.join(map(str, head))] + blocks)


_HOST = None
_PROGRAM_BYTES = None


def read_pinned_elf(path, digest):
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError(f'captured ELF digest mismatch: {path}')
    return payload


def captured_program_bytes():
    # Pin once and give the VM the exact immutable bytes which were checked.
    global _PROGRAM_BYTES
    if _PROGRAM_BYTES is None:
        _PROGRAM_BYTES = tuple(read_pinned_elf(path, ELF_SHA256[path]) for path in (PUMP_ELF, TOKEN_ELF))
    return _PROGRAM_BYTES


def host_binary():
    global _HOST
    if _HOST is None:
        out = Path(tempfile.mkdtemp()) / 'multi_hop_route_host'
        subprocess.run(['rustc', '--edition=2021', '-O', '-D', 'warnings', str(HOST_SOURCE), '-o', str(out)], check=True)
        _HOST = out
    return _HOST


def model(routes):
    text = ''.join(host_line(r) + '\n' for r in routes)
    answers = subprocess.run([str(host_binary())], input=text, capture_output=True, text=True, check=True).stdout.splitlines()
    if len(answers) != len(routes):
        raise ValueError(f'host returned {len(answers)} answers for {len(routes)} routes')
    return answers


def run_captured(r):
    pump_bytes, token_bytes = captured_program_bytes()
    vm = LiteSVM().with_transaction_history(0).with_sigverify(False)
    programdata = pda([bytes(PUMP)], UPGRADEABLE)
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + pump_bytes, UPGRADEABLE, False))
    vm.set_account(PUMP, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    vm.add_program(TOKEN, token_bytes)
    vm.set_clock(Clock(1000, 0, 0, 0, TS))
    user = USER.pubkey()
    state = {GLOBAL: (10**9, PUMP, global_data(r)), FEE_CONFIG: (10**9, FEES, fee_config_data()), user: (USER_LAMPORTS, SYSTEM, b'')}
    for i, m in enumerate(MINTS):
        state[m] = (10**9, TOKEN, mint_data(SUPPLY, 9 if i == 0 else 6))
    for c in r['curves']:
        key = curve_key(c)
        native = c['quote'] == 0
        state[key] = (CURVE_RENT + (c['rqr'] + c['cf'] + c['pf'] if native else 0), PUMP, curve_data(c))
        state[ata(key, MINTS[c['base']])] = (10**9, TOKEN, token_data(MINTS[c['base']], key, c['base_vault']))
        vault = token_data(WSOL, key, 0, TOKEN_RENT) if native else token_data(MINTS[c['quote']], key, c['quote_vault'])
        state[ata(key, MINTS[c['quote']])] = (TOKEN_RENT, TOKEN, vault)

    def user_ata(mint_id, amount):
        key = ata(user, MINTS[mint_id])
        data = token_data(WSOL, user, amount, TOKEN_RENT) if mint_id == 0 else token_data(MINTS[mint_id], user, amount)
        state[key] = (TOKEN_RENT + (amount if mint_id == 0 else 0), TOKEN, data)
        return key

    source = user_ata(r['source'], r['source_balance'])
    if r['destination'] != r['source']:
        user_ata(r['destination'], 0)
    destination = ata(user, MINTS[r['destination']])
    recipient = ata(BUYBACK, MINTS[r['recipient']])
    state[recipient] = (TOKEN_RENT, TOKEN, token_data(WSOL, BUYBACK, 0, TOKEN_RENT) if r['recipient'] == 0
                        else token_data(MINTS[r['recipient']], BUYBACK, 0))
    for key, (lamports, owner, data) in state.items():
        vm.set_account(key, Account(lamports, data, owner))
    metas = [AccountMeta(GLOBAL, False, False), AccountMeta(FEE_CONFIG, False, False), AccountMeta(AMM_CONFIG, True, False),
             AccountMeta(user, True, True), AccountMeta(user, True, False), AccountMeta(source, False, True),
             AccountMeta(destination, False, True), AccountMeta(recipient, False, True), AccountMeta(TOKEN, False, False),
             AccountMeta(TOKEN22, False, False), AccountMeta(SYSTEM, False, False), AccountMeta(pda([b'__event_authority']), False, False),
             AccountMeta(PUMP, False, False)]
    assert len(metas) == len(SWAP['accounts'])
    hop_keys = []
    for i in r['hops']:
        c = r['curves'][i]
        key = curve_key(c)
        hop_keys += [MINTS[c['base']], MINTS[c['quote']], key, ata(key, MINTS[c['base']]), ata(key, MINTS[c['quote']])]
    metas += [AccountMeta(k, False, j % 5 >= 2) for j, k in enumerate(hop_keys)][:r['remaining']]
    data = bytes(SWAP['discriminator']) + struct.pack('<QI', r['amount'], len(r['flags'])) + bytes(r['flags'])
    ixs = [set_compute_unit_limit(1_400_000), Instruction(PUMP, data, metas)]
    tx = Transaction.new_unsigned(Message.new_with_blockhash(ixs, user, vm.latest_blockhash()))
    tx.partial_sign([USER], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    amount = lambda key: struct.unpack_from('<Q', bytes(vm.get_account(key).data), 64)[0]
    curves = []
    for c in r['curves']:
        key = curve_key(c)
        a = vm.get_account(key)
        curves.append(dict(data=bytes(a.data), lamports=a.lamports - state[key][0], base_vault=amount(ata(key, MINTS[c['base']])),
                           quote_vault=amount(ata(key, MINTS[c['quote']]))))
    rollback_errors = []
    if failed:
        for key, (lamports, owner, data) in state.items():
            after = vm.get_account(key)
            expected_lamports = lamports - TX_FEE if key == user else lamports
            if (after is None or after.lamports != expected_lamports or after.owner != owner
                    or bytes(after.data) != data or after.executable):
                rollback_errors.append(str(key))
    return dict(error=str(result.err()) if failed else None, curves=curves, returned=bytes(meta.return_data().data),
                rollback_errors=rollback_errors,
                source=amount(source) - r['source_balance'], destination=amount(destination),
                recipient=vm.get_account(recipient).lamports - TOKEN_RENT if r['recipient'] == 0 else amount(recipient),
                user_lamports=vm.get_account(user).lamports - USER_LAMPORTS)


def check(r, got, answer):
    """List mismatches; malformed or incomplete model/capture results fail closed."""
    error = re.fullmatch(r'error:([0-9]+)', answer)
    if error:
        captured = re.search(r'Custom\(([0-9]+)\)', str(got['error']))
        bad = [] if captured and captured.group(1) == error.group(1) else [f"error {got['error']} != {error.group(1)}"]
        if got.get('rollback_errors') != []:
            bad.append('failed transaction did not restore every seeded account')
        if (got['source'] != 0 or got['destination'] != (r['source_balance'] if r['source'] == r['destination'] else 0)
                or got['recipient'] != 0 or got['user_lamports'] != -TX_FEE):
            bad.append('failed transaction changed a user or recipient balance')
        if len(got['curves']) != len(r['curves']):
            bad.append('failed transaction curve count')
        else:
            for c, g in zip(r['curves'], got['curves']):
                if (g['data'] != curve_data(c) or g['lamports'] != 0 or g['base_vault'] != c['base_vault']
                        or g['quote_vault'] != c['quote_vault']):
                    bad.append('failed transaction changed a curve or vault')
        return bad
    if got['error'] is not None:
        return [f"captured failed with {got['error']}"]
    blocks = answer.split('|')
    fields = blocks[0].split(',')
    if len(fields) != 7 or fields[0] != 'ok':
        return ['malformed model status or output fields']
    if len(blocks) - 1 != len(r['curves']) or len(got['curves']) != len(r['curves']):
        return ['model/capture curve count does not match route']
    try:
        out, buyback, source, destination, lamports, recipient = map(int, fields[1:])
        curves = [list(map(int, block.split(','))) for block in blocks[1:]]
    except ValueError:
        return ['noninteger model output']
    if any(len(values) != 12 for values in curves):
        return ['malformed model curve fields']
    if not 0 <= out <= U64 or not 0 <= buyback <= U64:
        return ['model return value out of range']
    bad = []
    if got['returned'] != struct.pack('<QQ', out, buyback):
        bad.append('return data')
    expected_source = source + destination if r['source'] == r['destination'] else source
    expected_destination = r['source_balance'] + expected_source if r['source'] == r['destination'] else destination
    if got['source'] != expected_source:
        bad.append(f"source {got['source']} != {expected_source}")
    if got['destination'] != expected_destination:
        bad.append(f"destination {got['destination']} != {expected_destination}")
    if got['user_lamports'] != lamports - TX_FEE:
        bad.append(f"user lamports {got['user_lamports']} != {lamports - TX_FEE}")
    if got['recipient'] != recipient:
        bad.append(f"recipient {got['recipient']} != {recipient}")
    for c, g, values in zip(r['curves'], got['curves'], curves):
        vtr, vqr, rtr, rqr, cf, pf, post_base, post_quote, complete, base_vault, quote_vault, delta = values
        if any(not 0 <= value <= U64 for value in values[:11]) or complete not in (0, 1):
            bad.append('model curve value out of range')
            continue
        after = bytearray(curve_data(c))
        struct.pack_into('<QQQQ', after, 8, vtr, vqr, rtr, rqr)
        after[48] = complete
        struct.pack_into('<QQ', after, 125, cf, pf)
        struct.pack_into('<QQ', after, 150, post_base, post_quote)
        if g['data'] != bytes(after):
            bad.append(f"curve {c['base']} bytes")
        if g['base_vault'] != base_vault:
            bad.append(f"curve {c['base']} base vault {g['base_vault']} != {base_vault}")
        if g['quote_vault'] != quote_vault:
            bad.append(f"curve {c['base']} quote vault {g['quote_vault']} != {quote_vault}")
        if g['lamports'] != delta:
            bad.append(f"curve {c['base']} lamports {g['lamports']} != {delta}")
    return bad


Q, A, B, C = 1, 2, 3, 4


def trip_small():
    return route([curve(A, Q, base_vault=10)], [0, 0], source=Q, destination=Q)


def spl_pair(**over):
    return [curve(A, Q, **over), curve(B, Q)]


def fixed_cases():
    out = []
    add = lambda label, r: out.append((label, r))
    sell_buy = lambda **k: route(spl_pair(), [0, 1], **dict(dict(source=A, destination=B), **k))
    native_pair = [curve(A, 0), curve(B, 0)]
    native = lambda **k: route(native_pair, [0, 1], **dict(dict(source=A, destination=B), **k))
    chain = lambda **k: route([curve(A, Q), curve(B, A, vqr=10**12, vtr=10**12, rtr=5 * 10**11, rqr=10**9, quote_vault=10**9)], [0, 1], source=Q, destination=B, **k)
    trip = lambda **k: route([curve(A, Q)], [0, 0], source=Q, destination=Q, **k)
    native_trip = lambda **k: route([curve(A, 0)], [0, 0], source=0, destination=0, **k)
    for f1 in range(4):
        for f2 in range(4):
            add(f'sell-buy-{f1}{f2}', sell_buy(flags=(f1, f2)))
            add(f'native-sell-buy-{f1}{f2}', native(flags=(f1, f2)))
            add(f'chain-{f1}{f2}', chain(flags=(f1, f2), recipient=Q))
            add(f'trip-{f1}{f2}', trip(flags=(f1, f2)))
            add(f'native-trip-{f1}{f2}', native_trip(flags=(f1, f2)))
    three = [curve(A, Q), curve(B, Q)]
    for f in ((0, 0, 0), (1, 1, 1), (3, 3, 3), (2, 0, 1)):
        add(f'three-{f}', route(three, [0, 1, 1], source=A, destination=Q, flags=f))
        add(f'four-{f}', route(three, [0, 1, 1, 0], source=A, destination=A, flags=f + (3,)))
    # Check order and continuity.
    add('hop-two-complete', route([curve(A, Q), curve(B, Q, complete=1)], [0, 1], source=A, destination=B))
    add('hop-two-mayhem', route([curve(A, Q), curve(B, Q, mayhem=1)], [0, 1], source=A, destination=B))
    add('hop-two-cashback', route([curve(A, Q), curve(B, Q, cashback=1)], [0, 1], source=A, destination=B, flags=(0, 2)))
    add('hop-two-cashback-free', route([curve(A, Q), curve(B, Q, cashback=1)], [0, 1], source=A, destination=B, flags=(0, 1)))
    add('complete-then-mayhem', route([curve(A, Q, complete=1, mayhem=1)], [0], source=A, destination=Q))
    add('recipient-mint-second-hop', chain(flags=(1, 1), recipient=Q))
    add('recipient-mint-first-hop', chain(flags=(1, 1), recipient=A))
    add('recipient-before-direction', route(spl_pair(), [0, 0], source=C, destination=Q, flags=(1, 1), recipient=A))
    add('discontinuous-first', route(spl_pair(), [0, 1], source=C, destination=B))
    add('discontinuous-second', route([curve(A, Q), curve(B, C, quote_vault=0)], [0, 1], source=A, destination=B))
    add('wrong-destination', sell_buy(destination=C))
    add('wrong-destination-native', native(destination=C))
    add('wrong-destination-native-sell', route([curve(A, 0)], [0], source=A, destination=C))
    add('wrong-destination-vault-short', route([curve(A, Q, base_vault=10)], [0], source=Q, destination=C))
    add('buy-budget-below-fees', route([curve(A, Q)], [0], amount=1, source=Q, destination=A, flags=(3,)))
    add('buy-net-trimmed-to-zero', route([curve(A, Q)], [0], amount=2, source=Q, destination=A, flags=(3,)))
    add('second-hop-budget-below-fees', route([curve(A, Q, vqr=10**4, vtr=10**15), curve(B, Q)], [0, 1], amount=10**7, source=A, destination=B, flags=(0, 3)))
    add('flags-too-few', sell_buy(flags=(0,)))
    add('flags-too-many', sell_buy(flags=(0, 0, 0)))
    add('flag-four-second', sell_buy(flags=(0, 4)))
    add('remaining-odd', sell_buy(remaining=9))
    add('amount-zero', sell_buy(amount=0))
    # The output of the first hop limits the second.
    add('sell-then-dust-buy', sell_buy(amount=1_000, flags=(3, 3)))
    add('sell-zero', sell_buy(amount=1, flags=(3, 3)))
    add('source-short', sell_buy(source_balance=10**9 - 1))
    add('first-vault-short', route([curve(A, Q, quote_vault=10), curve(B, Q)], [0, 1], source=A, destination=B))
    add('last-vault-short', route(spl_pair(), [0, 1], source=A, destination=B, amount=10**13, source_balance=10**14))
    add('second-buy-vault-short', route([curve(A, Q), curve(B, Q, base_vault=100, rtr=100)], [0, 1], source=A, destination=B))
    add('native-reserve-short', route([curve(A, 0, rqr=10)], [0], source=A, destination=0))
    add('buyback-all', sell_buy(flags=(1, 1), buyback_bps=10_000))
    add('buyback-none', sell_buy(flags=(1, 1), buyback_bps=0))
    add('buyback-third', sell_buy(flags=(3, 3), buyback_bps=3_333))
    add('no-creator', route([curve(A, Q, creator=0), curve(B, Q, creator=0)], [0, 1], source=A, destination=B, flags=(3, 3)))
    add('fee-overflow-second', route([curve(A, Q), curve(B, Q, cf=U64, quote_vault=0)], [0, 1], source=A, destination=B, flags=(3, 3)))
    # Crossing buys: the curve fills, the rest prices against the pool.
    for quote, q in (('sol', 0), ('spl', Q)):
        one = lambda **o: [curve(A, q, rtr=10**12, **o)]
        cross = lambda **k: route(one(), [0], source=q, destination=A, **k)
        for f in range(4):
            add(f'{quote}-cross-{f}', cross(flags=(f,)))
            add(f'{quote}-cross-bb0-{f}', cross(flags=(f,), buyback_bps=0))
            add(f'{quote}-cross-no-creator-{f}', route(one(creator=0), [0], source=q, destination=A, flags=(f,)))
            for amount in (30_030_031, 30_500_000, 30_600_000, 30_610_000, 31_000_000, 40_000_000):
                add(f'{quote}-cross-{amount}-{f}', cross(amount=amount, flags=(f,)))
        add(f'{quote}-cross-pool-fee', cross(pool_fee=3 * 10**9))
        add(f'{quote}-cross-pool-fee-over', cross(pool_fee=10**12))
        add(f'{quote}-cross-pool-base-zero', route(one(base_vault=10**12), [0], source=q, destination=A))
        add(f'{quote}-cross-pool-base-short', route(one(base_vault=10**12 - 1), [0], source=q, destination=A))
        add(f'{quote}-cross-all-vtr', route([curve(A, q, vtr=10**12, rtr=10**12)], [0], source=q, destination=A))
        add(f'{quote}-cross-then-complete', route(one(), [0, 0], source=q, destination=q))
        add(f'{quote}-exact-fill', route([curve(A, q, rtr=10**12, vtr=10**15)], [0], amount=30_030_030, source=q, destination=A, flags=(0,)))
        # Around the curve cost: the fill is dropped until the rest buys something.
        quote_cost = 30_030_031
        for f in range(4):
            bps = (TIER_BPS if q == 0 else FLAT_BPS)
            rate = (bps[0] if f & 1 else 0) + (bps[1] if f & 2 else 0)
            for d in range(-3, 13):
                add(f'{quote}-near-curve-{f}-{d}', cross(amount=quote_cost + (quote_cost * rate + 9_999) // 10_000 + d, flags=(f,)))
        add(f'{quote}-cross-pool-one-token', route(one(base_vault=10**12 + 1), [0], amount=31_000_000, source=q, destination=A))
        add(f'{quote}-cross-pool-quote-zero', cross(pool_fee=10**11 + quote_cost, amount=31_000_000))
    # A budget of one prices to nothing; a net trim still prices on budget - fees.
    add('buy-one-free', route([curve(A, Q)], [0], amount=1, source=Q, destination=A))
    for amount in range(300, 340):
        add(f'buy-trim-{amount}', route([curve(A, Q)], [0], amount=amount, source=Q, destination=A, flags=(3,)))
    for amount in (1_010, 2_020, 10_100):
        add(f'buy-untrimmed-{amount}', route([curve(A, Q)], [0], amount=amount, source=Q, destination=A, flags=(1,)))
    # A vault that already holds the input moves nothing, however little it holds.
    add('trip-small-base-vault', trip_small())
    add('cross-then-buy', route([curve(A, Q, rtr=10**12), curve(B, A, vqr=10**12, vtr=10**12, rtr=5 * 10**11, rqr=10**9, quote_vault=10**9)],
                                [0, 1], source=Q, destination=B))
    add('sell-into-cross', route([curve(A, Q), curve(B, Q, rtr=10**12)], [0, 1], amount=10**12, source=A, destination=B))
    return out


def random_cases(count=120, seed=20261030):
    rng = random.Random(seed)
    out = []
    for i in range(count):
        q = rng.choice([0, Q])
        small = rng.random() < 0.4
        rand_curve = lambda base: curve(base, q, vtr=rng.choice([10**15, 10**13]), vqr=rng.randrange(10**8, 10**11),
                                        rtr=rng.choice([10**12, rng.randrange(1, 10**12), 10**14]), rqr=rng.randrange(10**8, 10**12),
                                        creator=int(rng.random() < .8), cf=rng.randrange(10**6), pf=rng.randrange(10**6))
        curves = [rand_curve(A), rand_curve(B)]
        shape = rng.choice(['sell-buy', 'trip', 'three', 'cross'])
        hops, source, dest = {'sell-buy': ([0, 1], A, B), 'trip': ([0, 0], q, q), 'three': ([0, 1, 1], A, q), 'cross': ([0], q, A)}[shape]
        amount = rng.randrange(1, 10**6) if small else rng.randrange(10**6, 10**11)
        r = route(curves, hops, amount=amount, flags=tuple(rng.randrange(4) for _ in hops), source=source, destination=dest,
                  pool_fee=rng.choice([0, rng.randrange(10**9)]), buyback_bps=rng.choice([0, 5_000, 10_000, rng.randrange(10_001)]))
        out.append((f'random-{i}-{shape}', r))
    return out


class MultiHopRouteCaptured(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        captured_program_bytes()

    def run_all(self, labelled):
        self.assertTrue(labelled, 'at least one route is required')
        answers = model([r for _, r in labelled])
        self.assertEqual(len(answers), len(labelled), 'one model answer is required per captured route')
        results = []
        for (label, r), answer in zip(labelled, answers):
            with self.subTest(label):
                self.assertEqual(check(r, run_captured(r), answer), [], (label, answer))
            results.append(answer)
        return results

    def test_fixed_cases(self):
        cases = fixed_cases()
        self.assertEqual(len(cases), 387)
        results = self.run_all(cases)
        outcomes = {a.split(',')[0] for a in results}
        for want in ('ok', 'error:1', 'error:3', 'error:6004', 'error:6005', 'error:6020', 'error:6021', 'error:6022', 'error:6024', 'error:6027',
                     'error:6041', 'error:6042', 'error:6094', 'error:6098', 'error:6106', 'error:6108'):
            self.assertIn(want, outcomes)
        self.assertEqual(sum(a.startswith('ok,') for a in results), 342)
        self.assertEqual(sum(a.startswith('ok,') and len(r['hops']) >= 2
                             for (_, r), a in zip(cases, results)), 89, 'successful multi-hop routes')
        self.assertEqual(sum(a.startswith('ok,') and any(int(b.split(',')[6]) > 0 for b in a.split('|')[1:])
                             for a in results), 155, 'successful crossing fills')

    def test_random_cases(self):
        cases = random_cases()
        self.assertEqual(len(cases), 120)
        results = self.run_all(cases)
        self.assertEqual(sum(a.startswith('ok,') for a in results), 102)
        self.assertEqual(sum(a.startswith('ok,') and len(r['hops']) >= 2
                             for (_, r), a in zip(cases, results)), 65, 'successful multi-hop routes')
        self.assertEqual(sum(a.startswith('ok,') and any(int(b.split(',')[6]) > 0 for b in a.split('|')[1:])
                             for a in results), 21, 'successful crossing fills')

    def test_answer_cardinality_and_empty_batches_fail(self):
        r = route(spl_pair(), [0, 1], source=A, destination=B)
        with self.assertRaises(AssertionError):
            self.run_all([])
        for answers in ([], ['error:1', 'error:1']):
            with self.subTest(answers=answers), patch.dict(globals(), {'model': lambda routes: answers}):
                with self.assertRaises(AssertionError):
                    self.run_all([('one', r)])
        for stdout in ('', 'error:1\nerror:1\n'):
            with self.subTest(stdout=stdout), patch.dict(globals(), {'_HOST': Path('/unused')}):
                with patch('subprocess.run', return_value=SimpleNamespace(stdout=stdout)):
                    with self.assertRaisesRegex(ValueError, 'answers for'):
                        model([r])

    def test_elf_bytes_are_pinned_and_not_reopened_for_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'elf'
            path.write_bytes(b'pinned fixture')
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            bound = read_pinned_elf(path, digest)
            path.write_bytes(b'replaced fixture')
            self.assertEqual(bound, b'pinned fixture')
            with self.assertRaisesRegex(ValueError, 'digest mismatch'):
                read_pinned_elf(path, digest)
        r = route(spl_pair(), [0, 1], source=A, destination=B)
        answer = model([r])[0]
        # setUpClass has already retained the validated bytes. A reread now must fail.
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('ELF reopened after pin')):
            got = run_captured(r)
        self.assertEqual(check(r, got, answer), [])

    def test_checker_rejects_incomplete_or_malformed_outcomes(self):
        r = route(spl_pair(), [0, 1], source=A, destination=B)
        answer = model([r])[0]
        got = run_captured(r)
        head, *curves = answer.split('|')
        malformed = ['', answer.replace('ok,', 'unmodelled,', 1), 'error:', 'error:1junk',
                     head, '|'.join([head] + curves[:-1]), answer + '|' + curves[-1],
                     '|'.join([head] + [','.join(curves[0].split(',')[:-1])] + curves[1:]),
                     answer.replace('ok,', 'ok,no-number,', 1)]
        for bent in malformed:
            with self.subTest(answer=bent):
                self.assertNotEqual(check(r, got, bent), [])
        for count in (0, 1, 3):
            bent = copy.deepcopy(got)
            bent['curves'] = (bent['curves'] * 2)[:count]
            self.assertNotEqual(check(r, bent, answer), [])

    def test_error_outcomes_require_rollback(self):
        r = route([curve(A, Q), curve(B, Q, complete=1)], [0, 1], source=A, destination=B)
        answer = model([r])[0]
        got = run_captured(r)
        self.assertEqual(answer, 'error:6005')
        self.assertEqual(check(r, got, answer), [])
        self.assertNotEqual(check(r, got, 'error:600'), [])
        for key in ('source', 'destination', 'recipient', 'user_lamports'):
            bent = copy.deepcopy(got)
            bent[key] += 1
            self.assertNotEqual(check(r, bent, answer), [], key)
        for key in ('data', 'base_vault', 'quote_vault', 'lamports'):
            bent = copy.deepcopy(got)
            value = bent['curves'][0][key]
            bent['curves'][0][key] = bytes([value[0] ^ 1]) + value[1:] if isinstance(value, bytes) else value + 1
            self.assertNotEqual(check(r, bent, answer), [], key)
        bent = dict(got, rollback_errors=['changed unrelated seeded account'])
        self.assertNotEqual(check(r, bent, answer), [])

    def test_checker_rejects_tampered_outcomes(self):
        routes = [route(spl_pair(), [0, 1], source=A, destination=B, flags=(3, 3)),
                  route([curve(A, 0)], [0], source=0, destination=A, flags=(3,)),
                  route([curve(A, Q)], [0, 0], source=Q, destination=Q)]
        for r, answer in zip(routes, model(routes)):
            got = run_captured(r)
            self.assertEqual(check(r, got, answer), [])
            head, *curves = answer.split('|')
            fields = head.split(',')
            for i in range(1, len(fields)):
                bent = fields[:i] + [str(int(fields[i]) + 1)] + fields[i + 1:]
                self.assertNotEqual(check(r, got, '|'.join([','.join(bent)] + curves)), [], i)
            for j, block in enumerate(curves):
                parts = block.split(',')
                for i in range(len(parts)):
                    bent = parts[:i] + [str(int(parts[i]) + 1)] + parts[i + 1:]
                    others = curves[:j] + [','.join(bent)] + curves[j + 1:]
                    self.assertNotEqual(check(r, got, '|'.join([head] + others)), [], (j, i))
            bent = dict(got, destination=got['destination'] + 1)
            self.assertNotEqual(check(r, bent, answer), [])
            self.assertNotEqual(check(r, got, 'error:6024'), [])


if __name__ == '__main__':
    unittest.main()
