#!/usr/bin/env python3
# d.py <name> [lo hi]: disassemble fx/<name>/fn.bin in window offsets
import sys,os,subprocess
OUT=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1')
sys.path.insert(0,OUT+'/tools')
import dis as D
n=sys.argv[1]; p=f'{OUT}/fx/{n}/fn.bin' if not n.endswith('.bin') else n
lo=int(sys.argv[2],16) if len(sys.argv)>2 else 0; hi=int(sys.argv[3],16) if len(sys.argv)>3 else 1<<30
b=open(p,'rb').read()
for a,t in D.dis(b):
    a-=D.W
    if lo<=a<=hi: print(f'{a:#06x} {t}')
