# oracle: payload word 1 hinted to r9 by an empty inline-asm use in bb67 (the Err join), right after its phis
def f(t):
    i=t.index('\n  %_0.sroa.0.4 = phi i64 ')+1; j=t.index('\n',i)+1
    return t[:j]+'  call void asm sideeffect "", "{r9}"(ptr %_0.sroa.11.4)\n'+t[j:]
EDITS=[f]
