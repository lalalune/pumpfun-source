#!/usr/bin/env python3
"""chk.py <a.o|.so|fn.bin> <b...>: per-0x800 orig chunk matched-token counts (global SequenceMatcher blocks) for each candidate."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
O=G['mask'](G['orig_window']())
def load(p):
    if p.endswith('.bin'): return open(p,'rb').read()
    return G['elf_fn'](p,G['KEEP'])
off=[];a=0
for t in O: off.append(a); a+=len(t)
CH=int(os.environ.get('CH','0x800'),16)
rows=[]
for p in sys.argv[1:]:
    c=G['mask'](load(p)); sm=difflib.SequenceMatcher(None,O,c,autojunk=False)
    cnt={}
    for bl in sm.get_matching_blocks():
        for i in range(bl.a,bl.a+bl.size): k=off[i]//CH; cnt[k]=cnt.get(k,0)+1
    rows.append((os.path.basename(os.path.dirname(p))+'/'+os.path.basename(p),cnt,round(sm.ratio(),5)))
ks=sorted(set(k for r in rows for k in r[1]))
print('chunk   '+' '.join('%9s'%r[0][-9:] for r in rows))
for k in ks:
    v=[r[1].get(k,0) for r in rows]
    if len(set(v))>1: print('%#06x  '%(k*CH)+' '.join('%9d'%x for x in v)+('   d=%+d'%(v[1]-v[0]) if len(v)>1 else ''))
print('ratio   '+' '.join('%9s'%r[2] for r in rows))
