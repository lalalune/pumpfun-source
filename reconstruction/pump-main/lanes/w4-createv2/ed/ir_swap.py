def edit(t):
    a='  %val8.sroa.2 = alloca [24 x i8], align 8\n'; b='  %quote_mint = alloca [32 x i8], align 8\n'
    assert t.count(a)==1 and t.count(b)==1
    return t.replace(a,'@@A@@').replace(b,a).replace('@@A@@',b)
