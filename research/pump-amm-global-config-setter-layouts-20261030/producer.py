#!/usr/bin/env python3
"""pump_amm GlobalConfig setters: fee-bound / recipient checks and legacy account lengths.

Each case is a short sequence of admin instructions (create_config, update_fee_config,
update_creator_fee_config, set_boost_authority, disable, update_admin) sent to a fresh
LiteSVM that holds only the pump_amm image and a synthetic GlobalConfig (no captured
fixtures, no RPC). The GlobalConfig is written at the current 949-byte length or at one
of the legacy lengths the program still reads (907 = 899-byte body, 940 = 932-byte body)
or at neighbouring lengths. Every step records the error, compute units, full logs and
the post-state (config bytes, lengths, lamports) on the original image, the rebuilt image
and a control image (the original with its 'programs/pump-amm/' file-path prefix removed
from every AnchorError site, see strip_prefix()).

Usage: producer.py --root <repo> --images '{"original": P, "candidate": P}' --out <dir>
"""
import argparse, gzip, hashlib, json, pathlib, re, struct

from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.message import Message
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA')
SYSTEM = Pubkey.from_string('11111111111111111111111111111111')
FIXED_ADMIN = Pubkey.from_string('8LWu7QM2dGR1G8nKDHthckea57bkCzXyBTAKPJUBDHo8')
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
CONFIG = Pubkey.find_program_address([b'global_config'], PROGRAM)[0]
ADMIN = Keypair.from_seed(bytes([171]) * 32)
OTHER = Keypair.from_seed(bytes([172]) * 32)
NEW_ADMIN = Pubkey.from_bytes(bytes([0x42]) * 32)
BOOST_AUTH = Pubkey.from_bytes(bytes([0x43]) * 32)
GLOBAL_DISC = bytes([149, 8, 156, 202, 160, 252, 176, 217])
DISC = {
    'create_config': bytes.fromhex('c9cff3724b6f2fbd'),
    'update_fee_config': bytes.fromhex('68b867f258976b14'),
    'update_creator_fee_config': bytes.fromhex('3dafa0f9424288af'),
    'disable': bytes.fromhex('b9adbb5ad80feee9'),
    'update_admin': bytes.fromhex('a1b028d53cb8b3e4'),
    'set_boost_authority': bytes.fromhex('e3954c2a8227eacd'),
    'toggle_mayhem_mode': bytes.fromhex('01096fd0641fffa3'),
    'toggle_boost': bytes.fromhex('75a1a04adf897663'),
    'toggle_cashback_enabled': bytes.fromhex('7367e0ffbd5956c3'),
    'update_buyback_config': bytes.fromhex('fbe0ab92a01a71e9'),
    'set_reserved_fee_recipients': bytes.fromhex('6faca2e87259d58e'),
}
MAX = 2**64 - 1
RENT = {}  # filled per VM run (minimum_balance is constant in LiteSVM)
PREFIX = b'programs/pump-amm/'
SORTED = [Pubkey.from_bytes(bytes([0x10 + i]) * 32) for i in range(8)]


# ---------------------------------------------------------------- fixtures
def config_bytes(length, admin, flags=0, cfc=1, max_bps=300):
    """A full 949-byte GlobalConfig with recognisable field values, cut or padded to `length`."""
    d = bytearray(max(length, 949))
    d[:8] = GLOBAL_DISC; d[8:40] = bytes(admin)
    struct.pack_into('<QQ', d, 40, 20, 5); d[56] = flags
    for i in range(8):
        d[57 + 32 * i:89 + 32 * i] = bytes([0x20 + i]) * 32           # recipients (sorted)
    struct.pack_into('<Q', d, 313, 5)                                   # coin creator bps
    d[321:353] = bytes([0x30]) * 32                                     # admin_set_coin_creator_authority
    d[353:385] = bytes([0x31]) * 32                                     # whitelist_pda
    d[385:417] = bytes([0x32]) * 32                                     # reserved_fee_recipient
    d[417] = 1                                                          # mayhem_mode_enabled
    for i in range(7):
        d[418 + 32 * i:450 + 32 * i] = bytes([0x50 + i]) * 32
    d[642] = 1                                                          # is_cashback_enabled
    for i in range(8):
        d[643 + 32 * i:675 + 32 * i] = bytes([0x60 + i]) * 32           # buyback recipients
    struct.pack_into('<Q', d, 899, 5000)                                # buyback bps
    d[907:939] = bytes([0x70]) * 32                                     # boost authority
    d[939] = 1; d[940] = cfc; struct.pack_into('<Q', d, 941, max_bps)
    return bytes(d[:length])


def fee_args(lp=30, proto=40, recips=None, creator=100, cc_auth=None):
    recips = SORTED if recips is None else recips
    cc_auth = Pubkey.from_bytes(bytes([0x44]) * 32) if cc_auth is None else cc_auth
    return struct.pack('<QQ', lp, proto) + b''.join(bytes(k) for k in recips) + struct.pack('<Q', creator) + bytes(cc_auth)


def ix(name, args=b'', admin=None, admin_writable=None, admin_signer=True, extra=None):
    """Instruction for one admin handler with the IDL account order."""
    admin = ADMIN.pubkey() if admin is None else admin
    w = {'create_config': True, 'update_creator_fee_config': True}.get(name, False) if admin_writable is None else admin_writable
    metas = [AccountMeta(admin, admin_signer, w), AccountMeta(CONFIG, False, True)]
    if name == 'update_admin':
        metas.append(AccountMeta(NEW_ADMIN if extra is None else extra, False, False))
    if name == 'set_boost_authority':
        metas.append(AccountMeta(BOOST_AUTH if extra is None else extra, False, False))
    if name in ('create_config', 'update_creator_fee_config', 'set_boost_authority'):
        metas.append(AccountMeta(SYSTEM, False, False))
    if name == 'set_reserved_fee_recipients':
        metas[0], metas[1] = metas[1], metas[0]                         # IDL order: global_config, admin
    if name != 'toggle_boost':                                          # toggle_boost has no event CPI accounts
        metas += [AccountMeta(EVENT, False, False), AccountMeta(PROGRAM, False, False)]
    return {'name': name, 'data': (DISC[name] + args).hex(),
            'metas': [[str(m.pubkey), m.is_signer, m.is_writable] for m in metas]}


# ---------------------------------------------------------------- cases
def cases():
    out = []

    def c(name, steps, length=949, lamports=None, admin=None, flags=0, cfc=1, max_bps=300, no_config=False,
          payer='admin', sigverify=True):
        out.append({'name': name, 'steps': steps, 'length': length, 'lamports': lamports,
                    'admin': str(ADMIN.pubkey() if admin is None else admin), 'flags': flags, 'cfc': cfc,
                    'max_bps': max_bps, 'no_config': no_config, 'payer': payer, 'sigverify': sigverify})

    cc = lambda **kw: ix('create_config', fee_args(**kw), admin=FIXED_ADMIN)
    ufc = lambda **kw: ix('update_fee_config', fee_args(**kw))
    ucfc = lambda cfg, mx, raw=None: ix('update_creator_fee_config', (bytes([cfg]) + struct.pack('<Q', mx)) if raw is None else raw)
    dis = lambda *b: ix('disable', bytes(b))
    zero = Pubkey.default()

    # A: create_config (fixed admin, signature checks off, fixed admin pays)
    fa = dict(no_config=True, payer='fixed', sigverify=False)
    c('cc-ok', [cc()], **fa)
    c('cc-lp-1001', [cc(lp=1001)], **fa)
    c('cc-proto-1001', [cc(proto=1001)], **fa)
    c('cc-creator-1001', [cc(creator=1001)], **fa)
    c('cc-recipient0-zero', [cc(recips=[zero] + SORTED[1:])], **fa)
    c('cc-recipients-dup', [cc(recips=SORTED[:4] + [SORTED[3]] + SORTED[5:])], **fa)
    c('cc-creator1001-and-zero-recip', [cc(creator=1001, recips=[zero] + SORTED[1:])], **fa)
    c('cc-twice', [cc(), cc(lp=1)], **fa)
    c('cc-then-update', [cc(), ix('update_fee_config', fee_args(lp=1), admin=FIXED_ADMIN)], **fa)
    c('cc-non-fixed-admin', [ix('create_config', fee_args())], no_config=True)
    c('cc-over-existing', [cc()], payer='fixed', sigverify=False)
    # B: update_fee_config bounds on a 949-byte config
    c('ufc-ok', [ufc()])
    c('ufc-all-bps-1000', [ufc(lp=1000, proto=1000, creator=1000)])
    c('ufc-lp-1001', [ufc(lp=1001)])
    c('ufc-proto-1001', [ufc(proto=1001)])
    c('ufc-creator-1001', [ufc(creator=1001)])
    c('ufc-recipient-zero-mid', [ufc(recips=SORTED[:3] + [zero] + SORTED[4:])])
    c('ufc-recipients-dup-last', [ufc(recips=SORTED[:7] + [SORTED[6]])])
    c('ufc-non-admin', [ix('update_fee_config', fee_args(), admin=OTHER.pubkey())])
    # C: update_creator_fee_config / set_boost_authority (extend path) per length
    c('ucfc-ok', [ucfc(1, 500)])
    c('ucfc-non-admin', [ix('update_creator_fee_config', bytes([1]) + struct.pack('<Q', 1), admin=OTHER.pubkey())])
    for length in (907, 940, 948):
        c('ucfc-len%d' % length, [ucfc(1, 777)], length=length)
        if length != 940:
            c('sba-len%d' % length, [ix('set_boost_authority')], length=length)
    c('ucfc-len907-prefunded', [ucfc(1, 777)], length=907, lamports='rent949')
    c('ucfc-len906', [ucfc(1, 777)], length=906)
    c('ucfc-len950', [ucfc(1, 777)], length=950)
    c('sba-len949', [ix('set_boost_authority')])
    c('sba-len907-admin-readonly-nonpayer', [ix('set_boost_authority')], length=907, payer='other', sigverify=False)
    c('sba-len949-admin-readonly-nonpayer', [ix('set_boost_authority')], payer='other', sigverify=False)
    c('ucfc-len907-admin-readonly-nonpayer', [ix('update_creator_fee_config', bytes([1]) + struct.pack('<Q', 7),
                                                 admin_writable=False)], length=907, payer='other', sigverify=False)
    c('ucfc-len907-then-ufc', [ucfc(1, 777), ufc()], length=907)
    # D: setters without extend on legacy lengths
    for length in (907, 940, 948, 950):
        c('ufc-len%d' % length, [ufc()], length=length)
        c('dis-len%d' % length, [dis(1, 0, 1, 0, 1)], length=length)
        c('ua-len%d' % length, [ix('update_admin')], length=length)
    # E: disable bit layout
    c('dis-all-true-from-e0', [dis(1, 1, 1, 1, 1)], flags=0xE0)
    c('dis-all-false-from-ff', [dis(0, 0, 0, 0, 0)], flags=0xFF)
    # G: the remaining GlobalConfig setters on legacy / current lengths
    tog = lambda name, v: ix(name, bytes([v]))
    c('tb-len907', [tog('toggle_boost', 0)], length=907)
    c('tb-len940', [tog('toggle_boost', 0)], length=940)
    c('tb-len949', [tog('toggle_boost', 0)])
    c('tm-len907', [tog('toggle_mayhem_mode', 0)], length=907)
    c('tc-len907', [tog('toggle_cashback_enabled', 0)], length=907)
    c('bb-len907', [ix('update_buyback_config', b'\x01' + struct.pack('<Q', 7000))], length=907)
    c('bb-none-len949', [ix('update_buyback_config', b'\x00')])
    c('bb-10001-len949', [ix('update_buyback_config', b'\x01' + struct.pack('<Q', 10001))])
    c('srf-no-remaining-len949', [ix('set_reserved_fee_recipients', bytes([0x31]) * 32)])
    # F: update_admin sequences
    c('ua-then-old-admin', [ix('update_admin'), ufc()])
    c('ua-to-default-then-old', [ix('update_admin', extra=zero), dis(1, 1, 1, 1, 1)])
    c('ua-not-signer', [ix('update_admin', admin_signer=False)], payer='other')
    return out


# ---------------------------------------------------------------- execution
def run_case(case, image):
    vm = LiteSVM().with_log_bytes_limit(None).with_transaction_history(0)
    if not case['sigverify']:
        vm = vm.with_sigverify(False)
    if isinstance(image, bytes):
        vm.add_program(PROGRAM, image)
    else:
        vm.add_program_from_file(PROGRAM, image)
    vm.set_clock(Clock(100, 1234567890, 0, 0, 1234567890))
    for k in (ADMIN.pubkey(), OTHER.pubkey(), FIXED_ADMIN):
        vm.airdrop(k, 10**12)
    rent949 = vm.minimum_balance_for_rent_exemption(949)
    if not case['no_config']:
        data = config_bytes(case['length'], Pubkey.from_string(case['admin']), case['flags'], case['cfc'], case['max_bps'])
        lam = rent949 if case['lamports'] == 'rent949' else vm.minimum_balance_for_rent_exemption(len(data))
        vm.set_account(CONFIG, Account(lam, data, PROGRAM))
    payer = {'admin': ADMIN, 'other': OTHER, 'fixed': None}[case['payer']]
    payer_key = FIXED_ADMIN if payer is None else payer.pubkey()
    steps = []
    for st in case['steps']:
        metas = [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in st['metas']]
        inst = Instruction(PROGRAM, bytes.fromhex(st['data']), metas)
        bh = vm.latest_blockhash()
        signers = [kp for kp in (ADMIN, OTHER) if any(m.is_signer and m.pubkey == kp.pubkey() for m in metas)]
        if case['sigverify']:
            if payer is not None and payer not in signers:
                signers = [payer] + signers
            tx = Transaction.new_signed_with_payer([inst], payer_key, signers, bh)
        else:
            tx = Transaction.new_unsigned(Message.new_with_blockhash([inst], payer_key, bh))
            if payer is not None:
                tx.partial_sign([payer], bh)
        r = vm.send_transaction(tx)
        vm.expire_blockhash()
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        cfg = vm.get_account(CONFIG)
        steps.append({
            'step': st['name'],
            'tx_sha256': hashlib.sha256(bytes(tx)).hexdigest(),
            'error': str(r.err()) if failed else None,
            'cu': meta.compute_units_consumed(),
            'logs': list(meta.logs()),
            'config': None if cfg is None else {'len': len(cfg.data), 'lamports': cfg.lamports,
                                                'owner': str(cfg.owner), 'data': bytes(cfg.data).hex()},
            'lamports': {n: vm.get_account(k).lamports for n, k in
                         (('admin', ADMIN.pubkey()), ('other', OTHER.pubkey()), ('fixed_admin', FIXED_ADMIN))},
        })
    return {'rent949': rent949, 'steps': steps}


# ---------------------------------------------------------------- control image
def elf_sections(blob):
    shoff, = struct.unpack_from('<Q', blob, 0x28)
    shentsize, shnum, shstrndx = struct.unpack_from('<HHH', blob, 0x3a)
    hs = [struct.unpack_from('<IIQQQQIIQQ', blob, shoff + i * shentsize) for i in range(shnum)]
    st = hs[shstrndx]; names = blob[st[4]:st[4] + st[5]]
    return {names[h[0]:names.index(b'\0', h[0])].decode(): (h[4], h[5]) for h in hs if h[0]}


def strip_prefix(blob):
    """The original with every reference to a 'programs/pump-amm/src/*.rs' string moved 18 bytes
    later (past the prefix) and the matching length immediate lowered by 18, so its AnchorError
    file names read 'src/...' like the rebuild's. Nothing else changes."""
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


# ---------------------------------------------------------------- report
CODE = re.compile(r'Custom\((\d+)\)')


def code(err):
    if err is None:
        return 'ok'
    m = CODE.search(err)
    if m:
        return m.group(1)
    m = re.search(r'Fieldless\((\w+)\)', err)
    return m.group(1) if m else err


def site(logs):
    for l in logs:
        if 'AnchorError thrown in ' in l:
            return l.split('AnchorError thrown in ')[1].split('. Error Code')[0]
        if 'AnchorError caused by account: ' in l:
            return 'account:' + l.split('caused by account: ')[1].split('.')[0]
    return None


def nocu(logs):
    return [l for l in logs if not ('consumed' in l and 'compute units' in l)]


def norm_path(logs):
    return [l.replace('thrown in programs/pump-amm/src/', 'thrown in src/') for l in nocu(logs)]


BEHAVIOR = ('tx_sha256', 'error', 'config', 'lamports')


def compare(case, o, c, s):
    rows = []
    for i, (so, sc, ss) in enumerate(zip(o['steps'], c['steps'], s['steps'])):
        rows.append({
            'case': case['name'], 'index': i, 'step': so['step'],
            'code': {'original': code(so['error']), 'candidate': code(sc['error'])},
            'site': {'original': site(so['logs']), 'candidate': site(sc['logs'])},
            'same_behavior': all(so[k] == sc[k] for k in BEHAVIOR),
            'same_logs': so['logs'] == sc['logs'],
            'same_logs_ex_cu': nocu(so['logs']) == nocu(sc['logs']),
            'same_logs_path_normalized': norm_path(so['logs']) == norm_path(sc['logs']),
            'cu': {'original': so['cu'], 'candidate': sc['cu'], 'control': ss['cu']},
            'cu_delta': sc['cu'] - so['cu'],
            'control_equals_candidate': all(ss[k] == sc[k] for k in BEHAVIOR) and ss['logs'] == sc['logs'] and ss['cu'] == sc['cu'],
            'config_len': None if so['config'] is None else so['config']['len'],
            'config_lamports': None if so['config'] is None else so['config']['lamports'],
            'admin_lamports': so['lamports']['admin'], 'other_lamports': so['lamports']['other'],
            'fixed_admin_lamports': so['lamports']['fixed_admin'],
        })
    return rows


def decode_fields(hexdata):
    d = bytes.fromhex(hexdata)
    out = {'len': len(d)}
    if len(d) >= 57:
        out.update(admin=str(Pubkey.from_bytes(d[8:40])), lp=struct.unpack_from('<Q', d, 40)[0],
                   proto=struct.unpack_from('<Q', d, 48)[0], flags=d[56])
    if len(d) >= 321:
        out['creator_bps'] = struct.unpack_from('<Q', d, 313)[0]
    if len(d) >= 939:
        out['boost_authority'] = str(Pubkey.from_bytes(d[907:939]))
    if len(d) >= 949:
        out['creator_fee_configurable'] = d[940]; out['max_configurable_creator_fee_bps'] = struct.unpack_from('<Q', d, 941)[0]
    return out


def produce(images):
    control, sites = strip_prefix(pathlib.Path(images['original']).read_bytes())
    receipts, rows = [], []
    for case in cases():
        o = run_case(case, images['original'])
        c = run_case(case, images['candidate'])
        s = run_case(case, control)
        receipts.append({'case': case, 'original': o, 'candidate': c,
                         'control': {'steps': [{k: st[k] for k in ('cu', 'error', 'logs', 'config', 'lamports', 'tx_sha256', 'step')}
                                               for st in s['steps']]}})
        rows += compare(case, o, c, s)
    return receipts, rows, control, sites


def sha(b):
    return hashlib.sha256(b).hexdigest()


def summarize(images, receipts, rows, control, sites):
    final = []
    for r in receipts:
        last = r['original']['steps'][-1]['config']
        final.append({'case': r['case']['name'], 'final_config': None if last is None else decode_fields(last['data'])})
    hist = {}
    for r in rows:
        hist[str(r['cu_delta'])] = hist.get(str(r['cu_delta']), 0) + 1
    return {
        'image_sha256': {k: sha(pathlib.Path(v).read_bytes()) for k, v in images.items()},
        'control': {'sha256': sha(control), 'sites_patched': sites,
                    'steps_equal_to_candidate': sum(r['control_equals_candidate'] for r in rows)},
        'rent_949': receipts[0]['original']['rent949'],
        'case_count': len(receipts), 'step_count': len(rows),
        'same_behavior': sum(r['same_behavior'] for r in rows),
        'same_logs_exact': sum(r['same_logs'] for r in rows),
        'same_logs_ex_cu': sum(r['same_logs_ex_cu'] for r in rows),
        'same_logs_path_normalized': sum(r['same_logs_path_normalized'] for r in rows),
        'cu_equal': sum(r['cu_delta'] == 0 for r in rows),
        'cu_delta_histogram': dict(sorted(hist.items(), key=lambda kv: int(kv[0]))),
        'steps': rows,
        'final_configs': final,
    }


def dumps(o):
    return json.dumps(o, sort_keys=True, separators=(',', ':'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--images', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    images = json.loads(a.images)
    receipts, rows, control, sites = produce(images)
    out = pathlib.Path(a.out) / 'runtime'
    out.mkdir(parents=True, exist_ok=True)
    body = ''.join(dumps(r) + '\n' for r in receipts).encode()
    (out / 'receipts.jsonl.gz').write_bytes(gzip.compress(body, mtime=0))
    rep = summarize(images, receipts, rows, control, sites)
    rep['receipts_sha256'] = sha(body)
    (out / 'report.json.gz').write_bytes(gzip.compress(json.dumps(rep, sort_keys=True, indent=1).encode(), mtime=0))
    print(dumps({k: rep[k] for k in ('case_count', 'step_count', 'same_behavior', 'same_logs_exact', 'same_logs_ex_cu',
                                     'same_logs_path_normalized', 'cu_equal', 'cu_delta_histogram', 'control')}))


if __name__ == '__main__':
    main()
