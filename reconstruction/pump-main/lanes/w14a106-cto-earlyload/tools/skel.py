#!/usr/bin/env python3
"""skel.py fn.bin... : difflib matched instructions against the original admin_cto::execute at three masking levels.
L0 = call/lddw immediates and jump targets masked; L1 = also r10 frame offsets masked; L2 = also register numbers masked
(the instruction-selection / block skeleton). Text form from dis.py."""
import sys,os,re,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import dis as D
def norm(b,lvl):
    out=[]
    for _,s in D.d(b):
        s=re.sub(r'call 0x\w+','call',re.sub(r'lddw (r\d+), 0x\w+',r'lddw \1',s))
        if s.split()[0][0]=='j': s=re.sub(r', [0-9a-f]+$','',s) if s.split()[0]!='ja' else 'ja'
        if lvl>=1: s=re.sub(r'r10-0x\w+','fp',s)
        if lvl>=2: s=re.sub(r'r\d+','r',s)
        out.append(s)
    return out
o=D.orig(); O=[norm(o,l) for l in range(3)]
for f in sys.argv[1:]:
    c=open(f,'rb').read(); r=[]
    for l in range(3):
        sm=difflib.SequenceMatcher(None,O[l],norm(c,l),autojunk=False); r.append(sum(m.size for m in sm.get_matching_blocks()))
    print(f,len(c),'L0',r[0],'L1',r[1],'L2',r[2])
