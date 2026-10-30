#!/usr/bin/env python3
"""Pump Fees claim_social_fee_pda_v2 with Token-2022 quote mints.

The merged research/pump-fees-social-claim-sequences-20261030 packet ran
claim_social_fee_pda_v2 with legacy SPL mints only (USDC, WSOL). This packet
runs the same handler with Token-2022 quote mints and token accounts that carry
extensions (TransferFeeConfig / TransferFeeAmount, NonTransferable,
DefaultAccountState, MemoTransfer, CpiGuard, ImmutableOwner), with missing
ATAs (create-if-missing branch), wrong-program pairings and frozen accounts.
Every case runs on ONE persistent LiteSVM per image (original vs rebuild).

The Token-2022, Associated Token Account and Memo programs are the LiteSVM
built-ins shipped with solders 0.27.1; only pump_fees is swapped.

usage: producer.py --root <repo> --images '{"original": p, "candidate": p}' --out <packet dir>
Deterministic: fixed key seeds, fixed clock values, no paths in the output.
"""
import argparse, base64, gzip, hashlib, json, pathlib, struct
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
SYSTEM = Pubkey.default()
GLOBAL, GLOBAL_BUMP = Pubkey.find_program_address([b'fee-program-global'], PROGRAM)
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
ATA_PROGRAM = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
MEMO = Pubkey.from_string('MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr')
COMPUTE_BUDGET = Pubkey.from_string('ComputeBudget111111111111111111111111111111')
NOW = 1700000000
SEEDS = {'AUTH': 223, 'OTHER': 224, 'PAYER': 225, 'THIRD': 226}
KP = {k: Keypair.from_seed(bytes([v]) * 32) for k, v in SEEDS.items()}
A, O, T = KP['AUTH'].pubkey(), KP['OTHER'].pubkey(), KP['THIRD'].pubkey()
ZERO = Pubkey.default()
USER = ('12345', 0)
RENT_165 = 2039280
F = 5000000  # tokens held by the social PDA ATA in most cases


def disc(name, kind='global'):
    return hashlib.sha256(f'{kind}:{name}'.encode()).digest()[:8]


GLOBAL_DISC = disc('FeeProgramGlobal', 'account')
SOCIAL_DISC = disc('SocialFeePda', 'account')
EVENT_DISC = disc('SocialFeePdaClaimed', 'event')
SOCIAL = Pubkey.find_program_address([b'social-fee-pda', USER[0].encode(), bytes([USER[1]])], PROGRAM)[0]

# ---- quote mints: name -> (address seed byte, token program, decimals, extension spec) ----
# ext spec keys: fee=(bps, max), nontransferable, default_frozen
MINTS = {
    'P22': (90, TOKEN22, 6, {}),                                 # Token-2022, no extensions
    'P22D0': (91, TOKEN22, 0, {}),                               # Token-2022, 0 decimals
    'TF100': (92, TOKEN22, 6, {'fee': (100, 5000)}),             # 1 %, max 5,000
    'TF0': (93, TOKEN22, 6, {'fee': (0, 0)}),                    # 0 bps
    'TF10000': (94, TOKEN22, 6, {'fee': (10000, 2**64 - 1)}),    # 100 %, no cap
    'TFMAX0': (95, TOKEN22, 6, {'fee': (500, 0)}),               # 5 %, max 0
    'TF1': (96, TOKEN22, 6, {'fee': (1, 2**64 - 1)}),            # 0.01 %, no cap (ceil rounding)
    'NT': (97, TOKEN22, 6, {'nontransferable': True}),
    'DF': (98, TOKEN22, 6, {'default_frozen': True}),
    'HOOK': (89, TOKEN22, 6, {'hook': True}),                     # TransferHook -> Memo program id
    'LEG': (99, TOKEN, 6, {}),                                   # legacy SPL mint for program-mismatch cases
}


def mint_key(mk):
    return Pubkey.from_bytes(bytes([MINTS[mk][0]]) * 32)


def tlv(t, body):
    return struct.pack('<HH', t, len(body)) + body


def mint_data(mk):
    _, prog, dec, ext = MINTS[mk]
    md = bytearray(82); md[36:44] = (10**15).to_bytes(8, 'little'); md[44] = dec; md[45] = 1
    if prog == TOKEN or not ext:
        return bytes(md)
    body = b''
    if 'fee' in ext:
        bps, mx = ext['fee']
        fee = (0).to_bytes(8, 'little') + mx.to_bytes(8, 'little') + bps.to_bytes(2, 'little')
        body += tlv(1, bytes(64) + (0).to_bytes(8, 'little') + fee + fee)  # TransferFeeConfig
    if ext.get('nontransferable'):
        body += tlv(9, b'')  # NonTransferable
    if ext.get('default_frozen'):
        body += tlv(6, bytes([2]))  # DefaultAccountState = Frozen
    if ext.get('hook'):
        body += tlv(14, bytes(32) + bytes(MEMO))  # TransferHook (authority none, program = Memo)
    return bytes(md) + bytes(165 - 82) + bytes([1]) + body


def ata(owner, mk, prog=None):
    p = prog or MINTS[mk][1]
    return Pubkey.find_program_address([bytes(owner), bytes(p), bytes(mint_key(mk))], ATA_PROGRAM)[0]


def token_data(mk, owner, amount, frozen=False, memo=False, cpi_guard=False, drop_fee_amount=False):
    _, prog, _, ext = MINTS[mk]
    td = bytearray(165)
    td[:32] = bytes(mint_key(mk)); td[32:64] = bytes(owner); td[64:72] = amount.to_bytes(8, 'little'); td[108] = 2 if frozen else 1
    if prog == TOKEN:
        return bytes(td)
    body = tlv(7, b'')  # ImmutableOwner (as the ATA program creates it)
    if 'fee' in ext and not drop_fee_amount:
        body += tlv(2, (0).to_bytes(8, 'little'))  # TransferFeeAmount
    if ext.get('nontransferable'):
        body += tlv(13, b'')  # NonTransferableAccount
    if ext.get('hook'):
        body += tlv(15, bytes([0]))  # TransferHookAccount (transferring = false)
    if memo:
        body += tlv(8, bytes([1]))  # MemoTransfer required
    if cpi_guard:
        body += tlv(11, bytes([1]))  # CpiGuard enabled
    return bytes(td) + bytes([2]) + body


def global_data(authority, flags=0, social_authority=None, rate=60):
    sa = social_authority if social_authority is not None else authority
    return GLOBAL_DISC + bytes([GLOBAL_BUMP]) + bytes(authority) + bytes([flags]) + bytes(sa) + rate.to_bytes(8, 'little') + bytes(256)


def decode_social(d):
    if len(d) < 14 or d[:8] != SOCIAL_DISC:
        return None
    n = struct.unpack_from('<I', d, 10)[0]
    o = 14 + n
    total, last, stable = struct.unpack_from('<QQQ', d, o + 1)
    return {'total_claimed': total, 'last_claimed': last, 'total_stable_claimed': stable}


def decode_event(line):
    raw = base64.b64decode(line.split('Program data: ', 1)[1])
    if raw[:8] != EVENT_DISC:
        return None
    o = 16
    n = struct.unpack_from('<I', raw, o)[0]; o += 4 + n + 1 + 96
    amount, claimable, lifetime, before, after = struct.unpack_from('<QQQQQ', raw, o); o += 40
    quote = str(Pubkey.from_bytes(raw[o:o + 32])); stable = struct.unpack_from('<Q', raw, o + 32)[0]
    return {'amount_claimed': amount, 'claimable_before': claimable, 'lifetime_claimed': lifetime,
            'recipient_balance_before': before, 'recipient_balance_after': after, 'quote_mint': quote, 'lifetime_stable_claimed': stable}


def m(key, signer, writable):
    return [str(key), signer, writable]


def create():
    arg = len(USER[0]).to_bytes(4, 'little') + USER[0].encode() + bytes([USER[1]])
    return {'data_hex': (disc('create_social_fee_pda') + arg).hex(),
            'accounts': [m(A, True, True), m(SOCIAL, False, True), m(SYSTEM, False, False),
                         m(GLOBAL, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}, ['AUTH']


def claim_v2(mk, recipient=None, token_program=None, authority='AUTH', auth_writable=False, src=None, dst=None, cb_ix=True):
    arg = len(USER[0]).to_bytes(4, 'little') + USER[0].encode() + bytes([USER[1]])
    r = recipient if recipient is not None else T
    tp = token_program or MINTS[mk][1]
    cb = {'program_id': str(COMPUTE_BUDGET), 'data_hex': (bytes([2]) + (1400000).to_bytes(4, 'little')).hex(), 'accounts': []}
    ix = {'data_hex': (disc('claim_social_fee_pda_v2') + arg).hex(),
          'accounts': [m(r, False, True), m(SOCIAL, False, True), m(mint_key(mk), False, True),
                       m(src or ata(SOCIAL, mk, tp), False, True), m(dst or ata(r, mk, tp), False, True),
                       m(tp, False, False), m(ATA_PROGRAM, False, False), m(GLOBAL, False, False),
                       m(KP[authority].pubkey(), True, auth_writable), m(SYSTEM, False, False), m(EVENT, False, False), m(PROGRAM, False, False)]}
    return ([cb, ix] if cb_ix else [ix]), [authority]


def deposit(mk, n):
    # Token-2022 TransferChecked from PAYER's token account into the social PDA ATA (fee applies on the way in)
    data = bytes([12]) + n.to_bytes(8, 'little') + bytes([MINTS[mk][2]])
    return {'program_id': str(MINTS[mk][1]), 'data_hex': data.hex(),
            'accounts': [m(ata(KP['PAYER'].pubkey(), mk), False, True), m(mint_key(mk), False, False), m(ata(SOCIAL, mk), False, True),
                         m(KP['PAYER'].pubkey(), True, False)]}, []


def tx(label, *ixs, at=None):
    signers = []
    for _, s in ixs:
        for x in s:
            if x not in signers:
                signers.append(x)
    flat = []
    for i, _ in ixs:
        flat += i if isinstance(i, list) else [i]
    out = {'label': label, 'instructions': flat, 'signers': signers}
    if at is not None:
        out['clock_unix'] = at
    return out


def acct(key, data, owner, lamports=10**9):
    return {'pubkey': str(key), 'lamports': lamports, 'owner': str(owner), 'data_hex': data.hex()}


def tok(owner, mk, amount, key=None, **kw):
    d = token_data(mk, owner, amount, **kw)
    return acct(key or ata(owner, mk), d, MINTS[mk][1], RENT_165 + 10**6)


def cases():
    out = []

    def S(name, mk, steps, src=F, dst=0, extra=(), watch=(), src_kw=None, dst_kw=None, rate=60):
        """mk's mint exists; social PDA ATA holds `src` (None = missing); THIRD's ATA holds `dst` (None = missing)."""
        initial = [acct(GLOBAL, global_data(A, rate=rate), PROGRAM)]
        mks = [mk] if isinstance(mk, str) else list(mk)
        w = [str(SOCIAL)]
        for k in mks:
            initial.append(acct(mint_key(k), mint_data(k), MINTS[k][1]))
            w += [str(ata(SOCIAL, k)), str(ata(T, k))]
        k0 = mks[0]
        if src is not None:
            initial.append(tok(SOCIAL, k0, src, **(src_kw or {})))
        if dst is not None:
            initial.append(tok(T, k0, dst, **(dst_kw or {})))
        initial += list(extra)
        w += [str(x) for x in watch]
        out.append({'name': name, 'family': name.split('-')[0], 'clock_unix': NOW, 'initial': initial,
                    'steps': [tx('create social PDA', create())] + steps, 'watch': w})

    # ---- b: Token-2022 base mint, no extensions ----
    S('b-t22-plain-claim', 'P22', [tx('v2 P22', claim_v2('P22')), tx('v2 P22 again +60', claim_v2('P22'), at=NOW + 60)])
    S('b-t22-zero-decimals', 'P22D0', [tx('v2 P22D0', claim_v2('P22D0'))])
    S('b-t22-amount-1', 'P22', [tx('v2 P22 1 token', claim_v2('P22'))], src=1)
    S('b-t22-amount-u64-max', 'P22', [tx('v2 P22 u64 max', claim_v2('P22'))], src=2**64 - 1)
    S('b-t22-empty', 'P22', [tx('v2 P22 empty', claim_v2('P22')), tx('v2 P22 empty again', claim_v2('P22'))], src=0)
    S('b-t22-recipient-holds-balance', 'P22', [tx('v2 P22 (recipient holds 777)', claim_v2('P22'))], dst=777)

    # ---- m: ATA presence / create-if-missing branch ----
    S('m-recipient-ata-missing-auth-readonly', 'P22', [tx('v2 P22, recipient ATA missing, authority read-only', claim_v2('P22'))], dst=None)
    S('m-recipient-ata-missing-auth-writable', 'P22', [tx('v2 P22, recipient ATA missing, authority writable', claim_v2('P22', auth_writable=True)),
                                                       tx('v2 P22 +60 (ATA now exists)', claim_v2('P22'), at=NOW + 60)], dst=None)
    S('m-recipient-ata-missing-tf-mint', 'TF100', [tx('v2 TF100, recipient ATA missing, authority writable', claim_v2('TF100', auth_writable=True))], dst=None)
    S('m-recipient-ata-missing-default-frozen', 'DF', [tx('v2 DF, recipient ATA missing, authority writable', claim_v2('DF', auth_writable=True))], dst=None)
    S('m-social-ata-missing', 'P22', [tx('v2 P22, social ATA missing', claim_v2('P22', auth_writable=True))], src=None)
    S('m-recipient-ata-noncanonical', 'P22', [tx('v2 P22, recipient slot = OTHER-owned ATA', claim_v2('P22', dst=ata(O, 'P22')))],
      extra=[tok(O, 'P22', 0)], watch=[ata(O, 'P22')])

    # ---- p: token program pairing ----
    S('p-legacy-mint-control', 'LEG', [tx('v2 LEG with SPL Token', claim_v2('LEG'))])
    S('p-t22-ata-owned-by-legacy', 'P22', [tx('v2 P22, social ATA account owned by SPL Token', claim_v2('P22'))], src=None,
      extra=[acct(ata(SOCIAL, 'P22'), token_data('P22', SOCIAL, F)[:165], TOKEN, RENT_165)])

    # ---- f: TransferFee mints ----
    S('f-fee-100bps-cap-5000', 'TF100', [tx('v2 TF100 5,000,000', claim_v2('TF100'))])
    S('f-fee-100bps-below-cap', 'TF100', [tx('v2 TF100 123,456', claim_v2('TF100'))], src=123456)
    S('f-fee-100bps-amount-1', 'TF100', [tx('v2 TF100 1 token', claim_v2('TF100'))], src=1)
    S('f-fee-100bps-amount-99', 'TF100', [tx('v2 TF100 99 tokens', claim_v2('TF100'))], src=99)
    S('f-fee-100bps-amount-101', 'TF100', [tx('v2 TF100 101 tokens', claim_v2('TF100'))], src=101)
    S('f-fee-0bps', 'TF0', [tx('v2 TF0', claim_v2('TF0'))])
    S('f-fee-10000bps', 'TF10000', [tx('v2 TF10000', claim_v2('TF10000'))])
    S('f-fee-max-0', 'TFMAX0', [tx('v2 TFMAX0', claim_v2('TFMAX0'))])
    S('f-fee-1bps-ceil', 'TF1', [tx('v2 TF1 10,001 tokens', claim_v2('TF1'))], src=10001)
    S('f-fee-recipient-holds-balance', 'TF100', [tx('v2 TF100 (recipient holds 1,000,000)', claim_v2('TF100'))], dst=1000000)
    S('f-fee-recipient-lacks-fee-amount-ext', 'TF100', [tx('v2 TF100, recipient ATA without TransferFeeAmount', claim_v2('TF100'))], dst_kw={'drop_fee_amount': True})
    S('f-fee-twice-lifetime', 'TF100', [tx('v2 TF100', claim_v2('TF100')),
                                        tx('deposit 2,000,000 into social ATA', deposit('TF100', 2000000)),
                                        tx('v2 TF100 +59', claim_v2('TF100'), at=NOW + 59), tx('v2 TF100 +60', claim_v2('TF100'), at=NOW + 60)],
      extra=[tok(KP['PAYER'].pubkey(), 'TF100', 10**7)], watch=[ata(KP['PAYER'].pubkey(), 'TF100')])
    S('f-fee-social-is-recipient', 'TF100', [tx('v2 TF100 recipient = social PDA', claim_v2('TF100', recipient=SOCIAL))], dst=None)

    # ---- x: other extensions / account states ----
    S('x-transfer-hook', 'HOOK', [tx('v2 HOOK (hook program not passed)', claim_v2('HOOK'))])
    S('x-nontransferable', 'NT', [tx('v2 NT', claim_v2('NT'))])
    S('x-default-frozen-existing-thawed-dst', 'DF', [tx('v2 DF (both ATAs initialized, unfrozen)', claim_v2('DF'))])
    S('x-recipient-frozen', 'P22', [tx('v2 P22 recipient frozen', claim_v2('P22'))], dst_kw={'frozen': True})
    S('x-source-frozen', 'P22', [tx('v2 P22 social ATA frozen', claim_v2('P22'))], src_kw={'frozen': True})
    S('x-recipient-memo-required', 'P22', [tx('v2 P22 recipient requires memo', claim_v2('P22'))], dst_kw={'memo': True})
    S('x-source-memo-required', 'P22', [tx('v2 P22 social ATA requires memo', claim_v2('P22'))], src_kw={'memo': True})
    S('x-source-cpi-guard', 'P22', [tx('v2 P22 social ATA has CpiGuard', claim_v2('P22'))], src_kw={'cpi_guard': True})
    S('x-recipient-cpi-guard', 'P22', [tx('v2 P22 recipient has CpiGuard', claim_v2('P22'))], dst_kw={'cpi_guard': True})

    # ---- s: sequences mixing mints on one social PDA ----
    S('s-t22-then-legacy-same-second', ['P22', 'LEG'], [tx('v2 P22', claim_v2('P22')), tx('v2 LEG same second', claim_v2('LEG')),
                                                        tx('v2 LEG +60', claim_v2('LEG'), at=NOW + 60)],
      extra=[tok(SOCIAL, 'LEG', 700000), tok(T, 'LEG', 0)])
    S('s-fee-then-plain-lifetime', ['TF100', 'P22'], [tx('v2 TF100', claim_v2('TF100')), tx('v2 P22 +60', claim_v2('P22'), at=NOW + 60)],
      extra=[tok(SOCIAL, 'P22', 3000000), tok(T, 'P22', 0)])
    S('s-failed-nontransferable-keeps-window', ['NT', 'P22'], [tx('v2 NT', claim_v2('NT')), tx('v2 P22 same second', claim_v2('P22'))],
      extra=[tok(SOCIAL, 'P22', 3000000), tok(T, 'P22', 0)])
    S('s-rate-zero-double-fee-claim', 'TF100', [tx('v2 TF100 + v2 TF100 in one tx', claim_v2('TF100'), claim_v2('TF100', cb_ix=False)),
                                                tx('deposit 1,000,000', deposit('TF100', 1000000)), tx('v2 TF100 same second (rate 0)', claim_v2('TF100'))],
      rate=0, extra=[tok(KP['PAYER'].pubkey(), 'TF100', 10**7)], watch=[ata(KP['PAYER'].pubkey(), 'TF100')])
    return out


def watched_keys(case):
    keys = [GLOBAL, SOCIAL, A, O, T, KP['PAYER'].pubkey()]
    return keys + [Pubkey.from_string(k) for k in case['watch'] if Pubkey.from_string(k) not in keys]


def snap(a):
    if a is None:
        return None
    d = bytes(a.data)
    s = {'lamports': a.lamports, 'owner': str(a.owner), 'len': len(d), 'sha256': hashlib.sha256(d).hexdigest()}
    if str(a.owner) in (str(TOKEN), str(TOKEN22)) and len(d) >= 165:
        s['token_amount'] = int.from_bytes(d[64:72], 'little')
        s['token_state'] = d[108]
        if len(d) > 165 and d[165] == 2:
            o = 166
            while o + 4 <= len(d):
                t, n = struct.unpack_from('<HH', d, o)
                if t == 2 and n == 8:
                    s['withheld'] = int.from_bytes(d[o + 4:o + 12], 'little')
                o += 4 + n
    if d[:8] == SOCIAL_DISC:
        s['decoded'] = decode_social(d)
    return s


def run_case(binary, case):
    vm = LiteSVM().with_transaction_history(0).with_log_bytes_limit(None)
    vm.add_program_from_file(PROGRAM, binary)
    for k in KP.values():
        vm.set_account(k.pubkey(), Account(10**12, b'', ZERO))
    vm.set_clock(Clock(1000, 0, 0, 0, case['clock_unix']))
    for a in case['initial']:
        vm.set_account(Pubkey.from_string(a['pubkey']), Account(a['lamports'], bytes.fromhex(a['data_hex']), Pubkey.from_string(a['owner'])))
    watched = watched_keys(case)
    results = []
    for st in case['steps']:
        if 'clock_unix' in st:
            vm.set_clock(Clock(1000, 0, 0, 0, st['clock_unix']))
        ixs = [Instruction(Pubkey.from_string(i.get('program_id', str(PROGRAM))), bytes.fromhex(i['data_hex']), [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in i['accounts']]) for i in st['instructions']]
        signers = [KP['PAYER']] + [KP[s] for s in st['signers'] if s != 'PAYER']
        r = vm.send_transaction(Transaction.new_signed_with_payer(ixs, KP['PAYER'].pubkey(), signers, vm.latest_blockhash()))
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        logs = meta.logs()
        rd = meta.return_data()
        cu = meta.compute_units_consumed
        events = [l for l in logs if l.startswith('Program data:')]
        results.append({
            'error': str(r.err()) if failed else None,
            'custom_error': next((l.split('Error Code: ')[1].split('.')[0] for l in logs if 'Error Code: ' in l), None),
            'error_number': next((int(l.split('Error Number: ')[1].split('.')[0]) for l in logs if 'Error Number: ' in l), None),
            'return_hex': bytes(rd.data).hex() if rd is not None and len(rd.data) else None,
            'events': events,
            'events_decoded': [decode_event(l) for l in events],
            'program_logs': [l for l in logs if l.startswith('Program log:')],
            'state': {str(k): snap(vm.get_account(k)) for k in watched},
            'compute_units': cu() if callable(cu) else cu,
        })
    final = {}
    for k in watched:
        a = vm.get_account(k)
        final[str(k)] = None if a is None else {'lamports': a.lamports, 'owner': str(a.owner), 'data_hex': bytes(a.data).hex()}
    return results, final


COMPARED = ['error', 'custom_error', 'error_number', 'return_hex', 'events', 'program_logs', 'state']


def outcome(s):
    return 'ok' if s['error'] is None else (s['custom_error'] or s['error'])


def produce(images, cases_list):
    shas = {n: hashlib.sha256(pathlib.Path(images[n]).read_bytes()).hexdigest() for n in ['original', 'candidate']}
    receipts, summary = [], []
    for c in cases_list:
        per = {n: run_case(images[n], c) for n in ['original', 'candidate']}
        step_rows = []
        for i, st in enumerate(c['steps']):
            o, k = per['original'][0][i], per['candidate'][0][i]
            step_rows.append({'label': st['label'], 'match': all(o[f] == k[f] for f in COMPARED), 'original': o, 'candidate': k})
        final_match = per['original'][1] == per['candidate'][1]
        receipts.append({'case': c, 'steps': step_rows, 'final_state': {n: per[n][1] for n in per}, 'final_match': final_match})
        summary.append({'name': c['name'], 'family': c['family'], 'steps': len(c['steps']),
                        'match': final_match and all(s['match'] for s in step_rows),
                        'outcomes': [outcome(s['original']) for s in step_rows],
                        'outcomes_candidate': [outcome(s['candidate']) for s in step_rows],
                        'cu_original': [s['original']['compute_units'] for s in step_rows],
                        'cu_candidate': [s['candidate']['compute_units'] for s in step_rows]})
    report = {'program_id': str(PROGRAM), 'signer_seeds': SEEDS, 'compared_fields': COMPARED,
              'social_fee_pda': {'user_id': USER[0], 'platform': USER[1], 'address': str(SOCIAL)},
              'mints': {k: {'address': str(mint_key(k)), 'token_program': str(v[1]), 'decimals': v[2], 'extensions': {e: list(x) if isinstance(x, tuple) else x for e, x in v[3].items()}} for k, v in MINTS.items()},
              'scope': 'Pump Fees claim_social_fee_pda_v2 with Token-2022 quote mints and extension-bearing token accounts on persistent LiteSVM state (Token-2022 / ATA / Memo = solders 0.27.1 LiteSVM built-ins); compared per step: error, custom error, return data, events, program logs, watched account lamports/owner/len/sha256/token fields/decoded PDA; final account lamports, owner and bytes. Compute units recorded and compared separately.',
              'image_sha256': shas, 'case_count': len(summary), 'step_count': sum(s['steps'] for s in summary),
              'mismatched_cases': [s['name'] for s in summary if not s['match']],
              'cu_mismatched_cases': [s['name'] for s in summary if s['cu_original'] != s['cu_candidate']], 'cases': summary}
    return receipts, report


def gz(b):
    return gzip.compress(b, compresslevel=9, mtime=0)


def check_idl(root):
    idl = json.loads((root / 'evidence/upstream/pump_fees.json').read_text())
    assert idl['address'] == str(PROGRAM)
    ixs = {i['name']: i for i in idl['instructions']}
    for n in ['create_social_fee_pda', 'claim_social_fee_pda_v2']:
        assert bytes(ixs[n]['discriminator']) == disc(n), n
    assert [(a['name'], a.get('signer', False), a.get('writable', False)) for a in ixs['claim_social_fee_pda_v2']['accounts']] == [
        ('recipient', False, True), ('social_fee_pda', False, True), ('quote_mint', False, True), ('associated_social_fee_pda', False, True),
        ('associated_recipient', False, True), ('quote_token_program', False, False), ('associated_token_program', False, False),
        ('fee_program_global', False, False), ('social_claim_authority', True, False), ('system_program', False, False),
        ('event_authority', False, False), ('program', False, False)]
    accs = {a['name']: bytes(a['discriminator']) for a in idl['accounts']}
    assert accs['SocialFeePda'] == SOCIAL_DISC and accs['FeeProgramGlobal'] == GLOBAL_DISC
    evs = {e['name']: bytes(e['discriminator']) for e in idl.get('events', [])}
    assert evs['SocialFeePdaClaimed'] == EVENT_DISC


def load_images(arg):
    arg = arg.strip()
    return json.loads(arg if arg.startswith('{') else pathlib.Path(arg).read_text())


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--images', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    images = load_images(a.images)
    check_idl(pathlib.Path(a.root))
    receipts, report = produce(images, cases())
    rt = pathlib.Path(a.out) / 'runtime'
    rt.mkdir(parents=True, exist_ok=True)
    (rt / 'receipts.jsonl.gz').write_bytes(gz(b''.join(json.dumps(r, sort_keys=True, separators=(',', ':')).encode() + b'\n' for r in receipts)))
    (rt / 'report.json.gz').write_bytes(gz(json.dumps(report, sort_keys=True, indent=1).encode() + b'\n'))
    print(json.dumps({'cases': report['case_count'], 'steps': report['step_count'], 'mismatched': report['mismatched_cases'], 'cu_mismatched': report['cu_mismatched_cases']}))


if __name__ == '__main__':
    main()
