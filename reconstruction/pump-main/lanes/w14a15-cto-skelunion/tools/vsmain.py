#!/usr/bin/env python3
"""vsmain.py a b: per 0x400 region of a, median offset (b_off - a_off) of sk-aligned insns; shows where b gains/loses bytes vs a."""
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
a=dis(sys.argv[1]); b=dis(sys.argv[2]); step=int(sys.argv[3],16) if len(sys.argv)>3 else 0x400
sm=difflib.SequenceMatcher(None,[A.norm(t,True) for _,t in a],[A.norm(t,True) for _,t in b],autojunk=False); d={}
for x,y,s in sm.get_matching_blocks():
    for i in range(s): d.setdefault(a[x+i][0]//step,[]).append(b[y+i][0]-a[x+i][0])
print(' '.join('%x:%+d'%(k*step,int(statistics.median(v))) for k,v in sorted(d.items()) if len(v)>8))
