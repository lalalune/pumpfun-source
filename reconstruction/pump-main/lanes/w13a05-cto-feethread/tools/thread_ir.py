import sys,re
# thread_ir.py <in.slim.ll> <out.ll> <mode: h|hn|n>
src,dst,mode=sys.argv[1:4]
t=open(src).read()
def block(name):
    m=re.search(r'\n'+re.escape(name)+r':[^\n]*\n(.*?)\n\n',t,re.S); return m
def body(name): return block(name).group(1)
b70=body('bb70'); b19=body('bb19'); b17=body('bb17')
lines70=[l for l in b70.split('\n') if ' = phi ' not in l]
def mk70(suffix,vals,br):
    out=[]
    for l in lines70:
        if l.strip().startswith('br '): out.append('  '+br); continue
        for k,v in vals.items(): l=re.sub(re.escape(k)+r'\b',v,l)
        out.append(l)
    return f'bb70{suffix}:\n'+'\n'.join(out)+'\n'
def mkcopy(b,name,suffix):
    s=b
    for v in sorted(set(re.findall(r'(%[\w.]+) = ',s)),key=len,reverse=True):
        nv=('%v'+v[1:] if v[1:].isdigit() else v)+suffix
        s=re.sub(re.escape(v)+r'(?![\w.])',nv,s)
    return f'{name}{suffix}:\n'+s+'\n'
new=''
# bb22 phi additions
add={'%target.sroa.7.0':[], '%target.sroa.6.0':[], '%_401.sroa.0.0':[], '%_402.sroa.0.0.off0':[]}
if 'h' in mode:
    vals={'%_51.sroa.0.0.copyload':'0','%target.i.sroa.7.0':'%target.i.sroa.7.0.copyload','%target.i.sroa.8.0':'%target.i.sroa.8.0.copyload'}
    new+=mk70('H',vals,'br i1 %shared.sroa.0.0.off0, label %bb22, label %bb18H')
    new+='\nbb18H:\n  br i1 %_17.not.i, label %bb19H, label %bb22\n\n'
    new+=mkcopy(b19,'bb19','H').replace('br label %bb22','br label %bb22')+'\n'
    t=t.replace('br i1 %switch15.i, label %bb70, label %bb90.i','br i1 %switch15.i, label %bb70H, label %bb90.i')
    for p,src_ in (('bb70H','0'),('bb18H','2'),('bb19H','2')):
        add['%target.sroa.7.0'].append(f'[ %target.i.sroa.8.0.copyload, %{p} ]')
        add['%target.sroa.6.0'].append(f'[ %target.i.sroa.7.0.copyload, %{p} ]')
        add['%_401.sroa.0.0'].append(f'[ {src_}, %{p} ]')
        add['%_402.sroa.0.0.off0'].append(f'[ {"%v169H" if p=="bb19H" else "false"}, %{p} ]')
    t=re.sub(r'(%_51.sroa.0.0.copyload = phi i8 )\[ 0, %bb41.i \], ',r'\1',t)
    t=re.sub(r'(%target.i.sroa.7.0 = phi i64 )\[ %target.i.sroa.7.0.copyload, %bb41.i \], ',r'\1',t)
    t=re.sub(r'(%target.i.sroa.8.0 = phi ptr )\[ %target.i.sroa.8.0.copyload, %bb41.i \], ',r'\1',t)
if 'n' in mode:
    vals={'%_51.sroa.0.0.copyload':'1','%target.i.sroa.7.0':'%target.i.sroa.7.0.copyload306','%target.i.sroa.8.0':'%target.i.sroa.8.0.copyload307'}
    new+=mk70('N',vals,'br i1 %shared.sroa.0.0.off0, label %bb17N, label %bb19N')
    c17=mkcopy(b17,'bb17','N'); new+='\n'+c17+'\n'
    new+=mkcopy(b19,'bb19','N')+'\n'
    t=t.replace('br i1 %switch14.i, label %bb70, label %bb44.i','br i1 %switch14.i, label %bb70N, label %bb44.i')
    add['%target.sroa.7.0']+=['[ %_50.sroa.5.0.copyloadN, %bb17N ]','[ %target.i.sroa.8.0.copyload307, %bb19N ]']
    add['%target.sroa.6.0']+=['[ %_50.sroa.4.0.copyloadN, %bb17N ]','[ %target.i.sroa.7.0.copyload306, %bb19N ]']
    add['%_401.sroa.0.0']+=['[ 1, %bb17N ]','[ 2, %bb19N ]']
    add['%_402.sroa.0.0.off0']+=['[ false, %bb17N ]','[ %v169N, %bb19N ]']
    t=re.sub(r'(%_51.sroa.0.0.copyload = phi i8 [^\n]*?), \[ 1, %bb42.i \]',r'\1',t)
    t=re.sub(r'(%target.i.sroa.7.0 = phi i64 [^\n]*?), \[ %target.i.sroa.7.0.copyload306, %bb42.i \]',r'\1',t)
    t=re.sub(r'(%target.i.sroa.8.0 = phi ptr [^\n]*?), \[ %target.i.sroa.8.0.copyload307, %bb42.i \]',r'\1',t)
for k,v in add.items():
    if v: t=re.sub(r'(\n  '+re.escape(k)+r' = phi [^\n]*)',lambda m:m.group(1)+', '+', '.join(v),t,count=1)
# insert new blocks before bb22
t=t.replace('\nbb22:',('\n'+new+'\nbb22:'),1)
open(dst,'w').write(t)
