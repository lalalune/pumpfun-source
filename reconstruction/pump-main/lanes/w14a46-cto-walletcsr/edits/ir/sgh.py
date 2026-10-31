import os,runpy
B=os.environ['HB']; W=os.environ['HW']; a,b=W.split(',')
LINES={'start':"  br i1 %7, label %bb1, label %bb6\n",'bb1':"  br i1 %10, label %bb2, label %bb6\n",'bb6':"  br i1 %17, label %bb12, label %bb9\n"}
G=[] if os.environ.get('NOG') else runpy.run_path('e/ir/sg.py')['EDITS']
l=LINES[B]
EDITS=G+[(l,l[:-1]+", !prof !99991\n"),lambda t: t+'\n!99991 = !{!"branch_weights", i32 %s, i32 %s}\n'%(a,b)]
