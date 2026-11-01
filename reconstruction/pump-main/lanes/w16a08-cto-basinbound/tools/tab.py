#!/usr/bin/env python3
"""tab.py [names...]: stacked-bound table (placement restore -> frame normalisation -> RA ceiling) from stack/ and cm/."""
import json, os, re, sys
O = '/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a08-cto-basinbound'
def j(p):
    try: return json.load(open(p))
    except Exception: return {}
def climb(n):
    try:
        L = [json.loads(l) for l in open(f'{O}/cm/{n}.climb.log') if l.startswith('{')]
        c = L[-1]; return c, len([x for x in (c.get('force') or '').split(',') if x])
    except Exception: return {}, 0
def lddw(b):
    i = 0; k = 0
    while i < len(b):
        if b[i] == 0x18: k += 1; i += 16
        else: i += 8
    return k
names = sys.argv[1:] or ['m0', 'e1', 'F2', 'hc', 'X1', 'T289n', 'B2', 'Y2', 'Z2', 'v14', 'v21', 'v26', 'ov1a']
print('| basin | bytes raw / restored | M raw | M restored | extra bb56.i live-in (slot) | frame bound | RA pass 1: M @ bytes (forces) | RA pass 2 | stacked ceiling | vs 2,338 |')
print('| --- | --- | ---: | ---: | --- | ---: | --- | --- | ---: | ---: |')
for n in names:
    raw = j(f'{O}/rx/{n}/res.json'); ar = j(f'{O}/stack/{n}.ar.json'); ph = j(f'{O}/stack/{n}.ph.json')
    phr = j(f'{O}/stack/{n}.phr.json'); sh = j(f'{O}/stack/{n}.sh.json')
    fr = max(phr.get('Mhc', 0), sh.get('Mshhc', 0)) or None
    ex = [f"{f['reg'][1:]} ({f['slot']})" for jj in ar.get('ares', {}).get('joins', []) for f in jj.get('fix', [])]
    c1, n1 = climb(n); c2, n2 = climb(n + 'p2')
    def m_of(c):
        if not c.get('ratio'): return None
        # M from ratio: tokens = (bytes/8 - lddw); lddw count of the restored build is a close proxy
        b = open(f'{O}/rx/{n}__r/fn.bin', 'rb').read() if os.path.exists(f'{O}/rx/{n}__r/fn.bin') else open(f'{O}/rx/{n}/fn.bin', 'rb').read()
        t = c['bytes'] // 8 - lddw(b)
        return round(c['ratio'] * (3339 + t) / 2)
    jt = j(f'{O}/cm/{n}.joint.json'); jsh = j(f'{O}/cm/{n}.jsh.json'); jt2 = j(f'{O}/cm/{n}p2.joint.json'); jsh2 = j(f'{O}/cm/{n}p2.jsh.json')
    vals = [x for x in (jt.get('Mhc'), jsh.get('Mshhc'), jt2.get('Mhc'), jsh2.get('Mshhc')) if x]
    ceil = max(vals) if vals else None
    p1 = f"{m_of(c1)} @{c1.get('bytes')} ({n1})" if c1 else '-'
    p2 = f"{m_of(c2)} @{c2.get('bytes')} (+{n2 - n1})" if c2 else '-'
    print(f"| {n} | {raw.get('bytes')} / {ar.get('bytes')} | {ph.get('M')} | {ar.get('M')} | {', '.join(ex) or '-'} | {fr} | {p1} | {p2} | "
          f"{ceil} | {('%+d' % (ceil - 2338)) if ceil else ''} |")
