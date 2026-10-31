#!/usr/bin/env python3
"""mr.py <res.jsonl|names...> [--sort M|jM|ratio]: per result ratio, bytes, M (exact matched orig insns), jM (jump-masked matches)."""
import sys,os,difflib,json
ARGV=sys.argv[:]
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle
from jm import jm
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a42-cto-levy1port')
o=oracle.mask(oracle.orig_window()); oj=jm(oracle.orig_window())
a=ARGV[1:]; key='M'
if '--sort' in a: i=a.index('--sort'); key=a[i+1]; a=a[:i]+a[i+2:]
rows=[]
for x in a:
    if x.endswith('.jsonl'): rows+= [json.loads(l) for l in open(x) if l.strip()]
    else: rows.append(json.load(open(f'{O}/rx/{x}/res.json')))
out=[]
for r in rows:
    if 'ratio' not in r: continue
    try: raw=open(f"{O}/rx/{r['name']}/fn.bin",'rb').read()
    except Exception: continue
    c=oracle.mask(raw); M=sum(s for _,_,s in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks())
    J=sum(s for _,_,s in difflib.SequenceMatcher(None,oj,jm(raw),autojunk=False).get_matching_blocks())
    r['M']=M; r['jM']=J; out.append(r)
out.sort(key=lambda r:-r[key])
for r in out: print(f"{r['name']:40s} {r['ratio']:.5f} {r['bytes']:6d} M {r['M']:5d} jM {r['jM']:5d}")
