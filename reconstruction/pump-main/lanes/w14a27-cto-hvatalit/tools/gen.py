#!/usr/bin/env python3
"""gen.py <outdir> <listfile>: line-719 sweep create_idempotent per-account form screen.
name = <acct>_<form>[+<acct>_<form>...]; forms: C cl Kc Oc KOc Rc <order> a<order> ; or arm genes (see ARMS)."""
import sys,os
ACC={'prog':('CpiContext::new(','a.associated_token_program','a.associated_token_program.as_ref()'),
 'pay':('payer:','a.admin_set_creator_authority','a.admin_set_creator_authority.as_ref()'),
 'hat':('associated_token:','a.holder_creator_vault_quote_token_account','a.holder_creator_vault_quote_token_account.as_ref()'),
 'auth':('authority:','a.holder_creator_vault','&a.holder_creator_vault'),
 'qm':('mint:','a.quote_mint','a.quote_mint.as_ref().as_ref()'),
 'sp':('system_program:','a.system_program','a.system_program.as_ref()'),
 'tp':('token_program:','a.quote_token_program','a.quote_token_program.as_ref()')}
FLD={'K':'key:{x}.key','L':'lamports:{x}.lamports.clone()','D':'data:{x}.data.clone()','O':'owner:{x}.owner','R':'rent_epoch:{x}.rent_epoch',
 'S':'is_signer:{x}.is_signer','W':'is_writable:{x}.is_writable','E':'executable:{x}.executable'}
def form(k,o):
    f,e,r=ACC[k]
    if o=='C': return '{let x:&AccountInfo='+r+';x.clone()}'
    if o=='cl': return ('AccountInfo::clone('+r+')') if k!='auth' else 'a.holder_creator_vault.clone()'
    if o.endswith('c') and o[:-1] and set(o[:-1])<=set('KORSWE'):
        return '{let x:&AccountInfo='+r+';AccountInfo{'+','.join(FLD[c].format(x='x') for c in o[:-1])+',..x.clone()}}'
    if o.startswith('a'):
        return 'AccountInfo{'+','.join(FLD[c].format(x=e) for c in o[1:])+'}'
    return '{let x:&AccountInfo='+r+';AccountInfo{'+','.join(FLD[c].format(x='x') for c in o)+'}}'
A0='create_idempotent(CpiContext::new('
TPL="""E=%r
def T(s):
    i=s.rindex(%r); j=s.index('collect_v2::transfer_vault_tokens',i)
    seg=s[i:j]
    for a,b in E:
        assert seg.count(a)==1,(a,seg.count(a)); seg=seg.replace(a,b)
    return s[:i]+seg+s[j:]
"""
def edits(spec):
    E=[]
    for k,o in spec:
        f,e,r=ACC[k]
        E.append((f+e+'.to_account_info()',f+form(k,o)))
    return E
if __name__=='__main__':
    d=sys.argv[1]; os.makedirs(d,exist_ok=True)
    for l in open(sys.argv[2]):
        n=l.strip()
        if not n or n.startswith('#'): continue
        spec=[tuple(p.split('_',1)) for p in n.split('+')]
        open(f'{d}/{n}.py','w').write(TPL%(edits(spec),A0))
