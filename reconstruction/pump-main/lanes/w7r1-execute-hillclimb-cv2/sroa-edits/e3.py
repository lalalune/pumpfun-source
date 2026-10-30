def edit(f):
    a='  %268 = getelementptr inbounds i8, ptr %_84, i64 8\n  %_270.0 = load i64, ptr %268, align 8\n'
    b='  %269 = getelementptr inbounds i8, ptr %_84, i64 16\n  %_270.1 = load ptr, ptr %269, align 8\n'
    assert a+b in f
    return f.replace(a+b,b+a)
