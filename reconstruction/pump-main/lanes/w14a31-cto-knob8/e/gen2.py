import json,os
OUT=os.path.dirname(os.path.abspath(__file__))
V={
'wl_gate_swap':[("  if !collection_native||coin_present{anchor_spl","  if coin_present||!collection_native{anchor_spl")],
'wl_docoin_if':[("  let do_coin=coin_present&&!token_frozen(a.coin_creator_vault_ata.as_ref())?;","  let do_coin=if coin_present{!token_frozen(a.coin_creator_vault_ata.as_ref())?}else{false};")],
'wl_collect_match':[("if let Some((collected,quote_mint))=crate::collect_v2::collect(","match crate::collect_v2::collect("),("a.quote_mint.as_ref().as_ref(),&a.quote_token_program,a.system_program.as_ref())?{\n","a.quote_mint.as_ref().as_ref(),&a.quote_token_program,a.system_program.as_ref())?{None=>{}Some((collected,quote_mint))=>{\n"),("     }\n    }\n  }\n  if coin_present&do_coin{","     }\n    }}\n  }\n  if coin_present&do_coin{")],
'wl_ixlit':[("let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);","let ix=anchor_lang::solana_program::instruction::Instruction{program_id:crate::ID,accounts:vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)],data:ix_data};")],
'wl_inner_iter':[(".chain(inner_data.into_iter()).collect();",".chain(inner_data.iter().copied()).collect();")],
'wl_infos_ref':[("let event_infos=[authority_info];","let event_infos=[authority_info.clone()];")],
'wl_disc_ref':[("         let disc=anchor_lang::event::EVENT_IX_TAG_LE;","         let disc:&[u8]=anchor_lang::event::EVENT_IX_TAG_LE;")],
'wl_auth_a':[("         let authority_info=ctx.accounts.event_authority.to_account_info();","         let authority_info=a.event_authority.to_account_info();")],
'wl_writ_eq':[("if !a.current_creator.is_writable{return","if a.current_creator.is_writable==false{return")],
'wl_frozen_match':[("if token_frozen(a.current_creator_quote_token_account.as_ref())?{msg!(","if token_frozen(a.current_creator_quote_token_account.as_ref())?==true{msg!(")],
's_map_any':[(".map(|()|amount)}else{Ok(amount)}}",".map(|_|amount)}else{Ok(amount)}}")],
's_ok_zero':[(".map(|()|amount)}else{Ok(amount)}}",".map(|()|amount)}else{Ok(0)}}")],
's_ensure_let':[("crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;","let ()=crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;")],
's_dest_tuple':[("  let dest=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID).0;","  let (dest,_)=Pubkey::find_program_address(&[b\"creator-vault\",holder_key.as_ref()],&crate::ID);")],
'r410_if':[(" require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);"," if a.bonding_curve.creator_fee!=0{return Err(error!(PumpError::CreatorFeesNotSwept));}")],
'ev_old_fee_curve':[("old_creator_fee_bps:old_fee,new_creator_fee_bps:nf,","old_creator_fee_bps:old_fee,new_creator_fee_bps:a.bonding_curve.creator_fee_bps,")],
'tp_sig_pre':[(" let signer_seeds:&[&[&[u8]]]=&[&[b\"pool-authority\",mint.as_ref(),&[ctx.bumps.pool_authority]]];"," let pb=ctx.bumps.pool_authority;let signer_seeds:&[&[&[u8]]]=&[&[b\"pool-authority\",mint.as_ref(),&[pb]]];")],
'tp_pool_if':[(" if pool_updated{\n"," if pool_updated==true{\n")],
'sh_iflet':[(" match sharing_update{Some(val)=>{\n"," if let Some(val)=sharing_update{{\n"),("signer_seeds),val)?;\n\n }None=>{}}\n","signer_seeds),val)?;\n\n }}\n")],
'ev_swept_local':[("sharing_config_reset:sharing_update.is_some(),swept_to_holder_vault:swept,pool_updated};","swept_to_holder_vault:swept,sharing_config_reset:sharing_update.is_some(),pool_updated};")],
}
for n,e in V.items(): open(f'{OUT}/{n}.py','w').write('EDITS='+json.dumps(e)+'\n')
print(' '.join(V))
