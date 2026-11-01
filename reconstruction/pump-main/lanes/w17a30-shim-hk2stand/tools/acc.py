#!/usr/bin/env python3
"""acc.py <lo_hex> <hi_hex> [cand.bin|so ...]: r10-relative accesses (and lea r10+imm) with offsets in [-hi,-lo] per
region, original vs candidates. Prints offset -> list of region:count."""
import sys,os,collections
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import rc
def accs(raw):
    d=collections.defaultdict(list); i=0
    prev=None
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8; cl=op&7
        dst=raw[i+1]&15; src=raw[i+1]>>4; off=int.from_bytes(raw[i+2:i+4],'little',signed=True)
        imm=int.from_bytes(raw[i+4:i+8],'little',signed=True)
        if (cl==1 and src==10) or (cl in (2,3) and dst==10): d[off].append(i)
        if op==0xbf and src==10: prev=(dst,i)
        elif op==0x07 and prev and prev[0]==dst and prev[1]==i-8: d[imm].append(i); prev=None
        else: prev=None if op!=0xbf else prev
        i+=n
    return d
lo,hi=int(sys.argv[1],16),int(sys.argv[2],16)
O=rc.orig_window(); srcs=[('orig',O)]+[(os.path.basename(os.path.dirname(p)) or p,rc.elf_fn(p)) for p in sys.argv[3:]]
A=[(n,accs(b)) for n,b in srcs]
offs=sorted({o for _,d in A for o in d if -hi<=o<=-lo},reverse=True)
for o in offs:
    row=[]
    for n,d in A:
        c=collections.Counter(rc.reg_of(x) for x in d.get(o,[]))
        row.append(','.join(f'{k}{v}' for k,v in sorted(c.items())) or '.')
    print(f'{-o:#7x} '+' | '.join(f'{r:22s}' for r in row))
