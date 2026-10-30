import os,re
HOST=os.environ.get('HOST','_37.sroa.11')
def edit(t):
    k='  %_117.i74 = alloca [16 x i8], align 8\n'
    assert k in t
    t=t.replace(k,'',1)
    t=re.sub(r'%_117\.i74\b','%'+HOST,t)
    return t
