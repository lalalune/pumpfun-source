#!/usr/bin/env python3
"""pump_amm create_pool: initial-liquidity integer_sqrt, minimum-liquidity boundary and
pre-transfer error paths, original vs rebuilt image.

Each case builds a fresh LiteSVM with a synthetic GlobalConfig and plain SPL Token mints /
token accounts (no captured fixtures, no RPC), loads one pump_amm image plus LiteSVM's
built-in SPL Token, Token-2022 and Associated Token programs, sends one create_pool and
records the error, compute units, full log list and the post-state of every account the
instruction creates or touches.  The creator is a plain keypair (non-canonical pool).

Usage: producer.py --root <repo> --images '{"original": P, "candidate": P}' --out <dir>
"""
import argparse, gzip, hashlib, json, math, pathlib, re, struct
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
ATA = Pubkey.from_string('ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL')
SYSTEM = Pubkey.default()
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
USER = Keypair.from_seed(bytes([202]) * 32)
BASE = Pubkey.from_bytes(bytes([21]) * 32)
QUOTE = Pubkey.from_bytes(bytes([22]) * 32)
CONFIG = Pubkey.from_bytes(bytes([24]) * 32)
UBASE = Pubkey.from_bytes(bytes([31]) * 32)
UQUOTE = Pubkey.from_bytes(bytes([32]) * 32)
INDEX = 7
DISC = hashlib.sha256(b'global:create_pool').digest()[:8]
GLOBAL_DISC = bytes([149, 8, 156, 202, 160, 252, 176, 217])
MAX = 2**64 - 1


def ata(owner, m, prog):
    return Pubkey.find_program_address([bytes(owner), bytes(prog), bytes(m)], ATA)[0]


def addresses(quote=QUOTE):
    pool = Pubkey.find_program_address(
        [b'pool', INDEX.to_bytes(2, 'little'), bytes(USER.pubkey()), bytes(BASE), bytes(quote)], PROGRAM)[0]
    lp = Pubkey.find_program_address([b'pool_lp_mint', bytes(pool)], PROGRAM)[0]
    return {'pool': pool, 'lp_mint': lp, 'user_lp': ata(USER.pubkey(), lp, TOKEN22),
            'vault_base': ata(pool, BASE, TOKEN), 'vault_quote': ata(pool, quote, TOKEN)}


def mint(supply, decimals):
    d = bytearray(82)
    struct.pack_into('<I', d, 0, 1); d[4:36] = bytes([9]) * 32
    struct.pack_into('<Q', d, 36, supply); d[44] = decimals; d[45] = 1
    return bytes(d)


def token(m, owner, amount):
    d = bytearray(165); d[:32] = bytes(m); d[32:64] = bytes(owner)
    struct.pack_into('<Q', d, 64, amount); d[108] = 1
    return bytes(d)


def global_config(flags, mayhem_enabled, cashback_enabled):
    d = bytearray(949); d[:8] = GLOBAL_DISC; d[8:40] = bytes([5]) * 32
    struct.pack_into('<QQ', d, 40, 20, 5); d[56] = flags
    d[417] = mayhem_enabled; d[642] = cashback_enabled
    return bytes(d)


DEFAULT = dict(ub=MAX, uq=MAX, flags=0, mayhem=0, cashback=None, creator_fee=None, can_edit=None,
               holder=None, gm=0, gc=0, same_mint=False, tail=None)


def cases():
    out = []
    def c(name, group, base, quote, **kw):
        p = dict(DEFAULT); p.update(kw); p.update(name=name, group=group, base=base, quote=quote)
        out.append(p)
    # 1. integer_sqrt over the product magnitude: base = quote = 10^k (exact squares)
    for k in range(2, 20):
        c(f'sq-10e{k}', 'sqrt-decade', 10**k, 10**k)
    # 2. asymmetric / non-square products, incl. the u64 x u64 maximum
    for name, b, q in [('max-max', MAX, MAX), ('max-1', MAX, 1), ('1-max', 1, MAX), ('max-2', MAX, 2),
                       ('2e32-2e32', 2**32, 2**32), ('2e32p1-2e32m1', 2**32 + 1, 2**32 - 1),
                       ('2e63-2e63', 2**63, 2**63), ('2e63-4', 2**63, 4),
                       ('1e18-3', 10**18, 3), ('pow2-odd-127', 2**63, 2**63 - 1)]:
        c(f'asym-{name}', 'sqrt-asym', b, q)
    # 3. minimum liquidity (100) boundary: liquidity = floor(sqrt(base*quote))
    for name, b, q in [('99-99', 99, 99), ('99-101', 99, 101), ('100-100', 100, 100), ('1-9999', 1, 9999),
                       ('1-10000', 1, 10000), ('1-10200', 1, 10200), ('100-101', 100, 101), ('101-101', 101, 101),
                       ('1-1', 1, 1), ('3-3334', 3, 3334), ('3-3333', 3, 3333)]:
        c(f'min-{name}', 'min-liquidity', b, q)
    # 4. pre-transfer checks and their order
    c('err-base-0', 'checks', 0, 10**6)
    c('err-quote-0', 'checks', 10**6, 0)
    c('err-both-0', 'checks', 0, 0)
    c('err-disabled-flag1', 'checks', 10**6, 10**6, flags=1)
    c('ok-flags-254', 'checks', 10**6, 10**6, flags=254)
    c('err-disabled-and-base-0', 'checks', 0, 10**6, flags=1)
    c('err-mayhem-disabled', 'checks', 10**6, 10**6, mayhem=1, gm=0)
    c('err-mayhem-noncanonical', 'checks', 10**6, 10**6, mayhem=1, gm=1)
    c('err-cashback-disabled', 'checks', 10**6, 10**6, cashback=1, gc=0)
    c('err-cashback-noncanonical', 'checks', 10**6, 10**6, cashback=1, gc=1)
    c('err-mayhem-before-disabled', 'checks', 0, 10**6, mayhem=1, flags=1)
    c('err-creator-fee-noncanonical', 'checks', 10**6, 10**6, cashback=0, creator_fee=1)
    c('err-can-edit-noncanonical', 'checks', 10**6, 10**6, cashback=0, creator_fee=0, can_edit=1)
    c('ok-holder-noncanonical', 'checks', 10**6, 10**6, cashback=0, creator_fee=0, can_edit=0, holder=1)
    c('ok-creator-fee-arg-only', 'checks', 10**6, 10**6, cashback=0, creator_fee=0)
    c('err-user-base-short', 'checks', 10**6, 10**6, ub=10**6 - 1)
    c('err-user-quote-short', 'checks', 10**6, 10**6, uq=10**6 - 1)
    c('ok-user-exact', 'checks', 10**6, 10**6, ub=10**6, uq=10**6)
    c('ok-legacy-args-only', 'checks', 10**6, 10**6, tail='none')
    c('err-optionbool-2', 'checks', 10**6, 10**6, tail='bad-bool')
    c('err-same-mint', 'checks', 10**6, 10**6, same_mint=True)
    return out


def ix_data(p):
    d = DISC + struct.pack('<HQQ', INDEX, p['base'], p['quote']) + bytes([3]) * 32 + bytes([p['mayhem']])
    if p['tail'] == 'none':
        return d
    if p['tail'] == 'bad-bool':
        return d + bytes([2])
    for k, fmt in (('cashback', 'B'), ('creator_fee', '<Q'), ('can_edit', 'B'), ('holder', 'B')):
        if p[k] is None:
            break
        d += struct.pack(fmt, p[k])
    return d


def run_case(p, image):
    vm = LiteSVM().with_transaction_history(0)
    if isinstance(image, bytes):
        vm.add_program(PROGRAM, image)
    else:
        vm.add_program_from_file(PROGRAM, image)
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    vm.airdrop(USER.pubkey(), 10**12)
    vm.set_account(EVENT, Account(10**9, b'', Pubkey.default()))
    vm.set_account(CONFIG, Account(10**9, global_config(p['flags'], p['gm'], p['gc']), PROGRAM))
    quote = BASE if p['same_mint'] else QUOTE
    vm.set_account(BASE, Account(10**9, mint(MAX, 6), TOKEN))
    vm.set_account(QUOTE, Account(10**9, mint(MAX, 9), TOKEN))
    vm.set_account(UBASE, Account(10**9, token(BASE, USER.pubkey(), p['ub']), TOKEN))
    vm.set_account(UQUOTE, Account(10**9, token(quote, USER.pubkey(), p['uq']), TOKEN))
    a = addresses(quote)
    metas = [AccountMeta(k, s, w) for k, s, w in [
        (a['pool'], False, True), (CONFIG, False, False), (USER.pubkey(), True, True), (BASE, False, False),
        (quote, False, False), (a['lp_mint'], False, True), (UBASE, False, True), (UQUOTE, False, True),
        (a['user_lp'], False, True), (a['vault_base'], False, True), (a['vault_quote'], False, True),
        (SYSTEM, False, False), (TOKEN22, False, False), (TOKEN, False, False), (TOKEN, False, False),
        (ATA, False, False), (EVENT, False, False), (PROGRAM, False, False)]]
    tx = Transaction.new_signed_with_payer([Instruction(PROGRAM, ix_data(p), metas)], USER.pubkey(), [USER],
                                           vm.latest_blockhash())
    r = vm.send_transaction(tx)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    cu = meta.compute_units_consumed
    cu = cu() if callable(cu) else cu
    state = {}
    for role, k in list(a.items()) + [('user_base', UBASE), ('user_quote', UQUOTE)]:
        acc = vm.get_account(k)
        if acc is None or len(bytes(acc.data)) == 0:
            state[role] = None
        elif role == 'pool':
            state[role] = bytes(acc.data).hex()
        elif role == 'lp_mint':
            state[role] = str(struct.unpack_from('<Q', bytes(acc.data), 36)[0])
        else:
            state[role] = str(struct.unpack_from('<Q', bytes(acc.data), 64)[0])
    state['payer_lamports'] = str(vm.get_account(USER.pubkey()).lamports)
    return {'error': str(r.err()) if failed else None, 'cu': cu, 'logs': list(meta.logs()), 'state': state}


def anchor_code(logs):
    for line in logs:
        if 'Error Code: ' in line:
            return line.split('Error Code: ')[1].split('.')[0]
        if 'panicked' in line:
            return 'panic'
    return None


def program_logs(logs):
    return [l for l in logs if not ('consumed' in l and 'compute units' in l)]


def expected(p):
    """Independent model of the successful path: lp_supply = isqrt(base*quote), user gets lp - 100."""
    liq = math.isqrt(p['base'] * p['quote'])
    return {'initial_liquidity': str(liq), 'lp_out': str(liq - 100) if liq >= 100 else None}


def observed(rec):
    s = rec['state']
    if s['pool'] is None:
        return None
    pd = bytes.fromhex(s['pool'])
    return {'pool_lp_supply': str(struct.unpack_from('<Q', pd, 203)[0]), 'lp_mint_supply': s['lp_mint'],
            'user_lp': s['user_lp'], 'vault_base': s['vault_base'], 'vault_quote': s['vault_quote'],
            'pool_len': len(pd)}


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
        starts[ro_off + m.start()] = len(m.group(0))
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


def elf_sections(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    st = hs[shstrndx]; names = blob[st[4]:st[4] + st[5]]
    return {names[h[0]:names.index(b'\0', h[0])].decode(): (h[4], h[5]) for h in hs if h[0]}


def produce(images):
    stripped, _ = strip_prefix(pathlib.Path(images['original']).read_bytes())
    rows = []
    for p in cases():
        rec = {'case': p['name'], 'group': p['group'], 'ix_data': ix_data(p).hex(),
               'params': {k: (str(v) if isinstance(v, int) and not isinstance(v, bool) and abs(v) >= 2**53 else v)
                          for k, v in p.items() if k not in ('name', 'group')}}
        for tag in ('original', 'candidate'):
            rec[tag] = run_case(p, images[tag])
        s = run_case(p, stripped)
        o, c = rec['original'], rec['candidate']
        rec['stripped_original'] = {'cu': s['cu'], 'same_error_state_as_candidate': (s['error'], s['state']) == (c['error'], c['state']),
                                    'same_logs_as_candidate': s['logs'] == c['logs']}
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
        rec['expected'] = expected(p)
        rec['observed'] = observed(o)
        rows.append(rec)
    return rows


def sha_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def summarize(images, rows, body):
    st = strip_prefix(pathlib.Path(images['original']).read_bytes())
    ok = [r for r in rows if r['original']['error'] is None]
    return {
        'image_sha256': {k: sha_file(v) for k, v in images.items()},
        'case_count': len(rows),
        'success_count': len(ok),
        'behavior_match': sum(r['same_error'] and r['same_state'] for r in rows),
        'log_match_ex_cu': sum(r['same_logs_ex_cu'] for r in rows),
        'log_match_exact': sum(r['same_logs'] for r in rows),
        'log_match_path_normalized': sum(r['same_logs_path_normalized'] for r in rows),
        'cu_delta_histogram': {str(d): sum(r['cu_delta'] == d for r in rows) for d in sorted({r['cu_delta'] for r in rows})},
        'cu_equal': sum(r['cu_delta'] == 0 for r in rows),
        'model_match_success': sum(r['observed']['pool_lp_supply'] == r['expected']['initial_liquidity']
                                   and r['observed']['user_lp'] == r['expected']['lp_out'] for r in ok),
        'cases': [{'case': r['case'], 'group': r['group'], 'error': r['original']['error'],
                   'anchor_error': r['anchor_error'], 'cu_original': r['original']['cu'],
                   'cu_candidate': r['candidate']['cu'], 'cu_delta': r['cu_delta'],
                   'same_error': r['same_error'], 'same_state': r['same_state'],
                   'same_logs_ex_cu': r['same_logs_ex_cu'], 'error_site': r['error_site'],
                   'expected': r['expected'], 'observed': r['observed']} for r in rows],
        'receipts_sha256': hashlib.sha256(body).hexdigest(),
        'stripped_original_control': {
            'sites_patched': st[1], 'sha256': hashlib.sha256(st[0]).hexdigest(),
            'cu_equal_to_candidate': sum(r['stripped_original']['cu'] == r['candidate']['cu'] for r in rows),
            'logs_equal_to_candidate': sum(r['stripped_original']['same_logs_as_candidate'] for r in rows),
            'error_state_equal_to_candidate': sum(r['stripped_original']['same_error_state_as_candidate'] for r in rows),
        },
    }


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
    summary = summarize(images, rows, body)
    rep = json.dumps(summary, sort_keys=True, indent=1).encode()
    (out / 'report.json.gz').write_bytes(gzip.compress(rep, mtime=0))
    print(json.dumps({k: summary[k] for k in ('case_count', 'success_count', 'behavior_match', 'log_match_ex_cu',
                                              'log_match_exact', 'log_match_path_normalized', 'cu_equal',
                                              'cu_delta_histogram', 'model_match_success', 'stripped_original_control')}))


if __name__ == '__main__':
    main()
