# Genes from the 6/2 clone-RA builds (w10r1 hillclimb 7fb9a5e3e7a2 / stitch c4 / errseq t03 / hc f6eb16639005), ported to main 16c10e631.
SH0="let shared=if a.bonding_curve.creator==a.sharing_config.key(){a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()}else{false};"
QL="let quote_locked=crate::pump_quote::global_quote(a.bonding_curve.quote_mint,&a.global);"
HK="let holder_key;let hk=Pubkey::find_program_address(&[b\"holder-rewards\",mint.as_ref()],&crate::ID);holder_key=hk.0;"
GENES={
 'n298_iflet':[("if new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}","if let Some(_)=new{return Err(error!(PumpError::CtoNewCreatorNotAllowed));}")],
 'sko':[("let sk=a.sharing_config.key();",""),("&holder_key,&sk)?","&holder_key,a.sharing_config.key)?")],
 'n306_okorelse':[("let t=if let Some(t)=new{t}else{return Err(error!(PumpError::CtoNewCreatorRequired));};","let t=new.ok_or_else(||error!(PumpError::CtoNewCreatorRequired))?;")],
 'fee_unwrap_or':[("  if let Some(f)=fee{curve.creator_fee_bps=f;}","  curve.creator_fee_bps=fee.unwrap_or(old_fee);")],
 'curve_edit_first':[("  curve.creator=target;","  curve.can_edit_creator_fee=false;curve.creator=target;"),("  curve.can_edit_creator_fee=false;\n (old","\n (old")],
 'su_iflet':[(" match sharing_update{Some(val)=>{"," if let Some(val)=sharing_update{"),(" }None=>{}}"," }")],
 'shared_bitand':[("a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty()","(a.sharing_config.owner==&FEES)&!a.sharing_config.data_is_empty()")],
 'shared_owner_first':[(SH0,"let shared=if a.sharing_config.owner==&FEES{a.bonding_curve.creator==a.sharing_config.key()&&!a.sharing_config.data_is_empty()}else{false};")],
 'shared_flat':[(SH0,"let shared=a.bonding_curve.creator==a.sharing_config.key()&&a.sharing_config.owner==&FEES&&!a.sharing_config.data_is_empty();")],
 'holder_unwrap':[("let hopt=holder;let holder=hopt==Some(true);","let hopt=holder;let holder=hopt.unwrap_or(false);")],
 'ql_before_shared':[("let mint=a.mint.key();"+SH0,"let mint=a.mint.key();"+QL+SH0),(HK+QL,HK)],
 'v_holder_unwrap':[("->Result<Pubkey>{let holder=hopt==Some(true);","->Result<Pubkey>{let holder=hopt.unwrap_or(false);")],
}

TN="crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&vsigner)"
GENES.update({
 'nat_q':[(TN+".map(|()|amount)}else{Ok(amount)}}else{",TN+"?;Ok(amount)}else{Ok(amount)}}else{")],
 'nat_flat':[(TN+".map(|()|amount)}else{Ok(amount)}}else{",TN+"?;}Ok(amount)}else{")],
 'sweep7fb':[("  if native{let min=Rent::get()?","  let amount=if native{let min=Rent::get()?"),(TN+".map(|()|amount)}else{Ok(amount)}}else{",TN+"?;}amount}else{"),("   Ok(amount)}\n","   amount};Ok(amount)}\n")],
})
SS=' let signer_seeds:&[&[&[u8]]]=&[&[b"pool-authority",mint.as_ref(),&[ctx.bumps.pool_authority]]];'
NP=' }else{msg!("No canonical pump pool for this mint; curve only");}'
GENES.update({
 'ss_scope':[(SS+'\n',' let (old_creator,old_fee,pool_updated)={'+SS[1:]+'\n'),(NP+'\n',NP+'(old_creator,old_fee,pool_updated)};\n'),(' let e=AdminCtoEvent{',' let a=&ctx.accounts;let e=AdminCtoEvent{')],
})
GENES.update({
 'tok_map':[("   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);}else if amount>0{","   if frozen{require!(amount==0,PumpError::CtoSharedVaultFrozen);Ok(amount)}else if amount>0{"),
            ("a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner)?;}\n","a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&vsigner).map(|()|amount)}else{Ok(amount)}\n"),
            ("   Ok(amount)}\n","   }\n")],
})
