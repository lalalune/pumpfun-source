#!/usr/bin/env python3
"""reloads.py <fn.bin|orig>: counts of stack reloads (ldxdw rX,[r10-..]) and stack stores; JSON."""
import sys,struct,os,json
p=sys.argv[1]
if p=='orig':
    sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
    src=open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read(); g={}
    exec(src.split("OUT=os.environ")[0],g); b=g['orig_window']()
else: b=open(p,'rb').read()
i=0; ld=st=0
while i<len(b):
    op=b[i]; regs=b[i+1]; off=struct.unpack_from('<h',b,i+2)[0]
    if op==0x79 and (regs>>4)==10: ld+=1
    if op in (0x7b,0x7a) and (regs&15)==10: st+=1
    i+=16 if op==0x18 else 8
i=0; tags={}
while i<len(b):
    op=b[i]; regs=b[i+1]; imm=struct.unpack_from('<i',b,i+4)[0]
    if op in (0x15,0x55) and imm==2: tags[regs&15]=tags.get(regs&15,0)+1
    i+=16 if op==0x18 else 8
print(json.dumps({'reloads':ld,'stk_stores':st,'tag2':{('r%d'%k):v for k,v in sorted(tags.items())}}))
