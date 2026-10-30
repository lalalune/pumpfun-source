#!/usr/bin/env python3
"""spmap.py <fn.bin> [cut]: cand spill slot -> orig slot votes (only mismatching or all with -a)."""
import sys, difflib, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctoracle, framebound as fb
raw = Path(sys.argv[1]).read_bytes(); cut = 0x6d0
ctok = []; i = 0
while i < len(raw):
    n = 16 if raw[i] == 0x18 else 8; ctok.append(raw[i:i + n]); i += n
otok, w = ctoracle.orig_tokens()
oa = [ctoracle.abstract(t) for t in otok]; ca = [ctoracle.abstract(t) for t in ctok]
votes = collections.defaultdict(collections.Counter)
for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, oa, ca, autojunk=False).get_opcodes():
    if tag != 'equal': continue
    for k in range(i2 - i1):
        a, b = i1 + k, j1 + k
        fo = fb.frame_off(otok[a], otok[a - 1] if a else None); fc = fb.frame_off(ctok[b], ctok[b - 1] if b else None)
        if fo and fc and fo[0] == fc[0]: votes[-fc[1]][-fo[1]] += 1
allm='-a' in sys.argv
for c in sorted(votes):
    if c<cut: continue
    v=votes[c]; best,n=v.most_common(1)[0]
    if allm or best!=c: print(hex(c),'->',' '.join(f'{hex(o)}:{k}' for o,k in v.most_common(4)))
