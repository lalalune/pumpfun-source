#!/usr/bin/env python3
"""Measure a Fees candidate (symbols ELF) against the original with the repo's window_map normalizer.

usage: python3 -I measure.py CANDIDATE_SYMBOLS.so [--baseline BASELINE_SYMBOLS.so] [--json OUT.json]
Counts: normalized (original windows whose signature occurs in the candidate), raw-local (raw sha256),
unique pairs, unmatched original windows, unmatched candidate windows. With --baseline, reports gained/lost sets.
"""
import argparse, hashlib, importlib.util, json, pickle, sys
from pathlib import Path
sys.dont_write_bytecode = True
BASE = Path('/Users/shawwalters/fees100-run/base')
CACHE = Path(__file__).resolve().parent / 'cache'
def module(n, p):
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
w = module('wm', BASE / 'research/fees-composed-frontier188/window_map.py')
ORIG = (BASE / 'evidence/original/pump_fees/deployed.so').read_bytes()
_cache = {}
def windows(img):
    k = hashlib.sha256(img).hexdigest()
    if k not in _cache:
        f = CACHE / (k + '.windows.pickle')
        if f.exists():
            _cache[k] = pickle.loads(f.read_bytes())
        else:
            _cache[k] = w.windows(img)
            CACHE.mkdir(exist_ok=True); f.write_bytes(pickle.dumps(_cache[k]))
    return _cache[k]
def summary(img):
    o = windows(ORIG); c = windows(img)
    cs = {r['signature'] for r in c}; cr = {r['raw_sha256'] for r in c}
    norm = {r['address'] for r in o if r['signature'] in cs}
    raw = {r['address'] for r in o if r['raw_sha256'] in cr}
    comp = w.compare(o, c)
    um_o = [(r['address'], r['bytes'], r['name']) for r in comp['unmatched_original']]
    um_c = [(r['address'], r['bytes'], r['name']) for r in comp['unmatched_candidate']]
    return dict(original_windows=len(o), candidate_windows=len(c), normalized=len(norm), raw_local=len(raw),
                unique_pairs=len(comp['unique_pairs']), ambiguous=len(comp['ambiguous']),
                matched_bytes=sum(r['bytes'] for r in o if r['address'] in norm),
                raw_bytes=sum(r['bytes'] for r in o if r['address'] in raw),
                unmatched_original=um_o, unmatched_candidate=um_c), norm, raw
if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('candidate'); ap.add_argument('--baseline'); ap.add_argument('--json')
    a = ap.parse_args()
    img = Path(a.candidate).read_bytes()
    s, norm, raw = summary(img)
    s['sha256'] = hashlib.sha256(img).hexdigest()
    if a.baseline:
        b, bn, br = summary(Path(a.baseline).read_bytes())
        s['gained_normalized'] = sorted(norm - bn); s['lost_normalized'] = sorted(bn - norm)
        s['gained_raw'] = sorted(raw - br); s['lost_raw'] = sorted(br - raw)
    if a.json: Path(a.json).write_text(json.dumps(s, indent=1) + '\n')
    short = {k: v for k, v in s.items() if k not in ('unmatched_original', 'unmatched_candidate')}
    print(json.dumps(short))
    print('unmatched_original:', s['unmatched_original'])
    print('unmatched_candidate:', s['unmatched_candidate'])
