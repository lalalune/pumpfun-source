#!/usr/bin/env python3
"""absr.py name... : frame-abstracted ratio of rx/<name>/fn.bin vs original (r10 offsets and add64 imm after mov r10 masked)."""
import sys,os,difflib
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a28-cto-entrycopy2'
src=open(O+'/tools/rx.py').read(); pre=src[:src.index("OUT=os.environ.get('RX_OUT'")]
g={}; exec(pre,g)
def toks(raw):
    t=g['mask'](raw); out=[]; fp=set()
    for x in t:
        b=bytearray(x); op=b[0]; dst=b[1]&0xf; srcr=b[1]>>4
        cls=op&7
        if cls in (2,3) and dst==10: b[2:4]=b'\0\0'   # st/stx [r10+off]
        if cls==1 and srcr==10: b[2:4]=b'\0\0'        # ldx [r10+off]
        if op==0xbf and srcr==10: fp.add(dst)
        elif op==0x07 and dst in fp: b[4:8]=b'\0'*4; fp.discard(dst)
        elif cls in (4,7) and dst in fp: fp.discard(dst)
        out.append(bytes(b))
    return out
orig=toks(g['orig_window']())
for n in sys.argv[1:]:
    p=n if n.endswith('.bin') else O+'/rx/'+n+'/fn.bin'
    c=toks(open(p,'rb').read())
    print(n, round(difflib.SequenceMatcher(None,orig,c,autojunk=False).ratio(),5))
