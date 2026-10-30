#!/usr/bin/env python3
"""errseq.py <so|orig|m.o>...: error-site lines in CODE LAYOUT order (address of the From<AnchorError> call)."""
import sys,struct,re
sys.path.insert(0,'/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w13a52-cto-ovarm/reconstruction/harness')
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a52-cto-ovarm/tools')
def scan(raw):
    i=0; imms=[]; out=[]
    while i<len(raw):
        op,regs,off,imm=struct.unpack_from('<BBhi',raw,i)
        if op in (0x62,0x6a,0x72,0x7a): imms.append(imm)
        if op==0x85:
            lines=[x for x in imms if 280<=x<800]; codes=[x for x in imms if 2000<=x<6200]
            if lines and codes: out.append((i,lines[-1]))
            imms=[]
        i+=16 if op==0x18 else 8
    return out
def fn(p):
    if p=='orig':
        from score import sections,BASE
        from original_input import resolve_original
        b=resolve_original(BASE/'original.so').read_bytes(); s=sections(b); t=s['.text']; o=0x22a10-t['addr']+t['offset']; return b[o:o+27400]
    if p.endswith('.bin'): return open(p,'rb').read()
    import rx_elf
    return rx_elf.get(p)
for p in sys.argv[1:]:
    print(p[-30:], ' '.join(f'{l}' for a,l in scan(fn(p))))
