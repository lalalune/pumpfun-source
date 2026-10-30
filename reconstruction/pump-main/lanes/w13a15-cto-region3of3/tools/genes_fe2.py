# final emit_cpi!(e) of AdminCtoEvent: temporary-creation-order variants (w13a23 wallet mechanism), main bf9a05d text
FE_OLD="swept_to_holder_vault:swept,pool_updated};emit!(e);emit_cpi!(e);Ok(())"
H="swept_to_holder_vault:swept,pool_updated};emit!(e);"
AI="let authority_info=ctx.accounts.event_authority.to_account_info();let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;"
ID="let inner_data=anchor_lang::Event::data(&e);"
XD="let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();"
IX="let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);"
INV="anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b\"__event_authority\",&[authority_bump]]])"
ME=".map_err(anchor_lang::error::Error::from)?;"
SIG="let event_inner:&[&[u8]]=&[b\"__event_authority\",&[authority_bump]];fe_signers=[event_inner];"
INV2="anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&fe_signers)"
def g(body,pre=None):
    r=[(FE_OLD,H+"{"+body+"}Ok(())")]
    if pre: r.insert(0,(" let e=AdminCtoEvent{"," "+pre+"let e=AdminCtoEvent{"))
    return r
GENES={
 'f_wrap':g(AI+ID+XD+IX+"({"+INV+"})"+ME),
 'f_wrap_sig_out':g(AI+ID+XD+IX+"({"+SIG+INV2+"})"+ME,"let fe_signers:[&[&[u8]];1];"),
 'f_wrap_sig_in':g(AI+ID+XD+IX+"let fe_signers:[&[&[u8]];1];({"+SIG+INV2+"})"+ME),
 'f_sig_first':g("let fe_signers:[&[&[u8]];1];"+AI+ID+XD+IX+"({"+SIG+INV2+"})"+ME),
 'f_ixd_wrap':g(AI+ID+"let ix_data:Vec<u8>={disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect()};"+IX+INV+ME),
 'f_ix_wrap':g(AI+ID+XD+"let ix={anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)])};"+INV+ME),
 'f_res_let':g(AI+ID+XD+IX+"let res;res={"+INV+"};res"+ME),
 'f_wrap_all':g("({"+AI+ID+XD+IX+INV+"})"+ME),
 'f_ixd_then_wrap':g(AI+ID+"let ix_data:Vec<u8>={disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect()};"+IX+"({"+INV+"})"+ME),
}
