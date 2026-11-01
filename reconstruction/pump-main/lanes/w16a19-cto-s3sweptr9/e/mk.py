import runpy,json,sys
B='/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a19-cto-s3sweptr9/e/'
S3=runpy.run_path(B+'S3n.py')['EDITS']
SW0="swept=(!skip).then(||sweep(&ctx,&holder_key)).transpose()?.unwrap_or(0);"
D0="let dest=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}"
SIG0="fn sweep(ctx:&Context<AdminCto>,holder_key:&Pubkey)->Result<u64>{let a=&ctx.accounts;"
F={
 's_if':[[SW0,"swept=if skip{0}else{sweep(&ctx,&holder_key)?};"]],
 's_ifn':[[SW0,"swept=if !skip{sweep(&ctx,&holder_key)?}else{0};"]],
 's_mut':[[" let swept;\n"," let mut swept=0;\n"],[SW0,"if !skip{swept=sweep(&ctx,&holder_key)?;}"]],
 's_match':[[SW0,"swept=match skip{true=>0,false=>sweep(&ctx,&holder_key)?};"]],
 's_okq':[[SW0,"swept=if skip{Ok(0)}else{sweep(&ctx,&holder_key)}?;"]],
 's_uor':[[SW0,"swept=(!skip).then(||sweep(&ctx,&holder_key)).unwrap_or(Ok(0))?;"]],
 'd_scope':[[D0,"{"+D0+"}"]],
 'd_rev':[[D0,D0.replace("if a.holder_creator_vault.key()!=dest","if dest!=a.holder_creator_vault.key()")]],
 'b_arg':[[SW0,SW0.replace("sweep(&ctx,&holder_key)","sweep(&ctx,&holder_key,ctx.bumps.creator_vault)")],[SIG0,SIG0.replace("holder_key:&Pubkey)","holder_key:&Pubkey,bump:u8)")],["let bump=ctx.bumps.creator_vault;let old=",""+"let old="]],
 'b_accts':[[SW0,SW0.replace("sweep(&ctx,&holder_key)","sweep(&ctx.accounts,&ctx.bumps,&holder_key)")],[SIG0,"fn sweep(a:&AdminCto,bumps:&AdminCtoBumps,holder_key:&Pubkey)->Result<u64>{"],["let bump=ctx.bumps.creator_vault;let old=","let bump=bumps.creator_vault;let old="]],
 'r_chain':[["let min={let rent=Rent::get()?;rent.minimum_balance(0)};","let min=Rent::get()?.minimum_balance(0);"]],
 'g_hf':[[SW0,"swept=if shared&&_holder{sweep(&ctx,&holder_key)?}else{0};"]],
}
F['sd_if']=F['s_if']+F['d_scope']
F['sd_okq']=F['s_okq']+F['d_scope']
F['sd_mut']=F['s_mut']+F['d_scope']
F['db_arg']=F['d_scope']+F['b_arg']
for k,v in F.items():
    open(B+k+'.py','w').write('EDITS='+json.dumps(S3+v)+'\n')
print(' '.join(F))
