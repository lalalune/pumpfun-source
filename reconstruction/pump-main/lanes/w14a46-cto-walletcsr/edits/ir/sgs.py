import os,runpy
W=os.environ.get('SW','16,1')
a,b=W.split(',')
EDITS=runpy.run_path('e/ir/sg.py')['EDITS']+[("  br i1 %7, label %bb1, label %bb6\n","  br i1 %7, label %bb1, label %bb6, !prof !99991\n"),
lambda t: t+'\n!99991 = !{!"branch_weights", i32 %s, i32 %s}\n'%(a,b)]
