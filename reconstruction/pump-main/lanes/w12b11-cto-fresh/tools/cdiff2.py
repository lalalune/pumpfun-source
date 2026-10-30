#!/usr/bin/env python3
"""cdiff2.py orig_annot cand_annot LABEL OCC [maxhunks]: register+frame-abstracted diff of one chunk, with real orig/cand addresses."""
import sys,re,difflib
def ab(ins):
    ins=re.sub(r'lddw (r\d+), 0x[0-9a-f]+',r'lddw \1, X',ins)
    ins=re.sub(r'r10 - 0x[0-9a-f]+','FP',ins)
    ins=re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',ins)
    ins=re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',ins)
    ins=re.sub(r'\br[0-9]\b','R',ins)
    return ins
def chunk(p,label,occ):
    cur=[];c=0
    for l in open(p):
        if not l.strip(): continue
        a,rest=l.rstrip('\n').split(None,1)
        r=rest.split(';')[0].strip()
        if ' call ' in ' '+rest or r=='exit':
            if label in rest:
                c+=1
                if c==occ: return cur+[(a,r)]
            cur=[]
        else: cur.append((a,r))
o=chunk(sys.argv[1],sys.argv[3],int(sys.argv[4])); c=chunk(sys.argv[2],sys.argv[3],int(sys.argv[4]))
mx=int(sys.argv[5]) if len(sys.argv)>5 else 40
sm=difflib.SequenceMatcher(None,[ab(x[1]) for x in o],[ab(x[1]) for x in c],autojunk=False)
print('ratio',round(sm.ratio(),3),len(o),len(c))
k=0
for t,i1,i2,j1,j2 in sm.get_opcodes():
    if t=='equal': continue
    print(f'--- {t} orig[{i1}:{i2}] cand[{j1}:{j2}]')
    for x in o[i1:i2][:14]: print('  -',x[0],x[1])
    for x in c[j1:j2][:14]: print('  +',x[0],x[1])
    k+=1
    if k>=mx: break
