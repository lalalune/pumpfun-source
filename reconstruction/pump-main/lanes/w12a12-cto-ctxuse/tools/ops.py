import os,re
# OPS="rs:NAME:SIZE;pad:SIZE:ALIGN:BEFORE;..."
def edit(t):
    k=0
    for op in os.environ.get('OPS','').split(';'):
        if not op: continue
        p=op.split(':')
        if p[0]=='rs':
            r=re.compile(r'(  %'+re.escape(p[1])+r' = alloca )\[\d+ x i8\]')
            t,n=r.subn(r'\1['+p[2]+' x i8]',t,1); assert n==1,op
        elif p[0]=='pad':
            key=f'  %{p[3]} = alloca'; assert key in t,op
            t=t.replace(key,f'  %padop{k} = alloca [{p[1]} x i8], align {p[2]}\n'+key,1); k+=1
    return t
