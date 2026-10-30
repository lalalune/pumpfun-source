import runpy
TOP="let a=&ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;"
VS="let vsigner:[&[&[u8]];1];let bump=ctx.bumps.creator_vault;let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&[bump]];"
V={}
V['bumparr_top']=[(TOP,"let a=&ctx.accounts;let bumpa=[ctx.bumps.creator_vault];let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;"),(VS,"let vsigner:[&[&[u8]];1];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bumpa];")]
V['bumparr_late']=[(VS,"let vsigner:[&[&[u8]];1];let bumpa=[ctx.bumps.creator_vault];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),&bumpa];")]
V['bump_fromref']=[(VS,"let vsigner:[&[&[u8]];1];let old=a.current_creator.key();let vaultseeds:&[&[u8]]=&[b\"creator-vault\",old.as_ref(),std::slice::from_ref(&ctx.bumps.creator_vault)];")]
hk=runpy.run_path('hk1.py')['EDITS']
for k in list(V): V['hk1_'+k]=hk+V[k]
for k,v in V.items(): open(k+'.py','w').write('EDITS='+repr(v)+'\n')
print(list(V))
