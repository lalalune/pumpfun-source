#!/usr/bin/env python3
# sbs.py <name> <lo> <hi> [clo chi]: side by side of orig and candidate fn.bin
import os,sys,itertools
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
sys.path.insert(0,OUT+'/tools')
import dis as D, oracle
n=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16)
clo=int(sys.argv[4],16) if len(sys.argv)>4 else lo; chi=int(sys.argv[5],16) if len(sys.argv)>5 else hi
o=[(a-D.W,t) for a,t in D.dis(oracle.orig_window())]
c=[(a-D.W,t) for a,t in D.dis(open(f'{OUT}/fx/{n}/fn.bin','rb').read())]
oo=[x for x in o if lo<=x[0]<=hi]; cc=[x for x in c if clo<=x[0]<=chi]
for a,b in itertools.zip_longest(oo,cc):
    s1=f'{a[0]:#06x} {a[1]}' if a else ''
    s2=f'{b[0]:#06x} {b[1]}' if b else ''
    print(f'{s1:44s} | {s2}')
