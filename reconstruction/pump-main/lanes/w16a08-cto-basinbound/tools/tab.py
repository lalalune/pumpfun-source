#!/usr/bin/env python3
"""tab.py [names...]: stacked-bound table (placement restore -> frame normalisation -> RA ceiling) from stack/ and cm/."""
import json, os, re, sys
O = '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound'
def j(p):
    try: return json.load(open(p))
    except Exception: return None
def ev(n):
    try: t = open(f'{O}/stack/{n}.ev.txt').read().strip().split('\n')
    except Exception: return {}
    r = {}
    for l in t:
        k = l.split()[0]; m1 = re.search(r'L---=([+-]\d+) Lrfj=([+-]\d+) val\[(.*)\]', l)
        if m1: r[k] = (int(m1.group(1)), int(m1.group(2)), m1.group(3))
    return r
names = sys.argv[1:] or ['m0', 'F2', 'e1', 'hc', 'X1', 'T289n', 'B2', 'Y2', 'Z2', 'v14', 'v21', 'v26', 'ov1a']
rows = []
print('| basin | bytes raw / restored | M raw | M restored (placement) | extra bb56.i live-in | Mhc (frame: alloca unshift + spill perm) | RA: climb ratio @ bytes, forces | joint (RA + perm) | rfj vs main raw / restored |')
print('| --- | --- | ---: | ---: | --- | ---: | --- | ---: | --- |')
for n in names:
    raw = j(f'{O}/rx/{n}/res.json') or {}
    ar = j(f'{O}/stack/{n}.ar.json') or {}
    ph = j(f'{O}/stack/{n}.ph.json') or {}; phr = j(f'{O}/stack/{n}.phr.json') or {}
    sh = j(f'{O}/stack/{n}.sh.json') or {}
    fr = max(phr.get('Mhc', 0), sh.get('Mshhc', 0))
    ex = [(f['reg'], f['slot']) for jj in ar.get('ares', {}).get('joins', []) for f in jj.get('fix', [])]
    cl = None; nf = 0
    try:
        L = [json.loads(l) for l in open(f'{O}/cm/{n}.climb.log') if l.startswith('{')]
        cl = L[-1]; nf = len([x for x in (cl.get('force') or '').split(',') if x])
    except Exception: pass
    jt = j(f'{O}/cm/{n}.joint.json') or {}
    jsh = j(f'{O}/cm/{n}.jsh.json') or {}
    joint = max(jt.get('Mhc', 0), jsh.get('Mshhc', 0)) or None
    e = ev(n)
    er = e.get(n, (None, None, '')); err = e.get(n + '__r', (None, None, ''))
    print(f"| {n} | {raw.get('bytes')} / {ar.get('bytes')} | {ph.get('M')} | {ar.get('M')} | {ex or '-'} | {fr or None} | "
          f"{(str(cl['ratio']) + ' @' + str(cl['bytes']) + ', ' + str(nf)) if cl else '-'} | {joint} | {er[1]} / {err[1]} |")
