import sys,re,runpy,itertools; sys.path.insert(0,'.'); import irlib
pre=sys.argv[1] if len(sys.argv)>1 and sys.argv[1]!='-' else None
pair=len(sys.argv)>2 and sys.argv[2]=='pair'
t,m=irlib.load(); f0=m.group(0)
if pre: f0=runpy.run_path(pre)['edit'](f0)
Z='  call void @llvm.lifetime.start.p0(i64 0, ptr nonnull %_11.i.i29)\n  call void @llvm.lifetime.end.p0(i64 0, ptr nonnull %_11.i.i29)\n'
def lbl(l): return l if l.startswith('"') else l
def split(f,P,S,k):
    bl=irlib.blocks(f); out=[]
    new='ltz'+str(k)
    for lab,b in bl:
        if lab==P:
            lines=b.rstrip('\n').split('\n'); last=lines[-1]
            last=last.replace('label %'+S,'label %'+new,1); lines[-1]=last
            b='\n'.join(lines)+'\n'
            b=b+'\n'+new+':\n'+Z+'  br label %'+S+'\n'
        elif lab==S:
            pn=P if P.startswith('"') else P
            b=re.sub(r'(phi [^\n]*?)%'+re.escape(P)+r' \]', lambda mm: mm.group(0).replace('%'+P+' ]','%'+new+' ]'), b)
            b='\n'.join([re.sub(r'%'+re.escape(P)+r' \]','%'+new+' ]',l) if ' phi ' in l else l for l in b.split('\n')])
        out.append(b)
    head=f.split('{\n',1)[0]+'{\n'
    body='\n'.join(x.rstrip('\n')+'\n' for x in out)
    return head+body.replace('\n\n\n','\n\n')+'}\n'
edges=[(l,s) for l,b in irlib.blocks(f0) for s in irlib.term_succs(b)]
print(len(edges),'edges', irlib.run(f0)[0])
res=[]
cands=[(e,) for e in edges] if not pair else list(itertools.combinations(edges,2))
for k,es in enumerate(cands):
    f=f0
    for j,(P,S) in enumerate(es): f=split(f,P,S,f'{k}_{j}')
    r,d=irlib.run(f)
    if r is None: print('ERR',es,d[-300:]); continue
    res.append((r[1]+r[2],r,es))
    if not pair or r[1]+r[2]<12: print(r,es,flush=True)
res.sort(key=lambda x:x[0]); print('BEST',res[:5])
