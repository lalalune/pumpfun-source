def edit(f):
    f=f.replace('  %amount = alloca [8 x i8], align 8\n  store i64 %0, ptr %amount, align 8\n','')
    f=f.replace('  %_5 = load i64, ptr %amount, align 8, !noundef !2\n','  %_5 = add i64 %0, 0\n')
    f=f.replace('  %_25 = load i64, ptr %amount, align 8, !noundef !2\n','  %_25 = add i64 %0, 0\n')
    return f
