import sys,re,itertools; sys.path.insert(0,'.'); import irlib
t,m=irlib.load(); f0=m.group(0)
# group uses of %_11.i.i29 by region: blocks
regions={'s1':['start','bb3.i14','bb6.i18','bb5.i27','bb8.i26','_ZN14pump_recovered18protocol_fee_split17hf6474d0ddc81b131E.exit28','_ZN14pump_recovered18protocol_fee_split17hf6474d0ddc81b131E.exit28.thread'],
 's2':['bb4','bb3.i','bb6.i','bb5.i','bb8.i','_ZN14pump_recovered18protocol_fee_split17hf6474d0ddc81b131E.exit'],
 'c371':['bb17','bb3.i.i','"_ZN14pump_recovered5trade12v3_buy_costs28_$u7b$$u7b$closure$u7d$$u7d$17h60893dbbd01db6f1E.exit"'],
 'c375':['bb29','bb3.i.i39','"_ZN14pump_recovered5trade12v3_buy_costs28_$u7b$$u7b$closure$u7d$$u7d$17h5bcc5784b2938b24E.exit"']}
def mk(sel,pos='first'):
    bl=irlib.blocks(f0); out=[]
    for lab,b in bl:
        for r in sel:
            if lab in regions[r]: b=b.replace('%_11.i.i29','%zst.'+r)
        out.append(b)
    head=f0.split('{\n',1)[0]+'{\n'
    body='\n'.join(x.rstrip('\n')+'\n' for x in out)
    decl=''.join(f'  %zst.{r} = alloca [0 x i8], align 1\n' for r in sel)
    if pos=='first': body=body.replace('start:\n','start:\n'+decl,1)
    else: body=body.replace('  %_24 = alloca [16 x i8], align 8\n','  %_24 = alloca [16 x i8], align 8\n'+decl,1)
    return head+body+'}\n'
R=list(regions)
for n in range(1,5):
    for sel in itertools.combinations(R,n):
        for pos in ('first','last'):
            r,d=irlib.run(mk(sel,pos)); print(r,sel,pos)
