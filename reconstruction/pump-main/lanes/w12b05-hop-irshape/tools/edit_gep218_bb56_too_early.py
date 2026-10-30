def edit(t):
    G='  %_218 = getelementptr inbounds i8, ptr %_618, i64 8\n'
    assert t.count(G)==1; t=t.replace(G,'',1)
    a='  %_202 = icmp ugt i64 %_854110218, %reserves\n'
    assert t.count(a)==1
    return t.replace(a, a+'  %gl56 = load ptr, ptr %ctx.8.val, align 8, !nonnull !2, !align !3, !noundef !2\n  %_218 = getelementptr inbounds i8, ptr %gl56, i64 8\n',1)
