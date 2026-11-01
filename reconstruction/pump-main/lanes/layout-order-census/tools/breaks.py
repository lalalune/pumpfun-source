import json,sys,re,bisect
sys.path.insert(0,'./worktrees/restore/reconstruction/harness')
from win import demangle
from score import original_windows, candidate_functions
cand=sys.argv[1]; ref=sys.argv[2]
d=json.load(open(ref))
pair={int(k,16):int(v,16) for k,v in d['pair'].items()}
W={w['start']:w['bytes'] for w in original_windows()}
names={}
for a,s,n in candidate_functions(cand): names.setdefault(a,[]).append(n)
cst=sorted(names); nxt={cst[i]:cst[i+1] for i in range(len(cst)-1)}
MAIN_END=[a for a in cst if names[a][0]=='__rust_alloc_error_handler'][0]
def base(n): return re.sub(r'17h[0-9a-f]{16}E$','',n)
def cat(a,b):
    na,nb=names[a][0],names[b][0]
    if a>=MAIN_END or b>=MAIN_END: reg='dep'
    else: reg='main'
    if base(na)==base(nb): return reg+':same-generic(hash)'
    loc=lambda n: 'pump_recovered' in n and not re.match(r'_ZN(11anchor_lang|4core|5alloc|3std)',n)
    return reg+':'+('local' if loc(na) and loc(nb) else 'mixed' if loc(na) or loc(nb) else 'upstream')
os_=sorted(pair)
from collections import Counter
C=Counter(); rows=[]
cands_used=set(pair.values())
for i in range(len(os_)-1):
    a,b=pair[os_[i]],pair[os_[i+1]]
    # skip candidate functions not paired (aliases/extra fns)
    n=nxt.get(a)
    while n is not None and n not in cands_used: n=nxt.get(n)
    if n!=b:
        c=cat(a,b); C[c]+=1
        rows.append((hex(os_[i]),hex(os_[i+1]),c,demangle(names[a][0])[:70],demangle(names[b][0])[:70]))
print(C, sum(C.values()))
for r in rows: print(*r,sep=' | ')
