#!/usr/bin/env python3
# mm.py <xdir>... : M under masks: full (oratio), jumps masked (J), frame masked (F), both (JF)
import sys,re,difflib,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a19-cto-framebasis')
def toks(f,j,fr):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        if j: s=re.sub(r'^(j\w+ .*?)([+-]0x[0-9a-f]+|[+-]\d+)$',r'\1J',s)
        if fr: s=re.sub(r'r10 - 0x[0-9a-f]+','r10-X',s); s=re.sub(r'add64 (r\d), -0x[0-9a-f]+',r'add64 \1, -X',s)
        out.append(s)
    return out
for x in sys.argv[1:]:
    r=[]
    for j,fr in ((0,0),(1,0),(0,1),(1,1)):
        a=toks(O+'/orig_fn.txt',j,fr); b=toks(x+'/fn.txt',j,fr)
        sm=difflib.SequenceMatcher(None,a,b,autojunk=False); r.append(sum(m.size for m in sm.get_matching_blocks()))
    print(f"{os.path.basename(x):16s} n={len(b)} M={r[0]} J={r[1]} F={r[2]} JF={r[3]} ratio={2*r[0]/(len(a)+len(b)):.5f}")
