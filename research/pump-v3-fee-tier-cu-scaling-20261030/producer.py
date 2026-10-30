#!/usr/bin/env python3
"""Pump Main v3 trades: compute-unit scaling over FeeConfig tiers and amounts, original vs rebuild.

The v3 handlers (buy_v3, buy_exact_quote_in_v3, sell_v3) do not CPI pump_fees:
they deserialize the pump_fees FeeConfig account themselves and select a
market-cap fee tier. This packet sweeps the tier count (1..60, market cap in the
last tier), the selected tier position among 60 tiers, the token amount /
lamport input over orders of magnitude, and the FeeConfig account length.
Tier j charges protocol 50 + j bps so the TradeEvent shows which tier was used.
The per-series compute-unit range on each image and the per-case
original-minus-rebuild difference are reported in `series`.

Pump runs under the upgradeable loader (program account + programdata, the
mainnet layout). All account state is synthetic (IDL layouts), keys come from
fixed seeds, the clock is fixed, one fresh VM per case, no network. The full
initial account set of every case is written to runtime/plan.json.gz, so
verify.py replays without the repository.

Usage:
  python3 producer.py --root <repo> --images '{"original": "...", "candidate": "..."}' --out <packet dir>
"""
import argparse
import base64
import gzip
import hashlib
import json
import struct
from pathlib import Path

from solders.account import Account
from solders.clock import Clock
from solders.compute_budget import set_compute_unit_limit
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
FEE_PROGRAM = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
USER = Keypair.from_seed(bytes([231]) * 32)
CREATOR = Pubkey(bytes([60]) * 32)
MINT = Keypair.from_seed(bytes([61]) * 32).pubkey()
OTHER_MINT = Keypair.from_seed(bytes([62]) * 32).pubkey()
FEE_RECIPIENT = Pubkey(bytes([90]) * 32)
FEE_RECIPIENTS = [Pubkey(bytes([110 + i]) * 32) for i in range(7)]   # ascending: binary_search needs order
RESERVED = Pubkey(bytes([120]) * 32)
RESERVED_LIST = [Pubkey(bytes([121 + i]) * 32) for i in range(7)]
BUYBACK = [Pubkey(bytes([100 + i]) * 32) for i in range(8)]
STRANGER = Pubkey(bytes([200]) * 32)
BASE_TS = 1_800_000_000

DISC = {'Global': bytes([167, 232, 232, 177, 200, 108, 114, 127]),
        'BondingCurve': bytes([23, 183, 248, 55, 96, 216, 172, 96]),
        'GlobalVolumeAccumulator': bytes([202, 42, 246, 43, 142, 190, 30, 255]),
        'FeeConfig': bytes([143, 52, 146, 187, 219, 123, 76, 155])}
IX = {'buy': bytes([102, 6, 61, 18, 1, 218, 235, 234]),
      'buy_exact_sol_in': bytes([56, 252, 116, 8, 158, 223, 205, 95]),
      'sell': bytes([51, 230, 133, 164, 1, 127, 131, 173]),
      'buy_v2': bytes([184, 23, 238, 97, 103, 197, 211, 61]),
      'buy_exact_quote_in_v2': bytes([194, 171, 28, 70, 104, 77, 91, 47]),
      'sell_v2': bytes([93, 246, 130, 60, 231, 233, 64, 178])}
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')

pda = lambda seeds, program=PROGRAM: Pubkey.find_program_address(seeds, program)[0]
GLOBAL = pda([b'global'])
EVENT_AUTHORITY = pda([b'__event_authority'])
GVA = pda([b'global_volume_accumulator'])
UVA = pda([b'user_volume_accumulator', bytes(USER.pubkey())])
FEE_CONFIG = pda([b'fee_config', bytes(PROGRAM)], FEE_PROGRAM)


def ata(owner, mint):
    return pda([bytes(owner), bytes(TOKEN), bytes(mint)], ATA_PROGRAM)


V = {'vtr': 1_073_000_000_000_000, 'vqr': 30_000_000_000, 'rtr': 793_100_000_000_000,
     'rqr': 0, 'supply': 1_000_000_000_000_000}


def global_data(**kw):
    d = bytearray(1088)
    d[:8] = DISC['Global']
    d[8] = 1
    d[9:41] = bytes(Pubkey(bytes([91]) * 32))
    d[41:73] = bytes(FEE_RECIPIENT)
    struct.pack_into('<QQQQQ', d, 73, V['vtr'], V['vqr'], V['rtr'], V['supply'], 95)
    struct.pack_into('<Q', d, 154, 30)
    for i, k in enumerate(FEE_RECIPIENTS):
        d[162 + 32 * i:194 + 32 * i] = bytes(k)
    d[450] = 1
    d[451:483] = bytes(kw.get('whitelist', Pubkey(bytes([92]) * 32)))
    d[483:515] = bytes(RESERVED)
    d[515] = 1
    for i, k in enumerate(RESERVED_LIST):
        d[516 + 32 * i:548 + 32 * i] = bytes(k)
    for i, k in enumerate(BUYBACK):
        d[741 + 32 * i:773 + 32 * i] = bytes(k)
    struct.pack_into('<QQ', d, 997, kw.get('buyback_bps', 5000), V['vqr'])  # buyback_basis_points
    d[1045] = kw.get('creator_fee_configurable', 0)
    struct.pack_into('<Q', d, 1046, kw.get('max_creator_fee_bps', 0))
    return bytes(d)


def curve_data(mint=MINT, length=166, **kw):
    c = dict(V, complete=0, creator=CREATOR, mayhem=0, cashback=0, quote_mint=SYSTEM)
    c.update(kw)
    d = bytearray(166)
    d[:8] = DISC['BondingCurve']
    struct.pack_into('<QQQQQ', d, 8, c['vtr'], c['vqr'], c['rtr'], c['rqr'], c.get('tts', c['supply']))
    d[48] = c['complete']
    d[49:81] = bytes(c['creator'])
    d[81] = c['mayhem']
    d[82] = c['cashback']
    d[83:115] = bytes(c['quote_mint'])
    struct.pack_into('<Q', d, 115, c.get('creator_fee_bps', 0))
    struct.pack_into('<QQ', d, 125, c.get('creator_fee', 0), c.get('protocol_fees', 0))
    return bytes(d[:length])


def mint_data(supply=V['supply'], decimals=6):
    return struct.pack('<I32sQBBI32s', 0, bytes(32), supply, decimals, 1, 0, bytes(32))


def token_data(mint, owner, amount):
    return struct.pack('<32s32sQI32sBI8sQI32s', bytes(mint), bytes(owner), amount, 0, bytes(32), 1, 0,
                       bytes(8), 0, 0, bytes(32))


def gva_data():
    d = bytearray(8 + 24 + 32 + 480)
    d[:8] = DISC['GlobalVolumeAccumulator']
    struct.pack_into('<qqq', d, 8, BASE_TS - 86400, BASE_TS + 86400 * 30, 86400)
    return bytes(d)




IX.update({'buy_v3': bytes([7, 5, 29, 196, 245, 23, 101, 80]),
           'buy_exact_quote_in_v3': bytes([225, 247, 80, 30, 213, 179, 132, 136]),
           'sell_v3': bytes([28, 146, 222, 119, 38, 196, 105, 213])})
FEE_CONFIG_LEN = 2512  # get_fee_basis_points requires data_len >= 2512 (FeeConfigTooShort)
WHITELIST = USER.pubkey()


def fee_config_v3(bump, tiers=((0, 95, 30),), flat=(0, 95, 30), length=FEE_CONFIG_LEN, owner_disc=None):
    """FeeConfig: disc | bump | admin | flat_fees | fee_tiers vec<(u128 threshold, Fees)> | stable vec | exotic."""
    d = (owner_disc or DISC['FeeConfig']) + bytes([bump]) + bytes(Pubkey(bytes([93]) * 32)) + struct.pack('<QQQ', *flat)
    d += struct.pack('<I', len(tiers))
    for threshold, pb, cb in tiers:
        d += threshold.to_bytes(16, 'little') + struct.pack('<QQQ', 0, pb, cb)
    d += struct.pack('<I', 0) + struct.pack('<QQQ', 0, 0, 0)
    return d.ljust(length, b'\0')[:length] if length >= len(d) else d[:length]


def base_state(curve_kw=None, user_tokens=0, glob_kw=None, fee_kw=None, curve_lamports=None):
    curve_kw = curve_kw or {}
    curve = pda([b'bonding-curve', bytes(MINT)])
    rtr = curve_kw.get('rtr', V['rtr'])
    fc_bump = Pubkey.find_program_address([b'fee_config', bytes(PROGRAM)], FEE_PROGRAM)[1]
    fee_kw = dict(fee_kw or {})
    fee_owner = fee_kw.pop('owner', FEE_PROGRAM)
    glob_kw = dict(glob_kw or {})
    g = bytearray(global_data(**{k: v for k, v in glob_kw.items() if k != 'migration_fee'}))
    struct.pack_into('<Q', g, 146, glob_kw.get('migration_fee', 0))  # Global.pool_migration_fee
    return {
        GLOBAL: (10**9, PROGRAM, bytes(g)),
        MINT: (10**9, TOKEN, mint_data(curve_kw.get('supply', V['supply']))),
        OTHER_MINT: (10**9, TOKEN, mint_data()),
        WSOL: (10**9, TOKEN, mint_data(0, 9)),
        curve: (curve_lamports if curve_lamports is not None else RENT_166 + curve_kw.get('rqr', 0),
                PROGRAM, curve_data(**curve_kw)),
        ata(curve, MINT): (10**9, TOKEN, token_data(MINT, curve, curve_kw.get('curve_tokens', rtr))),
        ata(USER.pubkey(), MINT): (10**9, TOKEN, token_data(MINT, USER.pubkey(), user_tokens)),
        FEE_CONFIG: (10**9, fee_owner, fee_config_v3(fc_bump, **fee_kw)),
        USER.pubkey(): (10**13, SYSTEM, b''),
        BUYBACK[0]: (10**9, SYSTEM, b''),
        STRANGER: (10**9, SYSTEM, b''),
        pda([b'creator-vault', bytes(CREATOR)]): (890_880, SYSTEM, b''),
    }


RENT_166 = 2_046_240


def v3_metas(over=None):
    """IDL account order shared by buy_v3 / buy_exact_quote_in_v3 / sell_v3 (17 accounts, native-SOL curve)."""
    o = {'quote_mint': WSOL, 'buyback': BUYBACK[0], 'user_ata': ata(USER.pubkey(), MINT), 'fee_config': FEE_CONFIG,
         'base_token_program': TOKEN, 'quote_token_program': TOKEN, 'base_mint': MINT}
    o.update(over or {})
    curve = pda([b'bonding-curve', bytes(MINT)])
    w = lambda k: AccountMeta(k, False, True)
    r = lambda k: AccountMeta(k, False, False)
    quote_curve = pda([bytes(curve), bytes(o['quote_token_program']), bytes(o['quote_mint'])], ATA_PROGRAM)
    quote_user = pda([bytes(USER.pubkey()), bytes(o['quote_token_program']), bytes(o['quote_mint'])], ATA_PROGRAM)
    return [r(GLOBAL), r(o['base_mint']), r(o['quote_mint']), r(o['base_token_program']), r(o['quote_token_program']),
            w(curve), w(ata(curve, MINT)), w(quote_curve), AccountMeta(USER.pubkey(), True, True), w(o['user_ata']),
            w(quote_user), w(UVA), r(o['fee_config']), w(o['buyback']), r(SYSTEM), r(EVENT_AUTHORITY), r(PROGRAM)]


def ix_data(kind, a, b, tail=b''):
    return IX[kind] + struct.pack('<QQ', a, b) + tail


def case(name, kind, a, b, tail=None, state=None, metas=None, note=''):
    if tail is None:
        tail = b'' if kind == 'sell_v3' else b'\x00'
    st = state if state is not None else base_state()
    ms = metas if metas is not None else v3_metas()
    return {'case': name, 'instruction': kind, 'note': note, 'data_hex': ix_data(kind, a, b, tail).hex(),
            'metas': [[str(m.pubkey), m.is_signer, m.is_writable] for m in ms],
            'accounts': [[str(k), lam, str(owner), data.hex()] for k, (lam, owner, data) in
                         sorted(st.items(), key=lambda kv: str(kv[0]))]}


def curve_quote(amount, vqr=V['vqr'], vtr=V['vtr']):
    return amount * vqr // (vtr - amount) + 1


def ceil_fee(x, bps):
    return -(-x * bps // 10000)


def buy_total(amount, pb=95, cb=30, vqr=V['vqr'], vtr=V['vtr']):
    q = curve_quote(amount, vqr, vtr)
    return q + ceil_fee(q, pb) + ceil_fee(q, cb)


MCAP = V['vqr'] * V['supply'] // V['vtr']  # market cap used for tier selection at the default curve


POST_COMPLETE_EVENT = bytes.fromhex('6fb06d8b316cd5fb')
POST_FIELDS = ('timestamp', 'base_out', 'quote_in', 'fee_basis_points', 'fee', 'creator_fee_basis_points', 'creator_fee',
               'buyback_fee', 'pool_base_reserves_before', 'pool_quote_reserves_before', 'pool_base_reserves_after',
               'pool_quote_reserves_after')


def post_complete_events(receipt):
    out = []
    for e in receipt['events']:
        d = base64.b64decode(e)
        if d[:8] == POST_COMPLETE_EVENT and len(d) >= 8 + 128 + 96:
            out.append(dict(zip(POST_FIELDS, struct.unpack_from('<q11Q', d, 8 + 128))))
    return out


def mcap_of(vqr=V['vqr'], vtr=V['vtr'], supply=V['supply']):
    return vqr * supply // vtr


def tiers_select(n, k, mcap):
    """n ascending tiers whose thresholds put `mcap` inside tier k (gap >= mcap / (2k+1) on both sides).
    Tier j charges protocol 50 + j bps and creator 20 bps, so the event shows which tier was taken."""
    g = 2 * mcap // (2 * k + 1)
    return tuple((j * g, 50 + j, 20) for j in range(n))


def plan():
    S = base_state
    T = 10**12
    out = []
    add = lambda *a, **k: out.append(case(*a, **k))
    RICH = {'rqr': 10**11, 'rtr': V['rtr'] - 10**14, 'vtr': V['vtr'] - 10**14}
    m_buy = mcap_of()
    m_sell = mcap_of(vtr=RICH['vtr'])
    sell_state = lambda **fk: S(dict(RICH), user_tokens=10**14, fee_kw=fk or None)
    # 1. tier count n, market cap inside the LAST tier
    for n in (1, 2, 3, 4, 8, 16, 32, 60):
        add(f'tiers-last/buy_v3/n-{n}', 'buy_v3', T, 10**12, state=S(fee_kw={'tiers': tiers_select(n, n - 1, m_buy)}))
    for n in (1, 2, 3, 4, 8, 16, 32, 60):
        add(f'tiers-last/sell_v3/n-{n}', 'sell_v3', T, 0, state=sell_state(tiers=tiers_select(n, n - 1, m_sell)))
    # 2. 60 tiers, market cap inside tier k
    for k in (0, 1, 15, 30, 59):
        add(f'tiers-60/buy_v3/k-{k}', 'buy_v3', T, 10**12, state=S(fee_kw={'tiers': tiers_select(60, k, m_buy)}))
    for k in (0, 1, 15, 30, 59):
        add(f'tiers-60/sell_v3/k-{k}', 'sell_v3', T, 0, state=sell_state(tiers=tiers_select(60, k, m_sell)))
    # 3. amount sweeps on the default single tier
    for e in (0, 2, 4, 6, 8, 10, 12, 14):
        add(f'amount/buy_v3/1e{e}', 'buy_v3', 10**e, 10**13)
    for e in (0, 2, 4, 6, 8, 10, 12, 14):
        add(f'amount/sell_v3/1e{e}', 'sell_v3', 10**e, 0, state=sell_state())
    for e in (3, 5, 7, 9, 11):
        add(f'amount/buy_exact_quote_in_v3/1e{e}', 'buy_exact_quote_in_v3', 10**e, 1)
    # 3b. fee branches (single tier): which branch carries the buy_exact_quote_in_v3 CU offset
    for name, pb, cb in (('0-0', 0, 0), ('95-0', 95, 0), ('0-30', 0, 30), ('95-30', 95, 30)):
        tiers = ((0, pb, cb),)
        add(f'fee/buy_exact_quote_in_v3/{name}', 'buy_exact_quote_in_v3', 10**9, 1, state=S(fee_kw={'tiers': tiers}))
        add(f'fee/buy_v3/{name}', 'buy_v3', T, 10**13, state=S(fee_kw={'tiers': tiers}))
    # 4. FeeConfig account length (tail beyond the parsed vectors)
    for length in (2512, 4097, 10240):
        add(f'length/buy_v3/{length}', 'buy_v3', T, 10**12, state=S(fee_kw={'length': length}))
    return out


# ---- execution (verify.py carries an identical copy of everything below) ----

LOADERS = ('upgradeable',)
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')




def load_vm(image):
    """Pump under the upgradeable loader (program account + programdata, the mainnet layout).
    v3 reads FeeConfig as plain account data; no pump_fees program is loaded."""
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    elf = Path(image).read_bytes()
    programdata = Pubkey.find_program_address([bytes(PROGRAM)], UPGRADEABLE)[0]
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf,
                                        UPGRADEABLE, False))
    vm.set_account(PROGRAM, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    return vm


def run_case(vm, index, c):
    vm.expire_blockhash()
    vm.set_clock(Clock(1000 + index, 0, 0, 0, BASE_TS + index))
    keys = []
    for k, lam, owner, data in c['accounts']:
        key = Pubkey.from_string(k)
        keys.append(key)
        vm.set_account(key, Account(lam, bytes.fromhex(data), Pubkey.from_string(owner)))
    metas = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in c['metas']]
    ixs = [Instruction(PROGRAM, bytes.fromhex(c['data_hex']), metas)]
    for t in c.get('then', []):  # multi-instruction sequence: later trades in the same transaction
        ixs.append(Instruction(PROGRAM, bytes.fromhex(t['data_hex']),
                               [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in t['metas']]))
    if c.get('then'):
        ixs.insert(0, set_compute_unit_limit(600_000))
    payer = Keypair.from_seed(bytes([231]) * 32)
    tx = Transaction.new_signed_with_payer(ixs, payer.pubkey(), [payer], vm.latest_blockhash())
    result = vm.send_transaction(tx)
    failed = isinstance(result, FailedTransactionMetadata)
    meta = result.meta() if failed else result
    logs = list(meta.logs())
    ret = meta.return_data()
    after = {}
    for key in sorted(set(keys) | {m.pubkey for m in metas}, key=str):
        if key == PROGRAM:
            continue
        a = vm.get_account(key)
        if a is not None and not a.executable and (a.lamports or a.data):
            after[str(key)] = [a.lamports, str(a.owner), bytes(a.data).hex()]
    return {'case': c['case'], 'instruction': c['instruction'],
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'error': str(result.err()) if failed else None,
            'return_data_hex': bytes(ret.data).hex() if ret is not None else '',
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions'],
            'accounts_after': after, 'compute_units': meta.compute_units_consumed(), 'logs': logs}


def run_plan(image, loader, cases):
    assert loader in LOADERS
    return [run_case(load_vm(image), i, c) for i, c in enumerate(cases)]  # one fresh VM per case


BEHAVIOR = ('transaction_base64', 'error', 'return_data_hex', 'events',
            'inner_instructions', 'accounts_after')
SITE = 'Program log: AnchorError thrown in '


def classify_logs(original, candidate):
    if len(original) != len(candidate):
        return [{'kind': 'line-count', 'original': len(original), 'candidate': len(candidate)}]
    out = []
    for a, b in zip(original, candidate):
        if a == b:
            continue
        if a.startswith(SITE) and b.startswith(SITE) and a.split('. ', 1)[1:] == b.split('. ', 1)[1:]:
            out.append({'kind': 'anchor-error-site', 'original': a[len(SITE):].split('. ')[0],
                        'candidate': b[len(SITE):].split('. ')[0]})
        elif ' consumed ' in a and ' consumed ' in b:
            out.append({'kind': 'consumed', 'original': a, 'candidate': b})
        else:
            out.append({'kind': 'other', 'original': a, 'candidate': b})
    return out


def custom_code(error):
    if error and 'Custom(' in error:
        return int(error.split('Custom(', 1)[1].split(')', 1)[0])
    return error


def anchor_name(logs):
    for line in logs:
        if 'Error Code: ' in line:
            return line.split('Error Code: ', 1)[1].split('.', 1)[0]
    return None


# ---- report ----

TRADE_EVENT = bytes.fromhex('bddb7fd34ee661ee')


def trade_events(receipt):
    return [t for t in (trade_event(e) for e in receipt['events']) if t is not None]


def trade_event(e):
    if True:
        d = base64.b64decode(e)
        if d[:8] != TRADE_EVENT or len(d) < 266:
            return None
        o = 8 + 32
        sol, tokens, is_buy = struct.unpack_from('<QQB', d, o)
        vsr, vtr, rsr, rtr = struct.unpack_from('<QQQQ', d, o + 17 + 32 + 8)
        o += 17 + 32 + 8 + 32 + 32
        fee_bps, fee = struct.unpack_from('<QQ', d, o)
        creator_fee_bps, creator_fee = struct.unpack_from('<QQ', d, o + 16 + 32)
        return {'sol_amount': sol, 'token_amount': tokens, 'is_buy': bool(is_buy), 'fee_basis_points': fee_bps,
                'fee': fee, 'creator_fee_basis_points': creator_fee_bps, 'creator_fee': creator_fee,
                'virtual_sol_reserves': vsr, 'virtual_token_reserves': vtr, 'real_sol_reserves': rsr,
                'real_token_reserves': rtr}
    return None


def curve_after(receipt):
    a = receipt['accounts_after'].get(str(pda([b'bonding-curve', bytes(MINT)])))
    if a is None:
        return None
    d = bytes.fromhex(a[2])
    vtr, vqr, rtr, rqr, tts = struct.unpack_from('<QQQQQ', d, 8)
    cf, pf = struct.unpack_from('<QQ', d, 125)
    pbo, pqi = struct.unpack_from('<QQ', d, 150)
    return {'lamports': a[0], 'virtual_token_reserves': vtr, 'virtual_quote_reserves': vqr,
            'real_token_reserves': rtr, 'real_quote_reserves': rqr, 'token_total_supply': tts, 'complete': d[48],
            'creator_fee': cf, 'protocol_fees': pf, 'post_complete_base_out': pbo, 'post_complete_quote_in': pqi}


LABELS = {str(USER.pubkey()): 'user', str(FEE_RECIPIENT): 'fee_recipient', str(RESERVED): 'reserved_fee_recipient',
          str(FEE_RECIPIENTS[3]): 'fee_recipient_list_3', str(pda([b'bonding-curve', bytes(MINT)])): 'bonding_curve',
          str(pda([b'creator-vault', bytes(CREATOR)])): 'creator_vault',
          str(pda([b'creator-vault', bytes(SYSTEM)])): 'creator_vault_default', str(BUYBACK[0]): 'buyback_recipient',
          str(UVA): 'user_volume_accumulator'}


def lamport_deltas(c, receipt):
    before = {k: lam for k, lam, _, _ in c['accounts']}
    out = {}
    for k, v in receipt['accounts_after'].items():
        delta = v[0] - before.get(k, 0)
        if delta:
            out[LABELS.get(k, k)] = delta
    return dict(sorted(out.items()))


def summarize(cases, original, candidate):
    rows = []
    for c, ro, rc in zip(cases, original, candidate):
        rows.append({'case': c['case'], 'instruction': c['instruction'], 'note': c['note'],
                     'error_original': ro['error'], 'error_candidate': rc['error'],
                     'custom_code': custom_code(ro['error']),
                     'error_name': {'original': anchor_name(ro['logs']), 'candidate': anchor_name(rc['logs'])},
                     'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units'],
                                       'original_minus_candidate': ro['compute_units'] - rc['compute_units']},
                     'logs_equal': ro['logs'] == rc['logs'],
                     'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
                     'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]],
                     'trade_events': trade_events(ro), 'post_complete_events': post_complete_events(ro),
                     'curve_after': curve_after(ro),
                     'lamport_deltas': lamport_deltas(c, ro)})
    stops, deltas, kinds = {}, {}, {}
    for r in rows:
        stop = 'success' if r['error_original'] is None else (r['error_name']['original'] or str(r['custom_code']))
        stops[stop] = stops.get(stop, 0) + 1
        dk = f"{r['compute_units']['original_minus_candidate']}:{stop}"
        deltas[dk] = deltas.get(dk, 0) + 1
        kind = ','.join(sorted({d['kind'] for d in r['differing_log_lines']})) or 'none'
        kinds[kind] = kinds.get(kind, 0) + 1
    return {'case_count': len(rows),
            'behavior_mismatches': [r['case'] for r in rows if r['behavior_differences']],
            'compute_units_equal_cases': sum(r['compute_units']['original_minus_candidate'] == 0 for r in rows),
            'logs_equal_cases': sum(r['logs_equal'] for r in rows),
            'cases_by_stop': dict(sorted(stops.items())),
            'compute_unit_delta_by_stop': dict(sorted(deltas.items())),
            'log_difference_kinds': dict(sorted(kinds.items())),
            'series': series(rows), 'tier_model': tier_model(rows), 'cases': rows}


def series(rows):
    """Group cases by the first two name parts; CU range per image and the set of differences."""
    out = {}
    for r in rows:
        key = '/'.join(r['case'].split('/')[:2])
        s = out.setdefault(key, {'cases': 0, 'successes': 0, 'original_min': None, 'original_max': None,
                                 'candidate_min': None, 'candidate_max': None, 'differences': {}})
        cu = r['compute_units']
        s['cases'] += 1
        s['successes'] += r['error_original'] is None
        for img in ('original', 'candidate'):
            lo, hi = s[img + '_min'], s[img + '_max']
            s[img + '_min'] = cu[img] if lo is None else min(lo, cu[img])
            s[img + '_max'] = cu[img] if hi is None else max(hi, cu[img])
        d = str(cu['original_minus_candidate'])
        s['differences'][d] = s['differences'].get(d, 0) + 1
    for s in out.values():
        s['original_spread'] = s['original_max'] - s['original_min']
        s['candidate_spread'] = s['candidate_max'] - s['candidate_min']
    return out


def tier_model(rows):
    """Fit CU = base + per_tier * (n - 1) + per_skipped * (n - 1 - k) per handler and image from the
    tier cases (n tiers, market cap in tier k), then report every tier case's residual."""
    cu = {(r['case'], img): r['compute_units'][img] for r in rows for img in ('original', 'candidate')}
    out = {}
    for h in ('buy_v3', 'sell_v3'):
        for img in ('original', 'candidate'):
            base = cu[(f'tiers-last/{h}/n-1', img)]
            per_tier = cu[(f'tiers-last/{h}/n-2', img)] - base
            per_skipped = cu[(f'tiers-60/{h}/k-0', img)] - cu[(f'tiers-60/{h}/k-1', img)]
            residuals = {}
            for r in rows:
                parts = r['case'].split('/')
                if parts[1] != h or not parts[0].startswith('tiers'):
                    continue
                v = int(parts[2][2:])
                n, k = (v, v - 1) if parts[0] == 'tiers-last' else (60, v)
                residuals[r['case']] = cu[(r['case'], img)] - (base + per_tier * (n - 1) + per_skipped * (n - 1 - k))
            out[f'{h}/{img}'] = {'base': base, 'per_tier': per_tier, 'per_skipped_tier': per_skipped,
                                 'residuals': residuals, 'max_abs_residual': max(abs(v) for v in residuals.values())}
    return out


def write_gz(path, text):
    path.write_bytes(gzip.compress(text.encode(), mtime=0))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    images = json.loads(args.images)
    idl = json.loads((args.root / 'evidence/upstream/pump.json').read_text())
    assert idl['address'] == str(PROGRAM)
    for name, disc in IX.items():  # discriminators in this file must match the upstream IDL
        assert bytes(next(i['discriminator'] for i in idl['instructions'] if i['name'] == name)) == disc
    for a in idl['accounts']:
        if a['name'] in DISC:
            assert bytes(a['discriminator']) == DISC[a['name']]
    cases = plan()
    blobs = {n: Path(images[n]).read_bytes() for n in ('original', 'candidate')}
    runtime = args.out / 'runtime'
    runtime.mkdir(parents=True, exist_ok=True)
    for old in runtime.glob('*'):
        old.unlink()
    write_gz(runtime / 'plan.json.gz', json.dumps(cases, sort_keys=True, indent=0) + '\n')
    report = {'scope': 'Pump Main buy_v3 / buy_exact_quote_in_v3 / sell_v3 compute-unit scaling over FeeConfig tier count, '
                       'selected tier, amount and FeeConfig length on a native-SOL curve; FeeConfig read as account data '
                       '(no CPI); original vs rebuild under the upgradeable loader; synthetic state; no network.',
              'images': {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()},
              'image_bytes': {n: len(b) for n, b in blobs.items()},
              'image_bytes_difference_div_250': (len(blobs['original']) - len(blobs['candidate'])) / 250,
              'behavior_fields': list(BEHAVIOR), 'loaders': {}, 'receipts': {}}
    for loader in LOADERS:
        original = run_plan(images['original'], loader, cases)
        candidate = run_plan(images['candidate'], loader, cases)
        lines = []
        for ro, rc in zip(original, candidate):
            lines += [json.dumps({'loader': loader, 'image': 'original', **ro}, sort_keys=True, separators=(',', ':')),
                      json.dumps({'loader': loader, 'image': 'candidate', **rc}, sort_keys=True, separators=(',', ':'))]
        name = f'receipts-{loader}.jsonl.gz'
        write_gz(runtime / name, '\n'.join(lines) + '\n')
        report['receipts'][name] = {'count': len(lines),
                                    'sha256': hashlib.sha256((runtime / name).read_bytes()).hexdigest()}
        report['loaders'][loader] = summarize(cases, original, candidate)
    report['idl_sha256'] = hashlib.sha256((args.root / 'evidence/upstream/pump.json').read_bytes()).hexdigest()
    write_gz(runtime / 'report.json.gz', json.dumps(report, sort_keys=True, indent=1) + '\n')
    for loader, s in report['loaders'].items():
        print(loader, json.dumps({k: s[k] for k in ('case_count', 'behavior_mismatches', 'compute_units_equal_cases',
                                                    'logs_equal_cases', 'cases_by_stop', 'compute_unit_delta_by_stop',
                                                    'log_difference_kinds', 'series')}, indent=1))


if __name__ == '__main__':
    main()
