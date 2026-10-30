#!/usr/bin/env python3
# mratio2.py <orig_fn> <cand_fn>: token ratio with r10 offsets masked (frame-blind)
import sys,re,difflib
def toks(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'add64 (r\d), -0x[0-9a-f]+',r'add64 \1, -X',s)
        out.append(s)
    return out
a=toks(sys.argv[1]); b=toks(sys.argv[2])
print(f'masked {difflib.SequenceMatcher(None,a,b,autojunk=False).ratio():.5f}')
