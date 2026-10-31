#!/usr/bin/env python3
"""thr.py in.ll out.ll [which] : (holder-first tree IR, t_h_nest) thread the join bb83 for its fee-None preds:
bb44.i (holder) -> copy of bb83 -> bb19 ; bb45.i (non-holder) -> copy -> bb26 ; bb83 keeps only the fee-Some pred bb58.i.
which = hn (both, default) | h | n. SSA fixed with phis in bb19/bb26. Oracle only."""
import sys,re
src,dst=sys.argv[1:3]; which=sys.argv[3] if len(sys.argv)>3 else 'hn'
t=open(src).read()
def blk(n):
    k=t.index('\n'+n+':'); e=t.index('\n\n',k+1); return k,e
k,e=blk('bb83'); B=t[k:e].split('\n')
hdr=B[1]; P7=B[2]; P8=B[3]; body=B[4:-1]; term=B[-1]; assert 'phi i64' in P7 and 'phi ptr' in P8 and 'br i1' in term
def inc(p,pred): return re.search(r'\[ (%[\w.]+), %'+re.escape(pred)+r' \]',p).group(1)
new=[]; preds_keep=['bb58.i','bb44.i','bb45.i']
P19=[];P26=[]
for pred,tgt,tag in (('bb44.i','bb19','h'),('bb45.i','bb26','n')):
    if tag not in which: continue
    preds_keep.remove(pred)
    v7,v8=inc(P7,pred),inc(P8,pred)
    nb='bb83.'+tag
    new.append(f'\n{nb}:                                             ; preds = %{pred}\n'+'\n'.join(body)+f'\n  br label %{tgt}\n')
    k2,e2=blk(pred); x=t[k2:e2]; x=x.replace('label %bb83,','label %'+nb+',').replace('label %bb83\n','label %'+nb+'\n'); t=t[:k2]+x+t[e2:]
    (P19 if tgt=='bb19' else P26).append((nb,v7,v8))
# rebuild bb83 phis with remaining preds
def keep(p):
    return re.sub(r', \[ [^\]]+, %(bb44\.i|bb45\.i) \]|\[ [^\]]+, %(bb44\.i|bb45\.i) \], ',lambda m: '' if (m.group(1) or m.group(2)) not in preds_keep else m.group(0),p)
k,e=blk('bb83'); B=t[k:e].split('\n')
B[1]='bb83:                                             ; preds = '+', '.join('%'+p for p in preds_keep)
B[2]=keep(B[2]); B[3]=keep(B[3]); t=t[:k]+'\n'.join(B)+t[e:]
# phis at bb19 / bb26
def addphis(b,lst,sfx):
    global t
    if not lst: return None
    k,e=blk(b); x=t[k:e].split('\n')
    preds=re.search(r'; preds = (.*)',x[1]).group(1)
    x[1]=x[1].replace(preds,preds+', '+', '.join('%'+nb for nb,_,_ in lst))
    p7=f'  %p{sfx}.7 = phi i64 [ %target.i.sroa.7.0, %bb83 ], '+', '.join(f'[ {v7}, %{nb} ]' for nb,v7,_ in lst)
    p8=f'  %p{sfx}.8 = phi ptr [ %target.i.sroa.8.0, %bb83 ], '+', '.join(f'[ {v8}, %{nb} ]' for nb,_,v8 in lst)
    x=x[:2]+[p7,p8]+x[2:]; t=t[:k]+'\n'.join(x)+t[e:]
    return sfx
s19=addphis('bb19',P19,'19'); s26=addphis('bb26',P26,'26')
k,e=blk('bb33'); x=t[k:e]
for b,s in (('bb19',s19),('bb21',s19),('bb22',s19),('bb28',s26),('bb29',s26)):
    if not s: continue
    x=x.replace(f'[ %target.i.sroa.8.0, %{b} ]',f'[ %p{s}.8, %{b} ]').replace(f'[ %target.i.sroa.7.0, %{b} ]',f'[ %p{s}.7, %{b} ]')
t=t[:k]+x+t[e:]
i=t.index('\nbb83:'); t=t[:i]+''.join(new)+t[i:]
open(dst,'w').write(t)
