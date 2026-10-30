def edit(t):
    s = t.index('\nbb88:'); e = t.index('\n\n', s+2)
    blk = t[s:e]
    t = t[:s] + t[e:]
    a = "  br i1 %last, label %bb85, label %bb88\n"
    assert t.count(a) == 1
    i = t.index(a) + len(a)
    return t[:i] + blk + '\n' + t[i:]
