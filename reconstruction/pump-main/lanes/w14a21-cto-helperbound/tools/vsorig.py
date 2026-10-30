#!/usr/bin/env python3
"""vsorig.py name.. [--step 0x400]: per orig region, median (cand_off - orig_off) of sk-aligned insns, plus count."""
import sys,os,difflib,statistics,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import absratio as A
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a21-cto-helperbound')
def dis(n):
    t=subprocess.run(['bash',O+'/tools/dis.sh',f'{O}/rx/{n}/m.o'],capture_output=True,text=True).stdout
    return [(int(l.split()[0],16),l.split(None,1)[1]) for l in t.split('\n') if len(l.split(None,1))>1]
orig=[]; x=0
for l in open(O+'/orig.rel'):
    p=l.split(None,1)
    if len(p)>1: orig.append((x,p[1])); x+=16 if p[1].startswith('lddw') else 8
step=int(os.environ.get("STEP","0x400"),16)
for n in sys.argv[1:]:
    b=dis(n)
    sm=difflib.SequenceMatcher(None,[A.norm(t,True) for _,t in orig],[A.norm(t,True) for _,t in b],autojunk=False); d={}
    for x,y,s in sm.get_matching_blocks():
        for i in range(s): d.setdefault(orig[x+i][0]//step,[]).append(b[y+i][0]-orig[x+i][0])
    print(n.ljust(6),' '.join('%x:%+d'%(k*step,int(statistics.median(v))) for k,v in sorted(d.items()) if len(v)>8))
