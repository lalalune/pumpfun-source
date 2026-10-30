#!/usr/bin/env python3
"""r10.py orig|<so> LO HI : list instructions of admin_cto window touching [r10-T] with LO<=T<=HI (T positive),
including 'mov rX,r10; add rX,-T' address computations."""
import sys,struct,subprocess,re
sys.path.insert(0,str(__import__('pathlib').Path(__file__).resolve().parents[4]/'harness'))
av=sys.argv; sys.argv=av[:1]
import score
sys.argv=av
which,lo,hi=av[1],int(av[2],16),int(av[3],16)
if which=='orig':
    W={x['start']:x for x in score.original_windows()}
    raw=W[0x22a10]['raw']; base=0x22a10
else:
    from pathlib import Path
    cs=Path(which).read_bytes(); secs=score.sections(cs)
    f=next(x for x in score.candidate_functions(Path(which)) if re.search(r'admin_cto7execute',x[2]))
    raw=score.body(cs,secs,f[0],f[1]); base=f[0]
i=0; last_mov={}
out=[]
while i<len(raw):
    op,regs,off,imm=struct.unpack_from('<BBhi',raw,i); k=16 if op==0x18 else 8
    dst,src=regs&15,regs>>4; cls=op&7
    hit=None
    if cls in (1,2,3):
        b=src if cls==1 else dst
        if b==10 and lo<=-off<=hi: hit=f'{"ld" if cls==1 else "st"} T={-off:#x} w={ {0x18:8,0x10:1,0x00:4,0x08:2}.get(op&0x18,"?")} op={op:#x} {"r%d"%dst if cls==1 else ("r%d"%src if cls==3 else "imm %d"%imm)}'
    if op==0xbf and src==10: last_mov[dst]=i
    if op==0x07 and dst in last_mov and last_mov[dst]==i-8 and lo<=-imm<=hi: hit=f'lea r{dst} = r10-{-imm:#x}'
    if hit: out.append((base+i,hit))
    i+=k
for a,h in out: print(f'{a:#x}  {h}')
