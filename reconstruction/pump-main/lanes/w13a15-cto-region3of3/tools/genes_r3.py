# region-3 genes on main f7ce2e3 text (exact, newline-preserving substitutions)
TREE_OLD="let (sharing_update,collect_old,skip)=if shared{if holder{(Some(None),false,false)}else{target=st.creator;(Some(args.0),false,true)}}else{(None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};"
GENES={
 't_hphi':[(TREE_OLD,"let (holder,sharing_update,collect_old,skip)=if shared{if holder{(true,Some(None),false,false)}else{target=st.creator;(false,Some(args.0),false,true)}}else{(holder,None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};")],
 't_hcbphi':[(TREE_OLD,"let (holder,cashback,sharing_update,collect_old,skip)=if shared{if holder{(true,false,Some(None),false,false)}else{target=st.creator;(false,cashback,Some(args.0),false,true)}}else{(holder,cashback,None,!st.holder_reward&&st.creator!=Pubkey::default(),true)};(holder,cashback,target,sharing_update,collect_old,skip)};")],
 'ev_hr_curve':[("is_holder_reward:holder,is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_holder_reward:a.bonding_curve.is_holder_reward,is_cashback_coin:a.bonding_curve.is_cashback_coin,")],
 'ev_cb_local':[("is_holder_reward:holder,is_cashback_coin:a.bonding_curve.is_cashback_coin,","is_holder_reward:holder,is_cashback_coin:cashback,")],
 'pool_hrb':[("signer_seeds),target,holder,fee)?;","signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;")],
 'pool_tgt_curve':[("signer_seeds),target,holder,fee)?;","signer_seeds),a.bonding_curve.creator,holder,fee)?;")],
 'ev_fee_unwrap':[("new_creator_fee_bps:a.bonding_curve.creator_fee_bps,","new_creator_fee_bps:fee.unwrap_or(old_fee),")],
 'ev_reset_local':[(" let signer_seeds:&[&[&[u8]]]="," let reset=sharing_update.is_some();let signer_seeds:&[&[&[u8]]]="),("sharing_config_reset:sharing_update.is_some(),","sharing_config_reset:reset,")],
}
_SH_A="  crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees"
_SH_E="signer_seeds),val)?;"
for _n,_attr in [('sh_fn',''),('sh_fn_ia','#[inline(always)]'),('sh_fn_i','#[inline]')]:
    GENES[_n]=[(_SH_A,"  share(&ctx,signer_seeds,val)?;"+_attr+"fn share(ctx:&Context<AdminCto>,signer_seeds:&[&[&[u8]]],val:Option<Pubkey>)->Result<()>{let a=&ctx.accounts;crate::pump_fees::cpi::admin_cto_sharing_config(CpiContext::new_with_signer(a.pump_fees"),(_SH_E,"signer_seeds),val)}")]
_FE_OLD="swept_to_holder_vault:swept,pool_updated};emit!(e);emit_cpi!(e);Ok(())"
_BODY="let authority_info=ctx.accounts.event_authority.to_account_info();let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);"
GENES['fe_exp0']=[(_FE_OLD,"swept_to_holder_vault:swept,pool_updated};emit!(e);{"+_BODY+"anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b\"__event_authority\",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;}Ok(())")]
GENES['fe_sig_local']=[(_FE_OLD,"swept_to_holder_vault:swept,pool_updated};emit!(e);let fe_signers:[&[&[u8]];1];{"+_BODY+"let event_inner:&[&[u8]]=&[b\"__event_authority\",&[authority_bump]];fe_signers=[event_inner];anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&fe_signers).map_err(anchor_lang::error::Error::from)?;}Ok(())")]
GENES['fe_sig_early']=[(" let signer_seeds:&[&[&[u8]]]="," let fe_signers:[&[&[u8]];1];let signer_seeds:&[&[&[u8]]]="),(_FE_OLD,"swept_to_holder_vault:swept,pool_updated};emit!(e);{"+_BODY+"let event_inner:&[&[u8]]=&[b\"__event_authority\",&[authority_bump]];fe_signers=[event_inner];anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&fe_signers).map_err(anchor_lang::error::Error::from)?;}Ok(())")]
GENES['fe_ixd_early']=[(" let signer_seeds:&[&[&[u8]]]="," let ix_data:Vec<u8>;let signer_seeds:&[&[&[u8]]]="),(_FE_OLD,"swept_to_holder_vault:swept,pool_updated};emit!(e);{"+_BODY.replace("let ix_data:Vec<u8>=","ix_data=")+"anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b\"__event_authority\",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;}Ok(())")]
GENES['pool_hlocal']=[("signer_seeds),target,a.bonding_curve.is_holder_reward,fee)?;","signer_seeds),target,holder,fee)?;")]
GENES['ev_hr_curve2']=[("is_holder_reward:holder,","is_holder_reward:a.bonding_curve.is_holder_reward,")]
GENES['sk_inline']=[("let sk=a.sharing_config.key();let mut target=validate(&st,holder,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,holder,fee,new,&holder_key,&a.sharing_config.key())?;")]
GENES['cb_rev_back']=[("let cashback=st.cashback&&!holder;","let cashback=!holder&&st.cashback;")]
GENES['sk_inline']=[("let sk=a.sharing_config.key();let mut target=validate(&st,hopt,fee,new,&holder_key,&sk)?;","let mut target=validate(&st,hopt,fee,new,&holder_key,&a.sharing_config.key())?;")]
_OK="Ok::<_,anchor_lang::error::Error>"
GENES['vh_arm']=[(" match sharing_update{Some(val)=>{"," match sharing_update{Some(val)=>{let val="+_OK+"(val)?;")]
GENES['vh_su']=[(" match sharing_update{Some(val)=>{"," let sharing_update="+_OK+"(sharing_update)?;match sharing_update{Some(val)=>{")]
GENES['oc_hi']=[(" (old_creator,old_fee)};"," (old_creator,old_fee)};let (old_creator,old_fee)="+_OK+"((old_creator,old_fee))?;")]
GENES['oc_hi1']=[(" (old_creator,old_fee)};"," (old_creator,old_fee)};let old_creator="+_OK+"(old_creator)?;")]
GENES['sw_hi']=[(" let signer_seeds:&[&[&[u8]]]="," let swept="+_OK+"(swept)?;let signer_seeds:&[&[&[u8]]]=")]
GENES['ev_hi']=[(" let e=AdminCtoEvent{"," let e="+_OK+"(AdminCtoEvent{"),(",swept_to_holder_vault:swept,pool_updated};emit!(e);",",swept_to_holder_vault:swept,pool_updated})?;emit!(e);")]
GENES['tgt_hi_late']=[(" let a=&ctx.accounts;\n let pool_updated="," let a=&ctx.accounts;let target="+_OK+"(target)?;\n let pool_updated=")]
