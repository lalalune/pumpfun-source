def edit(t):
    a='  %_218 = getelementptr inbounds i8, ptr %_618, i64 8\n'
    assert t.count(a)==1; t=t.replace(a,'',1)
    b='  %_618 = load ptr, ptr %ctx.8.val, align 8, !nonnull !2, !align !3, !noundef !2\n'
    assert t.count(b)==1; t=t.replace(b,b+a,1)
    return t
