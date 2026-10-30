A='  %_0.sroa.0.4 = phi i64 [ %_43.sroa.16.1.ph, %bb67 ]'
def f(t):
    i=t.index(A); j=t.index('\n',i)+1
    return t[:j]+'  call void asm sideeffect "", "{r6}"(ptr %_0.sroa.11.4)\n'+t[j:]
EDITS=[f]
