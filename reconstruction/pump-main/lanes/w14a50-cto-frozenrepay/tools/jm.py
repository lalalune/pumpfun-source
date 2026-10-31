#!/usr/bin/env python3
"""jm.py <name...>: ratio and M with jump offsets masked, from rx/<n>/fn.bin (base: current baseline as 'MAIN')."""
import sys,os,difflib
sa=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a50-cto-frozenrepay')
def jm(raw):
    out=[]
    for x in mask(raw):
        op=x[0]
        if (op&7) in (5,6) and op not in (0x85,0x95): x=x[:2]+b'\0\0'+x[4:]
        out.append(x)
    return out
o=jm(orig_window())
for n in [x for x in sa[1:] if x=="MAIN" or os.path.exists(f"{O}/rx/{x}/fn.bin")]:
    raw=elf_fn(os.path.expanduser('~/.cache/pumpfun-reconstruction/w11/current-baseline/unstripped.so'),KEEP) if n=='MAIN' else open(f'{O}/rx/{n}/fn.bin','rb').read()
    sm=difflib.SequenceMatcher(None,o,jm(raw),autojunk=False)
    print(n,len(raw),'jm',round(sm.ratio(),5),'jM',sum(b.size for b in sm.get_matching_blocks()))
