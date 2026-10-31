#!/usr/bin/env python3
"""jdiff.py <obj|.bin>: align (jump-masked) vs original; list matched jump tokens whose raw offsets differ, with orig pc, target and our pc/target."""
import sys,os,difflib,struct
T=os.path.dirname(os.path.abspath(__file__))
src=open(T+'/rx.py').read(); G={}; exec(compile(src[:src.index("OUT=os.environ")],'rxhead','exec'),G)
O=G['orig_window']()
def toks(raw):
    out=[];pcs=[];pc=0
    for t in G['mask'](raw):
        t=bytearray(t); op=t[0]; pcs.append(pc); pc+=len(t)
        if op&7==5 and op not in (0x85,0x95): t[2:4]=b'\0\0'
        out.append(bytes(t))
    return out,pcs
p=sys.argv[1]; c=open(p,'rb').read() if p.endswith('.bin') else G['elf_fn'](p,G['KEEP'])
ot,op_=toks(O); ct,cp=toks(c)
sm=difflib.SequenceMatcher(None,ot,ct,autojunk=False); bad=0; rows=[]
for b in sm.get_matching_blocks():
    for k in range(b.size):
        i=b.a+k;j=b.b+k; a=op_[i]; bb=cp[j]
        if O[a]&7==5 and O[a] not in (0x85,0x95):
            oo=struct.unpack_from('<h',O,a+2)[0]; co=struct.unpack_from('<h',c,bb+2)[0]
            if oo!=co: rows.append((a,a+8+oo*8,bb,bb+8+co*8)); bad+=1
print('mismatched jumps',bad)
for r in rows: print('orig %#06x->%#06x  ours %#06x->%#06x  dshift %+d'%(r[0],r[1],r[2],r[3],(r[3]-r[2])-(r[1]-r[0])))
