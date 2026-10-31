#!/usr/bin/env python3
"""sinkx.py in.ll out.ll A BC : generalised sink76 (post-opt IR oracle, experiment only).
A = 7-byte target piece memcpy (target.i.sroa.0 -> target.sroa.0), BC = 9-byte piece via _48.sroa.11.
loc: 76 (stay in bb76, main), s19 (bb22 + top of bb19), s19h (bb22 + new bb19h on the holder edge, = sink76),
all (bb22 + bb19h + bb21 top), e22 (bb22 + bb19 end, before the holder br)."""
import sys,re
src,dst,la,lbc=sys.argv[1:5]
t=open(src).read()
i=t.index('\nbb76:'); j=t.index('br i1 %shared.sroa.0.0.off0, label %bb19, label %bb22',i)
blk=t[i:j].split('\n')
A=[l for l in blk if 'target.sroa.0, ptr' in l and 'memcpy' in l]+[l for l in blk if 'lifetime.end.p0(i64 7, ptr nonnull %target.i.sroa.0)' in l]
BC=[l for l in blk if ('memcpy' in l and ('%_48.sroa.11, ptr' in l or 'target.sroa.8, ptr' in l))]+[l for l in blk if 'lifetime.end' in l and ('target.i.sroa.9' in l or '_48.sroa.11' in l)]
assert len(A)==2 and len(BC)==4,(len(A),len(BC))
# keep original intra-order
order=[l for l in blk if l in A or l in BC]
def sel(units): return [l for l in order if l in units]
moving={'A':(la,A),'BC':(lbc,BC)}
mv={}
for k,(loc,ls) in moving.items():
    if loc!='76':
        for l in ls: blk.remove(l)
t=t[:i]+'\n'.join(blk)+t[j:]
locs={}
for k,(loc,ls) in moving.items():
    if loc!='76': locs.setdefault(loc,[]).extend(ls)
def ins_after_label(t,lab,lines):
    k=t.index('\n'+lab+':'); e=t.index('\n',k+1); return t[:e+1]+'\n'.join(lines)+'\n'+t[e+1:]
def ins_before_term(t,lab,lines,term):
    k=t.index('\n'+lab+':'); e=t.index(term,k); return t[:e]+'\n'.join(lines).lstrip()+'\n  '+t[e:]
need_h=[]; need21_ends=[]; need21_full=[]; top19=[]; end19=[]
for loc,ls in locs.items():
    ls=sel(ls)
    t=ins_after_label(t,'bb22',ls)
    if loc=='s19': top19+=ls
    elif loc=='e22': end19+=ls
    elif loc in ('s19h','all'): need_h+=ls
    if loc=='all': need21_full+=ls
    elif loc in ('s19h',): need21_ends+=[l for l in ls if 'lifetime.end' in l]
if top19: t=ins_after_label(t,'bb19',sel(top19))
if end19: t=ins_before_term(t,'bb19',sel(end19),'br i1 %_0.sroa.0.0.off0.i')
if need_h:
    t=t.replace('br i1 %_0.sroa.0.0.off0.i, label %bb26, label %bb21','br i1 %_0.sroa.0.0.off0.i, label %bb19h, label %bb21',1)
    k=t.index('\nbb19:'); e=t.index('\n\n',k+1)
    t=t[:e+1]+'\nbb19h:                                             ; preds = %bb19\n'+'\n'.join(sel(need_h))+'\n  br label %bb26\n'+t[e+1:]
    k=t.index('\nbb26:'); e=t.index('\n\n',k+1); b=t[k:e]
    b=b.replace(', %bb19 ]',', %bb19h ]').replace('preds = %bb19,','preds = %bb19h,')
    t=t[:k]+b+t[e:]
if need21_full: t=ins_after_label(t,'bb21',sel(need21_full))
if need21_ends: t=ins_after_label(t,'bb21',need21_ends)
open(dst,'w').write(t)
