#!/usr/bin/env python3
"""mdiff.py <a.bin> <b.bin> [min]: masked (regs, imms, offsets) opcode-run diff between two admin_cto blobs."""
import sys,re,difflib
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a10-shim-newpieces/tools'); import dis as D
def m(s):
    s=re.sub(r'r\d','r',s); s=re.sub(r'0x[0-9a-f]+','N',s); s=re.sub(r'[+-]N','N',s); return s
A=D.dis(open(sys.argv[1],'rb').read()); B=D.dis(open(sys.argv[2],'rb').read()); mn=int(sys.argv[3]) if len(sys.argv)>3 else 3
sm=difflib.SequenceMatcher(None,[m(s) for _,s in A],[m(s) for _,s in B],autojunk=False)
print('masked M',sum(x.size for x in sm.get_matching_blocks()),len(A),len(B))
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal' or (i2-i1)+(j2-j1)<mn: continue
    print(tag, hex(A[i1][0]) if i1<len(A) else 'end', i2-i1, hex(B[j1][0]) if j1<len(B) else 'end', j2-j1)
