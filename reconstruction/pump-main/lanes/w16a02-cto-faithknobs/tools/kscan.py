#!/usr/bin/env python3
"""kscan.py <res-<newmain>.jsonl>: for captures built on the new main (ev6+A6, 1f4e396): M against 2,251, where the byte
delta lands relative to the new main (region.py against H_ev6_A6), and the splice with sh_iflet on top (the remaining
-8 B polarity fix; its +8 B pay band on the new main is cand 0x5448-0x5578). Experiment only."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import splice,region
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w16a02-cto-faithknobs')
main=open(O+'/rx/main/fn.bin','rb').read(); shif=open(O+'/rx/sh_iflet/fn.bin','rb').read(); NEW=O+'/rx/H_ev6_A6/fn.bin'
for l in open(sys.argv[1]):
    r=json.loads(l)
    if 'error' in r: print(r['name'],'ERR'); continue
    fb=f"{O}/rx/{r['name']}/fn.bin"
    if not os.path.exists(fb): continue
    x=open(fb,'rb').read(); rg=region.regions(fb,NEW)
    s=splice.splice(main,[x,shif])
    print(f"{r['name']:16s} {len(x):6d} {len(x)-27400:+5d} M {r['M']} {r['M']-2251:+d} | +shif {'conflict' if s is None else (len(s),splice.M(s))} | {rg.get('by_region')} {[c[:3] for c in (rg.get('changes') or [])][:3]}")
