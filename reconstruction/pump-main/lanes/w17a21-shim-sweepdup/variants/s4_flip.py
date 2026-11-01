L663='  if native{let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);\n'
L664='   (if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)}else{Ok(())}).map(|()|amount)}else{let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;\n'
NATQ='if amount>0{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)?;}Ok(amount)'
NATM='let min={let rent=Rent::get()?;rent.minimum_balance(0)};let amount=a.creator_vault.lamports().saturating_sub(min);'
TOKH='let frozen=token_frozen(a.creator_vault_quote_token_account.as_ref())?;let amount=token_raw_amount(a.creator_vault_quote_token_account.as_ref())?;'
L720='   Ok(amount)}\n'
V={
 # s_nat1 as before
 'f_nat1':[(L664,'   '+NATQ+'}else{'+TOKH+'\n')],
 # flip: token first, native in the else arm on line 720
 'f_flip':[(L663,'  if !native{'+TOKH+'\n'),(L664,'\n'),(L720,'   Ok(amount)}else{'+NATM+NATQ+'}\n')],
 # flip with the original's polarity kept via ==false
 'f_flipf':[(L663,'  if native==false{'+TOKH+'\n'),(L664,'\n'),(L720,'   Ok(amount)}else{'+NATM+NATQ+'}\n')],
 # match form
 'f_match':[(L663,'  match native{false=>{'+TOKH+'\n'),(L664,'\n'),(L720,'   Ok(amount)}true=>{'+NATM+NATQ+'}}\n')],
}
