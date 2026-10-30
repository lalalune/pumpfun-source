#!/usr/bin/env python3
"""regmatch.py <fn.bin>...: exact-metric matched tokens per orig region (0x400 bins) for each candidate (vs first = reference)."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); g={}; exec(src.split("OUT=os.environ")[0],g)
orig=g['orig_window'](); o=g['mask'](orig)
# offsets of orig tokens
offs=[];p=0
for t in o: offs.append(p); p+=len(t)
B=0x800
res=[]
for f in sys.argv[1:]:
    c=g['mask'](open(f,'rb').read())
    sm=difflib.SequenceMatcher(None,o,c,autojunk=False)
    bins=[0]*((p+B-1)//B)
    for a,b,n in sm.get_matching_blocks():
        for i in range(a,a+n): bins[offs[i]//B]+=1
    res.append((f.split('/')[-2],bins,round(sm.ratio(),5)))
print('bin   '+' '.join('%10s'%n[:10] for n,_,_ in res))
for i in range(len(res[0][1])):
    print('%04x  '%(i*B)+' '.join('%10d'%(r[1][i]-(res[0][1][i] if j else 0)) for j,r in enumerate(res)))
print('ratio '+' '.join('%10s'%r[2] for r in res))
