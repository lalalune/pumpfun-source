def edit(t):
    a='  %_218 = getelementptr inbounds i8, ptr %_618, i64 8\n'
    assert t.count(a)==1; t=t.replace(a,'',1)
    b='  %_870 = getelementptr inbounds i8, ptr %_618, i64 648\n'
    assert t.count(b)==1; t=t.replace(b,b+a,1)
    return t
