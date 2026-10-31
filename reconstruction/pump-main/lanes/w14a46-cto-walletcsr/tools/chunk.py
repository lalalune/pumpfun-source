#!/usr/bin/env python3
"""chunk.py <a.ll|dis> <b.ll|dis> [chunk=0x400]: per-orig-chunk frame-masked (wf2 norm) matched-token counts, a vs b."""
import sys,os,difflib,subprocess
T=os.path.dirname(os.path.abspath(__file__))
g={'__file__':T+'/wf2.py'}; src=open(T+'/wf2.py').read().split("O=rd(")[0]; exec(src,g)
O=g['rd'](open(T+'/../or.dis'))
def load(p):
    d=subprocess.run(['bash',T+'/dll.sh',p],capture_output=True,text=True).stdout.split('\n') if p.endswith('.ll') else open(p).read().split('\n')
    return g['rd'](d)
def per(C,ch):
    sm=difflib.SequenceMatcher(None,[x[1] for x in O],[x[1] for x in C],autojunk=False); r={}
    for a,b,n in sm.get_matching_blocks():
        for i in range(a,a+n): k=O[i][0]//ch; r[k]=r.get(k,0)+1
    return r
ch=int(sys.argv[3],16) if len(sys.argv)>3 else 0x400
A=per(load(sys.argv[1]),ch); B=per(load(sys.argv[2]),ch)
for k in sorted(set(A)|set(B)):
    d=B.get(k,0)-A.get(k,0)
    if d: print('%05x %4d %4d %+4d'%(k*ch,A.get(k,0),B.get(k,0),d))
print('total',sum(A.values()),sum(B.values()))
