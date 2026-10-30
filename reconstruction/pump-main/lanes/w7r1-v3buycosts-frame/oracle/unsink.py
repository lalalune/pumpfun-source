import sys,re,itertools; sys.path.insert(0,'.'); import irlib
t,m=irlib.load(); f0=m.group(0)
bl=irlib.blocks(f0)
phi=[l for l in f0.split('\n') if '%.sink = phi' in l][0]
pairs=re.findall(r'\[ (\d+), %("[^"]+"|[\w.$]+) \]',phi)
print(pairs)
def mk(sel):
    # sel: set of preds that store their own tag; others keep the phi
    out=[]
    keep=[(v,p) for v,p in pairs if p not in sel]
    for lab,b in bl:
        if lab in sel:
            v=dict((p,v) for v,p in pairs)[lab]
            lines=b.rstrip('\n').split('\n')
            lines.insert(len(lines)-1,f'  store i64 {v}, ptr %_0, align 8')
            if not keep: lines[-1]=lines[-1]  # still br to bb15
            b='\n'.join(lines)+'\n'
        if lab=='bb15':
            if keep and len(keep)<len(pairs):
                # need intermediate: preds in sel jump to bb15 which would re-store; create bb15b for kept preds
                newphi='  %.sink = phi i64 '+', '.join(f'[ {v}, %{p} ]' for v,p in keep)
                b=b.replace(phi,newphi)
            elif not keep:
                b=b.replace(phi+'\n','').replace('  store i64 %.sink, ptr %_0, align 8\n','')
        out.append(b)
    f='\n'.join(x.rstrip('\n')+'\n' for x in out)
    head=f0.split('{\n',1)[0]+'{\n'
    f=head+f.split('{\n',1)[1] if f.startswith('define') else head+f
    return f
def mk2(sel):
    # sel preds store own tag and jump to new block bb15r (ret only); others go bb15 (phi+store+ret)
    out=[]; keep=[(v,p) for v,p in pairs if p not in sel]
    for lab,b in bl:
        if lab in sel:
            v=dict((p,v) for v,p in pairs)[lab]
            lines=b.rstrip('\n').split('\n')
            lines[-1]=lines[-1].replace('label %bb15','label %bb15r')
            lines.insert(len(lines)-1,f'  store i64 {v}, ptr %_0, align 8')
            b='\n'.join(lines)+'\n'
        if lab=='bb15':
            if keep:
                b=b.replace(phi,'  %.sink = phi i64 '+', '.join(f'[ {v}, %{p} ]' for v,p in keep))
                b=b+'\nbb15r:\n  ret void\n'
            else:
                b='bb15r:\n  ret void\n'
        out.append(b)
    body='\n'.join(x.rstrip('\n')+'\n' for x in out)
    return f0.split('{\n',1)[0]+'{\n'+body+'}\n'
P=[p for v,p in pairs]
for n in range(1,len(P)+1):
    for sel in itertools.combinations(P,n):
        r,d=irlib.run(mk2(set(sel)))
        print(r,[s[:30] for s in sel],flush=True)
