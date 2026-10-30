#!/usr/bin/env python3
"""Pump Fees FeeConfig tier-setter compute-unit cost model, original vs rebuild.

update_fee_config / update_stable_fee_config / upsert_fee_tiers /
upsert_stable_fee_tiers / set_exotic_flat_fees: compute units as a function of
the incoming tier count N, the stored tier counts, the upsert offset, the
position of the first failing tier and the account length. Every point runs
one transaction on a fresh LiteSVM per image. Behavior (error, logs, events,
account bytes) and compute units are compared per point; a per-sweep integer
linear fit CU = a + b*x is computed from the original image's measurements.

usage: producer.py --root <repo> --images '{"original": p, "candidate": p}' --out <packet dir>
--images also accepts a path to a file holding that JSON object.
Deterministic: fixed key seeds, fixed clock, no paths in the output.
"""
import argparse, gzip, hashlib, json, pathlib, struct
from solders.account import Account
from solders.clock import Clock
from solders.instruction import AccountMeta, Instruction
from solders.keypair import Keypair
from solders.litesvm import LiteSVM
from solders.pubkey import Pubkey
from solders.transaction import Transaction
from solders.transaction_metadata import FailedTransactionMetadata

PROGRAM = Pubkey.from_string('pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ')
CONFIG_PROGRAM = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
GLOBAL, GLOBAL_BUMP = Pubkey.find_program_address([b'fee-program-global'], PROGRAM)
CONFIG, CONFIG_BUMP = Pubkey.find_program_address([b'fee_config', bytes(CONFIG_PROGRAM)], PROGRAM)
EVENT = Pubkey.find_program_address([b'__event_authority'], PROGRAM)[0]
ZERO = Pubkey.default()
NOW = 1700000000
SEEDS = {'AUTH': 213, 'OTHER': 214, 'PAYER': 215}
KP = {k: Keypair.from_seed(bytes([v]) * 32) for k, v in SEEDS.items()}
A = KP['AUTH'].pubkey()
RENT_4097 = 29406000  # rent-exempt minimum for 4097 bytes


def disc(name, kind='global'):
    return hashlib.sha256(f'{kind}:{name}'.encode()).digest()[:8]


GLOBAL_DISC = disc('FeeProgramGlobal', 'account')
CONFIG_DISC = disc('FeeConfig', 'account')


def fees(f):
    return struct.pack('<QQQ', *f)


def tiers(xs):
    return struct.pack('<I', len(xs)) + b''.join(t.to_bytes(16, 'little') + fees(f) for t, f in xs)


def global_data(authority):
    return GLOBAL_DISC + bytes([GLOBAL_BUMP]) + bytes(authority) + bytes([0]) + bytes([44]) * 32 + (123).to_bytes(8, 'little') + bytes(256)


def config_data(normal, stable, alloc):
    d = CONFIG_DISC + bytes([CONFIG_BUMP]) + bytes(A) + fees((11, 22, 33)) + tiers(normal) + tiers(stable) + fees((44, 55, 66))
    return d[:alloc].ljust(alloc, b'\0')


def ramp(n, base=0, step=10, f=(1, 1, 1)):
    return [(base + i * step, f) for i in range(n)]


def m(key, signer, writable):
    return [str(key), signer, writable]


def c_admin_ix(name, signer, arg, system=False):
    accs = [m(CONFIG, False, True), m(KP[signer].pubkey(), True, system), m(CONFIG_PROGRAM, False, False)]
    if system:
        accs.append(m(ZERO, False, False))
    accs += [m(EVENT, False, False), m(PROGRAM, False, False)]
    return {'data_hex': (disc(name) + arg).hex(), 'accounts': accs, 'signer': signer}


def update(ts, flat=(1, 1, 1), signer='AUTH'):
    return c_admin_ix('update_fee_config', signer, tiers(ts) + fees(flat))


def update_stable(ts, signer='AUTH'):
    return c_admin_ix('update_stable_fee_config', signer, tiers(ts))


def upsert(ts, offset, stable=False, signer='AUTH'):
    return c_admin_ix('upsert_stable_fee_tiers' if stable else 'upsert_fee_tiers', signer, tiers(ts) + bytes([offset]))


def set_exotic(f):
    return c_admin_ix('set_exotic_flat_fees', 'AUTH', fees(f), system=True)


def cases():
    out = []

    def C(name, family, x_name, points):
        out.append({'name': name, 'family': family, 'x': x_name, 'points': points})

    def P(x, ix, normal=None, stable=None, alloc=4097, lamports=10**9):
        normal = ramp(2) if normal is None else normal
        stable = ramp(1) if stable is None else stable
        return {'x': x, 'ix': ix, 'normal': [[t, list(f)] for t, f in normal], 'stable': [[t, list(f)] for t, f in stable], 'alloc': alloc, 'lamports': lamports}

    NS = range(1, 51)
    MS = [0, 1, 2, 5, 10, 20, 30, 40, 49, 50]

    # ---- successful writes: CU vs incoming N, stored M, offset k ----
    C('ok-update-n', 'update_fee_config', 'N incoming', [P(n, update(ramp(n))) for n in NS])
    C('ok-update-stored-normal', 'update_fee_config', 'M stored normal', [P(mm, update(ramp(1)), normal=ramp(mm)) for mm in MS])
    C('ok-update-stored-stable', 'update_fee_config', 'M stored stable', [P(mm, update(ramp(1)), stable=ramp(mm)) for mm in MS])
    C('ok-stable-n', 'update_stable_fee_config', 'N incoming', [P(n, update_stable(ramp(n))) for n in NS])
    C('ok-stable-stored-stable', 'update_stable_fee_config', 'M stored stable', [P(mm, update_stable(ramp(1)), stable=ramp(mm)) for mm in MS])
    C('ok-stable-stored-normal', 'update_stable_fee_config', 'M stored normal', [P(mm, update_stable(ramp(1)), normal=ramp(mm)) for mm in MS])
    C('ok-upsert-n-at-0-empty', 'upsert_fee_tiers', 'N incoming (stored 0, offset 0)', [P(n, upsert(ramp(n), 0), normal=[]) for n in NS])
    C('ok-upsert-n-at-0-over-50', 'upsert_fee_tiers', 'N incoming (stored 50, offset 0)', [P(n, upsert(ramp(n, f=(2, 2, 2)), 0), normal=ramp(50)) for n in NS])
    # one tier written at offset k into 50 stored tiers (threshold 10k+1 keeps the list sorted for k >= 1)
    C('ok-upsert-offset-k-of-50', 'upsert_fee_tiers', 'offset k (stored 50, N 1)', [P(k, upsert([(k * 10 + (1 if k else 0), (3, 3, 3))], k), normal=ramp(50)) for k in range(50)])
    # one tier appended at offset M to M stored tiers
    C('ok-upsert-append-at-m', 'upsert_fee_tiers', 'M stored = offset (N 1)', [P(mm, upsert([(mm * 10, (3, 3, 3))], mm), normal=ramp(mm)) for mm in range(50)])
    C('ok-upsert-stable-n-at-0-empty', 'upsert_stable_fee_tiers', 'N incoming (stored 0, offset 0)', [P(n, upsert(ramp(n), 0, stable=True), stable=[]) for n in NS])
    C('ok-upsert-stable-append-at-m', 'upsert_stable_fee_tiers', 'M stored = offset (N 1)', [P(mm, upsert([(mm * 10, (3, 3, 3))], mm, stable=True), stable=ramp(mm)) for mm in range(50)])

    # ---- failing writes: where the work stops ----
    def bad_fee_at(i, n=50):
        return [(t, (10001, 0, 0) if j == i else f) for j, (t, f) in enumerate(ramp(n))]

    def unsorted_at(i, n=50):
        r = ramp(n)
        r[i + 1] = (r[i][0], r[i + 1][1])
        return r
    C('err-update-invalid-fee-at-i', 'update_fee_config', 'index i of the 10001-bps tier (N 50)', [P(i, update(bad_fee_at(i))) for i in range(50)])
    C('err-update-unsorted-at-i', 'update_fee_config', 'index i of the first non-increasing pair (N 50)', [P(i, update(unsorted_at(i))) for i in range(49)])
    C('err-stable-invalid-fee-at-i', 'update_stable_fee_config', 'index i of the 10001-bps tier (N 50)', [P(i, update_stable(bad_fee_at(i))) for i in range(50)])
    C('err-upsert-invalid-fee-in-kept-prefix', 'upsert_fee_tiers', 'stored M with a 10001-bps stored tier 0, N 1 appended at M', [P(mm, upsert([(mm * 10, (1, 1, 1))], mm), normal=[(0, (10001, 0, 0))] + ramp(mm - 1, 10)) for mm in range(1, 50)])
    C('err-update-flat-invalid-n', 'update_fee_config', 'N incoming, flat (10001,0,0)', [P(n, update(ramp(n), flat=(10001, 0, 0))) for n in NS])
    C('err-update-wrong-admin-n', 'update_fee_config', 'N incoming, non-admin signer', [P(n, update(ramp(n), signer='OTHER')) for n in NS])
    C('err-update-too-many-n', 'update_fee_config', 'N incoming > 50', [P(n, update(ramp(n))) for n in range(51, 61)])
    C('err-upsert-offset-gap', 'upsert_fee_tiers', 'N incoming at offset 3 over 2 stored', [P(n, upsert(ramp(n, 1000), 3)) for n in [1, 2, 5, 10, 20, 30, 40, 50]])
    C('err-upsert-merged-over-50', 'upsert_fee_tiers', 'offset k with N 2 over 50 stored (end = k + 2)', [P(k, upsert([(k * 10 + 1, (1, 1, 1)), (k * 10 + 2, (1, 1, 1))], k), normal=ramp(50)) for k in [49, 50]])

    # ---- account length / layout ----
    # update_fee_config N sweep on legacy-length accounts (stored normal 2, stored stable 0)
    for alloc in [2512, 4073]:
        C(f'ok-update-n-alloc-{alloc}', 'update_fee_config', f'N incoming (account {alloc} B)', [P(n, update(ramp(n)), stable=[], alloc=alloc) for n in NS if 65 + 4 + 40 * n + 4 + (24 if alloc >= 4097 else 0) <= alloc])
    # set_exotic_flat_fees: resize to 4097 (with rent top-up) vs already 4097, vs stored normal M
    for alloc in [2512, 4073, 4097]:
        C(f'ok-exotic-alloc-{alloc}', 'set_exotic_flat_fees', f'M stored normal (account {alloc} B)',
          [P(mm, set_exotic((100, 200, 300)), normal=ramp(mm), stable=[], alloc=alloc, lamports=RENT_4097 - 1000) for mm in [0, 1, 10, 25, 50]])
    return out


def new_vm(binary):
    vm = LiteSVM().with_transaction_history(0).with_log_bytes_limit(None)
    vm.add_program_from_file(PROGRAM, binary)
    return vm


def run_point(vm, pt):
    # every account the transaction touches is reset, so each point starts from the same state
    vm.expire_blockhash()
    for k in KP.values():
        vm.set_account(k.pubkey(), Account(10**12, b'', ZERO))
    vm.set_account(CONFIG_PROGRAM, Account(10**9, b'', ZERO))
    vm.set_clock(Clock(1000, 0, 0, 0, NOW))
    normal = [(t, tuple(f)) for t, f in pt['normal']]
    stable = [(t, tuple(f)) for t, f in pt['stable']]
    vm.set_account(GLOBAL, Account(10**9, global_data(A), PROGRAM))
    vm.set_account(CONFIG, Account(pt['lamports'], config_data(normal, stable, pt['alloc']), PROGRAM))
    ix = pt['ix']
    i = Instruction(PROGRAM, bytes.fromhex(ix['data_hex']), [AccountMeta(Pubkey.from_string(k), s, w) for k, s, w in ix['accounts']])
    signers = [KP['PAYER']] + ([KP[ix['signer']]] if ix['signer'] != 'PAYER' else [])
    t = Transaction.new_signed_with_payer([i], KP['PAYER'].pubkey(), signers, vm.latest_blockhash())
    r = vm.send_transaction(t)
    failed = isinstance(r, FailedTransactionMetadata)
    meta = r.meta() if failed else r
    logs = list(meta.logs())
    a = vm.get_account(CONFIG)
    cu = meta.compute_units_consumed
    return {
        'error': str(r.err()) if failed else None,
        'custom_error': next((l.split('Error Code: ')[1].split('.')[0] for l in logs if 'Error Code: ' in l), None),
        'logs': logs,
        'config': {'lamports': a.lamports, 'len': len(a.data), 'sha256': hashlib.sha256(bytes(a.data)).hexdigest()},
        'compute_units': cu() if callable(cu) else cu,
        'tx_bytes': len(bytes(t)),
    }


def run_case(binary, case):
    vm = new_vm(binary)
    return [run_point(vm, pt) for pt in case['points']]


def behavior(res):
    # everything except compute units: all logs minus the "consumed N of M compute units" lines
    def norm(l):
        if ' consumed ' in l and 'compute units' in l:
            return None
        return l
    return {'error': res['error'], 'custom_error': res['custom_error'], 'config': res['config'],
            'logs': [x for x in map(norm, res['logs']) if x is not None]}


def fit(xs, ys):
    # integer linear fit through the first two distinct x; residual list for the rest
    if len(xs) < 2:
        return None
    x0, y0 = xs[0], ys[0]
    x1, y1 = xs[1], ys[1]
    if x1 == x0:
        return None
    b = (y1 - y0) / (x1 - x0)
    a = y0 - b * x0
    res = [y - (a + b * x) for x, y in zip(xs, ys)]
    return {'a': a, 'b': b, 'nonzero_residuals': sum(1 for r in res if abs(r) > 1e-9), 'residuals': res}


def produce(images, cases_list):
    shas = {n: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for n, p in images.items()}
    receipts, summary = [], []
    for c in cases_list:
        per = {n: run_case(images[n], c) for n in ['original', 'candidate']}
        rows = []
        for i, pt in enumerate(c['points']):
            o, k = per['original'][i], per['candidate'][i]
            rows.append({'x': pt['x'], 'behavior_match': behavior(o) == behavior(k), 'cu_match': o['compute_units'] == k['compute_units'],
                         'logs_match': o['logs'] == k['logs'], 'original': o, 'candidate': k})
        xs = [r['x'] for r in rows]
        cu_o = [r['original']['compute_units'] for r in rows]
        cu_k = [r['candidate']['compute_units'] for r in rows]
        outcomes = sorted(set('ok' if r['original']['error'] is None else (r['original']['custom_error'] or r['original']['error']) for r in rows))
        receipts.append({'case': c, 'points': rows})
        summary.append({'name': c['name'], 'family': c['family'], 'x': c['x'], 'points': len(rows), 'xs': xs,
                        'outcomes': outcomes,
                        'behavior_match': all(r['behavior_match'] for r in rows),
                        'cu_match': all(r['cu_match'] for r in rows),
                        'logs_match': all(r['logs_match'] for r in rows),
                        'cu_original': cu_o, 'cu_candidate': cu_k,
                        'cu_delta': [k - o for o, k in zip(cu_o, cu_k)],
                        'tx_bytes': [r['original']['tx_bytes'] for r in rows],
                        'fit_original': fit(xs, cu_o), 'fit_candidate': fit(xs, cu_k)})
    report = {'program_id': str(PROGRAM), 'signer_seeds': SEEDS, 'clock_unix': NOW,
              'scope': 'Pump Fees FeeConfig tier setters (update_fee_config, update_stable_fee_config, upsert_fee_tiers, upsert_stable_fee_tiers, set_exotic_flat_fees): compute units vs incoming tier count, stored tier counts, upsert offset, failing-tier position and account length; one transaction per point on a fresh LiteSVM per image. behavior = error, custom error, all logs except the compute-unit lines, FeeConfig lamports/len/sha256 after the transaction; compute units compared separately.',
              'image_sha256': shas, 'case_count': len(summary), 'point_count': sum(s['points'] for s in summary),
              'behavior_mismatched_cases': [s['name'] for s in summary if not s['behavior_match']],
              'cu_mismatched_cases': [s['name'] for s in summary if not s['cu_match']],
              'logs_mismatched_cases': [s['name'] for s in summary if not s['logs_match']],
              'cases': summary}
    return receipts, report


def gz(b):
    return gzip.compress(b, compresslevel=9, mtime=0)


def encode(receipts, report):
    rec = gz(b''.join(json.dumps(r, sort_keys=True, separators=(',', ':')).encode() + b'\n' for r in receipts))
    rep = gz(json.dumps(report, sort_keys=True, indent=1).encode() + b'\n')
    return rec, rep


def check_idl(root):
    # discriminators are derived locally; confirm them against the repository IDL
    idl = json.loads((root / 'evidence/upstream/pump_fees.json').read_text())
    assert idl['address'] == str(PROGRAM)
    ixs = {i['name']: bytes(i['discriminator']) for i in idl['instructions']}
    for n in ['update_fee_config', 'update_stable_fee_config', 'upsert_fee_tiers', 'upsert_stable_fee_tiers', 'set_exotic_flat_fees']:
        assert ixs[n] == disc(n), n
    accs = {a['name']: bytes(a['discriminator']) for a in idl['accounts']}
    assert accs['FeeConfig'] == CONFIG_DISC and accs['FeeProgramGlobal'] == GLOBAL_DISC


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
    rec, rep = encode(*produce(images, cases()))
    rt = pathlib.Path(a.out) / 'runtime'
    rt.mkdir(parents=True, exist_ok=True)
    (rt / 'receipts.jsonl.gz').write_bytes(rec)
    (rt / 'report.json.gz').write_bytes(rep)
    r = json.loads(gzip.decompress(rep))
    print(json.dumps({'cases': r['case_count'], 'points': r['point_count'], 'behavior_mismatched': r['behavior_mismatched_cases'],
                      'cu_mismatched': r['cu_mismatched_cases'], 'logs_mismatched': r['logs_mismatched_cases']}))


if __name__ == '__main__':
    main()
