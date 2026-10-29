import os,re
SYMP=os.environ.get('SYM','trade15buy_exact_quote17h')
def blocks_of(t):
    L=t.split('\n'); s=next(i for i,l in enumerate(L) if l.startswith('define') and SYMP in l); e=next(i for i in range(s,len(L)) if L[i]=='}')
    body=L[s+1:e]; bl=[]; cur=['start',[]]
    for l in body:
        m=re.match(r'^([A-Za-z0-9_.$"]+):',l)
        if m: bl.append(cur); cur=[m.group(1),[l]]
        else: cur[1].append(l)
    bl.append(cur); return L,s,e,bl
def edit(t):
    ops=os.environ['OPS'].split()
    L,s,e,bl=blocks_of(t)
    for op in ops:
        x,y=op.split('>'); bx=next(b for b in bl if b[0]==x); bl.remove(bx)
        iy=next(i for i,b in enumerate(bl) if b[0]==y); bl.insert(iy+1,bx)
    ren=lambda t: re.sub(r'^([0-9]+):', r'v\1:', re.sub(r'%([0-9]+)\b', r'%v\1', t))
    out=L[:s]+[ren(L[s])]
    for n,b in bl: out+=[ren(x) for x in b]
    return '\n'.join(out+L[e:])
