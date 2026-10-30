#!/usr/bin/env python3
# oratio.py <orig_fn.txt> <cand_fn.txt> : approx token ratio (calls and lddw immediates masked), sizes, lddw/to_string counts
import sys,re,difflib
def toks(f):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip()
        s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        out.append(s)
    return out
a=toks(sys.argv[1]); b=toks(sys.argv[2])
sm=difflib.SequenceMatcher(None,a,b,autojunk=False)
bb=sum(16 if x.startswith('lddw') else 8 for x in b)
print(f'ratio {sm.ratio():.5f} insns {len(a)} {len(b)} bytes {bb} lddw {sum(x.startswith("lddw") for x in b)}')
