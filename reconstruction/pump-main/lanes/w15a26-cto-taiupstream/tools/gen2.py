#!/usr/bin/env python3
"""gen2.py: tai base (TCF program = a.pump_amm.to_account_info()) x upstream sweep-head / blocker source forms. Writes e/<name>.py."""
import itertools,os,runpy
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w15a26-cto-taiupstream'
E='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a26-cto-taiupstream/e'
s=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
T=runpy.run_path(E+'/p_tai.py')['EDITS']
G={}
G['dbl']=[('sweep(&ctx,&holder_key)','sweep(&&ctx,&holder_key)'),('fn sweep(ctx:&Context<AdminCto>,','fn sweep(ctx:&&Context<AdminCto>,')]
G['bh']=[('->Result<u64>{let a=&ctx.accounts;','->Result<u64>{let a=&ctx.accounts;let bump=ctx.bumps.creator_vault;'),('let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;','let vsigner:[&[&[u8]];1];')]
G['ammp']=[('else if !a.coin_creator_vault_ata.data_is_empty(){crate::pump_amm','else if amm_present{crate::pump_amm')]
G['drev']=[('if a.holder_creator_vault.key()!=dest{','if dest!=a.holder_creator_vault.key(){')]
G['dbor']=[('if a.holder_creator_vault.key()!=dest{','if *a.holder_creator_vault.key!=dest{')]
NAT='let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;'
G['nlate']=[('->Result<u64>{let a=&ctx.accounts;'+NAT,'->Result<u64>{let a=&ctx.accounts;'),('  if native{let min=','  '+NAT+'if native{let min=')]
G['hcv']=[('->Result<u64>{let a=&ctx.accounts;','->Result<u64>{let a=&ctx.accounts;let hcv=&a.holder_creator_vault;'),
          ('if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}','if hcv.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((hcv.key(),dest)));}'),
          ('&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,','&a.admin_set_creator_authority,hcv)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,hcv,'),
          ('authority:a.holder_creator_vault.to_account_info()','authority:hcv.to_account_info()')]
# accounts sub-literals -> to_account_info() (natural form), applied after T
L=s.split('\n')[660]
def sub(field,src):
    i=L.index(field+':{let x:&AccountInfo='); j=L.index('}}',i)+2
    return (L[i:j], field+':'+src+'.to_account_info()')
G['s0']=[sub('coin_creator_vault_ata','a.coin_creator_vault_ata')]
G['s1']=[sub('pump_creator_vault_ata','a.creator_vault_quote_token_account')]
G['s2']=[sub('program','a.pump_amm')]
def chk(ed):
    t=s
    for a,b in ed:
        assert t.count(a)==1,(a[:80],t.count(a)); t=t.replace(a,b)
    assert t.count('\n')==s.count('\n')
def w(name,keys):
    ed=list(T)+[e for k in keys for e in G[k]]; chk(ed)
    open(f'{E}/{name}.py','w').write('EDITS='+repr(ed)+'\n'); return name
out=[]
for k in G: out.append(w('t_'+k,[k]))
for a,b in itertools.combinations(['dbl','bh','ammp','nlate','hcv','drev'],2):
    try: out.append(w(f't_{a}_{b}',[a,b]))
    except AssertionError: pass
print(' '.join(out))
