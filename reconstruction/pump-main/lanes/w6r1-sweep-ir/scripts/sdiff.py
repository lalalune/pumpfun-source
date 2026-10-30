import re,sys,difflib
def L(p):
    out=[];off=0
    for l in open(p):
        s=l.strip()
        if not s: continue
        x=re.sub(r'([+-]0x[0-9a-f]+)$','J',s) if re.match(r'(ja|j[a-z]+ )',s) else s
        x=re.sub(r'r10 - 0x[0-9a-f]+','r10-S',re.sub(r'\br[0-9]\b','r',x))
        out.append((off,x)); off+=16 if s.startswith('lddw') else 8
    return out
o=L('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w6r1-sweep-ir/orig-norm.txt'); c=L(sys.argv[1])
sm=difflib.SequenceMatcher(None,[x for _,x in o],[x for _,x in c],autojunk=False)
for tag,i1,i2,j1,j2 in sm.get_opcodes():
    if tag=='equal': continue
    oo=o[i1][0] if i1<len(o) else o[-1][0]; cc=c[j1][0] if j1<len(c) else c[-1][0]
    print(f'{tag:8s} orig {oo:#6x} +{i2-i1:3d}   cand {cc:#6x} +{j2-j1:3d}   ', ' | '.join(x for _,x in o[i1:min(i2,i1+3)]), ' >> ', ' | '.join(x for _,x in c[j1:min(j2,j1+3)]))
