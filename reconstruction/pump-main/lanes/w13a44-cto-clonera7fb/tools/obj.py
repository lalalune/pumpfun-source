#!/usr/bin/env python3
"""obj.py <so|fn.bin>...: clone-run objectives for 0x22a10: clonefeat spill/reg, and per-0x200 segment
reg+frame-masked ('both') matched tokens over orig 0x3e00-0x4a00 (segstat), plus plain matched there."""
import sys,os,difflib,collections,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ctoracle as co, tokio, clonefeat, segstat_lib as sl
otok,_=co.orig_tokens()
for p in sys.argv[1:]:
    ct=tokio.toks(p); s,r=clonefeat.feats(ct)
    seg=sl.segs(otok,ct,0x200)
    both={hex(k):v[3] for k,v in seg.items() if 0x3e00<=k<0x4a00}
    plain=sum(v[0] for k,v in seg.items() if 0x3e00<=k<0x4a00)
    print(json.dumps({'f':p.split('/')[-2] if p.endswith('fn.bin') else p,'cf':f'{s}/{r}','both42':both.get('0x4200'),'both44':both.get('0x4400'),'both_sum':sum(both.values()),'plain_sum':plain}))
