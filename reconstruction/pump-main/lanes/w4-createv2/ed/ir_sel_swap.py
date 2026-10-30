import runpy
sel=runpy.run_path('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w4-createv2/ed/ir_sel.py')['edit']
def edit(t):
    t=sel(t)
    a='  %val8.sroa.2 = alloca [24 x i8], align 8\n'; b='  %quote_mint = alloca [32 x i8], align 8\n'
    assert t.count(a)==1 and t.count(b)==1
    t=t.replace(a,'@@A@@').replace(b,a).replace('@@A@@',b)
    return t
