#!/usr/bin/env python3
# mms.py <orig> <cand>...: M raw vs spill-slot-masked (r10 offsets >= LO, default 0x8d0) vs object-masked (< LO)
import sys,re,difflib,os
LO=int(os.environ.get('LO','0x8d0'),16)
def toks(f,mode):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].strip(); s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        def rep(m):
            v=int(m.group(1),16)
            return 'r10-S' if (mode=='s' and v>=LO) or (mode=='o' and v<LO) else m.group(0)
        if mode!='raw': s=re.sub(r'r10 - 0x([0-9a-f]+)',rep,s)
        out.append(s)
    return out
def M(a,b): return sum(bl.size for bl in difflib.SequenceMatcher(None,a,b,autojunk=False).get_matching_blocks())
for f in sys.argv[2:]:
    print(f.split('/')[-2],*[f'{m}:{M(toks(sys.argv[1],m),toks(f,m))}' for m in ('raw','s','o')])
