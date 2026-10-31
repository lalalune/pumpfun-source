#!/usr/bin/env python3
"""mcount.py <fn.bin|so>...: matched score tokens M, token counts and ratio against the original (rx.py masks)"""
import sys,os,difflib
sa=sys.argv[:]; sys.argv=['x','n']
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'rx.py')).read().split('OUT=os.environ')[0])
OT=mask(orig_window())
for p in sa[1:]:
    raw=open(p,'rb').read() if p.endswith('.bin') else elf_fn(p,KEEP)
    c=mask(raw); sm=difflib.SequenceMatcher(None,OT,c,autojunk=False); M=sum(x.size for x in sm.get_matching_blocks())
    print(f'{p.split("/")[-2] if p.endswith("fn.bin") else p.split("/")[-1]:20s} M {M} Lo {len(OT)} Lc {len(c)} ratio {2*M/(len(OT)+len(c)):.5f} bytes {len(raw)}')
