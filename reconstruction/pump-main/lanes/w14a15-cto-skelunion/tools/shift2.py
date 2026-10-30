#!/usr/bin/env python3
"""shift2.py name...: median (cand_off - orig_off) of sk-aligned insns per 0x400 orig region."""
import sys,os,difflib,statistics,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import absratio as A
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a15-cto-skelunion')
def dis(n):
    t=subprocess.run(['bash',O+'/tools/dis.sh',f'{O}/rx/{n}/m.o'],capture_output=True,text=True).stdout
    r=[];x=0
    for l in t.split('\n'):
        p=l.split(None,1)
        if len(p)>1: r.append((x,p[1])); x+=16 if p[1].startswith('lddw') else 8
    return r
od=[];x=0
for l in A.O: od.append((x,l)); x+=16 if l.startswith('lddw') else 8
ot=[A.norm(t,True) for _,t in od]
for n in sys.argv[1:]:
    cd=dis(n); ct=[A.norm(t,True) for _,t in cd]
    sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); d={}
    for a,b,s in sm.get_matching_blocks():
        for i in range(s): d.setdefault(od[a+i][0]//0x400,[]).append(cd[b+i][0]-od[a+i][0])
    print(n,' '.join('%x:%+d'%(k*0x400,int(statistics.median(v))) for k,v in sorted(d.items()) if len(v)>8))
