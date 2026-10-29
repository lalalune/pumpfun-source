def edit(t):
    a='  %_208.0.i = extractvalue { i64, ptr } %104, 0\n  %_208.1.i = extractvalue { i64, ptr } %104, 1\n'
    b='  %_208.1.i = extractvalue { i64, ptr } %104, 1\n  %_208.0.i = extractvalue { i64, ptr } %104, 0\n'
    assert t.count(a)==1; return t.replace(a,b)
