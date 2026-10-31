#!/usr/bin/env python3
"""screen1.py <base m.ll dir name> : singles/pairs of head live-range edits (hcv gep, bump, native, sharing tag) through px.py"""
import sys, itertools, subprocess, json, os
sys.path.insert(0, 'tools'); from ed import *
B = sys.argv[1]
BR = ("  store i8 %ctx.val57, ptr %_111.i, align 1, !noalias !8627", "  %bre = getelementptr inbounds i8, ptr %ctx, i64 35\n  %brl = load i8, ptr %bre, align 1\n  store i8 %brl, ptr %_111.i, align 1, !noalias !8627")
def fu(lbl, tag):
    return lambda t: t.replace(lbl + '\n', lbl + '\n  call void asm sideeffect "", "r"(i8 %_539.sroa.0.0)\n', 1)
A = {
 'b1': [BR],
 'g1': [remat('%327')], 'g2': [remat('%327', keep=2)], 'g3': [remat('%327', keep=3)],
 's1': [via_slot('%327')], 'sb': [via_slot('%ctx.val57', keep=0, tag='b', ty='i8')],
 'fu84': [fu('bb84:                                             ; preds = %bb35', 0)],
 'fu25': [lambda t: t.replace('bb25.i:                                           ; preds', 'bb25.i:                                           ; preds', 1)],
}
names = [k for k in A if k != 'fu25']
combos = [(k,) for k in names] + [c for c in itertools.combinations(names, 2) if not (c[0][0] == c[1][0] == 'g') and not ('s1' in c and c[0][0]=='g' or 's1' in c and c[1][0]=='g')]
out = open(f'screen1_{B}.jsonl', 'a')
for c in combos:
    n = f'{B}_' + '+'.join(c)
    open(f'e/{n}.py', 'w').write("import sys; sys.path.insert(0,'tools')\nfrom screen1_edits import get\nEDITS=get(%r)\n" % (list(c),))
    r = subprocess.run(['python3', 'tools/px.py', n, f'e/{n}.py', '--base', f'rx/{B}/m.ll'], capture_output=True, text=True)
    if r.returncode: print(n, 'ERR', r.stdout[-300:], r.stderr[-300:]); continue
    d = json.loads(r.stdout.strip().split('\n')[-1])
    for l in (0, 1, 2):
        s = subprocess.run(['python3', 'tools/segdiff.py', 'rx/m0/fn.bin', f'px/{n}/fn.bin', '--lvl', str(l), '--top', '0'], capture_output=True, text=True).stdout.split('\n')[0]
        d[f'l{l}'] = int(s.split('variant ')[1].split(' ')[0])
    d['tcf'] = subprocess.run(['python3', 'tools/segregs.py', f'px/{n}/fn.bin'], capture_output=True, text=True).stdout.strip()[:90]
    print(json.dumps(d)); out.write(json.dumps(d) + '\n'); out.flush()
