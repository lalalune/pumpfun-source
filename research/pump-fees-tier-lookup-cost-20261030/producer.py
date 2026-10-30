#!/usr/bin/env python3
"""Pump Fees fee-tier lookup cost: compute units of get_fees / get_fees_with_quote_mint
as a function of the tier-list lengths and of the tier that is selected.

Each case writes one synthetic FeeConfig account (normal tiers N, stable tiers M)
and sends read-only query transactions to it, on one LiteSVM per image (original
and rebuilt candidate). Every step records error, Anchor error, return data,
the full log list and compute units on both images. The report also fits a
linear cost model per query route from the measured compute units.

usage: producer.py --root <repo> --images '{"original": p, "candidate": p}' --out <packet dir>
Deterministic: fixed key seed, fixed clock, no paths or times in the output.
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
PUMP = Pubkey.from_string('6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P')
CONFIG, CONFIG_BUMP = Pubkey.find_program_address([b'fee_config', bytes(PUMP)], PROGRAM)
WSOL = Pubkey.from_string('So11111111111111111111111111111111111111112')
USDC = Pubkey.from_string('EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v')
USDT = Pubkey.from_string('Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB')
MINT77 = Pubkey.from_bytes(bytes([77]) * 32)
ZERO = Pubkey.default()
PAYER_SEED = 227
PAYER = Keypair.from_seed(bytes([PAYER_SEED]) * 32)
U128 = 2**128 - 1
QUOTES = {'zero': ZERO, 'wsol': WSOL, 'usdc': USDC, 'usdt': USDT, 'mint77': MINT77}


def disc(name, kind='global'):
    return hashlib.sha256(f'{kind}:{name}'.encode()).digest()[:8]


CONFIG_DISC = disc('FeeConfig', 'account')
GET_FEES = disc('get_fees')
GET_FEES_Q = disc('get_fees_with_quote_mint')


def fees(f):
    return struct.pack('<QQQ', *f)


def tiers(xs):
    return struct.pack('<I', len(xs)) + b''.join(t.to_bytes(16, 'little') + fees(f) for t, f in xs)


def config_data(normal, stable, flat=(11, 22, 33), exotic=(44, 55, 66), allocation=4097):
    d = CONFIG_DISC + bytes([CONFIG_BUMP]) + bytes([213]) * 32 + fees(flat) + tiers(normal) + tiers(stable) + fees(exotic)
    assert len(d) <= allocation, (len(d), allocation)
    return d.ljust(allocation, b'\0')


def ladder(n, base, step=100, first=100):
    # thresholds first, first+step, ...; fees (base+i, i, 1) so every tier returns a distinct value
    return [(first + i * step, (base + i, i, 1)) for i in range(n)]


def q_step(cap, quote, pool=1, label=None, k=None):
    qn = next(n for n, v in QUOTES.items() if v == quote)
    return {'label': label or f'get_fees_with_quote_mint pool={pool} cap={cap} quote={qn}', 'k': k,
            'data_hex': (GET_FEES_Q + bytes([pool]) + cap.to_bytes(16, 'little') + bytes(quote)).hex()}


def g_step(cap, opt=0, pool=1, label=None, k=None):
    return {'label': label or f'get_fees pool={pool} cap={cap} trade=1000000 opt={opt}', 'k': k,
            'data_hex': (GET_FEES + bytes([pool]) + cap.to_bytes(16, 'little') + (1_000_000).to_bytes(8, 'little') + bytes([opt])).hex()}


def scan_steps(tl, mk):
    # one step per selectable tier index k (cap = exact threshold of tier k, inclusive),
    # plus cap below tier 0 (early return) and cap u128 max (top tier)
    out = [mk(0, 'below')] if tl and tl[0][0] > 0 else []
    out += [mk(t, k) for k, (t, _) in enumerate(tl)]
    out.append(mk(U128, 'top'))
    return out


ROUTES = {
    'quote-wsol-normal': ('normal', lambda cap, k: q_step(cap, WSOL, k=k)),
    'quote-zero-normal': ('normal', lambda cap, k: q_step(cap, ZERO, k=k)),
    'legacy-opt0-normal': ('normal', lambda cap, k: g_step(cap, 0, k=k)),
    'quote-usdc-stable': ('stable', lambda cap, k: q_step(cap, USDC, k=k)),
    'legacy-opt1-stable': ('stable', lambda cap, k: g_step(cap, 1, k=k)),
}


def cases():
    out = []

    def C(name, family, route, normal, stable, steps, allocation=4097, exotic=(44, 55, 66), note=''):
        out.append({'name': name, 'family': family, 'route': route, 'n_normal': len(normal), 'n_stable': len(stable),
                    'allocation': allocation, 'note': note,
                    'initial': [{'pubkey': str(CONFIG), 'lamports': 10**9, 'owner': str(PROGRAM),
                                 'data_hex': config_data(normal, stable, exotic=exotic, allocation=allocation).hex()}],
                    'steps': steps})

    # n-*: normal list length N, stable list fixed at 1, every selectable k (main WSOL route)
    for n in [1, 2, 3, 5, 8, 10, 16, 25, 32, 40, 49, 50]:
        tl = ladder(n, 1000)
        C(f'n-wsol-normal-{n}', 'normal-scan', 'quote-wsol-normal', tl, ladder(1, 2000),
          scan_steps(tl, ROUTES['quote-wsol-normal'][1]))
    # the other normal routes at three lengths
    for route in ['quote-zero-normal', 'legacy-opt0-normal']:
        for n in [1, 10, 50]:
            tl = ladder(n, 1000)
            C(f'n-{route}-{n}', 'normal-scan', route, tl, ladder(1, 2000), scan_steps(tl, ROUTES[route][1]))
    # s-*: stable list length M, normal list fixed at 1
    for route, lens in [('quote-usdc-stable', [1, 2, 5, 10, 25, 49, 50]), ('legacy-opt1-stable', [1, 10, 50])]:
        for mlen in lens:
            sl = ladder(mlen, 3000)
            C(f's-{route}-{mlen}', 'stable-scan', route, ladder(1, 1000), sl, scan_steps(sl, ROUTES[route][1]))
    # x-*: does the length of the list that is NOT searched change the cost?
    n10 = ladder(10, 1000)
    for mlen in [0, 1, 10, 25, 50]:
        C(f'x-normal10-stable{mlen}', 'cross', 'quote-wsol-normal', n10, ladder(mlen, 2000),
          [q_step(100, WSOL, k=0), q_step(1000, WSOL, k=9)])
    s10 = ladder(10, 3000)
    for n in [1, 10, 25, 50]:
        C(f'x-stable10-normal{n}', 'cross', 'quote-usdc-stable', ladder(n, 1000), s10,
          [q_step(100, USDC, k=0), q_step(1000, USDC, k=9)])
    # f-*: routes that never scan a tier list, at small and full lists
    for n, mlen in [(1, 1), (50, 50)]:
        steps = [q_step(500, WSOL, pool=0, label='get_fees_with_quote_mint pool=0 quote=wsol'),
                 g_step(500, 0, pool=0, label='get_fees pool=0 opt=0'),
                 q_step(500, MINT77, label='get_fees_with_quote_mint quote=mint77 (exotic)'),
                 q_step(500, USDT, label='get_fees_with_quote_mint quote=usdt (exotic)')]
        C(f'f-flat-routes-{n}-{mlen}', 'flat', 'flat', ladder(n, 1000), ladder(mlen, 3000), steps)
        C(f'f-flat-routes-exotic-zero-{n}-{mlen}', 'flat', 'flat', ladder(n, 1000), ladder(mlen, 3000), steps[2:], exotic=(0, 0, 0),
          note='exotic fees all zero -> flat fees returned')
    # a-*: account allocation larger than the serialized FeeConfig
    # w-*: both lists full (50 + 50 is the most a 4097-byte FeeConfig holds), every scanning route
    full_n, full_s = ladder(50, 1000), ladder(50, 3000)
    for route, (which, mk) in ROUTES.items():
        tl = full_n if which == 'normal' else full_s
        C(f'w-full-{route}', 'worst-case', route, full_n, full_s,
          [mk(0, 'below'), mk(tl[0][0], 0), mk(tl[25][0], 25), mk(tl[49][0], 49), mk(U128, 'top')])
    for alloc in [2512, 2513, 4072, 4073, 4097, 8192, 10240]:
        C(f'a-alloc-{alloc}', 'allocation', 'quote-wsol-normal', n10, ladder(10, 2000),
          [q_step(100, WSOL, k=0), q_step(1000, WSOL, k=9), q_step(1000, USDC, k=9)], allocation=alloc)
    # z-*: threshold layout: first threshold 0 (no early return possible), all thresholds equal
    z0 = ladder(10, 1000, first=0)
    C('z-first-threshold-zero-10', 'layout', 'quote-wsol-normal', z0, ladder(1, 2000), scan_steps(z0, ROUTES['quote-wsol-normal'][1]))
    zeq = [(500, (1000 + i, i, 1)) for i in range(10)]
    C('z-equal-thresholds-10', 'layout', 'quote-wsol-normal', zeq, ladder(1, 2000),
      [q_step(499, WSOL, k='below'), q_step(500, WSOL, k='equal'), q_step(U128, WSOL, k='top')],
      note='all 10 thresholds 500; the reverse scan stops at the last entry')
    # e-*: empty searched list (known panic-path divergence, PR #1907)
    C('e-empty-normal', 'empty', 'quote-wsol-normal', [], ladder(1, 2000), [q_step(100, WSOL, k='empty')])
    C('e-empty-stable', 'empty', 'quote-usdc-stable', ladder(1, 1000), [], [q_step(100, USDC, k='empty')])
    return out


def run_case(binary, case):
    vm = LiteSVM().with_transaction_history(0)
    vm.add_program_from_file(PROGRAM, binary)
    vm.set_account(PAYER.pubkey(), Account(10**12, b'', ZERO))
    vm.set_clock(Clock(1000, 0, 0, 0, 1700000000))
    for a in case['initial']:
        vm.set_account(Pubkey.from_string(a['pubkey']), Account(a['lamports'], bytes.fromhex(a['data_hex']), Pubkey.from_string(a['owner'])))
    results = []
    for st in case['steps']:
        vm.expire_blockhash()
        ix = Instruction(PROGRAM, bytes.fromhex(st['data_hex']), [AccountMeta(CONFIG, False, False), AccountMeta(PUMP, False, False)])
        t = Transaction.new_signed_with_payer([ix], PAYER.pubkey(), [PAYER], vm.latest_blockhash())
        r = vm.send_transaction(t)
        failed = isinstance(r, FailedTransactionMetadata)
        meta = r.meta() if failed else r
        rd = meta.return_data()
        logs = list(meta.logs())
        cfg = vm.get_account(CONFIG)
        results.append({
            'error': str(r.err()) if failed else None,
            'custom_error': next((l.split('Error Code: ')[1].split('.')[0] for l in logs if 'Error Code: ' in l), None),
            'return_hex': bytes(rd.data).hex() if rd is not None and len(rd.data) else None,
            'return_fees': list(struct.unpack('<QQQ', bytes(rd.data))) if rd is not None and len(rd.data) == 24 else None,
            'logs': logs,
            'config_sha256': hashlib.sha256(bytes(cfg.data)).hexdigest(),
            'compute_units': meta.compute_units_consumed(),
        })
    return results


BEHAVIOR = ['error', 'custom_error', 'return_hex', 'logs', 'config_sha256']


def fit(points):
    # points: (family, total = N + M, depth, cu); depth = tiers above the selected one (len-1-k).
    # Model cu = A + B*total + C*depth. B and C come from the scan families only
    # (two anchor differences); residuals are then taken over every point,
    # including the cross / allocation / worst-case families that did not set B or C.
    scan = [p for p in points if p[0] in ('normal-scan', 'stable-scan')]
    by = {}
    for _, t, d, c, _ in scan:
        by.setdefault((t, d), c)
    tot = sorted({t for _, t, _, _, _ in scan})
    t_lo, t_hi = tot[0], tot[-1]
    b = (by[(t_hi, 0)] - by[(t_lo, 0)]) // (t_hi - t_lo)
    d_hi = max(d for _, t, d, _, _ in scan if t == t_hi)
    c_ = (by[(t_hi, d_hi)] - by[(t_hi, 0)]) // d_hi
    a = by[(t_lo, 0)] - b * t_lo
    res, off = {}, []
    for f, t, d, c, name in points:
        r = c - (a + b * t + c_ * d)
        res[f] = max(res.get(f, 0), abs(r))
        if r:
            off.append({'case': name, 'stored_tiers': t, 'depth': d, 'cu': c, 'residual': r})
    return {'points': len(points), 'A': a, 'B_per_tier_stored': b, 'C_per_tier_scanned': c_,
            'max_abs_residual_by_family': dict(sorted(res.items())), 'nonzero_residual_points': off}


def step_route(data_hex):
    # route name of a query step, decoded from its instruction data
    d = bytes.fromhex(data_hex)
    if d[8] != 1:
        return 'flat'
    if d[:8] == GET_FEES_Q:
        q = Pubkey.from_bytes(d[25:57])
        return {WSOL: 'quote-wsol-normal', ZERO: 'quote-zero-normal', USDC: 'quote-usdc-stable'}.get(q, 'flat')
    return 'legacy-opt1-stable' if d[33] == 1 else 'legacy-opt0-normal'


def produce(images, cases_list):
    shas = {n: hashlib.sha256(pathlib.Path(images[n]).read_bytes()).hexdigest() for n in ['original', 'candidate']}
    receipts, summary = [], []
    model_pts = {}
    for c in cases_list:
        per = {n: run_case(images[n], c) for n in ['original', 'candidate']}
        rows = []
        for i, st in enumerate(c['steps']):
            o, k = per['original'][i], per['candidate'][i]
            rows.append({'label': st['label'], 'k': st['k'], 'behavior_match': all(o[f] == k[f] for f in BEHAVIOR),
                         'cu_match': o['compute_units'] == k['compute_units'], 'original': o, 'candidate': k})
            route = step_route(st['data_hex'])
            if isinstance(st['k'], int) and route in ROUTES and c['allocation'] == 4097 and o['error'] is None:
                n = c['n_normal'] if ROUTES[route][0] == 'normal' else c['n_stable']
                model_pts.setdefault(route, []).append((c['family'], c['n_normal'] + c['n_stable'], n - 1 - st['k'], o['compute_units'], c['name']))
        receipts.append({'case': c, 'steps': rows})
        summary.append({'name': c['name'], 'family': c['family'], 'route': c['route'], 'n_normal': c['n_normal'], 'n_stable': c['n_stable'],
                        'allocation': c['allocation'], 'steps': len(rows), 'k': [r['k'] for r in rows],
                        'behavior_match': all(r['behavior_match'] for r in rows), 'cu_match': all(r['cu_match'] for r in rows),
                        'errors_original': [r['original']['custom_error'] or r['original']['error'] for r in rows],
                        'errors_candidate': [r['candidate']['custom_error'] or r['candidate']['error'] for r in rows],
                        'returns_original': [r['original']['return_fees'] for r in rows],
                        'cu_original': [r['original']['compute_units'] for r in rows],
                        'cu_candidate': [r['candidate']['compute_units'] for r in rows]})
    report = {'program_id': str(PROGRAM), 'payer_seed': PAYER_SEED, 'behavior_fields': BEHAVIOR,
              'scope': 'Pump Fees get_fees / get_fees_with_quote_mint compute units vs. tier-list length and selected tier on synthetic FeeConfig state; per step: error, Anchor error, return data, full log list, FeeConfig sha256 (behavior) and compute units.',
              'image_sha256': shas, 'case_count': len(summary), 'step_count': sum(s['steps'] for s in summary),
              'behavior_mismatched_cases': [s['name'] for s in summary if not s['behavior_match']],
              'cu_mismatched_cases': [s['name'] for s in summary if not s['cu_match']],
              'cost_model_original': {r: fit(p) for r, p in sorted(model_pts.items())},
              'cases': summary}
    return receipts, report


def gz(b):
    return gzip.compress(b, compresslevel=9, mtime=0)


def check_idl(root):
    idl = json.loads((root / 'evidence/upstream/pump_fees.json').read_text())
    assert idl['address'] == str(PROGRAM)
    ixs = {i['name']: bytes(i['discriminator']) for i in idl['instructions']}
    assert ixs['get_fees'] == GET_FEES and ixs['get_fees_with_quote_mint'] == GET_FEES_Q
    accs = {a['name']: bytes(a['discriminator']) for a in idl['accounts']}
    assert accs['FeeConfig'] == CONFIG_DISC


def load_images(arg):
    arg = arg.strip()
    return json.loads(arg if arg.startswith('{') else pathlib.Path(arg).read_text())


def encode(receipts, report):
    r = gz(b''.join(json.dumps(x, sort_keys=True, separators=(',', ':')).encode() + b'\n' for x in receipts))
    p = gz(json.dumps(report, sort_keys=True, indent=1).encode() + b'\n')
    return r, p


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    p.add_argument('--images', required=True)
    p.add_argument('--out', required=True)
    a = p.parse_args()
    images = load_images(a.images)
    check_idl(pathlib.Path(a.root))
    receipts, report = produce(images, cases())
    r, rep = encode(receipts, report)
    rt = pathlib.Path(a.out) / 'runtime'
    rt.mkdir(parents=True, exist_ok=True)
    (rt / 'receipts.jsonl.gz').write_bytes(r)
    (rt / 'report.json.gz').write_bytes(rep)
    print(json.dumps({'cases': report['case_count'], 'steps': report['step_count'],
                      'behavior_mismatched': report['behavior_mismatched_cases'], 'cu_mismatched': report['cu_mismatched_cases'],
                      'model': report['cost_model_original']}))


if __name__ == '__main__':
    main()
