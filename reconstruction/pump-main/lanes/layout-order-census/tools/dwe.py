"""Data-window offset census: of the matched windows with data lddw, how many already point at the
same in-section offsets as the original (they turn raw once .text size and section bases match).
dwe.py <cand.so> <refined.json>"""
import sys; sys.path.insert(0,__file__.rsplit('/',1)[0])
import fastmodel as F, census as C
from collections import Counter
M=F.Model(sys.argv[1],sys.argv[2]); cand=open(sys.argv[1],'rb').read()
o,c=M.osec,M.csec; ok=tot=0; bad=Counter(); badw=[]
for st in M.ost:
    if st in M.UN: continue
    a=M.pair[st]; oo=C.operands(M.wins[st]['raw'],st,o); co=C.operands(C.body(cand,c,a,M.units[a][0]),a,c)
    d=[(x,y) for x,y in zip(oo,co) if x[1]=='lddw' and x[3]!='.text']
    if not d: continue
    tot+=1; g=[x[3]==y[3] and x[2]-o[x[3]]['addr']==y[2]-c[y[3]]['addr'] for x,y in d]
    ok+=all(g); bad.update(x[3] for (x,y),gg in zip(d,g) if not gg)
print(f'data windows {tot}, all offsets equal {ok}, bad operands {dict(bad)}; rodata {c[".rodata"]["size"]:#x} vs {o[".rodata"]["size"]:#x}')
