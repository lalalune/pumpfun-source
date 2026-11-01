#!/usr/bin/env python3
"""addc2.py name...: fold c2/<name>.log (re-vote climb) and rx/j_<name>/mp.json (joint) into st/<name>/step.json"""
import sys, os, json
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for n in sys.argv[1:]:
    p = f'{OUT}/st/{n}/step.json'; s = json.load(open(p))
    lg = f'{OUT}/c2/{n}.log'
    if os.path.exists(lg):
        for l in open(lg):
            if l.startswith('{"final"'):
                x = json.loads(l); s['climb2'] = {'M': x['final']['M'], 'bytes': x['final']['bytes'], 'n': len(x['final']['forces']), 'forces': x['final']['forces']}
                s['climb2_at'] = (x.get('best_at') or {}).get('M')
    jp = f'{OUT}/rx/j_{n}/mp.json'
    if os.path.exists(jp):
        j = json.load(open(jp)); s['joint'] = {k: j[k] for k in ('M', 'Mperm', 'Mhc', 'bytes', 'lcs_hc')}
    json.dump(s, open(p, 'w')); print(n, s.get('climb2', {}).get('M'), s.get('climb2', {}).get('bytes'), s.get('climb2', {}).get('n'), s.get('climb2_at'), s.get('joint'))
