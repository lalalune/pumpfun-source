import re
P='@_ZN14pump_recovered6extend21prepare_bonding_curve17hd9c6422a7455e9efE'
def edit(t):
    t=t.replace('declare hidden { i64, ptr } '+P+'(','declare hidden void '+P+'(ptr sret([16 x i8]) align 8, ',1)
    i=t.index('  %2 = tail call { i64, ptr } '+P)
    j=t.index('\n',i)
    line=t[i:j]
    args=line[line.index(P)+len(P)+1:]
    new='  call void '+P+'(ptr noalias nocapture noundef sret([16 x i8]) align 8 dereferenceable(16) %sret0, '+args+'\n  %3 = load i64, ptr %sret0, align 8\n  %sret0p = getelementptr inbounds i8, ptr %sret0, i64 8\n  %12 = load ptr, ptr %sret0p, align 8'
    t=t[:i]+new+t[j:]
    t=t.replace('  %3 = extractvalue { i64, ptr } %2, 0\n','',1)
    t=t.replace('bb60:                                             ; preds = %start\n  %12 = extractvalue { i64, ptr } %2, 1\n','bb60:                                             ; preds = %start\n',1)
    k=t.index('define hidden { i64, ptr } @_ZN14pump_recovered5trade4sell17h'); k=t.index('start:\n',k)+7
    t=t[:k]+'  %sret0 = alloca [16 x i8], align 8\n'+t[k:]
    return t
