#!/usr/bin/env python3
"""jdiff.py <a> <b>: original jump insns matched (exact token) in a but not b, and vice versa; plus shift profile."""
import sys,os,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import oracle,dis
OUT=os.path.dirname(T)
ow=oracle.orig_window(); oi=dis.split(ow); ot=oracle.mask(ow)
def load(n):
    p=n if os.path.exists(n) else f'{OUT}/fx/{n}/fn.bin'; return open(p,'rb').read()
def matched(raw):
    ci=dis.split(raw); ct=oracle.mask(raw)
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); mp={}
    for a,b,n in sm.get_matching_blocks():
        for k in range(n): mp[a+k]=b+k
    return mp,ci
A,B=sys.argv[1],sys.argv[2]
ma,ca=matched(load(A)); mb,cb=matched(load(B))
def isj(i): op=oi[i][1][0]; return (op&7)==5 and op not in (0x85,0x95)
onlyA=[i for i in ma if i not in mb]; onlyB=[i for i in mb if i not in ma]
print('only in',A,len(onlyA),'jumps',sum(isj(i) for i in onlyA)); print('only in',B,len(onlyB),'jumps',sum(isj(i) for i in onlyB))
for nm,lst,mp,ci in ((A,onlyA,ma,ca),(B,onlyB,mb,cb)):
    print('--',nm)
    for i in sorted(lst): print('  orig %5x -> %5x  %s'%(oi[i][0],ci[mp[i]][0],dis.dec(oi[i][1])))
