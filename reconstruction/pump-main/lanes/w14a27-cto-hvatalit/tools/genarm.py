import os,sys
d=sys.argv[1]
H='if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{'
C0='anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.holder_creator_vault_quote_token_account.to_account_info(),authority:a.holder_creator_vault.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}))'
TV='crate::collect_v2::transfer_vault_tokens(&a.quote_token_program,&a.creator_vault_quote_token_account,&a.holder_creator_vault_quote_token_account,&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner)'
CUR=H+C0+'?;'+TV+'?;}\n   Ok(amount)}'
R='require!(amount==0,PumpError::CtoSharedVaultFrozen);'
V={
'b1_map':'if frozen{'+R+'Ok(amount)}else if amount>0{'+C0+'?;'+TV+'.map(|()|amount)}else{Ok(amount)}\n   }',
'b2_andthen':'if frozen{'+R+'Ok(amount)}else if amount>0{'+C0+'.and_then(|()|'+TV+').map(|()|amount)}else{Ok(amount)}\n   }',
'b3_pol':'if !frozen{if amount>0{'+C0+'?;'+TV+'?;}}else{'+R+'}\n   Ok(amount)}',
'b4_and':'if !frozen&&amount>0{'+C0+'?;'+TV+'?;}else if frozen{'+R+'}\n   Ok(amount)}',
'b6_reqnf':'if amount>0{require!(!frozen,PumpError::CtoSharedVaultFrozen);'+C0+'?;'+TV+'?;}\n   Ok(amount)}',
'b7_ne':CUR.replace('amount>0{','amount!=0{'),
'b8_mapz':'if frozen{'+R+'}else if amount>0{'+C0+'?;return '+TV+'.map(|()|amount);}\n   Ok(amount)}',
'b9_tvq_ok':'if frozen{'+R+'}else if amount>0{'+C0+'?;'+TV+'?;return Ok(amount);}\n   Ok(amount)}',
'b10_ne0z':'if frozen{'+R+'}else if amount==0{}else{'+C0+'?;'+TV+'?;}\n   Ok(amount)}',
'b11_frozenlast':'if !frozen{if amount>0{'+C0+'?;'+TV+'?;}}else if amount!=0{return Err(error!(PumpError::CtoSharedVaultFrozen));}\n   Ok(amount)}',
}
for n,v in V.items():
    open(f'{d}/{n}.py','w').write('EDITS=[(%r,%r)]\n'%(CUR,v))
print(' '.join(V))
