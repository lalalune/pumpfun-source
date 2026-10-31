#!/usr/bin/env python3
"""edge19h.py in.ll out.ll BODY : split the bb19 -> bb26 (shared+holder) edge with a new block holding BODY lines
(';'-separated IR, may be empty). Post-opt IR oracle, experiment only."""
import sys
src,dst=sys.argv[1:3]; body=[x for x in (sys.argv[3] if len(sys.argv)>3 else '').split(';') if x.strip()]
t=open(src).read()
t=t.replace('br i1 %_0.sroa.0.0.off0.i, label %bb26, label %bb21','br i1 %_0.sroa.0.0.off0.i, label %bb19h, label %bb21',1)
k=t.index('\nbb19:'); e=t.index('\n\n',k+1)
t=t[:e+1]+'\nbb19h:                                             ; preds = %bb19\n'+''.join('  '+b.strip()+'\n' for b in body)+'  br label %bb26\n'+t[e+1:]
k=t.index('\nbb26:'); e=t.index('\n\n',k+1); b=t[k:e]
b=b.replace(', %bb19 ]',', %bb19h ]').replace('preds = %bb19,','preds = %bb19h,')
t=t[:k]+b+t[e:]
open(dst,'w').write(t)
