#!/usr/bin/env python3
# mratio.py orig_fn cand_fn... : ratio exact / frame-masked / frame+reg-masked / jumps masked
import sys,re,difflib
def toks(f,mode):
    out=[]
    for l in open(f):
        p=l.split(None,1)
        if len(p)<2: continue
        s=p[1].split(';')[0].strip()
        s=re.sub(r'^call .*','call',s); s=re.sub(r'lddw (r\d+), .*',r'lddw \1',s)
        if mode>=1: s=re.sub(r'r10 - 0x[0-9a-f]+','FP',s); s=re.sub(r'^add64 (r\d+), -0x[0-9a-f]+$',r'add64 \1, -A',s)
        if mode>=2: s=re.sub(r'^(j\w+ .*)[+-]0x[0-9a-f]+$',r'\1J',s); s=re.sub(r'^ja .*','ja',s)
        if mode>=3: s=re.sub(r'\br[0-9]\b','R',s)
        out.append(s)
    return out
o=[toks(sys.argv[1],m) for m in range(4)]
for c in sys.argv[2:]:
    r=[difflib.SequenceMatcher(None,o[m],toks(c,m),autojunk=False).ratio() for m in range(4)]
    print(f'{c:40s} exact {r[0]:.5f} fp {r[1]:.5f} fp+j {r[2]:.5f} fp+j+reg {r[3]:.5f}')
