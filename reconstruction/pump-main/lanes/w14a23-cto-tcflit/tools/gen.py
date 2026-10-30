#!/usr/bin/env python3
"""gen.py <outdir> <listfile>: TCF-CPI per-account literal-order screen edits. Name = <acct>_<order> or <acct>_a<order> (direct a.X.f reads)."""
import sys,os
ACC={'pay':('payer','a.admin_set_creator_authority','a.admin_set_creator_authority.as_ref()'),
 'qm':('quote_mint','a.quote_mint','a.quote_mint.as_ref().as_ref()'),
 'tp':('token_program','a.quote_token_program','a.quote_token_program.as_ref()'),
 'sp':('system_program','a.system_program','a.system_program.as_ref()'),
 'ata':('associated_token_program','a.associated_token_program','a.associated_token_program.as_ref()'),
 'cc':('coin_creator','a.current_creator','&a.current_creator'),
 'cva':('coin_creator_vault_authority','a.coin_creator_vault_authority','a.coin_creator_vault_authority.as_ref()'),
 'cvt':('coin_creator_vault_ata','a.coin_creator_vault_ata','a.coin_creator_vault_ata.as_ref()'),
 'pcv':('pump_creator_vault','a.creator_vault','&a.creator_vault'),
 'ev':('event_authority','a.pump_amm_event_authority','a.pump_amm_event_authority.as_ref()')}
FLD={'K':'key:{x}.key','L':'lamports:{x}.lamports.clone()','D':'data:{x}.data.clone()','O':'owner:{x}.owner','R':'rent_epoch:{x}.rent_epoch',
 'S':'is_signer:{x}.is_signer','W':'is_writable:{x}.is_writable','E':'executable:{x}.executable'}
def lit(k,order):
    f,e,r=ACC[k]
    if order.startswith('a'):
        return 'AccountInfo{'+','.join(FLD[c].format(x=e) for c in order[1:])+'}'
    return '{let x:&AccountInfo='+r+';AccountInfo{'+','.join(FLD[c].format(x='x') for c in order)+'}}'
def edits(spec):  # spec: list of (k,order)
    E=[]
    for k,o in spec:
        f,e,r=ACC[k]; E.append((f+':'+e+'.to_account_info()',f+':'+lit(k,o)))
    return E
TPL="""E=%s
def T(s):
    i=s.index('TransferCreatorFeesToPumpV2{payer:'); j=s.index('\\n',i)
    seg=s[i:j]
    for a,b in E:
        assert seg.count(a)==1,(a,seg.count(a)); seg=seg.replace(a,b)
    return s[:i]+seg+s[j:]
"""
if __name__=='__main__':
    d=sys.argv[1]; os.makedirs(d,exist_ok=True)
    for l in open(sys.argv[2]):
        n=l.strip()
        if not n: continue
        spec=[tuple(p.split('_',1)) for p in n.split('+')]
        open(f'{d}/{n}.py','w').write(TPL%repr(edits(spec)))
