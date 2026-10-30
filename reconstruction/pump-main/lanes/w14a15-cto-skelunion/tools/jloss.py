#!/usr/bin/env python3
"""jloss.py name..: per 0x800 orig region, matched orig insns in raw alignment vs jump-masked alignment."""
import sys,os,difflib,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import oracle, jm as J
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a15-cto-skelunion')
ow=oracle.orig_window(); o=oracle.mask(ow); oj=J.jm(ow)
oa=[];x=0
for t in o: oa.append(x); x+=len(t)
def hits(a,b):
    h=collections.Counter()
    for i,j,s in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks():
        for k in range(s): h[oa[i+k]//0x800*0x800]+=1
    return h
for n in sys.argv[1:]:
    raw=open(f'{O}/rx/{n}/fn.bin','rb').read()
    r=hits(o,oracle.mask(raw)); j=hits(oj,J.jm(raw))
    print(n,'raw',sum(r.values()),'jm',sum(j.values()))
    print('  ',' '.join(f'{k:#x}:{r[k]}/{j[k]}' for k in sorted(j)))
