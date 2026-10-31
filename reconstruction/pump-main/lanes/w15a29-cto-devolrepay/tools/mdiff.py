#!/usr/bin/env python3
"""mdiff.py a.bin b.bin: M of each vs original (rx mask), and which instructions (by offset) are LCS-matched in a but not b and vice versa."""
import sys,os,difflib
T='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a29-cto-devolrepay'
sys.path.insert(0,T+'/rp'); from bdis import decode
src=open(T+'/tools/rx.py').read().split('OUT=os.environ')[0]; exec(src)
O=mask(open(T+'/orig.bin','rb').read())
def mm(f):
    c=open(f,'rb').read(); ci=decode(c); ct=mask(c)
    sm=difflib.SequenceMatcher(None,O,ct,autojunk=False); matched={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): matched[b+k]=a+k
    return ci,matched
A=mm(sys.argv[1]); B=mm(sys.argv[2])
print('M',len(A[1]),len(B[1]))
# report matched sets by instruction text+offset
def rep(X,Y,lab):
    ci,m=X; cj,mj=Y
    s=set((ci[i]['off'],ci[i]['txt'],m[i]) for i in m); s2=set((cj[i]['off'],cj[i]['txt'],mj[i]) for i in mj)
    oi=decode(open(T+'/orig.bin','rb').read())
    for off,txt,oidx in sorted(s-s2): print(lab,'%04x'%off,txt,'-> orig %04x'%oi[oidx]['off'])
rep(A,B,'onlyA'); rep(B,A,'onlyB')
