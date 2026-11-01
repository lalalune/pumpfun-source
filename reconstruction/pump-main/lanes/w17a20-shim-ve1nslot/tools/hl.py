#!/usr/bin/env python3
"""hl.py: IR 'holder late': compute hopt's and/icmp after validate's mayhem test (orig reloads r3 once at +0x610, in bb6.i)
and the cashback bool at its post-validate use. On m0n / ve1n / ve1nP. Experiment only."""
import sys,os,json,re
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,os.path.join(os.path.dirname(T),'tools12'))
import ce3,pscore,pfirst
A='  %i44 = and i8 %arg, -3\n  %_0.sroa.0.0.off0.i.not = icmp eq i8 %i44, 0\n'
C='  %extract.t = icmp ne i8 %i33, 0\n  %cashback.sroa.0.0.off0 = and i1 %_0.sroa.0.0.off0.i.not, %extract.t\n'
B6='bb6.i:                                            ; preds = %bb12\n'
USE='  %i168 = zext i1 %cashback.sroa.0.0.off0 to i8\n'
def hl(t,mode):
    assert t.count(A+C)==1,'AC'; assert t.count(B6)==1; assert t.count(USE)==1
    t=t.replace(A+C,'')
    if mode=='1':   # holder in bb6.i, cashback at its use
        t=t.replace(B6,B6+A); t=t.replace(USE,C+USE)
    elif mode=='2': # holder + cashback in bb6.i
        t=t.replace(B6,B6+A+C)
    return t
if __name__=='__main__':
    for nm,base in (('m0',ce3.BASE),('ve1n',ce3.ve1n())):
        for md in '12':
            for P in ('','P'):
                x=hl(base,md)
                if P: x=pfirst.pfirst(x)
                n=f'{nm}_hl{md}{P}'; open(os.environ['LANE_OUT']+f'/ir/{n}.ll','w').write(x)
                print(json.dumps(pscore.score_text(x,n,keepobj=True)))
