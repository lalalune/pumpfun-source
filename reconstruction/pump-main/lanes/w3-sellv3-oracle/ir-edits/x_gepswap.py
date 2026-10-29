def edit(f):
    a="  %_7 = getelementptr inbounds i8, ptr %a, i64 112\n  %_8 = getelementptr inbounds i8, ptr %a, i64 64\n"
    b="  %_8 = getelementptr inbounds i8, ptr %a, i64 64\n  %_7 = getelementptr inbounds i8, ptr %a, i64 112\n"
    return f.replace(a,b)
