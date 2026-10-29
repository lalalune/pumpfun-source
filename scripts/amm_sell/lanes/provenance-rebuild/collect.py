#!/usr/bin/env python3
"""Collect every historical AMM sell.rs (with fn cashback) on this machine, dedupe by sha256."""
import hashlib, json, os, subprocess, sys, tarfile
from pathlib import Path

LANE = Path(__file__).resolve().parent.parent
OUT = LANE / 'src'
OUT.mkdir(exist_ok=True)
REPO = Path('/Users/shawwalters/Documents/Codex/2026-10-24/pumpfun-source')
H = Path.home() / '.codex/worktrees/pump-swap-remaining-20261028/pumpfun-source'
REL = 'programs/pump-amm/src/instructions/swap/sell.rs'

manifest = {}


def ok(b):
    return b'fn cashback' in b and b'UserVolumeAccumulator' in b and b'InvalidCashbackAccumulator' in b


def add(b, origin):
    if not ok(b):
        return
    h = hashlib.sha256(b).hexdigest()
    if h not in manifest:
        (OUT / f'{h}.rs').write_bytes(b)
        manifest[h] = []
    if len(manifest[h]) < 20:
        manifest[h].append(origin)


roots = [H, REPO / 'research', Path('/Users/shawwalters/Documents/Codex/2026-10-24')]
seen_files = set()
for root in roots:
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in ('target', 'node_modules', '.git', 'provenance-rebuild')]
        for f in fn:
            p = Path(dp) / f
            rp = p.resolve()
            if rp in seen_files:
                continue
            seen_files.add(rp)
            try:
                if f.endswith('.rs'):
                    if p.stat().st_size < 400_000:
                        add(p.read_bytes(), str(p))
                elif f.endswith('.tar.gz') or f.endswith('.tgz'):
                    if p.stat().st_size > 400_000_000:
                        continue
                    with tarfile.open(p) as t:
                        for m in t.getmembers():
                            if m.isfile() and m.name.endswith('sell.rs') and 'pump-amm' in m.name:
                                add(t.extractfile(m).read(), f'{p}::{m.name}')
            except Exception as e:
                print('skip', p, e, file=sys.stderr)

# git history (all refs) in REPO and H
for g in (REPO, H):
    try:
        revs = subprocess.run(['git', '-C', str(g), 'log', '--all', '--format=%H', '--', REL],
                              capture_output=True, text=True).stdout.split()
    except Exception:
        revs = []
    for r in revs:
        b = subprocess.run(['git', '-C', str(g), 'show', f'{r}:{REL}'], capture_output=True).stdout
        add(b, f'git:{g.name}:{r[:12]}')

(LANE / 'work' / 'manifest.json').write_text(json.dumps(manifest, indent=1))
print('distinct', len(manifest))
