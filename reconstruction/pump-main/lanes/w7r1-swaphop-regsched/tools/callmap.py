#!/usr/bin/env python3
import sys, os, re, subprocess, json, collections
O = os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-regsched')
L = os.path.expanduser('~/.cache/solana/v1.44/platform-tools/llvm/bin')
so, sym = sys.argv[1:3]
syms = {}
for l in subprocess.run([L + '/llvm-readelf', '-sW', so], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) >= 8 and p[3] == 'FUNC': syms[int(p[1], 16)] = p[7]
st = None
for l in subprocess.run([L + '/llvm-readelf', '-sW', so], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) >= 8 and p[7] == sym: st, sz = int(p[1], 16), int(p[2], 0)
txt = subprocess.run([L + '/llvm-objdump', '-d', '--no-show-raw-insn', so, f'--start-address={st:#x}', f'--stop-address={st+sz:#x}'], capture_output=True, text=True).stdout
cn = []
for l in txt.splitlines():
    m = re.match(r'\s*(\d+):\s+call (-?0x[0-9a-f]+)', l)
    if m:
        t = (int(m.group(1)) + 1 + int(m.group(2), 16)) * 8
        cn.append(syms.get(t, hex(t)))
oc = []
for l in open(O + '/orig.dis'):
    m = re.match(r'(0x[0-9a-f]+)\s+call (-?0x[0-9a-f]+)', l)
    if m: oc.append(int(m.group(1), 16) + 8 + int(m.group(2), 16) * 8)
print(len(cn), len(oc))
# multiset match: per-name counts vs per-target counts, then order
cc = collections.Counter(cn); ocn = collections.Counter(oc)
votes = collections.defaultdict(collections.Counter)
import difflib
# align by count signature sequence
sm = difflib.SequenceMatcher(None, [ocn[x] for x in oc], [cc[x] for x in cn], autojunk=False)
for op, i1, i2, j1, j2 in sm.get_opcodes():
    if op == 'equal':
        for k in range(i2 - i1): votes[oc[i1 + k]][cn[j1 + k]] += 1
mp = {hex(t): v.most_common(1)[0][0] for t, v in votes.items()}
json.dump(mp, open(O + '/callmap.json', 'w'), indent=0)
dm = lambda n: re.sub(r'17h[0-9a-f]{16}E$', '', n)[-70:]
for t in sorted(set(oc)): print(hex(t), ocn[t], dm(mp.get(hex(t), '?')))
