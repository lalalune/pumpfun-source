def edit(f):
    return f.replace('%_270.1 = load ptr, ptr %269, align 8','%_270.1i = load i64, ptr %269, align 8\n  %_270.1 = inttoptr i64 %_270.1i to ptr')
