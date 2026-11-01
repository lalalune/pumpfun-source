#!/usr/bin/env python3
"""h1.py: IR edits on m0n/ve1n: holder computed once as and-1 at the CtoState block and reused at the P1 curve store (orig r3&1 at +0x610, spilled -0x950). Experiment only."""
import sys,os,json
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); sys.path.insert(0,os.path.join(os.path.dirname(T),'tools12'))
import ce3,pscore
A44='  %i44 = and i8 %arg, -3\n'
A676='  %i676 = and i8 %arg, 1\n'
def h1(t,mode='a'):
    assert t.count(A44)==1 and t.count(A676)==1
    if mode=='a':   # test becomes and-1 (same semantics on range [0,3)), P1 reuses it
        t=t.replace(A44,'  %i44 = and i8 %arg, 1\n').replace(A676,'')
        t=t.replace('store i8 %i676,','store i8 %i44,')
    elif mode=='b': # keep main's test, add a separate early and-1 for P1
        t=t.replace(A44,A44+'  %hf = and i8 %arg, 1\n').replace(A676,'')
        t=t.replace('store i8 %i676,','store i8 %hf,')
    elif mode=='c': # test and-1 only (P1 still recomputes)
        t=t.replace(A44,'  %i44 = and i8 %arg, 1\n')
    return t
if __name__=='__main__':
    for nm,base in (('m0',ce3.BASE),('ve1n',ce3.ve1n())):
        for md in 'abc':
            t=h1(base,md); open(os.environ['LANE_OUT']+f'/ir/{nm}_h1{md}.ll','w').write(t)
            print(json.dumps(pscore.score_text(t,f'{nm}_h1{md}',keepobj=True)))
