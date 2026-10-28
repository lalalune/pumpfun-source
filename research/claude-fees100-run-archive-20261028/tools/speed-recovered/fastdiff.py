#!/usr/bin/env python3
"""Batch scorer: N candidates x M original windows in one process (same scoring as fndiff.py).

usage: python3 -I fastdiff.py CAND.so [CAND2.so ...] [--addr 120816,147944,163920] [--symbol ADDR=SUBSTR ...]
                                [--raw] [--measure] [--baseline BASE.so] [--tsv OUT.tsv] [--json OUT.json] [--diff N]

For every (candidate, window) prints one TSV row:
  cand  sha12  addr  ratio  span  identical  orig_insns  cand_insns  cand_bytes  [normalized raw lost gained]
ratio / differing-insn-span / identical are computed exactly as fndiff.py computes them (same masked listing and the
same original-call naming through unique normalized pairs), so the numbers agree with `fndiff.py ADDR CAND`.
--measure adds whole-program counts (and lost/gained normalized sets vs --baseline, default the CURRENT frontier's
native baseline).  --diff N prints the first N differing masked lines per pair (unified diff, context 0).
Default windows: the 3 remaining targets (120816 147944 163920). Window -> candidate function uses fndiff.TARGETS
unless --symbol ADDR=SUBSTR overrides it. Candidate window tables are cached by sha256 (tools/cache/windows).
Library use:  fd = <load by path>;  fd.score(cand_bytes, addr) -> dict(ratio=..., span=..., identical=...)
"""
import argparse, difflib, hashlib, importlib.util, json, sys, time
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
R = HERE.parents[1]


def module(n, p):
    if n in sys.modules: return sys.modules[n]
    s = importlib.util.spec_from_file_location(n, p); m = importlib.util.module_from_spec(s); sys.modules[n] = m; s.loader.exec_module(m); return m


fw = module('fastwin', HERE / 'fastwin.py')
dis = module('fees_dis', HERE / 'dis.py')
fndiff = module('fees_fndiff', HERE / 'fndiff.py')
w = fw.w
ORIG = fndiff.ORIG
TARGETS = dict(fndiff.TARGETS)
DEFAULT_ADDRS = [120816, 147944, 163920]


def _orig_window(addr):
    return {r['address']: r for r in fw.windows(ORIG)}[addr]


def score(cand, addr, symbol=None, raw=False, want_diff=0, _names=None):
    """Exactly fndiff.main()'s computation. cand = candidate image bytes."""
    key = symbol or TARGETS.get(addr)
    funcs = [f for f in w.m.functions(cand) if key and key in (f['name'] or '')]
    if not funcs:
        return dict(addr=addr, error=f'no candidate function matching {key!r}')
    f = funcs[0]
    if _names is None:
        _names = (dis.names_for(cand), dis.names_for(ORIG, cand))
    cnames, onames = _names
    mask = not raw
    o = [t for _, t in dis.listing(ORIG, addr, onames, mask)]
    c = [t for _, t in dis.listing(cand, f['address'], cnames, mask)]
    sm = difflib.SequenceMatcher(None, o, c, autojunk=False)
    ops = sm.get_opcodes()
    span = sum(max(i2 - i1, j2 - j1) for tag, i1, i2, j1, j2 in ops if tag != 'equal')
    res = dict(addr=addr, orig_bytes=_orig_window(addr)['bytes'], orig_insns=len(o), cand_name=f['name'],
               cand_addr=f['address'], cand_bytes=f['bytes'], cand_insns=len(c), ratio=round(sm.ratio(), 4),
               span=span, identical=o == c)
    if want_diff:
        lines = [l for l in difflib.unified_diff(o, c, 'original', 'candidate', n=0, lineterm='')
                 if l[:1] in '+-' and not l.startswith(('---', '+++'))]
        res['diff'] = lines[:want_diff]
    return res


def measure(cand, baseline=None):
    o = fw.windows(ORIG); c = fw.windows(cand)
    cs = {r['signature'] for r in c}; cr = {r['raw_sha256'] for r in c}
    norm = {r['address'] for r in o if r['signature'] in cs}
    rawm = {r['address'] for r in o if r['raw_sha256'] in cr}
    res = dict(normalized=len(norm), raw_local=len(rawm))
    if baseline is not None:
        b = fw.windows(baseline)
        bs = {r['signature'] for r in b}
        bn = {r['address'] for r in o if r['signature'] in bs}
        res.update(lost_normalized=sorted(bn - norm), gained_normalized=sorted(norm - bn))
    return res


def default_baseline():
    cur = (R / 'shared/frontier/CURRENT').read_text().strip()
    p = R / 'shared/frontier/native' / f'{cur}-symbols.so'
    return p if p.exists() else None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('candidates', nargs='+')
    ap.add_argument('--addr', default=','.join(map(str, DEFAULT_ADDRS)))
    ap.add_argument('--symbol', action='append', default=[], help='ADDR=SUBSTR override of the candidate function')
    ap.add_argument('--raw', action='store_true'); ap.add_argument('--measure', action='store_true')
    ap.add_argument('--baseline'); ap.add_argument('--tsv'); ap.add_argument('--json')
    ap.add_argument('--diff', type=int, default=0)
    a = ap.parse_args()
    addrs = [int(x, 0) for x in a.addr.split(',') if x]
    syms = {}
    for s in a.symbol:
        k, v = s.split('=', 1); syms[int(k, 0)] = v
    base = None
    if a.measure:
        bp = Path(a.baseline) if a.baseline else default_baseline()
        base = bp.read_bytes() if bp else None
    rows, out = [], []
    hdr = ['cand', 'sha12', 'addr', 'ratio', 'span', 'identical', 'orig_insns', 'cand_insns', 'cand_bytes']
    if a.measure: hdr += ['normalized', 'raw', 'lost', 'gained']
    out.append('\t'.join(hdr))
    for p in a.candidates:
        t0 = time.time()
        img = Path(p).read_bytes(); sha = hashlib.sha256(img).hexdigest()
        names = (dis.names_for(img), dis.names_for(ORIG, img))
        ms = measure(img, base) if a.measure else None
        for addr in addrs:
            r = score(img, addr, syms.get(addr), a.raw, a.diff, names)
            r.update(cand=p, sha256=sha, seconds=round(time.time() - t0, 3))
            if ms: r.update(ms)
            rows.append(r)
            if 'error' in r:
                line = [p, sha[:12], str(addr), 'ERR', r['error']]
            else:
                line = [p, sha[:12], str(addr), f"{r['ratio']:.4f}", str(r['span']), str(r['identical']),
                        str(r['orig_insns']), str(r['cand_insns']), str(r['cand_bytes'])]
            if ms:
                line += [str(ms['normalized']), str(ms['raw_local']),
                         ','.join(map(str, ms.get('lost_normalized', []))) or '-',
                         ','.join(map(str, ms.get('gained_normalized', []))) or '-']
            out.append('\t'.join(line))
            for d in r.get('diff', []):
                out.append('    ' + d)
    text = '\n'.join(out) + '\n'
    sys.stdout.write(text)
    if a.tsv: Path(a.tsv).write_text(text)
    if a.json: Path(a.json).write_text(json.dumps(rows, indent=1) + '\n')
    return 0 if all(r.get('identical') for r in rows) else 1


if __name__ == '__main__':
    sys.exit(main())
