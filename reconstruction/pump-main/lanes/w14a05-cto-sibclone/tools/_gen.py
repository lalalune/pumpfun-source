import re,sys
SRC='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a05-cto-sibclone/programs/pump/src/creator/admin_cto.rs'
L=open(SRC).read().split('\n')
SH=L[748]  # line 749
assert SH.startswith('  crate::pump_fees::cpi::admin_cto_sharing_config'),SH[:60]
TCF=[l for l in L if 'transfer_creator_fees_to_pump_v2' in l][0]
SH_TAI='  crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:a.pool_authority.to_account_info(),authority:a.admin_set_creator_authority.to_account_info(),global:a.global.to_account_info(),mint:a.mint.to_account_info(),sharing_config:a.sharing_config.to_account_info(),event_authority:a.pump_fees_event_authority.to_account_info(),program:a.pump_fees.to_account_info()},signer_seeds),val)?;'
def shfn(body_call, sig, call):
    return body_call, sig, call
CALL='crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees.to_account_info(),crate::pump_fees::cpi::accounts::AdminCtoSharingConfig{pool_authority:a.pool_authority.to_account_info(),authority:a.admin_set_creator_authority.to_account_info(),global:a.global.to_account_info(),mint:a.mint.to_account_info(),sharing_config:a.sharing_config.to_account_info(),event_authority:a.pump_fees_event_authority.to_account_info(),program:a.pump_fees.to_account_info()},signer_seeds),val)'
V={}
V['s1_tai']=[(SH,'  '+CALL+'?;')]
V['s2_fnctx']=[(SH,'  fn share(ctx:&Context<AdminCto>,signer_seeds:&[&[&[u8]]],val:Option<Pubkey>)->Result<()>{let a=&ctx.accounts;'+CALL+'}share(&ctx,signer_seeds,val)?;')]
V['s3_fnacc']=[(SH,"  fn share<'info>(a:&AdminCto<'info>,signer_seeds:&[&[&[u8]]],val:Option<Pubkey>)->Result<()>{"+CALL+'}share(a,signer_seeds,val)?;')]
V['s4_fnmig']=[(SH,"  fn share(ctx:&Context<AdminCto>,val:Option<Pubkey>)->Result<()>{let bump=ctx.bumps.pool_authority;let a=&ctx.accounts;let signer_seeds:&[&[&[u8]]]=&[&[b\"pool-authority\",a.mint.key().as_ref(),&[bump]]];"+CALL+'}share(&ctx,val)?;')]
V['s5_clos']=[(SH,"  let share=move|signer_seeds:&[&[&[u8]];1]|"+CALL.replace('signer_seeds),val)','signer_seeds),val)')+';share(&[signer_seeds[0]])?;')]
V['s6_fnctx_inl']=[(SH,'  #[inline(always)]fn share(ctx:&Context<AdminCto>,signer_seeds:&[&[&[u8]]],val:Option<Pubkey>)->Result<()>{let a=&ctx.accounts;'+CALL+'}share(&ctx,signer_seeds,val)?;')]
V['s7_fnctx_inlhint']=[(SH,'  #[inline]fn share(ctx:&Context<AdminCto>,signer_seeds:&[&[&[u8]]],val:Option<Pubkey>)->Result<()>{let a=&ctx.accounts;'+CALL+'}share(&ctx,signer_seeds,val)?;')]
import os
for k,v in V.items():
    open(os.path.join(os.path.dirname(os.path.abspath(SRC.replace(SRC,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a05-cto-sibclone/edits/x'))),k+'.py'),'w').write('EDITS='+repr(v)+'\n')
