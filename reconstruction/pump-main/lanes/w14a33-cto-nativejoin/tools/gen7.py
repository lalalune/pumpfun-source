import json,os
O=os.path.expanduser('~/.cache/pumpfun-reconstruction/lanes/w14a33-cto-nativejoin/e/')
L663="  if native{let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);\n"
NAT="(if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)"
L664a="   "+NAT+"}else{let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;"
TAIL="amount,&vsigner)?;return Ok(amount);}\n   Ok(amount)}"
NATB="let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);"+NAT
S={
'x_swap':[[L663,"  if !native{\n"],[L664a,"   let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;"],[TAIL,"amount,&vsigner)?;return Ok(amount);}\n   Ok(amount)}else{"+NATB+"}"]],
'x_match':[[L663,"  match native{false=>{\n"],[L664a,"   let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;"],[TAIL,"amount,&vsigner)?;return Ok(amount);}\n   Ok(amount)}true=>{"+NATB+"}}"]],
'x_matcht':[[L663,"  match native{true=>{let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);\n"],[L664a,"   "+NAT+"}false=>{let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;"],[TAIL,"amount,&vsigner)?;return Ok(amount);}\n   Ok(amount)}}"]],
}
for k,v in S.items(): open(O+k+'.py','w').write('EDITS='+json.dumps(v)+'\n')
print(' '.join(S))
