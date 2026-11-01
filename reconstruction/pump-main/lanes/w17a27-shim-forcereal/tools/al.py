#!/usr/bin/env python3
"""al.py <fn.bin> <lo_hex> <hi_hex> [--asm tagged.s] [--mode 3]: side-by-side view of the candidate (cand offsets lo..hi)
against the original via an m<mode> (default m3: regs/frame/jumps masked) difflib alignment. '=' marks scorer-exact
(m0) token equality. Experiment only."""
import sys,os,re,difflib
T=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,T)
import d as D, skel, oracle
def asm_tags(path):
    out=[]
    for l in open(path):
        if re.match(r'^\s*(\.|#)',l) or re.match(r'^[A-Za-z_.$"0-9]+:',l) or not l.strip(): continue
        m=re.search(r'# rp (\S+)(.*)$',l)
        out.append((m.group(1)+m.group(2)).strip() if m else '')
    return out
def main():
    a=sys.argv[1:]; mode=3; asm=None
    if '--mode' in a: k=a.index('--mode'); mode=int(a[k+1]); del a[k:k+2]
    if '--asm' in a: k=a.index('--asm'); asm=a[k+1]; del a[k:k+2]
    cb=D.load(a[0]); lo=int(a[1],16); hi=int(a[2],16)
    O=oracle.orig_window(); od=D.dis(O); cd=D.dis(cb)
    to=skel.toks(O,mode); tc=skel.toks(cb,mode); t0o=skel.toks(O,0); t0c=skel.toks(cb,0)
    tags=asm_tags(asm) if asm else None
    sm=difflib.SequenceMatcher(None,to,tc,autojunk=False)
    c2o={}
    for blk in sm.get_matching_blocks():
        for k in range(blk.size): c2o[blk.b+k]=blk.a+k
    # also full-mode-0 alignment for exactness flag
    sm0=difflib.SequenceMatcher(None,t0o,t0c,autojunk=False); ex=set()
    for blk in sm0.get_matching_blocks():
        for k in range(blk.size): ex.add(blk.b+k)
    for ci,(off,s) in enumerate(cd):
        if off<lo or off>hi: continue
        oi=c2o.get(ci)
        os_=f'{od[oi][0]:#06x} {od[oi][1]}' if oi is not None else ''
        mark='=' if ci in ex else ('~' if oi is not None else ' ')
        tg=(' | '+tags[ci][:60]) if tags and ci<len(tags) else ''
        print(f'{off:#06x} {mark} {s:<34} {os_:<40}{tg}')
if __name__=='__main__': main()
