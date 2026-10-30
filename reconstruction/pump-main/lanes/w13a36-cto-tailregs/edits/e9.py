def edit(f):
    a='  store i64 %_90.sroa.0.0, ptr %702, align 8\n'; assert f.count(a)==1
    return f.replace(a,'  store i64 0, ptr %702, align 8\n')
