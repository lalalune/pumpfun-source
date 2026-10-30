def edit(f):
    a='  %_0 = alloca [16 x i8], align 8\n'
    f=f.replace(a,'',1)
    return f.replace('start:\n','start:\n'+a,1)
