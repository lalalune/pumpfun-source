import os,re
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a50-cto-frozenrepay')
WT='/Users/shawwalters/Documents/Codex/2026-10-24/pump-main-swarm/worktrees/w14a50-cto-frozenrepay'
s=open(WT+'/programs/pump/src/creator/admin_cto.rs').read()
L=s.split('\n'); l719=L[718]; l664=L[663]; l720=L[719]
assert l720=='   Ok(amount)}', repr(l720)
i=l719.index('anchor_spl::associated_token::create_idempotent('); j=l719.index(').and_then(|()|')
C=l719[i:j+1]
k=l719.index('crate::collect_v2::transfer_vault_tokens('); m=l719.index('))?;return Ok(amount);}')
TV=l719[k:m+1]
R='require!(amount==0,PumpError::CtoSharedVaultFrozen);'
H='   if frozen{'+R+'}else if amount>0{'
assert l719==H+C+'.and_then(|()|'+TV+')?;return Ok(amount);}', 'mismatch'
FR='let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;'
AM='let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;'
assert l664.endswith(FR+AM)
CUR=l719+'\n'+l720
V={
'e1_retmap':H+C+'.and_then(|()|'+TV+').map(|()|amount);}\n'+l720,
'e2_match':H+'match '+C+'.and_then(|()|'+TV+'){Ok(())=>return Ok(amount),Err(e)=>return Err(e)}}\n'+l720,
'e3_iflet':H+'if let Err(e)='+C+'.and_then(|()|'+TV+'){return Err(e);}return Ok(amount);}\n'+l720,
'e4_ne':H.replace('amount>0','amount!=0')+C+'.and_then(|()|'+TV+')?;return Ok(amount);}\n'+l720,
'e5_frok0':'   if frozen{'+R+'return Ok(0);}else if amount>0{'+C+'.and_then(|()|'+TV+')?;return Ok(amount);}\n'+l720,
'e6_clos':H+C+'.and_then(|()|{'+TV+'?;Ok(())})?;return Ok(amount);}\n'+l720,
'e7_andmap':H+C+'.and_then(|()|'+TV+'.map(|()|amount))\n   }else{Ok(amount)}}',
'e8_expr':'   if frozen{'+R+'Ok(amount)}else if amount>0{'+C+'.and_then(|()|'+TV+')?;Ok(amount)}else{Ok(amount)}\n   }',
'e9_notfrozen':'   if !frozen{if amount>0{'+C+'.and_then(|()|'+TV+')?;return Ok(amount);}}else{'+R+'}\n'+l720,
'e11_okq':H+'return Ok('+C+'.and_then(|()|'+TV+').map(|()|amount)?);}\n'+l720,
'e12_frif':'   if frozen{if amount!=0{return Err(error!(PumpError::CtoSharedVaultFrozen));}}else if amount>0{'+C+'.and_then(|()|'+TV+')?;return Ok(amount);}\n'+l720,
'e13_gt0first':'   if !frozen&&amount>0{'+C+'.and_then(|()|'+TV+')?;return Ok(amount);}else if frozen{'+R+'}\n'+l720,
}
os.makedirs(O+'/ka',exist_ok=True)
for n,v in V.items():
    assert v.count('\n')==1,n
    open(f'{O}/ka/{n}.py','w').write('EDITS=%r\n'%([(CUR,v)],))
F={
'f1_tuple':'let (frozen,amount)=(token_frozen(a.creator_vault_quote_token_account.as_ref())?,token_raw_amount(a.creator_vault_quote_token_account.as_ref())?);',
'f2_acct':'let ta=a.creator_vault_quote_token_account.as_ref();let frozen=token_frozen(ta)?;let amount=token_raw_amount(ta)?;',
'f3_acct_rawfirst':'let ta=a.creator_vault_quote_token_account.as_ref();let amount=token_raw_amount(ta)?;let frozen=token_frozen(ta)?;',
'f4_tuple_raw':'let (amount,frozen)=(token_raw_amount(a.creator_vault_quote_token_account.as_ref())?,token_frozen(a.creator_vault_quote_token_account.as_ref())?);',
}
for n,v in F.items():
    open(f'{O}/ka/{n}.py','w').write('EDITS=%r\n'%([(FR+AM,v)],))
print(len(V)+len(F))
