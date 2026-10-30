import re,os
def edit(t):
    t=re.sub(r'  %_94\.sroa\.0\.1 = phi ptr .*\n','',t,1)
    t=t.replace('  %200 = getelementptr inbounds i8, ptr %ctx, i64 33\n','  %_94.sroa.0.1 = getelementptr inbounds i8, ptr %a, i64 32\n  %200 = getelementptr inbounds i8, ptr %ctx, i64 33\n',1)
    if os.environ.get('THR'):
        t=t.replace('br i1 %64, label %bb28, label %bb26.thread','br i1 %64, label %bb28, label %bb30')
        t=re.sub(r'bb26\.thread:[^\n]*\n  %65 = getelementptr inbounds i8, ptr %a, i64 32\n  br label %bb30\n\n','',t)
        t=t.replace('  %70 = phi ptr [ %65, %bb26.thread ], [ %60, %bb26 ]\n','')
        t=t.replace('  %71 = getelementptr inbounds i8, ptr %a, i64 24\n','  %70 = getelementptr inbounds i8, ptr %a, i64 32\n  %71 = getelementptr inbounds i8, ptr %a, i64 24\n',1)
        t=t.replace('%bb26.thread','%bb98')
    return t
