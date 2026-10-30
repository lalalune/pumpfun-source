#!/usr/bin/env python3
"""Propose beam extensions from multi-copy screens on a base composite.

  beam.py <multi.jsonl> <base_tag> <base_ratio> [--prefix g1+g2] [--top N] [--max-d 8]

Reads single-gene screen rows on base <base_tag> (rows whose genes are prefix + [g]), then proposes
  - singles at exactly 27,400 B that beat the base ratio, and
  - pairs/triples of compatible genes whose summed byte deltas cancel (|sum| <= --max-d) ranked by
    summed ratio gain (gene effects are not additive, so every proposal must be screened again).
Prints trial lines `name=gene+gene+...` (prefix included) for multi.py.
"""
import itertools, json, sys, importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('genes', str(HERE / 'genes.py'))
genes = importlib.util.module_from_spec(spec); spec.loader.exec_module(genes)
args = sys.argv[1:]
opt = lambda k, d: (args[args.index(k) + 1] if k in args else d)
mj, btag, bratio = args[0], args[1], float(args[2])
prefix = [g for g in opt('--prefix', '').split('+') if g]
top = int(opt('--top', '40'))
maxd = int(opt('--max-d', '8'))
base = Path(opt('--base-file', '/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a03-cto-genes/programs/pump/src/creator/admin_cto.rs')).read_text()
rows = {}
for l in Path(mj).read_text().splitlines():
    r = json.loads(l)
    if r.get('base') != btag or r.get('bytes') is None:
        continue
    gl = r['genes']
    if gl[:len(prefix)] != prefix or len(gl) != len(prefix) + 1:
        continue
    rows[gl[-1]] = r
singles = [(g, r['bytes'] - 27400, r['ratio'] - bratio) for g, r in rows.items()]
good = [s for s in singles if s[2] > -0.002]
out = []
for g, db, dr in sorted(singles, key=lambda s: -s[2]):
    if db == 0 and dr > 0:
        out.append((dr, [g]))


def compatible(gs):
    try:
        genes.apply(base, prefix + list(gs))
        return True
    except Exception:
        return False


cands = []
for a, b in itertools.combinations(good, 2):
    if abs(a[1] + b[1]) <= maxd and (a[1] or b[1]) and a[2] + b[2] > 0:
        cands.append((a[2] + b[2], [a[0], b[0]]))
for a, b, c in itertools.combinations(good, 3):
    if abs(a[1] + b[1] + c[1]) <= maxd and a[2] + b[2] + c[2] > 0.002:
        cands.append((a[2] + b[2] + c[2], [a[0], b[0], c[0]]))
cands.sort(key=lambda x: -x[0])
seen = set()
for dr, gs in out + cands:
    key = tuple(sorted(gs))
    if key in seen or not compatible(gs):
        continue
    seen.add(key)
    print(f"{'_'.join(gs)[:60]}={'+'.join(prefix + gs)}  # pred {dr:+.5f}")
    top -= 1
    if top <= 0:
        break
