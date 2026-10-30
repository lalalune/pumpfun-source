def edit(f):
    g='  store i8 %571, ptr %696, align 8\n'; assert f.count(g)==1
    return f.replace(g,'  %hrx.p = getelementptr inbounds i8, ptr %_318, i64 165\n  %hrx = load i8, ptr %hrx.p, align 1\n  store i8 %hrx, ptr %696, align 8\n')
