#!/usr/bin/env python3
"""Annotated disassembly.
  odis.py orig <start> [--from A --to B]      original window (call targets named via matched candidates / sites)
  odis.py cand <so> <addr|regex> [--from A --to B]
Jump targets are printed as absolute addresses; calls show the callee window/function identity;
Source sites (file:line code) are annotated at their stdw slot."""
import re, subprocess, sys
from cf import *
OBJ = str(Path.home() / '.cache/solana/v1.52/platform-tools/llvm/bin/llvm-objdump')
args = sys.argv[1:]
def opt(name, default=None):
    if name in args:
        i = args.index(name); v = args[i + 1]; del args[i:i + 2]; return int(v, 0)
    return default
fr = opt('--from'); to = opt('--to')
O = load_orig()
mode = args[0]
if mode == 'orig':
    so = SC / 'base/original.so'; start = int(args[1], 0); size = O[start]['bytes']; side = O
    C = load_cand(str(SC / 'base/i1/unstripped.so')) if len(args) < 3 else load_cand(args[2])
    M = matched_map(O, C)
    def name(t):
        if t in O:
            w = O[t]
            nm = C[M[t][0]]['name'][:70] if t in M else ''
            return f"W{t:#x}[{w['bytes']}B {'M ' + nm if nm else ''} {fmt_sites(w['sites'][:3])}]"
        return f'{t:#x}?'
    sites = O[start]['sites']
else:
    so = Path(args[1]); C = load_cand(str(so))
    key = args[2]
    if re.fullmatch(r'0x[0-9a-f]+', key):
        start = int(key, 16)
    else:
        rx = re.compile(key); cands = [a for a, f in C.items() if rx.search(f['name'])]
        assert len(cands) == 1, [(hex(a), C[a]['name']) for a in cands]
        start = cands[0]
    size = C[start]['bytes']; side = C
    def name(t):
        f = C.get(t)
        return f"F{t:#x}[{f['bytes']}B {f['name'][:80]} {fmt_sites(f['sites'][:3])}]" if f else f'{t:#x}?'
    sites = C[start]['sites']
slot = {start + s['len_slot']: s for s in sites}
lo = fr or start; hi = to or start + size
txt = subprocess.check_output([OBJ, '-d', '--no-show-raw-insn', f'--start-address={lo:#x}', f'--stop-address={hi:#x}', str(so)], text=True)
for line in txt.splitlines():
    m = re.match(r'^\s*([0-9a-f]+):\s+(.*)$', line)
    if not m:
        continue
    a = int(m.group(1), 16); t = m.group(2).strip()
    mm = re.match(r'call (-?0x[0-9a-f]+)$', t)
    if mm:
        tgt = a + 8 + int(mm.group(1), 16) * 8
        t = f'call {name(tgt)}'
    t = re.sub(r'<\.text\+0x([0-9a-f]+)>', lambda x: f'-> {int(x.group(1), 16) + 0x120:#x}', t)
    t = re.sub(r'<[A-Za-z0-9_]+>', '', t)
    note = ''
    if a in slot:
        s = slot[a]; note = f"   ;; SITE {s['short']}:{s['line']} ({s['code']})"
    print(f'{a:#08x}  {t}{note}')
