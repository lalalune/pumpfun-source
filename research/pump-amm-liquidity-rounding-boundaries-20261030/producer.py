#!/usr/bin/env python3
"""pump_amm single-hop deposit/withdraw ratio, rounding and error-path boundaries.

Each case builds a fresh LiteSVM with synthetic GlobalConfig / Pool / mint /
token accounts (no captured fixtures, no RPC), loads one pump_amm image and
LiteSVM's built-in SPL Token / Token-2022 programs, sends one deposit or
withdraw and records the error, compute units, full log list and the
post-state of every account the instruction touches.  The same case list is
run against the original and the rebuilt image.

Usage: producer.py --root <repo> --images '{"original": P, "candidate": P}' --out <dir>
"""
import argparse, gzip, hashlib, json, pathlib, re, struct
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
TOKEN = Pubkey.from_string('TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA')
TOKEN22 = Pubkey.from_string('TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb')
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
USER = Keypair.from_seed(bytes([201]) * 32)
CREATOR = Pubkey.from_bytes(bytes([11]) * 32)
BASE = Pubkey.from_bytes(bytes([21]) * 32)
QUOTE = Pubkey.from_bytes(bytes([22]) * 32)
LP = Pubkey.from_bytes(bytes([23]) * 32)
CONFIG = Pubkey.from_bytes(bytes([24]) * 32)
UBASE = Pubkey.from_bytes(bytes([31]) * 32)
UQUOTE = Pubkey.from_bytes(bytes([32]) * 32)
ULP = Pubkey.from_bytes(bytes([33]) * 32)
VBASE = Pubkey.from_bytes(bytes([34]) * 32)
VQUOTE = Pubkey.from_bytes(bytes([35]) * 32)
INDEX = 0
POOL, BUMP = Pubkey.find_program_address(
    [b'pool', INDEX.to_bytes(2, 'little'), bytes(CREATOR), bytes(BASE), bytes(QUOTE)], PROGRAM)
DISC = {'deposit': bytes.fromhex('f223c68952e1f2b6'), 'withdraw': bytes.fromhex('b712469c946da122')}
GLOBAL_DISC = bytes([149, 8, 156, 202, 160, 252, 176, 217])
POOL_DISC = bytes([241, 154, 109, 4, 17, 177, 109, 188])
MAX = 2**64 - 1
WATCH = {'pool': POOL, 'lp_mint': LP, 'user_base': UBASE, 'user_quote': UQUOTE, 'user_lp': ULP,
         'vault_base': VBASE, 'vault_quote': VQUOTE}


def mint(authority, supply, decimals):
    d = bytearray(82)
    struct.pack_into('<I', d, 0, 1); d[4:36] = bytes(authority)
    struct.pack_into('<Q', d, 36, supply); d[44] = decimals; d[45] = 1
    return bytes(d)


def token(m, owner, amount):
    d = bytearray(165); d[:32] = bytes(m); d[32:64] = bytes(owner)
    struct.pack_into('<Q', d, 64, amount); d[108] = 1
    return bytes(d)


def global_config(flags):
    d = bytearray(949); d[:8] = GLOBAL_DISC; d[8:40] = bytes([5]) * 32
    struct.pack_into('<QQ', d, 40, 20, 5); d[56] = flags
    return bytes(d)


def pool(lp_supply, vqr, pf, cf):
    d = bytearray(300); d[:8] = POOL_DISC; d[8] = BUMP
    struct.pack_into('<H', d, 9, INDEX)
    for off, k in [(11, CREATOR), (43, BASE), (75, QUOTE), (107, LP), (139, VBASE), (171, VQUOTE), (211, CREATOR)]:
        d[off:off + 32] = bytes(k)
    struct.pack_into('<Q', d, 203, lp_supply)
    d[245:261] = vqr.to_bytes(16, 'little', signed=True)
    struct.pack_into('<QQ', d, 271, pf, cf)
    return bytes(d)


# case defaults: reserves B/Q, pool lp_supply S, LP mint supply M, user LP balance L
DEFAULT = dict(B=10**12, Q=10**11, S=10**10, M=None, L=None, V=0, pf=0, cf=0, flags=0,
               ub=10**15, uq=10**15, base_limit=None, quote_limit=None)


def cases():
    out = []
    def c(name, ix, amount, **kw):
        p = dict(DEFAULT); p.update(kw); p['ix'] = ix; p['amount'] = amount; p['name'] = name
        if p['base_limit'] is None: p['base_limit'] = MAX if ix == 'deposit' else 0
        if p['quote_limit'] is None: p['quote_limit'] = MAX if ix == 'deposit' else 0
        out.append(p)
    # deposit: ceil rounding
    c('dep-exact-ratio', 'deposit', 10**6)
    c('dep-amount-1-ceil', 'deposit', 1)                         # 100 base, 10 quote exact
    c('dep-amount-1-ceil-up', 'deposit', 1, B=10**12 + 1, Q=10**11 + 1)  # 100.0..1 -> 101
    c('dep-small-pool-ceil', 'deposit', 1, B=3, Q=7, S=2)
    c('dep-amount-0', 'deposit', 0)
    c('dep-supply-1', 'deposit', 1, S=1, M=1, L=1)
    c('dep-double-supply', 'deposit', 10**10)
    c('dep-base-limit-exact', 'deposit', 3, B=10, Q=10, S=3, base_limit=10)
    c('dep-base-limit-minus-1', 'deposit', 3, B=10, Q=10, S=3, base_limit=9)
    c('dep-quote-limit-exact', 'deposit', 1, B=10, Q=10, S=3, quote_limit=4)
    c('dep-quote-limit-minus-1', 'deposit', 1, B=10, Q=10, S=3, quote_limit=3)
    c('dep-fees-excluded', 'deposit', 10**6, pf=10**10, cf=10**10, V=-2 * 10**10)
    c('dep-fees-eq-vault', 'deposit', 10**6, pf=6 * 10**10, cf=4 * 10**10, V=-10**11)
    c('dep-fees-exceed-vault', 'deposit', 10**6, pf=6 * 10**10, cf=4 * 10**10 + 1, V=-10**11 - 1)
    c('dep-fees-sum-overflow', 'deposit', 10**6, pf=MAX, cf=1)
    c('dep-supply-0', 'deposit', 1, S=0, M=0, L=0)
    c('dep-truncation-base', 'deposit', MAX, B=MAX, S=1, M=1, L=1)
    c('dep-truncation-quote', 'deposit', 2**33, B=1, Q=2**40, S=1, M=1, L=1)
    c('dep-boost-floor', 'deposit', 3, V=10**6 + 7)              # 3*(V+0)/S floor
    c('dep-boost-floor-zero', 'deposit', 1, V=9)
    c('dep-boost-with-fees', 'deposit', 10**6, V=5 * 10**9, pf=10**9, cf=10**9)
    c('dep-boost-negative-total', 'deposit', 10**6, V=-5)
    c('dep-boost-i128-large', 'deposit', 10**10, V=2**120)
    c('dep-lp-mint-to-overflow', 'deposit', MAX, V=2**127 - 1, B=1, Q=1, S=MAX, M=MAX, L=0)
    c('dep-disabled-flag2', 'deposit', 10**6, flags=2)
    c('dep-flag4-only', 'deposit', 10**6, flags=4)
    c('dep-flags-255', 'deposit', 10**6, flags=255)
    c('dep-user-base-insufficient', 'deposit', 10**6, ub=99999999)
    c('dep-user-quote-insufficient', 'deposit', 10**6, uq=9999999)
    c('dep-lp-supply-overflow', 'deposit', 1, S=MAX, M=0, L=0, B=1, Q=1)
    # withdraw: floor rounding
    c('wd-exact-ratio', 'withdraw', 10**6)
    c('wd-amount-1', 'withdraw', 1)
    c('wd-floor-down', 'withdraw', 1, B=10**12 - 1, Q=10**11 - 1)
    c('wd-small-pool-floor', 'withdraw', 1, B=3, Q=7, S=2, M=2, L=2)
    c('wd-amount-0', 'withdraw', 0)
    c('wd-all-supply', 'withdraw', 10**10, L=10**10)
    c('wd-base-limit-exact', 'withdraw', 1, B=10, Q=10, S=3, M=3, L=3, base_limit=3)
    c('wd-base-limit-plus-1', 'withdraw', 1, B=10, Q=10, S=3, M=3, L=3, base_limit=4)
    c('wd-quote-limit-exact', 'withdraw', 1, B=10, Q=10, S=3, M=3, L=3, quote_limit=3)
    c('wd-quote-limit-plus-1', 'withdraw', 1, B=10, Q=10, S=3, M=3, L=3, quote_limit=4)
    c('wd-seed-lock-mint-gt-pool', 'withdraw', 10**6, M=10**10 + 1)
    c('wd-pool-gt-mint', 'withdraw', 10**6, M=10**10 - 1)
    c('wd-amount-gt-supply', 'withdraw', 10**10 + 1, L=10**10, M=10**10)
    c('wd-amount-gt-user-lp', 'withdraw', 10**6, L=10**6 - 1)
    c('wd-fees-excluded', 'withdraw', 10**6, pf=10**10, cf=10**10, V=-2 * 10**10)
    c('wd-fees-exceed-vault', 'withdraw', 10**6, pf=10**11, cf=1, V=-10**11 - 1)
    c('wd-supply-0', 'withdraw', 0, S=0, M=0, L=0)
    c('wd-truncation-base', 'withdraw', 2, B=MAX, S=1, M=1, L=2)
    c('wd-boost-ceil', 'withdraw', 3, V=10**6 + 7)
    c('wd-boost-ceil-one', 'withdraw', 1, V=9)
    c('wd-boost-with-fees', 'withdraw', 10**6, V=5 * 10**9, pf=10**9, cf=10**9)
    c('wd-boost-negative-total', 'withdraw', 10**6, V=-5)
    c('wd-boost-change-truncation', 'withdraw', 10**10, V=2**70, L=10**10)
    c('wd-boost-negative-total-large', 'withdraw', 10**10, V=-(2**127) + 1, pf=MAX, cf=0, Q=MAX, L=10**10)
    c('wd-disabled-flag4', 'withdraw', 10**6, flags=4)
    c('wd-flag2-only', 'withdraw', 10**6, flags=2)
    c('wd-flags-255', 'withdraw', 10**6, flags=255)
    return out


def run_case(p, image):
    vm = LiteSVM().with_transaction_history(0)
    if isinstance(image, bytes):
        vm.add_program(PROGRAM, image)
    else:
        vm.add_program_from_file(PROGRAM, image)
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    vm.airdrop(USER.pubkey(), 10**12)
    vm.set_account(EVENT, Account(10**9, b'', Pubkey.default()))
    S = p['S']; M = S if p['M'] is None else p['M']; L = S // 2 if p['L'] is None else p['L']
    vm.set_account(CONFIG, Account(10**9, global_config(p['flags']), PROGRAM))
    vm.set_account(POOL, Account(10**9, pool(S, p['V'], p['pf'], p['cf']), PROGRAM))
    vm.set_account(BASE, Account(10**9, mint(CREATOR, 10**18, 6), TOKEN))
    vm.set_account(QUOTE, Account(10**9, mint(CREATOR, 10**18, 9), TOKEN))
    vm.set_account(LP, Account(10**9, mint(POOL, M, 9), TOKEN22))
    vm.set_account(UBASE, Account(10**9, token(BASE, USER.pubkey(), p['ub']), TOKEN))
    vm.set_account(UQUOTE, Account(10**9, token(QUOTE, USER.pubkey(), p['uq']), TOKEN))
    vm.set_account(ULP, Account(10**9, token(LP, USER.pubkey(), L), TOKEN22))
    vm.set_account(VBASE, Account(10**9, token(BASE, POOL, p['B']), TOKEN))
    vm.set_account(VQUOTE, Account(10**9, token(QUOTE, POOL, p['Q']), TOKEN))
    metas = [AccountMeta(k, s, w) for k, s, w in [
        (POOL, False, True), (CONFIG, False, False), (USER.pubkey(), True, False), (BASE, False, False),
        (QUOTE, False, False), (LP, False, True), (UBASE, False, True), (UQUOTE, False, True),
        (ULP, False, True), (VBASE, False, True), (VQUOTE, False, True), (TOKEN, False, False),
        (TOKEN22, False, False), (EVENT, False, False), (PROGRAM, False, False)]]
    data = DISC[p['ix']] + struct.pack('<QQQ', p['amount'], p['base_limit'], p['quote_limit'])
    tx = Transaction.new_signed_with_payer([Instruction(PROGRAM, data, metas)], USER.pubkey(), [USER],
                                           vm.latest_blockhash())
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    cu = meta.compute_units_consumed
    cu = cu() if callable(cu) else cu
    state = {}
    for role, k in WATCH.items():
        a = vm.get_account(k)
        state[role] = bytes(a.data).hex() if role in ('pool', 'lp_mint') else struct.unpack_from('<Q', bytes(a.data), 64)[0]
    return {'error': str(r.err()) if failed else None, 'cu': cu, 'logs': list(meta.logs()), 'state': state}


def anchor_code(logs):
    for line in logs:
        if 'Error Code: ' in line:
            return line.split('Error Code: ')[1].split('.')[0]
        if 'panicked' in line:
            return 'panic'
    return None


def program_logs(logs):
    """Full log list without the per-program 'consumed N of M compute units' lines."""
    out = []
    for line in logs:
        if 'consumed' in line and 'compute units' in line:
            continue
        out.append(line)
    return out


def observed(p, rec):
    """Token movements and pool fields after the instruction (original image)."""
    s = rec['state']; L = p['S'] // 2 if p['L'] is None else p['L']
    pd = bytes.fromhex(s['pool']); md = bytes.fromhex(s['lp_mint'])
    return {'base_to_pool': s['vault_base'] - p['B'], 'quote_to_pool': s['vault_quote'] - p['Q'],
            'user_lp_delta': s['user_lp'] - L,
            'pool_lp_supply': struct.unpack_from('<Q', pd, 203)[0],
            'lp_mint_supply': struct.unpack_from('<Q', md, 36)[0],
            'virtual_quote_reserves': str(int.from_bytes(pd[245:261], 'little', signed=True))}


PREFIX = b'programs/pump-amm/'


def strip_prefix(blob):
    """Control image: the original with every reference to a 'programs/pump-amm/src/*.rs' string
    moved 18 bytes later (past the prefix) and the matching length immediate lowered by 18,
    so its AnchorError file names read 'src/...' like the rebuild's. Nothing else changes."""
    b = bytearray(blob)
    secs = elf_sections(bytes(b))
    ro_off, ro_len = secs['.rodata']; tx_off, tx_len = secs['.text']
    starts = {}
    for m in re.finditer(re.escape(PREFIX) + rb'src/[A-Za-z0-9_/]+\.rs', bytes(b[ro_off:ro_off + ro_len])):
        starts[ro_off + m.start()] = len(m.group(0))  # sh_addr == sh_offset for .rodata here
    sites = 0
    for i in range(tx_off, tx_off + tx_len - 16, 8):
        if b[i] != 0x18:
            continue
        imm = struct.unpack_from('<I', b, i + 4)[0] | (struct.unpack_from('<I', b, i + 12)[0] << 32)
        if imm not in starts:
            continue
        n = starts[imm]
        for j in range(i + 16, i + 16 + 8 * 12, 8):
            if b[j] in (0x7a, 0x62, 0xb7, 0xb4) and struct.unpack_from('<i', b, j + 4)[0] == n:
                struct.pack_into('<i', b, j + 4, n - len(PREFIX))
                new = imm + len(PREFIX)
                struct.pack_into('<I', b, i + 4, new & 0xffffffff); struct.pack_into('<I', b, i + 12, new >> 32)
                sites += 1
                break
    return bytes(b), sites


def produce(images):
    stripped, _ = strip_prefix(pathlib.Path(images['original']).read_bytes())
    rows = []
    for p in cases():
        rec = {'case': p['name'], 'instruction': p['ix'],
               'params': {k: (str(v) if isinstance(v, int) and abs(v) >= 2**53 else v) for k, v in p.items() if k not in ('name', 'ix')}}
        for tag in ('original', 'candidate'):
            rec[tag] = run_case(p, images[tag])
        s = run_case(p, stripped)
        rec['stripped_original'] = {'cu': s['cu'], 'same_error_state_as_candidate': (s['error'], s['state']) == (rec['candidate']['error'], rec['candidate']['state']),
                                    'same_logs_as_candidate': s['logs'] == rec['candidate']['logs']}
        o, c = rec['original'], rec['candidate']
        rec['same_error'] = o['error'] == c['error']
        rec['same_state'] = o['state'] == c['state']
        rec['same_logs_ex_cu'] = program_logs(o['logs']) == program_logs(c['logs'])
        rec['same_logs'] = o['logs'] == c['logs']
        norm = lambda logs: [l.replace('thrown in programs/pump-amm/src/', 'thrown in src/') for l in program_logs(logs)]
        rec['same_logs_path_normalized'] = norm(o['logs']) == norm(c['logs'])
        rec['cu_delta'] = c['cu'] - o['cu']
        rec['anchor_error'] = {'original': anchor_code(o['logs']), 'candidate': anchor_code(c['logs'])}
        rec['error_site'] = {t: next((l.split('AnchorError thrown in ')[1].split('. Error Code')[0]
                                      for l in rec[t]['logs'] if 'AnchorError thrown in ' in l), None)
                             for t in ('original', 'candidate')}
        rec['observed'] = observed(p, o)
        rows.append(rec)
    return rows


def elf_sections(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    st = hs[shstrndx]; names = blob[st[4]:st[4] + st[5]]
    return {names[h[0]:names.index(b'\0', h[0])].decode(): (h[4], h[5]) for h in hs if h[0]}


def image_compare(images):
    """Section sizes and the count of differing 8-byte .text slots between the two images."""
    blobs = {k: pathlib.Path(v).read_bytes() for k, v in images.items()}
    secs = {k: elf_sections(b) for k, b in blobs.items()}
    out = {'sections': {k: {n: s[1] for n, s in sorted(v.items())} for k, v in secs.items()}}
    (oa, ol), (ca, cl) = secs['original']['.text'], secs['candidate']['.text']
    to, tc = blobs['original'][oa:oa + ol], blobs['candidate'][ca:ca + cl]
    slots = min(ol, cl) // 8
    out['text_slots'] = slots
    out['text_slots_differing'] = sum(to[i * 8:i * 8 + 8] != tc[i * 8:i * 8 + 8] for i in range(slots))
    out['path_prefix'] = {k: sum(blobs[k].count(p) for p in [b'programs/pump-amm/src/']) for k in blobs}
    return out


def sha_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    images = json.loads(a.images)
    rows = produce(images)
    out = pathlib.Path(a.out) / 'runtime'
    out.mkdir(parents=True, exist_ok=True)
    body = ''.join(json.dumps(r, sort_keys=True, separators=(',', ':')) + '\n' for r in rows).encode()
    (out / 'receipts.jsonl.gz').write_bytes(gzip.compress(body, mtime=0))
    summary = {
        'image_sha256': {k: sha_file(v) for k, v in images.items()},
        'case_count': len(rows),
        'behavior_match': sum(r['same_error'] and r['same_state'] for r in rows),
        'log_match_ex_cu': sum(r['same_logs_ex_cu'] for r in rows),
        'log_match_exact': sum(r['same_logs'] for r in rows),
        'log_match_path_normalized': sum(r['same_logs_path_normalized'] for r in rows),
        'cu_delta_histogram': {str(d): sum(r['cu_delta'] == d for r in rows) for d in sorted({r['cu_delta'] for r in rows})},
        'cu_equal': sum(r['cu_delta'] == 0 for r in rows),
        'cases': [{'case': r['case'], 'instruction': r['instruction'], 'error': r['original']['error'],
                   'anchor_error': r['anchor_error'], 'cu_original': r['original']['cu'],
                   'cu_candidate': r['candidate']['cu'], 'cu_delta': r['cu_delta'],
                   'same_error': r['same_error'], 'same_state': r['same_state'],
                   'same_logs_ex_cu': r['same_logs_ex_cu'], 'error_site': r['error_site'],
                   'observed': r['observed']} for r in rows],
        'receipts_sha256': hashlib.sha256(body).hexdigest(),
        'image_compare': image_compare(images),
        'stripped_original_control': {
            'sites_patched': strip_prefix(pathlib.Path(images['original']).read_bytes())[1],
            'sha256': hashlib.sha256(strip_prefix(pathlib.Path(images['original']).read_bytes())[0]).hexdigest(),
            'cu_equal_to_candidate': sum(r['stripped_original']['cu'] == r['candidate']['cu'] for r in rows),
            'logs_equal_to_candidate': sum(r['stripped_original']['same_logs_as_candidate'] for r in rows),
            'error_state_equal_to_candidate': sum(r['stripped_original']['same_error_state_as_candidate'] for r in rows),
            'cu_original_minus_stripped_histogram': {str(d): sum(r['original']['cu'] - r['stripped_original']['cu'] == d for r in rows)
                                                     for d in sorted({r['original']['cu'] - r['stripped_original']['cu'] for r in rows})},
        },
    }
    rep = json.dumps(summary, sort_keys=True, indent=1).encode()
    (out / 'report.json.gz').write_bytes(gzip.compress(rep, mtime=0))
    print(json.dumps({k: summary[k] for k in ('case_count', 'behavior_match', 'log_match_ex_cu', 'log_match_exact',
                                              'log_match_path_normalized', 'cu_equal', 'cu_delta_histogram',
                                              'stripped_original_control')}))


if __name__ == '__main__':
    main()
