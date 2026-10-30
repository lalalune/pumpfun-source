#!/usr/bin/env python3
# mm.py <orig_fn> <cand_fn>...: matched orig insns M under raw / reg-masked / frame-masked / both masks (difflib, calls+lddw masked like regcmp)
import sys,re,difflib
def toks(f,mr,mf):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        if mf: s=re.sub(r'r10 - 0x[0-9a-f]+','r10-F',s); s=re.sub(r'add64 (r\d+), -0x[0-9a-f]{3}$',r'add64 \1, -F',s)
        if mr: s=re.sub(r"^(j\w+ .*), [+-]0x[0-9a-f]+$",r"\1, J",s); s=re.sub(r"^ja [+-]0x[0-9a-f]+$","ja J",s)
        out.append(s)
    return out
def M(a,b): return sum(bl.size for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks())
for f in sys.argv[2:]:
    r=[]
    for mr,mf in ((0,0),(1,0),(0,1),(1,1)):
        r.append(M(toks(sys.argv[1],mr,mf),toks(f,mr,mf)))
    print(f.split('/')[-2], 'raw',r[0],'reg',r[1],'frame',r[2],'both',r[3])
