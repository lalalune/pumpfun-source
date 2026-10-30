#!/usr/bin/env python3
"""o9edit.py <in m.ll> <out m.ll>: IR oracle o9 - bb60 (event/Clock Err merge) branches straight to bb64, so bb62
(post-sweep Err merge) keeps only the two CPI preds (lets the sweep exit's swept copy coalesce first)."""
import sys
t=open(sys.argv[1]).read()
i=t.index('\nbb60:'); j=t.index('\n\n',i+1); blk=t[i:j]
b2=blk.replace('  br label %bb62','  %o9p = extractvalue { i64, ptr } %.pn, 1\n  br label %bb64'); assert b2!=blk
t=t[:i]+b2+t[j:]
for a in [', [ %.pn, %bb60 ]',', [ %_0.sroa.0.1, %bb60 ]']:
    assert t.count(a)==1,a; t=t.replace(a,'')
t=t.replace('preds = %bb60, %bb41,','preds = %bb41,',1)
a='%_0.sroa.11.4 = phi ptr ['; assert t.count(a)==1; t=t.replace(a,a+' %o9p, %bb60 ], [')
a='%_0.sroa.0.4 = phi i64 ['; assert t.count(a)==1; t=t.replace(a,a+' %_0.sroa.0.1, %bb60 ], [')
open(sys.argv[2],'w').write(t)
