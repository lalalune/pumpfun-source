#!/usr/bin/env python3
"""Pump Main: compute-unit scaling of the trade handlers, original vs rebuild.

Each series runs one handler (legacy buy / sell / buy_exact_sol_in, native-SOL
buy_v2 / sell_v2) on otherwise identical state while one operand is swept over
orders of magnitude: the token amount, the lamport input, the curve reserve
magnitude (the amount * virtual_quote_reserves product leaves u64 for the
larger curves) and the fee basis points. Behavior is compared field by field;
the per-series compute-unit range on each image and the per-case
original-minus-rebuild difference are reported in `series`.

pump_fees is not one of the two images. Its slot holds a deterministic
9-instruction SBPFv0 program that this file generates (`fee_stub`): it ignores
its input and returns the case's `fee_bps` as the 24-byte `Fees` value through
sol_set_return_data. Both images see the identical stub.

Pump runs under the upgradeable loader (program account + programdata), the
mainnet layout. All account state is synthetic (IDL layouts), keys come from
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


def fee_config_data(bump):
    fees = struct.pack('<QQQ', 0, 95, 30)
    return DISC['FeeConfig'] + bytes([bump]) + bytes(Pubkey(bytes([93]) * 32)) + fees + bytes(8) + fees


RENT_166 = 2_046_240  # rent-exempt minimum for 166 bytes under LiteSVM's default Rent


def base_state(curve_kw=None, user_tokens=0, curve_lamports=None, curve_len=166, glob_kw=None):
    curve_kw = curve_kw or {}
    curve = pda([b'bonding-curve', bytes(MINT)])
    rtr = curve_kw.get('rtr', V['rtr'])
    fc_bump = Pubkey.find_program_address([b'fee_config', bytes(PROGRAM)], FEE_PROGRAM)[1]
    state = {
        GLOBAL: (10**9, PROGRAM, global_data(**(glob_kw or {}))),
        MINT: (10**9, TOKEN, mint_data(curve_kw.get('supply', V['supply']))),
        OTHER_MINT: (10**9, TOKEN, mint_data()),
        WSOL: (10**9, TOKEN, mint_data(0, 9)),
        curve: (curve_lamports if curve_lamports is not None else RENT_166 + curve_kw.get('rqr', 0),
                PROGRAM, curve_data(length=curve_len, **curve_kw)),
        ata(curve, MINT): (10**9, TOKEN, token_data(MINT, curve, rtr)),
        ata(USER.pubkey(), MINT): (10**9, TOKEN, token_data(MINT, USER.pubkey(), user_tokens)),
        ata(USER.pubkey(), OTHER_MINT): (10**9, TOKEN, token_data(OTHER_MINT, USER.pubkey(), user_tokens)),
        GVA: (10**9, PROGRAM, gva_data()),
        FEE_CONFIG: (10**9, FEE_PROGRAM, fee_config_data(fc_bump)),
        USER.pubkey(): (10**13, SYSTEM, b''),
        FEE_RECIPIENT: (10**9, SYSTEM, b''),
        RESERVED: (10**9, SYSTEM, b''),
        STRANGER: (10**9, SYSTEM, b''),
        BUYBACK[0]: (10**9, SYSTEM, b''),
        FEE_RECIPIENTS[3]: (10**9, SYSTEM, b''),
        RESERVED_LIST[2]: (10**9, SYSTEM, b''),
    }
    return state


def trade_metas(kind, over=None):
    """IDL account order for buy / buy_exact_sol_in (16) and sell (14), plus remaining accounts."""
    o = {'fee_recipient': FEE_RECIPIENT, 'mint': MINT, 'curve_mint': MINT, 'user_ata': ata(USER.pubkey(), MINT),
         'creator': CREATOR, 'fee_config': FEE_CONFIG, 'remaining': None}
    o.update(over or {})
    curve = pda([b'bonding-curve', bytes(o['curve_mint'])])
    curve_ata = o.get('curve_ata', ata(curve, o['mint']))
    w = lambda k: AccountMeta(k, False, True)
    r = lambda k: AccountMeta(k, False, False)
    vault = o.get('creator_vault', pda([b'creator-vault', bytes(o['creator'])]))
    head = [r(GLOBAL), w(o['fee_recipient']), r(o['mint']), w(curve), w(curve_ata), w(o['user_ata']),
            AccountMeta(USER.pubkey(), True, True), r(SYSTEM)]
    if kind == 'sell':
        metas = head + [w(vault), r(TOKEN), r(EVENT_AUTHORITY), r(PROGRAM), r(o['fee_config']), r(FEE_PROGRAM)]
    else:
        metas = head + [r(TOKEN), w(vault), r(EVENT_AUTHORITY), r(PROGRAM), r(GVA), w(UVA),
                        r(o['fee_config']), r(FEE_PROGRAM)]
    remaining = o['remaining']
    if remaining is None:
        remaining = [pda([b'bonding-curve-v2', bytes(o['curve_mint'])]), BUYBACK[0]]
    return metas + [w(k) for k in remaining]


def v2_metas(kind, over=None):
    """IDL account order for buy_v2 / buy_exact_quote_in_v2 (27) and sell_v2 (26); native-SOL curve (WSOL quote)."""
    o = {'fee_recipient': FEE_RECIPIENT, 'buyback': BUYBACK[0], 'quote_mint': WSOL,
         'user_ata': ata(USER.pubkey(), MINT), 'sharing_config': pda([b'sharing-config', bytes(MINT)], FEE_PROGRAM)}
    o.update(over or {})
    q = o['quote_mint']
    curve = pda([b'bonding-curve', bytes(MINT)])
    vault = pda([b'creator-vault', bytes(CREATOR)])
    w = lambda k: AccountMeta(k, False, True)
    r = lambda k: AccountMeta(k, False, False)
    metas = [r(GLOBAL), r(MINT), r(q), r(TOKEN), r(TOKEN), r(ATA_PROGRAM),
             w(o['fee_recipient']), w(ata(o['fee_recipient'], q)), w(o['buyback']), w(ata(o['buyback'], q)),
             w(curve), w(ata(curve, MINT)), w(ata(curve, q)), AccountMeta(USER.pubkey(), True, True),
             w(o['user_ata']), w(ata(USER.pubkey(), q)), w(vault), w(ata(vault, q)), r(o['sharing_config'])]
    if kind != 'sell_v2':
        metas.append(r(GVA))
    metas += [w(UVA), w(ata(UVA, q)), r(FEE_CONFIG), r(FEE_PROGRAM), r(SYSTEM), r(EVENT_AUTHORITY), r(PROGRAM)]
    return metas


def ix_data(kind, a, b, tail=b''):
    return IX[kind] + struct.pack('<QQ', a, b) + tail


def then(kind, a, b, tail=b'', metas=None):
    ms = metas if metas is not None else (v2_metas(kind) if kind.endswith('_v2') else trade_metas(kind))
    return {'instruction': kind, 'data_hex': ix_data(kind, a, b, tail).hex(),
            'metas': [[str(m.pubkey), m.is_signer, m.is_writable] for m in ms]}


def case(name, kind, a, b, tail=b'', state=None, metas=None, note='', fee=(0, 95, 30), seq=None):
    st = state if state is not None else base_state()
    ms = metas if metas is not None else trade_metas(kind)
    extra = {'then': seq} if seq else {}
    return {**extra,'case': name, 'instruction': kind, 'note': note, 'data_hex': ix_data(kind, a, b, tail).hex(),
            'fee_bps': list(fee),
            'metas': [[str(m.pubkey), m.is_signer, m.is_writable] for m in ms],
            'accounts': [[str(k), lam, str(owner), data.hex()] for k, (lam, owner, data) in
                         sorted(state_items(st), key=lambda kv: str(kv[0]))]}


def state_items(st):
    return list(st.items())


def buy_cost(amount, vqr=V['vqr'], vtr=V['vtr'], fee=(0, 95, 30)):
    """Total lamports the curve charges for `amount` tokens (pump formula, used only to place boundaries)."""
    sol = amount * vqr // (vtr - amount) + 1
    return sol + -(-sol * fee[1] // 10000) + -(-sol * fee[2] // 10000)


def sell_output(amount, vqr=V['vqr'], vtr=V['vtr'], fee=(0, 95, 30)):
    sol = amount * vqr // (vtr + amount)
    return sol - -(-sol * fee[1] // 10000) - -(-sol * fee[2] // 10000)


SELL_RQR = 10**10  # real quote reserves (lamports above rent) of the sell fixtures


def plan():
    """CU-scaling series: the same handler with one operand swept over magnitudes. Every series is
    a success path (or its natural end), so the CU difference isolates arithmetic cost."""
    out = []
    big = 10**15
    rtr = V['rtr']
    sb = 10**15                     # user token balance for the sell series
    sell_state = lambda **kw: base_state(user_tokens=sb, curve_kw=dict({'rqr': 10**12}, **kw))
    # 1. legacy buy: token amount 10^0 .. 10^14 (default 1.073e15 / 3e10 curve)
    for e in range(0, 15):
        if e in (1, 2, 3):
            continue
        out.append(case(f'amount/buy/1e{e}', 'buy', 10**e, big))
    # 2. legacy sell: token amount 10^0 .. 10^14
    for e in range(0, 15):
        if e in (1, 2, 3):
            continue
        out.append(case(f'amount/sell/1e{e}', 'sell', 10**e, 0, state=sell_state()))
    # 3. buy_exact_sol_in: spendable lamports 10^3 .. 10^11
    for e in (3, 5, 7, 9, 11):
        out.append(case(f'amount/buy_exact_sol_in/1e{e}', 'buy_exact_sol_in', 10**e, 1))
    # 4. native buy_v2 / sell_v2: token amount 10^0, 10^5, 10^10, 10^14
    for e in (0, 5, 10, 14):
        out.append(case(f'amount/buy_v2/1e{e}', 'buy_v2', 10**e, big, metas=v2_metas('buy_v2')))
    for e in (0, 5, 10, 14):
        out.append(case(f'amount/sell_v2/1e{e}', 'sell_v2', 10**e, 0, state=sell_state(),
                        metas=v2_metas('sell_v2')))
    # 4b. v2 fee branches on a 10^9-token trade: which transfer carries the v2 CU difference
    for name, fee in (('0-0-0', (0, 0, 0)), ('0-95-0', (0, 95, 0)), ('0-0-30', (0, 0, 30))):
        out.append(case(f'v2fee/buy_v2/{name}', 'buy_v2', 10**9, big, fee=fee, metas=v2_metas('buy_v2')))
        out.append(case(f'v2fee/sell_v2/{name}', 'sell_v2', 10**9, 0, fee=fee, state=sell_state(),
                        metas=v2_metas('sell_v2')))
    # 4c. creator vault already rent-exempt: ensure_rent_exempt does not transfer, the creator fee still moves
    vault = pda([b'creator-vault', bytes(CREATOR)])
    funded = lambda st: {**st, vault: (10**9, SYSTEM, b'')}
    out.append(case('v2fee/buy_v2/0-0-30-vault-funded', 'buy_v2', 10**9, big, fee=(0, 0, 30),
                    state=funded(base_state()), metas=v2_metas('buy_v2')))
    out.append(case('v2fee/sell_v2/0-0-30-vault-funded', 'sell_v2', 10**9, 0, fee=(0, 0, 30),
                    state=funded(sell_state()), metas=v2_metas('sell_v2')))
    out.append(case('v2fee/buy/0-0-30-vault-funded', 'buy', 10**9, big, fee=(0, 0, 30), state=funded(base_state())))
    # 5. reserve magnitude: vtr = 10^k, vqr = 3*10^(k-2), rtr = 0.739*vtr, buy 10^6 tokens
    #    (the a*vqr product leaves u64 for k >= 16)
    for k in (10, 12, 14, 16, 18):
        kw = {'vtr': 10**k, 'vqr': 3 * 10**(k - 2), 'rtr': 739 * 10**(k - 3), 'supply': 10**k}
        out.append(case(f'reserves/buy/vtr-1e{k}', 'buy', 10**6, big, state=base_state(kw)))
    for k in (10, 14, 18):
        kw = {'vtr': 10**k, 'vqr': 3 * 10**(k - 2), 'rtr': 739 * 10**(k - 3), 'supply': 10**k}
        out.append(case(f'reserves/sell/vtr-1e{k}', 'sell', 10**6, 0,
                        state=base_state(dict(kw, rqr=10**12), user_tokens=sb)))
    # 6. fee basis points on a fixed 10^9-token buy
    for name, fee in (('0-0-0', (0, 0, 0)), ('0-1-1', (0, 1, 1)), ('0-95-30', (0, 95, 30)),
                      ('0-9999-1', (0, 9999, 1)), ('0-10000-0', (0, 10000, 0)), ('0-2^31-1', (0, 2**31 - 1, 0))):
        out.append(case(f'fee/buy/{name}', 'buy', 10**9, big, fee=fee))
    return out


# ---- execution (verify.py carries an identical copy of everything below) ----

LOADERS = ('upgradeable',)
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')


# -- pump_fees test double --------------------------------------------------
# pump_fees is not one of the two images. Its slot holds a 9-instruction SBPFv0
# program generated below: it ignores its input and answers every call with the
# 24-byte Fees return value (lp_fee_bps, protocol_fee_bps, creator_fee_bps) of the
# case, via sol_set_return_data. Same bytes for both images.

def murmur3_32(data, seed=0):
    c1, c2 = 0xcc9e2d51, 0x1b873593
    h = seed
    n = len(data) // 4
    for i in range(n):
        k = struct.unpack_from('<I', data, i * 4)[0]
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
        h = ((h << 13) | (h >> 19)) & 0xffffffff
        h = (h * 5 + 0xe6546b64) & 0xffffffff
    tail = data[n * 4:]
    k = 0
    for i, b in enumerate(tail):
        k |= b << (8 * i)
    if tail:
        k = (k * c1) & 0xffffffff
        k = ((k << 15) | (k >> 17)) & 0xffffffff
        k = (k * c2) & 0xffffffff
        h ^= k
    h ^= len(data)
    h ^= h >> 16
    h = (h * 0x85ebca6b) & 0xffffffff
    h ^= h >> 13
    h = (h * 0xc2b2ae35) & 0xffffffff
    h ^= h >> 16
    return h


def insn(op, dst=0, src=0, off=0, imm=0):
    return struct.pack('<BBhi', op, dst | (src << 4), off, imm)


def fee_stub(lp_bps, protocol_bps, creator_bps):
    for v in (lp_bps, protocol_bps, creator_bps):
        assert 0 <= v < 2**31
    text = b''.join([
        insn(0x7a, 10, 0, -24, lp_bps),        # stdw [r10-24], lp
        insn(0x7a, 10, 0, -16, protocol_bps),  # stdw [r10-16], protocol
        insn(0x7a, 10, 0, -8, creator_bps),    # stdw [r10-8], creator
        insn(0xbf, 1, 10),                     # mov64 r1, r10
        insn(0x07, 1, 0, 0, -24),              # add64 r1, -24
        insn(0xb7, 2, 0, 0, 24),               # mov64 r2, 24
        insn(0x85, 0, 0, 0, -1),               # call sol_set_return_data (R_BPF_64_32)
        insn(0xb7, 0, 0, 0, 0),                # mov64 r0, 0
        insn(0x95),                            # exit
    ])
    return _elf(text, call_offset=6 * 8)


def _elf(text, call_offset):
    # Layout: ehdr | phdr(PT_DYNAMIC) | .text | .dynamic | .dynsym | .dynstr | .rel.dyn | .shstrtab | shdrs
    # Virtual addresses equal file offsets.
    shnames = [b'', b'.text', b'.dynamic', b'.dynsym', b'.dynstr', b'.rel.dyn', b'.shstrtab']
    shstr = b'\0'.join(shnames) + b'\0'
    name_off = [0]
    for n in shnames[1:]:
        name_off.append(name_off[-1] + len(shnames[len(name_off) - 1]) + 1)
    dynstr = b'\0sol_set_return_data\0'
    dynsym = bytes(24) + struct.pack('<IBBHQQ', 1, 0x10, 0, 0, 0, 0)
    text_off = 64 + 56
    dyn_off = text_off + len(text)
    ndyn = 7
    sym_off = dyn_off + 16 * ndyn
    str_off = sym_off + len(dynsym)
    rel_off = (str_off + len(dynstr) + 7) & ~7
    shs_off = rel_off + 16
    sh_off = (shs_off + len(shstr) + 7) & ~7
    rel = struct.pack('<QQ', text_off + call_offset, (1 << 32) | 10)
    dynamic = b''.join(struct.pack('<QQ', t, v) for t, v in [
        (17, rel_off), (18, 16), (19, 16), (6, sym_off), (5, str_off), (10, len(dynstr)), (0, 0)])
    ehdr = b'\x7fELF' + bytes([2, 1, 1, 0]) + bytes(8)
    ehdr += struct.pack('<HHIQQQIHHHHHH', 3, 247, 1, text_off, 64, sh_off, 0, 64, 56, 1, 64, 7, 6)
    phdr = struct.pack('<IIQQQQQQ', 2, 6, dyn_off, dyn_off, dyn_off, len(dynamic), len(dynamic), 8)
    body = ehdr + phdr + text + dynamic + dynsym + dynstr
    body += bytes(rel_off - len(body)) + rel + shstr
    body += bytes(sh_off - len(body))

    def sh(i, typ, flags, off, size, link=0, info=0, align=1, entsize=0):
        return struct.pack('<IIQQQQIIQQ', name_off[i], typ, flags, off, off, size, link, info, align, entsize)
    return body + bytes(64) + sh(1, 1, 6, text_off, len(text), align=8) \
        + sh(2, 6, 3, dyn_off, len(dynamic), link=4, align=8, entsize=16) \
        + sh(3, 11, 2, sym_off, len(dynsym), link=4, info=1, align=8, entsize=24) \
        + sh(4, 3, 2, str_off, len(dynstr)) \
        + sh(5, 9, 2, rel_off, 16, link=3, align=8, entsize=16) \
        + struct.pack('<IIQQQQIIQQ', name_off[6], 3, 0, 0, shs_off, len(shstr), 0, 0, 1, 0)



def load_vm(image, fee_bps):
    """Pump under the upgradeable loader (program account + programdata, the mainnet
    layout); the fee stub in the pump_fees slot."""
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    elf = Path(image).read_bytes()
    programdata = Pubkey.find_program_address([bytes(PROGRAM)], UPGRADEABLE)[0]
    vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf,
                                        UPGRADEABLE, False))
    vm.set_account(PROGRAM, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    vm.add_program(FEE_PROGRAM, fee_stub(*fee_bps))
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
        if key in (PROGRAM, FEE_PROGRAM):
            continue
        a = vm.get_account(key)
        if a is not None and not a.executable and (a.lamports or a.data):
            after[str(key)] = [a.lamports, str(a.owner), bytes(a.data).hex()]
    fee_invoke = f'Program {FEE_PROGRAM} invoke [2]'
    return {'case': c['case'], 'instruction': c['instruction'],
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'error': str(result.err()) if failed else None,
            'reached_fee_cpi': fee_invoke in logs,
            'fee_cpi_returned': f'Program return: {FEE_PROGRAM} ' in ' '.join(logs),
            'return_data_hex': bytes(ret.data).hex() if ret is not None else '',
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions'],
            'accounts_after': after, 'compute_units': meta.compute_units_consumed(), 'logs': logs}


def run_plan(image, loader, cases):
    assert loader in LOADERS
    # one fresh VM per case: each case carries its own fee stub answer
    return [run_case(load_vm(image, c['fee_bps']), i, c) for i, c in enumerate(cases)]


BEHAVIOR = ('transaction_base64', 'error', 'reached_fee_cpi', 'fee_cpi_returned', 'return_data_hex', 'events',
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
    return {'lamports': a[0], 'virtual_token_reserves': vtr, 'virtual_quote_reserves': vqr,
            'real_token_reserves': rtr, 'real_quote_reserves': rqr, 'token_total_supply': tts, 'complete': d[48]}


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
                     'reached_fee_cpi': {'original': ro['reached_fee_cpi'], 'candidate': rc['reached_fee_cpi']},
                     'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units'],
                                       'original_minus_candidate': ro['compute_units'] - rc['compute_units']},
                     'logs_equal': ro['logs'] == rc['logs'],
                     'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
                     'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]],
                     'fee_bps_returned_by_stub': c['fee_bps'],
                     'trade_events': trade_events(ro), 'curve_after': curve_after(ro),
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
            'reached_fee_cpi_cases': sum(r['reached_fee_cpi']['original'] for r in rows),
            'compute_units_equal_cases': sum(r['compute_units']['original_minus_candidate'] == 0 for r in rows),
            'logs_equal_cases': sum(r['logs_equal'] for r in rows),
            'cases_by_stop': dict(sorted(stops.items())),
            'compute_unit_delta_by_stop': dict(sorted(deltas.items())),
            'log_difference_kinds': dict(sorted(kinds.items())),
            'series': series(rows), 'cases': rows}


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
    report = {'scope': 'Pump Main trade-handler compute-unit scaling (legacy buy / sell / buy_exact_sol_in, native-SOL '
                       'buy_v2 / sell_v2) over token amount, lamport input, reserve magnitude and fee bps; original vs '
                       'rebuild under the upgradeable loader; the pump_fees slot holds a generated 9-instruction stub '
                       'that returns the case fee_bps; synthetic state; no network.',
              'fee_stub_sha256_default': hashlib.sha256(fee_stub(0, 95, 30)).hexdigest(),
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
