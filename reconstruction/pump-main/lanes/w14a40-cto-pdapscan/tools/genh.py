#!/usr/bin/env python3
"""genh.py <base.py> <outdir> name=acct:order[+acct:order]...: hand-written inline-field literal for coin_creator (cc) / pump_creator_vault (pcv)."""
import sys,os
ACC={'cc':('coin_creator:a.current_creator.to_account_info()','coin_creator:','&a.current_creator','a.current_creator'),
     'pcv':('pump_creator_vault:a.creator_vault.to_account_info()','pump_creator_vault:','&a.creator_vault','a.creator_vault')}
FLD={'K':'key:{x}.key','L':'lamports:{x}.lamports.clone()','D':'data:{x}.data.clone()','O':'owner:{x}.owner','R':'rent_epoch:{x}.rent_epoch','S':'is_signer:{x}.is_signer','W':'is_writable:{x}.is_writable','E':'executable:{x}.executable'}
def lit(k,o):
    old,pre,r,e=ACC[k]
    if o.startswith('a'): return pre+'AccountInfo{'+','.join(FLD[c].format(x=e) for c in o[1:])+'}'
    return pre+'{let x:&AccountInfo='+r+';AccountInfo{'+','.join(FLD[c].format(x='x') for c in o)+'}}'
base,od=sys.argv[1],sys.argv[2]; os.makedirs(od,exist_ok=True)
for spec in sys.argv[3:]:
    n,s=spec.split('=')
    E2=[(ACC[k][0],lit(k,o)) for k,o in (p.split(':') for p in s.split('+'))]
    open(f'{od}/{n}.py','w').write(open(base).read()+'''
E2=%r
_T0=T
def T(s):
    s=_T0(s)
    i=s.index('TransferCreatorFeesToPumpV2{payer:'); j=s.index('\\n',i); seg=s[i:j]
    for a,b in E2:
        assert seg.count(a)==1,(a,seg.count(a)); seg=seg.replace(a,b)
    return s[:i]+seg+s[j:]
'''%E2)
    print(n)
