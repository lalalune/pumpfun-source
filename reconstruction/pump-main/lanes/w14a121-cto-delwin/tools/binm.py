#!/usr/bin/env python3
"""binm.py a b [bin]: per-orig-bin matched-token counts of rx/a vs rx/b (b - a)"""
import sys,os,difflib
D=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+'/'
A=sys.argv[1:]; sys.argv=['x','n']
exec(open(D+'tools/rx.py').read().split('OUT=os.environ')[0])
o=mask(orig_window()); offs=[];x=0
for t in o: offs.append(x); x+=len(t)
B=int(A[2],0) if len(A)>2 else 0x400
def prof(n):
    c=mask(open(D+'rx/'+n+'/fn.bin','rb').read()); p={}
    for a,b,s in difflib.SequenceMatcher(None,o,c,autojunk=False).get_matching_blocks():
        for i in range(a,a+s): k=offs[i]//B; p[k]=p.get(k,0)+1
    return p
pa=prof(A[0]); pb=prof(A[1])
print(' '.join('%x:%+d'%(k*B,pb.get(k,0)-pa.get(k,0)) for k in sorted(set(pa)|set(pb)) if pb.get(k,0)!=pa.get(k,0)))
