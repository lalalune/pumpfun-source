#!/usr/bin/env python3
"""amap.py <so|o> [off...]: map candidate offsets to orig offsets via sk alignment (nearest matched insn)"""
import sys,os,subprocess,difflib,bisect
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T); import absratio as A
M=os.path.dirname(T)
def lines(p):
    t=subprocess.run(['bash',T+'/disso.sh',p],capture_output=True,text=True).stdout
    return [l.split(None,1) for l in t.split('\n') if len(l.split(None,1))>1]
OL=[l.split(None,1) for l in open(M+'/orig.rel') if len(l.split(None,1))>1]
def amap(p):
    C=lines(p)
    a=[A.norm(x[1],True) for x in OL]; b=[A.norm(x[1],True) for x in C]
    sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    pairs=[]
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): pairs.append((int(C[blk.b+k][0],16),int(OL[blk.a+k][0],16)))
    return pairs,C
if __name__=='__main__':
    pairs,C=amap(sys.argv[1]); cs=[p[0] for p in pairs]
    for o in sys.argv[2:]:
        o=int(o,16); i=max(0,bisect.bisect_right(cs,o)-1); print(hex(o),'->',hex(pairs[i][1]+(o-pairs[i][0])), '(anchor',hex(pairs[i][0]),')')
