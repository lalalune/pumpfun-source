def edit(f):
    a='%_185 = icmp ne i8 %683, 0'; assert f.count(a)==1
    f=f.replace(a,'%_185 = icmp ne i8 %571, 0')
    b='  store i8 %571, ptr %696, align 8\n'; assert f.count(b)==1
    f=f.replace(b,'  %hrx.p = getelementptr inbounds i8, ptr %_318, i64 165\n  %hrx = load i8, ptr %hrx.p, align 1\n  store i8 %hrx, ptr %696, align 8\n')
    return f
