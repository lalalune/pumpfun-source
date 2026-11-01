#!/usr/bin/env python3
"""tab.py [filter-substring]: table of this lane's screen rows (res-vc.jsonl) with Mperm/Mhc from mp.py (rx/mp_<name>/mp.json)."""
import json,os,sys
O=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
f=sys.argv[1] if len(sys.argv)>1 else ''
rows=[json.loads(l) for l in open(O+'/res-vc.jsonl')]
seen={}
for r in rows: seen[r['name']]=r
for n,r in seen.items():
    if f and f not in n: continue
    if 'error' in r: print(f"{n:22s} ERR {r['error'][:80]}"); continue
    mp={}
    p=f"{O}/rx/mp_{n}/mp.json"
    if os.path.exists(p): mp=json.load(open(p))
    print(f"{n:22s} {r['bytes']:6d} M {r['M']:5d} {r['M']-2251:+5d} Mperm {mp.get('Mperm','-'):>5} Mhc {mp.get('Mhc','-'):>5} {r['genes'][:40]:40s} {r['dreg']}")
