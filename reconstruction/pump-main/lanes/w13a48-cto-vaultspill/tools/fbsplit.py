#!/usr/bin/env python3
"""fbsplit.py <fn.bin> [cut]: perfect-frame bound split: remap only named objects (our offset < cut) vs only the
spill area (>= cut, default 0x6d0 = first RA spill slot)."""
import sys, difflib, collections
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import ctoracle, framebound as fb
raw = Path(sys.argv[1]).read_bytes(); cut = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x6d0
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
remap = {c: v.most_common(1)[0][0] for c, v in votes.items()}
def apply(sel):
    new = []
    for j, t in enumerate(ctok):
        fc = fb.frame_off(t, ctok[j - 1] if j else None)
        if fc and -fc[1] in remap and sel(-fc[1]): t = fb.setoff(t, fc[0], -remap[-fc[1]])
        new.append(t)
    return round(difflib.SequenceMatcher(None, otok, new, autojunk=False).ratio(), 5)
print({'plain': apply(lambda o: False), 'named_only': apply(lambda o: o < cut), 'spill_only': apply(lambda o: o >= cut), 'all': apply(lambda o: True)})
