#!/usr/bin/env python3
"""frame.py <unstripped.so> : stack-frame facts of admin_cto::execute (min r10 offset, first r10 store offset, distinct r10 offsets)."""
import sys, re, struct
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w12a13-cto-sizeknobs/reconstruction/harness'
sys.path.insert(0,H)
from win import Cand, demangle


def facts(raw):
    offs=[]; first=None; i=0
    while i < len(raw):
        op=raw[i]; regs=raw[i+1]; dst=regs&15; src=regs>>4; off=struct.unpack_from('<h',raw,i+2)[0]
        cls=op&7
        if cls in (1,):      # LDX: src is base
            if src==10: offs.append(off)
        elif cls in (2,3):   # ST/STX: dst is base
            if dst==10:
                offs.append(off)
                if first is None: first=off
        i+=16 if op==0x18 else 8
    return {'min_r10': min(offs) if offs else None, 'first_store': first, 'n_r10': len(offs), 'distinct_r10': len(set(offs))}


def frame_of(so, sym=r'admin_cto::execute$'):
    c=Cand(so)
    for s,n,nm in c.funcs:
        if re.search(sym, demangle(nm)):
            return facts(c.fn(s,n))
    return None


if __name__=='__main__':
    print(frame_of(sys.argv[1]))
