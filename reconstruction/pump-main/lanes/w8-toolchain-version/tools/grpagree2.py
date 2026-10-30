"""(w8-toolchain-version copy of layout-order-census grpagree.py: reuses refined.json, lists failing L/D groups.)
Hash-group order agreement per region: for groups of same-base-name instances, does our order equal the original's?"""
import sys,re,json,subprocess
import os.path as _p
sys.path.insert(0,'.'); sys.path.insert(0,_p.join(_p.dirname(_p.abspath(__file__)),'..','..','layout-order-census','tools'))  # run from layout-order-census/tools (refine.py)
cand=sys.argv[1]; out=sys.argv[2]
import os
if not os.path.exists(out): subprocess.run([sys.executable,'refine.py',cand,out],check=True,stdout=subprocess.DEVNULL)
import census as C
d=json.load(open(out)); pair={int(k,16):int(v,16) for k,v in d['pair'].items()}; inv={v:k for k,v in pair.items()}
units={}
for a,s,n in C.candidate_functions(cand): units.setdefault(a,n)
cst=sorted(units); mend=[a for a in cst if units[a]=='__rust_alloc_error_handler'][0]
main=[a for a in cst if a<mend and a in inv]
lstart=next(main[i] for i in range(1,len(main)) if units[main[i]]<units[main[i-1]])
reg=lambda a:'U' if a<lstart else 'L' if a<mend else 'D'
base=lambda a: re.sub(r'17h[0-9a-f]{16}E$','',units[a])
g={}
for a in cst:
    if a in inv: g.setdefault((reg(a),base(a)),[]).append(a)
from collections import Counter
tot=Counter(); ok=Counter(); pairs_ok=Counter(); pairs=Counter()
for (r,b),m in g.items():
    if len(m)<2: continue
    tot[r]+=1; o=[inv[a] for a in m]
    ok[r]+= o==sorted(o)
    for i in range(len(o)):
        for j in range(i+1,len(o)): pairs[r]+=1; pairs_ok[r]+= o[i]<o[j]
for r in 'ULD': print(r,'groups',tot[r],'exact',ok[r],'pairwise %d/%d'%(pairs_ok[r],pairs[r]))
print('lis',open(out).read().count('')>0 and len(d['ooo']))
for (r,b),m in g.items():
    if len(m)>1 and r in 'DL':
        o=[inv[a] for a in m]
        if o!=sorted(o): print(r,len(m),b[:110],[hex(x) for x in o],[units[a][-20:-1] for a in m])
