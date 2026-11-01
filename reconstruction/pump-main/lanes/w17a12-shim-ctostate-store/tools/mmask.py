#!/usr/bin/env python3
"""mmask.py <fn.bin>...: M under masks: raw | frame(r10 offsets) | regs | frame+regs | frame+regs+jumps."""
import sys,os,difflib
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import oracle
def toks(raw,frame=False,regs=False,jumps=False):
    out=[];i=0
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8; t=bytearray(raw[i:i+n])
        if op==0x85: t[1]&=0x0f; t[4:8]=b'\0'*4
        if op==0x18: t[4:8]=b'\0'*4; t[12:16]=b'\0'*4
        dst=t[1]&0xf; src=t[1]>>4; cls=op&7
        if frame:
            # ldx: src is base; stx/st: dst is base
            if cls==1 and src==10: t[2:4]=b'\0\0'
            if cls in (2,3) and dst==10: t[2:4]=b'\0\0'
            if cls==7 and dst!=10 and False: pass
        if jumps and cls in (5,6) and op not in (0x85,0x95): t[2:4]=b'\0\0'
        if regs and op!=0x85:
            nd=dst if dst==10 else 0; ns=src if src==10 else 0
            t[1]=(ns<<4)|nd
        out.append(bytes(t)); i+=n
    return out
O=oracle.orig_window()
def M(c,**k):
    a=toks(O,**k); b=toks(c,**k); sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
    return sum(x.size for x in sm.get_matching_blocks())
if __name__=='__main__':
  for p in sys.argv[1:]:
    c=open(p,'rb').read()
    print(os.path.basename(os.path.dirname(p)), len(c), M(c), M(c,frame=True), M(c,regs=True), M(c,frame=True,regs=True), M(c,frame=True,regs=True,jumps=True))
