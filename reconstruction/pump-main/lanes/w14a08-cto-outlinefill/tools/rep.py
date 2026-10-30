#!/usr/bin/env python3
# rep.py [res.jsonl]: per trial ratio@bytes and M = matched orig insns = ratio*(3339+n)/2 (n = cand insns); pin-equivalent ratio = M/3339 if filled with non-matching code
import json,sys,os
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a08-cto-outlinefill'
rows=[]
for l in open(sys.argv[1] if len(sys.argv)>1 else O+'/res.jsonl'):
    r=json.loads(l); out=[r['name']]
    for w in ('none','1:2'):
        x=r.get(w)
        if isinstance(x,dict):
            tag=f"{r['name']}_{w.replace(':','')}"; fn=f'{O}/bw/{tag}/fn.txt'
            n=sum(1 for _ in open(fn)) if os.path.exists(fn) else None
            M=round(x['ratio']*(3339+n)/2) if n else None
            out.append(f"{x['ratio']:.5f}@{x['bytes']} M{M} o{len(x['outl'].split(','))}")
        else: out.append(str(x)[:26])
    rows.append(out)
for o in rows: print(f'{o[0]:26s} {o[1]:32s} {o[2]:32s}')
