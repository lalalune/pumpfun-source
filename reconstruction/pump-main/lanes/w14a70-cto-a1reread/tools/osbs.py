#!/usr/bin/env python3
"""osbs.py <baseline unstripped.so> <variant m.o|-> lo hi : whole-function alignment (frame/regs/jumps masked) of the
original vs a raw-IR oracle object (rx/<v>/m.o) or, with '-', the baseline build; prints orig range [lo,hi)."""
import sys, re, difflib, subprocess, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'harness'))
from win import objdump_text, Cand, demangle
OD = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump')
c = Cand(sys.argv[1]); mo = sys.argv[2]; lo = int(sys.argv[3], 16); hi = int(sys.argv[4], 16)
ORIG = Path(__file__).resolve().parents[4].parent / 'evidence/original/pump/deployed.so'
s, n = [(s, n) for s, n, nm in c.funcs if re.search(r'admin_cto.*execute', demangle(nm))][0]
def sh(nm): return '::'.join(re.sub(r'::h[0-9a-f]{16}$', '', demangle(nm)).split('::')[-2:])
names = {a: sh(nm) for a, _, nm in c.funcs}
def dis(path):
    out = []
    for a, t in sorted(objdump_text(path, s, s + n).items()):
        t = re.sub(r'\s*<[^>]*>', '', t)
        m = re.match(r'call (-?0x[0-9a-f]+|-?\d+)$', t)
        if m:
            tgt = a + 8 + int(m.group(1), 0) * 8
            if tgt in names: t = 'call ' + names[tgt]
        out.append((a - s, t))
    return out
def odis(path):
    txt = subprocess.check_output([OD, '-dr', '--no-show-raw-insn', path], text=True)
    out = []; on = False; last = None
    for l in txt.splitlines():
        m = re.match(r'^[0-9a-f]+ <(.*)>:$', l)
        if m and not m.group(1).startswith('LBB'): on = 'admin_cto7execute' in m.group(1); continue
        if m: continue
        if not on: continue
        m = re.match(r'^\s*[0-9a-f]+:\s+R_\S+\s+(\S+)', l)
        if m:
            if out and out[-1][1].startswith('call'): out[-1][1] = 'call ' + sh(m.group(1))
            continue
        m = re.match(r'^\s*([0-9]+):\s+(.*)$', l)
        if m:
            t = re.sub(r'\s*<[^>]*>', '', m.group(2).strip()); out.append([int(m.group(1)) * 8, t]); continue
        m = re.match(r'^\s*[0-9a-f]+:\s+R_\S+\s+(\S+)', l)
        if m and out and out[-1][1].startswith('call'): out[-1][1] = 'call ' + sh(m.group(1))
    return [tuple(x) for x in out]
o = dis(ORIG); k = dis(c.path) if mo == '-' else odis(mo)
def key(t):
    t = re.sub(r'r10 ?([+-]) ?0x[0-9a-f]+', 'r10+F', t); t = re.sub(r'\br\d\b', 'R', t)
    return re.sub(r'[+-]0x[0-9a-f]+$', 'J', t)
sm = difflib.SequenceMatcher(None, [key(t) for _, t in o], [key(t) for _, t in k], autojunk=False)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    for d in range(max(i2 - i1, j2 - j1)):
        a = o[i1 + d] if i1 + d < i2 else None; b = k[j1 + d] if j1 + d < j2 else None
        ref = a[0] if a else (o[i1 + d - 1][0] if i1 + d - 1 >= 0 and i1 + d - 1 < len(o) else 0)
        if not (lo <= ref < hi): continue
        at = '%04x %-44s' % (a[0], a[1][:44]) if a else ' ' * 49
        bt = '%04x %s' % (b[0], b[1][:50]) if b else ''
        mark = '  ' if tag == 'equal' and a[1] == b[1] else ('~ ' if tag == 'equal' else '! ')
        print(mark + at + ' | ' + bt)
