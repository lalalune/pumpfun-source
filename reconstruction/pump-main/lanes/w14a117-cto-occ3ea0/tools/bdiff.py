#!/usr/bin/env python3
"""bdiff.py a.bin b.bin [minlen]: L2 (frame+regs masked) diff of two admin_cto fn blobs; prints non-equal opcode runs."""
import sys,os,difflib,types
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
from bdis import decode
C=types.ModuleType('C'); C.__dict__['__file__']=T+'/cls.py'; _s=open(T+'/cls.py').read(); exec(_s[:_s.index('def main')],C.__dict__)
def tk(f):
    b=open(f,'rb').read(); ins=decode(b); return ins,[C.mask(b[d['off']:d['off']+d['n']],2) for d in ins]
mi,mt=tk(sys.argv[1]); ni,nt=tk(sys.argv[2]); mn=int(sys.argv[3]) if len(sys.argv)>3 else 8
sm=difflib.SequenceMatcher(None,mt,nt,autojunk=False)
for tag,a1,a2,b1,b2 in sm.get_opcodes():
    if tag!='equal' and (a2-a1>=mn or b2-b1>=mn):
        o=lambda I,i:'%04x'%I[i]['off'] if i<len(I) else 'end'
        print(tag,'A %s+%d'%(o(mi,a1),a2-a1),'B %s+%d'%(o(ni,b1),b2-b1))
        for d in (ni[b1:b1+4] if b2>b1 else mi[a1:a1+4]): print('    ',d['txt'])
