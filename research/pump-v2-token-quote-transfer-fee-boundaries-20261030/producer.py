#!/usr/bin/env python3
"""Pump Main v2 trades on a token-quote curve, up to the pump_fees CPI, original vs rebuild.

On a curve whose `quote_mint` is an SPL Token or Token-2022 mint, `buy_v2`,
`buy_exact_quote_in_v2` and `sell_v2` admit six quote associated token accounts
(curve, user, creator vault, user volume accumulator, fee recipient, buyback
recipient; four of them may be created through the ATA program). Before the
fee CPI, `buy_v2` and `buy_exact_quote_in_v2` also read the Token-2022
TransferFeeConfig extension of the quote mint, choose the older or newer fee
by the current epoch, and apply it:

  buy_v2                 gross = pre_fee_amount(fee, quote)    (Token-2022 gross-up)
  buy_exact_quote_in_v2  available = input - fee(input)        (post-fee amount)

This packet measures that part: the TLV parser, the epoch choice, the fee
arithmetic boundaries (0 / 1 / 9,999 / 10,000 / 10,001 basis points, maximum
fee caps, u64 overflow) and quote-ATA admission.

pump_fees is not one of the two images, so the fee-program slot
(pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ) holds the image under test. Its
Anchor entry rejects the call, so a case that passes every pre-CPI check ends
with a deterministic error raised inside `invoke [2]` of the fee program
(`reached_fee_cpi`). No trade completes; every transaction is rolled back.

Programs are loaded under the upgradeable loader (program account + programdata,
the mainnet layout). Every transaction starts with SetComputeUnitLimit(1,400,000)
unless the case says otherwise, because up to four ATA-create CPIs exceed the
200,000 default. SPL Token, Token-2022 and the ATA program are LiteSVM's
built-in copies. All state is synthetic (IDL / SPL layouts), keys come from
fixed seeds, the clock is fixed per case and there is no network. The full
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
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
SYSTEM = Pubkey.default()
USER = Keypair.from_seed(bytes([231]) * 32)
CREATOR = Pubkey(bytes([60]) * 32)
MINT = Keypair.from_seed(bytes([61]) * 32).pubkey()       # base mint (SPL Token)
OTHER_MINT = Keypair.from_seed(bytes([62]) * 32).pubkey()
QUOTE22 = Keypair.from_seed(bytes([63]) * 32).pubkey()    # Token-2022 quote mint
QUOTE_SPL = Keypair.from_seed(bytes([64]) * 32).pubkey()  # SPL Token quote mint
FEE_RECIPIENT = Pubkey(bytes([90]) * 32)
FEE_RECIPIENTS = [Pubkey(bytes([110 + i]) * 32) for i in range(7)]
RESERVED = Pubkey(bytes([120]) * 32)
RESERVED_LIST = [Pubkey(bytes([121 + i]) * 32) for i in range(7)]
BUYBACK = [Pubkey(bytes([100 + i]) * 32) for i in range(8)]
STRANGER = Pubkey(bytes([200]) * 32)
BASE_TS = 1_800_000_000
CU_LIMIT = 1_400_000

DISC = {'Global': bytes([167, 232, 232, 177, 200, 108, 114, 127]),
        'BondingCurve': bytes([23, 183, 248, 55, 96, 216, 172, 96]),
        'GlobalVolumeAccumulator': bytes([202, 42, 246, 43, 142, 190, 30, 255]),
        'FeeConfig': bytes([143, 52, 146, 187, 219, 123, 76, 155])}
IX = {'buy_v2': bytes([184, 23, 238, 97, 103, 197, 211, 61]),
      'buy_exact_quote_in_v2': bytes([194, 171, 28, 70, 104, 77, 91, 47]),
      'sell_v2': bytes([93, 246, 130, 60, 231, 233, 64, 178])}

pda = lambda seeds, program=PROGRAM: Pubkey.find_program_address(seeds, program)[0]
GLOBAL = pda([b'global'])
EVENT_AUTHORITY = pda([b'__event_authority'])
GVA = pda([b'global_volume_accumulator'])
UVA = pda([b'user_volume_accumulator', bytes(USER.pubkey())])
FEE_CONFIG = pda([b'fee_config', bytes(PROGRAM)], FEE_PROGRAM)
CURVE = pda([b'bonding-curve', bytes(MINT)])
VAULT = pda([b'creator-vault', bytes(CREATOR)])
SHARING = pda([b'sharing-config', bytes(MINT)], FEE_PROGRAM)


def ata(owner, mint, program=TOKEN):
    return pda([bytes(owner), bytes(program), bytes(mint)], ATA_PROGRAM)


V = {'vtr': 1_073_000_000_000_000, 'vqr': 30_000_000_000, 'rtr': 793_100_000_000_000,
     'rqr': 0, 'supply': 1_000_000_000_000_000}


def global_data():
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
    d[451:483] = bytes(Pubkey(bytes([92]) * 32))
    d[483:515] = bytes(RESERVED)
    d[515] = 1
    for i, k in enumerate(RESERVED_LIST):
        d[516 + 32 * i:548 + 32 * i] = bytes(k)
    for i, k in enumerate(BUYBACK):
        d[741 + 32 * i:773 + 32 * i] = bytes(k)
    struct.pack_into('<QQ', d, 997, 5000, V['vqr'])
    return bytes(d)


def curve_data(quote_mint, **kw):
    c = dict(V, complete=0, creator=CREATOR, mayhem=0, cashback=0)
    c.update(kw)
    d = bytearray(166)
    d[:8] = DISC['BondingCurve']
    struct.pack_into('<QQQQQ', d, 8, c['vtr'], c['vqr'], c['rtr'], c['rqr'], c['supply'])
    d[48] = c['complete']
    d[49:81] = bytes(c['creator'])
    d[81] = c['mayhem']
    d[82] = c['cashback']
    d[83:115] = bytes(quote_mint)
    return bytes(d)


def mint_base(supply=V['supply'], decimals=6):
    return struct.pack('<I32sQBBI32s', 0, bytes(32), supply, decimals, 1, 0, bytes(32))


def fee(epoch=0, maximum=2**64 - 1, bps=0):
    return struct.pack('<QQH', epoch, maximum, bps)


def tfc_entry(older, newer, tag=1, length=108):
    body = bytes(Pubkey(bytes([94]) * 32)) + bytes(Pubkey(bytes([95]) * 32)) + struct.pack('<Q', 0) + older + newer
    body = (body + bytes(max(0, length - len(body))))[:length]
    return struct.pack('<HH', tag, length) + body


def mint22(entries=None, padding=b'', account_type=1, tail=b''):
    """Token-2022 mint: base(82) + zero padding to 165 + account type + TLV entries."""
    if entries is None:
        return mint_base()
    pad = (padding + bytes(83))[:83]
    return mint_base() + pad + bytes([account_type]) + b''.join(entries) + tail


def token_data(mint, owner, amount, extension=False):
    d = struct.pack('<32s32sQI32sBI8sQI32s', bytes(mint), bytes(owner), amount, 0, bytes(32), 1, 0,
                    bytes(8), 0, 0, bytes(32))
    if extension:  # Token-2022 account type + TransferFeeAmount extension
        d += bytes([2]) + struct.pack('<HHQ', 2, 8, 0)
    return d


def gva_data():
    d = bytearray(8 + 24 + 32 + 480)
    d[:8] = DISC['GlobalVolumeAccumulator']
    struct.pack_into('<qqq', d, 8, BASE_TS - 86400, BASE_TS + 86400 * 30, 86400)
    return bytes(d)


def fee_config_data(bump):
    fees = struct.pack('<QQQ', 0, 95, 30)
    return DISC['FeeConfig'] + bytes([bump]) + bytes(Pubkey(bytes([93]) * 32)) + fees + bytes(8) + fees


RENT_166 = 2_046_240
QUOTE_HOLDERS = {'curve': CURVE, 'user': USER.pubkey(), 'vault': VAULT, 'uva': UVA,
                 'fee_recipient': FEE_RECIPIENT, 'buyback': BUYBACK[0]}
DEFAULT_TF = [tfc_entry(fee(0, 2**64 - 1, 100), fee(0, 2**64 - 1, 100))]


def state(quote='t22', mint_data=None, curve_kw=None, missing=(), quote_accounts=None, user_tokens=10**12):
    """quote: 't22' (Token-2022 quote mint QUOTE22) or 'spl' (SPL Token quote mint QUOTE_SPL)."""
    q, prog = (QUOTE22, TOKEN22) if quote == 't22' else (QUOTE_SPL, TOKEN)
    fc_bump = Pubkey.find_program_address([b'fee_config', bytes(PROGRAM)], FEE_PROGRAM)[1]
    if mint_data is None:
        mint_data = mint22(DEFAULT_TF) if quote == 't22' else mint_base()
    st = {
        GLOBAL: (10**9, PROGRAM, global_data()),
        MINT: (10**9, TOKEN, mint_base()),
        OTHER_MINT: (10**9, TOKEN, mint_base()),
        q: (10**9, prog, mint_data),
        CURVE: (RENT_166, PROGRAM, curve_data(q, **(curve_kw or {}))),
        ata(CURVE, MINT): (10**9, TOKEN, token_data(MINT, CURVE, (curve_kw or {}).get('rtr', V['rtr']))),
        ata(USER.pubkey(), MINT): (10**9, TOKEN, token_data(MINT, USER.pubkey(), user_tokens)),
        GVA: (10**9, PROGRAM, gva_data()),
        FEE_CONFIG: (10**9, FEE_PROGRAM, fee_config_data(fc_bump)),
        USER.pubkey(): (10**13, SYSTEM, b''),
        FEE_RECIPIENT: (10**9, SYSTEM, b''),
        BUYBACK[0]: (10**9, SYSTEM, b''),
        STRANGER: (10**9, SYSTEM, b''),
    }
    for name, holder in QUOTE_HOLDERS.items():
        if name in missing:
            continue
        st[ata(holder, q, prog)] = (10**9, prog, token_data(q, holder, 10**15, prog == TOKEN22))
    for key, value in (quote_accounts or {}).items():
        st[key] = value
    return st


def v2_metas(kind, quote='t22', over=None):
    """IDL account order for buy_v2 / buy_exact_quote_in_v2 (27) and sell_v2 (26)."""
    q, prog = (QUOTE22, TOKEN22) if quote == 't22' else (QUOTE_SPL, TOKEN)
    o = {'quote_mint': q, 'quote_program': prog, 'fee_recipient': FEE_RECIPIENT, 'buyback': BUYBACK[0]}
    o.update(over or {})
    q, qp = o['quote_mint'], o['quote_program']
    qa = lambda holder: o.get('ata_' + holder, ata(QUOTE_HOLDERS.get(holder, o.get(holder)) if holder in
                                                   ('curve', 'user', 'vault', 'uva') else o[holder], q, qp))
    w = lambda k: AccountMeta(k, False, True)
    r = lambda k: AccountMeta(k, False, False)
    metas = [r(GLOBAL), r(MINT), r(q), r(TOKEN), r(qp), r(ATA_PROGRAM),
             w(o['fee_recipient']), w(qa('fee_recipient')), w(o['buyback']), w(qa('buyback')),
             w(CURVE), w(ata(CURVE, MINT)), w(qa('curve')), AccountMeta(USER.pubkey(), True, True),
             w(ata(USER.pubkey(), MINT)), w(qa('user')), w(VAULT), w(qa('vault')), r(SHARING)]
    if kind != 'sell_v2':
        metas.append(r(GVA))
    metas += [w(UVA), w(qa('uva')), r(FEE_CONFIG), r(FEE_PROGRAM), r(SYSTEM), r(EVENT_AUTHORITY), r(PROGRAM)]
    return metas


def case(name, kind, a, b, st=None, metas=None, quote='t22', epoch=0, cu_limit=CU_LIMIT, note=''):
    st = st if st is not None else state(quote)
    ms = metas if metas is not None else v2_metas(kind, quote)
    return {'case': f'{kind}/{name}', 'instruction': kind, 'note': note, 'epoch': epoch, 'cu_limit': cu_limit,
            'data_hex': (IX[kind] + struct.pack('<QQ', a, b)).hex(),
            'metas': [[str(m.pubkey), m.is_signer, m.is_writable] for m in ms],
            'accounts': [[str(k), lam, str(owner), data.hex()] for k, (lam, owner, data) in
                         sorted(st.items(), key=lambda kv: str(kv[0]))]}


def tf(older_bps, newer_bps=None, older_max=2**64 - 1, newer_max=None, newer_epoch=0):
    newer_bps = older_bps if newer_bps is None else newer_bps
    newer_max = older_max if newer_max is None else newer_max
    return state(mint_data=mint22([tfc_entry(fee(0, older_max, older_bps), fee(newer_epoch, newer_max, newer_bps))]))


def plan():
    out = []
    big = 2**64 - 1
    amt = 10**9                      # buy_v2 token amount; quote = 27,960 on the default curve
    # A curve where a 5e14-token buy costs about 4.0e18 quote units (near u64).
    hi = {'vqr': 2**62, 'rtr': V['rtr']}
    hi_amt = 5 * 10**14
    b = lambda name, st=None, a=amt, lim=big, **kw: case(name, 'buy_v2', a, lim, st, **kw)
    x = lambda name, st=None, a=10**6, lim=1, **kw: case(name, 'buy_exact_quote_in_v2', a, lim, st, **kw)
    s = lambda name, st=None, a=10**9, lim=0, **kw: case(name, 'sell_v2', a, lim, st, **kw)
    t22 = lambda entries, **kw: state(mint_data=mint22(entries, **kw))
    out += [
        # --- buy_v2: TransferFeeConfig parser (Token-2022 quote mint) ---
        b('t22-no-extensions-82-bytes', state(mint_data=mint22(None)), note='mint of 82 bytes: no fee'),
        b('t22-transfer-fee-100bps', note='default fixture'),
        b('t22-account-type-only-166-bytes', t22([]), note='parser requires >= 167 bytes'),
        b('t22-account-type-and-1-byte', t22([], tail=b'\x00'), note='167 bytes, rest < 2'),
        b('t22-terminator-before-config', t22([b'\x00\x00\x00\x00'] + DEFAULT_TF), note='tag 0 ends parsing'),
        b('t22-other-extension-then-config', t22([struct.pack('<HH', 18, 64) + bytes(64)] + DEFAULT_TF),
          note='MetadataPointer (tag 18) before TransferFeeConfig'),
        b('t22-config-length-107', t22([tfc_entry(fee(bps=100), fee(bps=100), length=107)])),
        b('t22-config-length-109', t22([tfc_entry(fee(bps=100), fee(bps=100), length=109)])),
        b('t22-config-duplicated', t22(DEFAULT_TF + DEFAULT_TF)),
        b('t22-entry-length-past-end', t22([struct.pack('<HH', 18, 200) + bytes(64)])),
        b('t22-trailing-3-bytes', t22(DEFAULT_TF, tail=b'\x12\x00\x00')),
        b('t22-trailing-1-byte', t22(DEFAULT_TF, tail=b'\x12')),
        b('t22-nonzero-padding', t22(DEFAULT_TF, padding=b'\x01')),
        b('t22-account-type-2', t22(DEFAULT_TF, account_type=2)),
        b('t22-tag-0-only-entry', t22([b'\x00\x00\x00\x00'])),
        # --- buy_v2: epoch choice (older fee 100 bps valid, newer fee 10,001 bps would fail) ---
        b('epoch-4-newer-at-5', tf(100, 10001, newer_epoch=5), epoch=4, note='older fee applies'),
        b('epoch-5-newer-at-5', tf(100, 10001, newer_epoch=5), epoch=5, note='newer fee applies'),
        b('epoch-6-newer-at-5', tf(100, 10001, newer_epoch=5), epoch=6),
        b('epoch-0-newer-at-u64-max', tf(10001, 100, newer_epoch=2**64 - 1), epoch=0, note='older 10,001 bps'),
        # --- buy_v2: pre_fee_amount (gross-up) boundaries ---
        b('bps-0', tf(0)),
        b('bps-1', tf(1)),
        b('bps-9999', tf(9999)),
        b('bps-10000-max-fee-0', tf(10000, older_max=0), note='gross = quote + max fee'),
        b('bps-10000-max-fee-u64', tf(10000), note='quote + u64::MAX overflows'),
        b('bps-10001', tf(10001), note='10,000 - bps underflows'),
        b('bps-65535', tf(65535)),
        b('bps-65535-max-fee-0', tf(65535, older_max=0), note='the cap is applied after 10,000 - bps'),
        b('bps-100-max-fee-0', tf(100, older_max=0)),
        b('bps-100-max-fee-1', tf(100, older_max=1)),
        b('near-u64-bps-5000', state(mint_data=tf(5000)[QUOTE22][2], curve_kw=hi), a=hi_amt,
          note='quote ~4.0e18, gross ~8.0e18 fits u64'),
        b('near-u64-bps-9000-uncapped', state(mint_data=tf(9000)[QUOTE22][2], curve_kw=hi), a=hi_amt,
          note='gross ~4.0e19 > u64::MAX'),
        b('near-u64-bps-9000-max-fee-1', state(mint_data=tf(9000, older_max=1)[QUOTE22][2], curve_kw=hi), a=hi_amt,
          note='cap applies before the u64 conversion'),
        b('near-u64-bps-10000-max-fee-near-limit',
          state(mint_data=tf(10000, older_max=2**64 - 1 - 4 * 10**18)[QUOTE22][2], curve_kw=hi), a=hi_amt,
          note='quote + max fee near u64::MAX'),
        # --- buy_exact_quote_in_v2: post_fee_amount boundaries ---
        b('t22-create-4-atas', state(missing=('vault', 'uva', 'fee_recipient', 'buyback')),
          note='ATA program sizes Token-2022 accounts for a transfer-fee mint'),
        x('t22-transfer-fee-100bps'),
        x('input-1-bps-100', a=1, note='fee rounds up to 1, available 0'),
        x('input-2-bps-100', a=2),
        x('input-1-bps-0', tf(0), a=1),
        x('bps-10000-uncapped', tf(10000), note='fee = input, available 0'),
        x('bps-10000-max-fee-999999', tf(10000, older_max=999_999), note='available 1'),
        x('bps-10001', tf(10001), note='fee > input'),
        x('bps-65535-max-fee-0', tf(65535, older_max=0), note='cap 0 hides the invalid rate'),
        x('input-u64-max-bps-9999', tf(9999), a=2**64 - 1, note='input * bps fits u128'),
        x('t22-config-length-107', t22([tfc_entry(fee(bps=100), fee(bps=100), length=107)])),
        x('epoch-5-newer-at-5', tf(100, 10001, newer_epoch=5), epoch=5),
        # --- quote ATA admission (SPL Token quote mint) ---
        b('spl-all-atas-present', quote='spl'),
        b('spl-default-cu-limit-all-present', quote='spl', cu_limit=None),
        b('spl-create-4-atas', state('spl', missing=('vault', 'uva', 'fee_recipient', 'buyback')), quote='spl'),
        b('spl-create-4-atas-default-cu-limit', state('spl', missing=('vault', 'uva', 'fee_recipient', 'buyback')),
          quote='spl', cu_limit=None, note='200,000 CU default'),
        b('spl-create-vault-ata-only', state('spl', missing=('vault',)), quote='spl'),
        b('spl-curve-ata-missing', state('spl', missing=('curve',)), quote='spl', note='allow_create = false'),
        b('spl-user-ata-missing', state('spl', missing=('user',)), quote='spl'),
        b('spl-user-ata-wrong-mint', state('spl', quote_accounts={
            ata(USER.pubkey(), QUOTE_SPL): (10**9, TOKEN, token_data(OTHER_MINT, USER.pubkey(), 10**15))}), quote='spl'),
        b('spl-user-ata-wrong-owner', state('spl', quote_accounts={
            ata(USER.pubkey(), QUOTE_SPL): (10**9, TOKEN, token_data(QUOTE_SPL, STRANGER, 10**15))}), quote='spl'),
        b('spl-user-quote-account-non-ata', state('spl', quote_accounts={
            STRANGER: (10**9, TOKEN, token_data(QUOTE_SPL, USER.pubkey(), 10**15))}),
          metas=v2_metas('buy_v2', 'spl', {'ata_user': STRANGER}), quote='spl',
          note='user quote account is only owner/mint checked'),
        b('spl-curve-ata-wrong-mint', state('spl', quote_accounts={
            ata(CURVE, QUOTE_SPL): (10**9, TOKEN, token_data(OTHER_MINT, CURVE, 10**15))}), quote='spl'),
        b('spl-vault-ata-owned-by-token22', state('spl', quote_accounts={
            ata(VAULT, QUOTE_SPL): (10**9, TOKEN22, token_data(QUOTE_SPL, VAULT, 0))}), quote='spl'),
        b('spl-fee-recipient-ata-wrong-key', metas=v2_metas('buy_v2', 'spl', {'ata_fee_recipient': ata(STRANGER, QUOTE_SPL)}),
          quote='spl'),
        b('spl-uva-ata-wrong-key', metas=v2_metas('buy_v2', 'spl', {'ata_uva': ata(STRANGER, QUOTE_SPL)}), quote='spl'),
        b('spl-quote-program-token22', metas=v2_metas('buy_v2', 'spl', {'quote_program': TOKEN22}), quote='spl',
          note='SPL mint passed with the Token-2022 program'),
        b('spl-quote-mint-other', metas=v2_metas('buy_v2', 'spl', {'quote_mint': OTHER_MINT}), quote='spl'),
        b('spl-quote-mint-wsol', state('spl', quote_accounts={WSOL: (10**9, TOKEN, mint_base(0, 9))}),
          metas=v2_metas('buy_v2', 'spl', {'quote_mint': WSOL}), quote='spl'),
        b('spl-complete-and-curve-ata-missing', state('spl', curve_kw={'complete': 1}, missing=('curve',)), quote='spl',
          note='which check runs first'),
        b('spl-fee-recipient-stranger-and-ata-missing', state('spl', missing=('fee_recipient',)),
          metas=v2_metas('buy_v2', 'spl', {'fee_recipient': STRANGER}), quote='spl'),
        b('spl-buyback-stranger', metas=v2_metas('buy_v2', 'spl', {'buyback': STRANGER}), quote='spl'),
        x('spl-all-atas-present', quote='spl'),
        x('spl-create-4-atas', state('spl', missing=('vault', 'uva', 'fee_recipient', 'buyback')), quote='spl'),
        x('spl-curve-ata-missing', state('spl', missing=('curve',)), quote='spl'),
        x('spl-user-ata-wrong-owner', state('spl', quote_accounts={
            ata(USER.pubkey(), QUOTE_SPL): (10**9, TOKEN, token_data(QUOTE_SPL, STRANGER, 10**15))}), quote='spl'),
        # --- sell_v2: quote ATA admission (transfer fee is read only after the fee CPI) ---
        s('spl-all-atas-present', quote='spl'),
        s('spl-create-4-atas', state('spl', missing=('vault', 'uva', 'fee_recipient', 'buyback')), quote='spl'),
        s('spl-create-4-atas-default-cu-limit', state('spl', missing=('vault', 'uva', 'fee_recipient', 'buyback')),
          quote='spl', cu_limit=None),
        s('spl-curve-ata-missing', state('spl', missing=('curve',)), quote='spl'),
        s('spl-user-ata-wrong-mint', state('spl', quote_accounts={
            ata(USER.pubkey(), QUOTE_SPL): (10**9, TOKEN, token_data(OTHER_MINT, USER.pubkey(), 10**15))}), quote='spl'),
        s('spl-vault-ata-owned-by-token22', state('spl', quote_accounts={
            ata(VAULT, QUOTE_SPL): (10**9, TOKEN22, token_data(QUOTE_SPL, VAULT, 0))}), quote='spl'),
        s('t22-transfer-fee-10001bps', tf(10001), note='invalid rate is not read before the fee CPI'),
        s('t22-config-length-107', t22([tfc_entry(fee(bps=100), fee(bps=100), length=107)])),
    ]
    return out


# ---- execution (verify.py imports this from the packet copy) ----

LOADERS = ('upgradeable',)
UPGRADEABLE = Pubkey.from_string('BPFLoaderUpgradeab1e11111111111111111111111')


def load_vm(image):
    """Upgradeable loader: program account (36 bytes) + programdata, the mainnet layout.
    The fee-program slot gets the image under test too; it rejects the fee CPI deterministically."""
    vm = LiteSVM().with_transaction_history(0).with_sigverify(True)
    elf = Path(image).read_bytes()
    for key in (PROGRAM, FEE_PROGRAM):
        programdata = Pubkey.find_program_address([bytes(key)], UPGRADEABLE)[0]
        vm.set_account(programdata, Account(10**10, struct.pack('<IQB', 3, 0, 0) + bytes(32) + elf,
                                            UPGRADEABLE, False))
        vm.set_account(key, Account(10**9, struct.pack('<I', 2) + bytes(programdata), UPGRADEABLE, True))
    return vm


def run_case(vm, index, c):
    vm.expire_blockhash()
    vm.set_clock(Clock(1000 + index, BASE_TS, c['epoch'], c['epoch'], BASE_TS + index))
    keys = []
    for k, lam, owner, data in c['accounts']:
        key = Pubkey.from_string(k)
        keys.append(key)
        vm.set_account(key, Account(lam, bytes.fromhex(data), Pubkey.from_string(owner)))
    metas = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in c['metas']]
    payer = Keypair.from_seed(bytes([231]) * 32)
    ixs = [] if c['cu_limit'] is None else [set_compute_unit_limit(c['cu_limit'])]
    ixs.append(Instruction(PROGRAM, bytes.fromhex(c['data_hex']), metas))
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
        if a is not None and (a.lamports or a.data):
            after[str(key)] = [a.lamports, str(a.owner), hashlib.sha256(bytes(a.data)).hexdigest()]
    for key in set(keys) | {m.pubkey for m in metas}:  # reset so the next case starts from its own state only
        if key not in (PROGRAM, FEE_PROGRAM, TOKEN, TOKEN22, ATA_PROGRAM, SYSTEM):
            vm.set_account(key, Account(0, b'', SYSTEM))
    fee_invoke = f'Program {FEE_PROGRAM} invoke [2]'
    return {'case': c['case'], 'instruction': c['instruction'],
            'transaction_base64': base64.b64encode(bytes(tx)).decode(),
            'error': str(result.err()) if failed else None,
            'reached_fee_cpi': fee_invoke in logs,
            'ata_creates': sum(l == f'Program {ATA_PROGRAM} invoke [2]' for l in logs),
            'return_data_hex': bytes(ret.data).hex() if ret is not None else '',
            'events': [l[14:] for l in logs if l.startswith('Program data: ')],
            'inner_instructions': json.loads(meta.to_json())['inner_instructions'],
            'accounts_after': after, 'compute_units': meta.compute_units_consumed(), 'logs': logs}


def run_plan(image, loader, cases):
    assert loader == 'upgradeable'
    vm = load_vm(image)
    return [run_case(vm, i, c) for i, c in enumerate(cases)]


BEHAVIOR = ('transaction_base64', 'error', 'reached_fee_cpi', 'ata_creates', 'return_data_hex', 'events',
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


def anchor_site(logs):
    for line in logs:
        if line.startswith(SITE):
            return line[len(SITE):].split('. ')[0]
    return None


# ---- report ----

def summarize(cases, original, candidate):
    rows = []
    for c, ro, rc in zip(cases, original, candidate):
        rows.append({'case': c['case'], 'instruction': c['instruction'], 'note': c['note'],
                     'error_original': ro['error'], 'error_candidate': rc['error'],
                     'custom_code': custom_code(ro['error']),
                     'error_name': {'original': anchor_name(ro['logs']), 'candidate': anchor_name(rc['logs'])},
                     'error_site': {'original': anchor_site(ro['logs']), 'candidate': anchor_site(rc['logs'])},
                     'reached_fee_cpi': {'original': ro['reached_fee_cpi'], 'candidate': rc['reached_fee_cpi']},
                     'ata_creates': {'original': ro['ata_creates'], 'candidate': rc['ata_creates']},
                     'compute_units': {'original': ro['compute_units'], 'candidate': rc['compute_units'],
                                       'original_minus_candidate': ro['compute_units'] - rc['compute_units']},
                     'logs_equal': ro['logs'] == rc['logs'],
                     'differing_log_lines': classify_logs(ro['logs'], rc['logs']),
                     'behavior_differences': [k for k in BEHAVIOR if ro[k] != rc[k]]})
    stops, deltas, kinds = {}, {}, {}
    for r in rows:
        stop = 'fee-cpi' if r['reached_fee_cpi']['original'] else (r['error_name']['original'] or str(r['custom_code']))
        stops[stop] = stops.get(stop, 0) + 1
        dk = f"{r['compute_units']['original_minus_candidate']}:{stop}"
        deltas[dk] = deltas.get(dk, 0) + 1
        kind = ','.join(sorted({d['kind'] for d in r['differing_log_lines']})) or 'none'
        kinds[kind] = kinds.get(kind, 0) + 1
    return {'case_count': len(rows),
            'behavior_mismatches': [r['case'] for r in rows if r['behavior_differences']],
            'reached_fee_cpi_cases': [r['case'] for r in rows if r['reached_fee_cpi']['original']],
            'compute_units_equal_cases': sum(r['compute_units']['original_minus_candidate'] == 0 for r in rows),
            'logs_equal_cases': sum(r['logs_equal'] for r in rows),
            'cases_by_stop': dict(sorted(stops.items())),
            'compute_unit_delta_by_stop': dict(sorted(deltas.items())),
            'log_difference_kinds': dict(sorted(kinds.items())),
            'cases': rows}


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
        ix = next(i for i in idl['instructions'] if i['name'] == name)
        assert bytes(ix['discriminator']) == disc
        assert len(ix['accounts']) == len(v2_metas(name)), name
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
    report = {'scope': 'Pump Main buy_v2 / buy_exact_quote_in_v2 / sell_v2 on a token-quote curve '
                       '(Token-2022 TransferFeeConfig parsing, epoch choice, transfer-fee arithmetic, quote ATA '
                       'admission) up to the pump_fees CPI; original vs rebuild; upgradeable loader; '
                       'fee-program slot holds the image under test; synthetic state; no network.',
              'images': {n: hashlib.sha256(b).hexdigest() for n, b in blobs.items()},
              'image_bytes': {n: len(b) for n, b in blobs.items()},
              'cu_limit': CU_LIMIT, 'behavior_fields': list(BEHAVIOR), 'loaders': {}, 'receipts': {}}
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
                                                    'log_difference_kinds')}, indent=1))


if __name__ == '__main__':
    main()
