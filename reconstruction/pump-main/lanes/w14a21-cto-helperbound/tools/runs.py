#!/usr/bin/env python3
"""runs.py name lo hi: matching runs (sk-normalized) orig range -> cand range, in orig order, for orig [lo,hi)."""
import sys,os,difflib,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import absratio as A
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
def dis(n):
    t=subprocess.run(['bash',O+'/tools/dis.sh',f'{O}/rx/{n}/m.o'],capture_output=True,text=True).stdout
    return [(int(l.split()[0],16),l.split(None,1)[1]) for l in t.split('\n') if len(l.split(None,1))>1]
orig=[];x=0
for l in open(O+'/orig.rel'):
    p=l.split(None,1)
    if len(p)>1: orig.append((x,p[1])); x+=16 if p[1].startswith('lddw') else 8
n=sys.argv[1]; lo=int(sys.argv[2],16); hi=int(sys.argv[3],16); C=dis(n)
sm=difflib.SequenceMatcher(None,[A.norm(t,True) for _,t in orig],[A.norm(t,True) for _,t in C],autojunk=False)
for a,b,s in sm.get_matching_blocks():
    if s and lo<=orig[a][0]<hi and s>=3: print(f'orig {orig[a][0]:05x}-{orig[a+s-1][0]:05x} -> cand {C[b][0]:05x}-{C[b+s-1][0]:05x}  n={s}  d={C[b][0]-orig[a][0]:+d}')
