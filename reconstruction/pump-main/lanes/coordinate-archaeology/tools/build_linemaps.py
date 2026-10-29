#!/usr/bin/env python3
"""Build LINEMAPS.json: per unmatched window, every original Source/panic site paired with our site.

Pairing: exact (kind, path, code|col, line) first, then (kind, path, code|col) for the leftovers.
Each row: original order/slot/line, our order/slot/line, statement kind and text at our line,
error-code name, and status (match | line-mismatch | orig-only | cand-only).

  build_linemaps.py --cand unstripped.so --src <crate dir> --out LINEMAPS.json
"""
import argparse, json, re, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from linemap import Image, BASE, original_windows, body, TARGETS, find_fn, src_line, classify  # noqa

ANCHOR = {2000: 'ConstraintMut', 2001: 'ConstraintHasOne', 2003: 'ConstraintRaw', 2006: 'ConstraintSeeds', 2012: 'ConstraintAddress',
          2500: 'RequireViolated', 2501: 'RequireEqViolated', 2502: 'RequireKeysEqViolated', 2503: 'RequireNeqViolated',
          2504: 'RequireKeysNeqViolated', 2505: 'RequireGtViolated', 2506: 'RequireGteViolated', 3007: 'AccountOwnedByWrongProgram'}
FN = {0x14f4e0: 'buy_exact_sol_in', 0x80df8: 'trade::v3_buy_costs', 0x6cd78: 'legacy_sell::process_cashback_inner',
      0x83c00: 'trade::v3_execute_buy', 0x13f630: 'buy_v2::buy_exact_quote_in_handler', 0x13b9b8: 'buy_v2::buy_handler',
      0x144508: 'sell_v2::execute', 0x4c158: 'migrate_v2::create_token_account_v2', 0x147ba0: 'trade::buy (buy_v3)',
      0x14a8a8: 'trade::sell (sell_v3)', 0x1489f8: 'trade::buy_exact_quote', 0x72810: 'sweep::execute', 0x1e7c0: 'create_v2::execute',
      0x77940: 'cashback::claim_v2', 0x5b3b0: 'multi_hop_curve::swap_hop', 0x22a10: 'admin_cto::execute'}


def pump_codes(src):
    txt = (Path(src) / 'src/lib.rs').read_text()
    body_ = txt[txt.index('enum PumpError'):]
    body_ = body_[:body_.index('\n}')]
    names = re.findall(r'^\s*([A-Z][A-Za-z0-9]+)\s*,', body_, re.M)
    return {6000 + i: n for i, n in enumerate(names)}


def short(p):
    return p.split('/src/')[-1] if p.startswith('programs/') else 'std:' + p.split('/')[-1]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--cand', required=True); ap.add_argument('--src', required=True); ap.add_argument('--out', required=True)
    a = ap.parse_args()
    codes = dict(ANCHOR); codes.update(pump_codes(a.src))
    orig = Image(BASE / 'original.so'); cand = Image(a.cand)
    wins = {w['start']: w for w in original_windows()}
    res = {}
    for start, rx in TARGETS.items():
        w = wins[start]; f = find_fn(a.cand, rx)
        os_ = orig.sites(start, w['raw']); cs = cand.sites(f[0], body(cand.blob, cand.secs, f[0], f[1]))
        for i, s in enumerate(os_): s['order'] = i
        for i, s in enumerate(cs): s['order'] = i
        k2 = lambda s: (s['kind'], s['path'], s['code'] if s['kind'] == 'source' else s['col'])
        rows = []; used = set()
        for exact in (True, False):
            for o in os_:
                if o.get('_p'):
                    continue
                for c in cs:
                    if id(c) in used or k2(c) != k2(o) or (exact and c['line'] != o['line']):
                        continue
                    used.add(id(c)); o['_p'] = c; break
        for o in os_:
            c = o.get('_p')
            r = {'orig_order': o['order'], 'orig_slot': o['slot'], 'kind': o['kind'], 'file': short(o['path']), 'orig_line': o['line'],
                 'col': o['col'], 'code': o['code'], 'code_name': codes.get(o['code'])}
            if c:
                txt = full = None
                p = Path(a.src) / c['path'].split('programs/pump/')[-1] if c['path'].startswith('programs/pump/') else None
                if p and p.exists():
                    L = p.read_text().splitlines(); full = L[c['line'] - 1].strip() if 0 < c['line'] <= len(L) else None; txt = full[:200] if full else None
                r.update({'cand_order': c['order'], 'cand_slot': c['slot'], 'cand_line': c['line'], 'statement': classify(full, c['kind']) if txt else ('std' if not p else None),
                          'cand_text': txt, 'status': 'match' if c['line'] == o['line'] else 'line-mismatch'})
            else:
                r['status'] = 'orig-only'
            rows.append(r)
        for c in cs:
            if id(c) not in used:
                rows.append({'cand_order': c['order'], 'cand_slot': c['slot'], 'kind': c['kind'], 'file': short(c['path']), 'cand_line': c['line'],
                             'col': c['col'], 'code': c['code'], 'code_name': codes.get(c['code']), 'status': 'cand-only'})
        perm = [r.get('cand_order') for r in rows if 'orig_order' in r]
        st = Counter(r['status'] for r in rows)
        files = Counter(short(s['path']) for s in os_ if s['path'].startswith('programs/'))
        res[hex(start)] = {
            'function': FN[start], 'window_bytes': w['bytes'], 'candidate_symbol': f[2], 'candidate_bytes': f[1],
            'original_source_files': dict(files) or None,
            'status_counts': dict(st),
            'site_order_identical': perm == sorted(perm) and st.get('cand-only', 0) == 0 and st.get('orig-only', 0) == 0,
            'cand_order_by_original_order': perm,
            'sites': rows,
        }
        print(hex(start), FN[start], dict(files), dict(st), 'order-identical' if res[hex(start)]['site_order_identical'] else 'order-differs')
    meta = {'schema': 'pump-main-coordinate-linemaps-v1', 'candidate': str(a.cand), 'original': 'reconstruction/base/original.so',
            'pairing': 'exact (kind,path,code|col,line) first, then (kind,path,code|col)',
            'extraction': 'Source sites: coords.py pattern with the LINE taken from the nearest stw [r10+X+8] in the same straight-line run '
                          '(coords.py takes the first in +-30 insns, which mislabels sites that reuse a stack slot); error code = stw [r10+X+136]. '
                          'Panic sites: lddw of a .data.rel.ro core::panic::Location {ptr<<32,len,line,col}.',
            'statements': 'statement/cand_text are read from OUR source at cand_line; the original statement is inferred to be the same kind.'}
    Path(a.out).write_text(json.dumps({'meta': meta, 'targets': res}, indent=1) + '\n')


if __name__ == '__main__':
    main()
