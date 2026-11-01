#!/usr/bin/env python3
"""lcsbp.py: bit-parallel LCS length of two token lists (Hyyro/Allison-Dix). Experiment only."""
def lcs(a,b):
    # bitset over positions of a
    pos={}
    for i,t in enumerate(a): pos[t]=pos.get(t,0)|(1<<i)
    S=0; mask=(1<<len(a))-1
    V=mask  # V = ~S style (Hyyro): use the Allison-Dix formulation
    for t in b:
        M=pos.get(t,0)
        U=V&M
        V=((V+U)|(V-U))&mask
    return len(a)-bin(V).count('1')
if __name__=='__main__':
    import sys,os
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
    import oracle,fx
    O=fx.O()
    for p in sys.argv[1:]:
        C=oracle.mask(open(p,'rb').read())
        print(p,'LCS',lcs(O,C),'difflib',fx.Mof(open(p,'rb').read())[0])
