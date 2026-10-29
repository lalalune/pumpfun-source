#!/usr/bin/env python3
"""Whole-program census of string literals referenced from .text (lddw rX, ptr ; mov/stdw len)
and of .data.rel.ro &str slices: which original literals are absent from the candidate image."""
import sys, json, struct
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from linemap import Image, decode, BASE, original_windows
def lits(img, text_raw_iter):
    c = Counter()
    for start, raw in text_raw_iter:
        ins = decode(raw)
        for k, (p, op, rg, of, im) in enumerate(ins):
            if op != 0x18: continue
            for j in range(k + 1, min(len(ins), k + 4)):
                if ins[j][1] in (0xb7, 0x7a) and 4 <= ins[j][4] < 400:
                    s = img.read(im, ins[j][4])
                    if s and all(32 <= x < 127 for x in s):
                        c[(s.decode(), start)] += 1
                    break
    return c
cand = Image(sys.argv[1]); orig = Image(BASE / 'original.so')
ws = [(w['start'], w['raw']) for w in original_windows()]
oc = lits(orig, ws)
missing = {}
for (s, start), n in oc.items():
    if cand.blob.find(s.encode()) < 0:
        missing.setdefault(s, []).append(hex(start))
for s, w in sorted(missing.items()):
    print(repr(s), w)
print('original literal refs:', len(oc), 'distinct missing from candidate image:', len(missing))
# reverse: candidate .text literal refs absent from original
t = cand.secs['.text']; raw = cand.blob[t['offset']:t['offset'] + t['size']]
cc = lits(cand, [(t['addr'], raw)])
rev = sorted({s for (s, _) in cc if orig.blob.find(s.encode()) < 0})
print('candidate-only literals:', len(rev)); [print('  +', repr(s)) for s in rev]
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(json.dumps({'missing_from_candidate': missing, 'candidate_only': rev}, indent=1))
