#!/usr/bin/env python3
"""Multiset of error-code-like immediates (stw/mov imm in [2000,7000)) and of rodata string
literals referenced (lddw + adjacent length) per unmatched target, original vs candidate."""
import sys, json
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from linemap import Image, decode, BASE, original_windows, body, TARGETS, find_fn
cand_path = sys.argv[1]
orig = Image(BASE / 'original.so'); cand = Image(cand_path)
wins = {w['start']: w for w in original_windows()}
out = {}
def prof(img, raw):
    ins = decode(raw); codes = Counter(); strs = Counter()
    for k, (p, op, rg, of, im) in enumerate(ins):
        if op in (0x62, 0xb4, 0xb7, 0x7a) and 2000 <= im < 7000:
            codes[im] += 1
        if op == 0x18:
            for j in range(k + 1, min(len(ins), k + 4)):
                if ins[j][1] in (0xb7, 0x7a) and 0 < ins[j][4] < 120:
                    s = img.read(im, ins[j][4])
                    if s and all(32 <= c < 127 for c in s):
                        strs[s.decode()] += 1
                    break
    return codes, strs
for start, rx in TARGETS.items():
    w = wins[start]; f = find_fn(cand_path, rx)
    oc, os_ = prof(orig, w['raw']); cc, cs = prof(cand, body(cand.blob, cand.secs, f[0], f[1]))
    r = {'codes_orig_only': dict(oc - cc), 'codes_cand_only': dict(cc - oc), 'strings_orig_only': dict(os_ - cs), 'strings_cand_only': dict(cs - os_)}
    out[hex(start)] = r
    print(hex(start), json.dumps(r)[:900])
if len(sys.argv) > 2:
    Path(sys.argv[2]).write_text(json.dumps(out, indent=1))
