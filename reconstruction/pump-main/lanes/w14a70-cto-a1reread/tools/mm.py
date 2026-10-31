#!/usr/bin/env python3
"""mm.py name... : M (matched masked tokens) and jM (jump offsets also masked) of rx/<name>/fn.bin vs the original."""
import sys, os, difflib, importlib.util
H='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w11-baseline/reconstruction/harness'
sys.path.insert(0,H)
from score import original_windows
OUT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def mask(raw,j=False):
    m=bytearray(raw); i=0; toks=[]
    while i<len(raw):
        op=raw[i]; n=16 if op==0x18 else 8
        if op==0x85: m[i+1]&=0x0f; m[i+4:i+8]=b'\0'*4
        if op==0x18: m[i+4:i+8]=b'\0'*4; m[i+12:i+16]=b'\0'*4
        if j and (op&7) in (5,6) and op not in (0x85,0x95): m[i+2:i+4]=b'\0\0'
        toks.append(bytes(m[i:i+n])); i+=n
    return toks
o=[w for w in original_windows() if w['start']==0x22a10][0]['raw']
for n in sys.argv[1:]:
    c=open(f'{OUT}/rx/{n}/fn.bin','rb').read()
    r=[]
    for j in (False,True):
        a=mask(o,j); b=mask(c,j); sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
        r.append(sum(x.size for x in sm.get_matching_blocks()))
    print(n, len(c), 'M', r[0], 'jM', r[1], 'ratio', round(2*r[0]/(len(mask(o))+len(mask(c))),5))
