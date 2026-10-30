import os,re
V=os.environ.get('SPV','amount')
def edit(f):
    hdr,body=f.split('\n',1)
    L=body.split('\n'); out=[]; n=0
    for l in L:
        if re.search(r'%'+V+r'\b',l) and not l.lstrip().startswith('%_0 = alloca'):
            n+=1; out.append(f'  %sp.l{n} = load i64, ptr %sp.a, align 8'); l=re.sub(r'%'+V+r'\b',f'%sp.l{n}',l)
        out.append(l)
    body='\n'.join(out)
    body=body.replace('  %_0 = alloca [16 x i8], align 8\n',f'  %_0 = alloca [16 x i8], align 8\n  %sp.a = alloca [8 x i8], align 8\n  store i64 %{V}, ptr %sp.a, align 8\n',1)
    return hdr+'\n'+body
