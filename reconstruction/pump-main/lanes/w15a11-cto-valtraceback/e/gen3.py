import json,runpy
O='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a11-cto-valtraceback'
HK='let holder_key;let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;'
H={'h1':[(HK,'let holder_key=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID).0;')],
   'h2':[(HK,'let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);')],
   'h3':[(HK,'let holder_key;{let hk=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);holder_key=hk.0;}')]}
V={}
for h,e in H.items():
    V[h]=e
    for b in ('b01','b03','b05'):
        V[h+b]=e+[tuple(x) for x in json.loads(open(f'{O}/e/{b}.py').read()[6:])]
for k,v in V.items(): open(f'{O}/e/{k}.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(V))
