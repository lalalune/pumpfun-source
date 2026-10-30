# frame-position scan for the expanded final emit_cpi!(e) of AdminCtoEvent (main 2ca4d03 text)
FE_OLD="swept_to_holder_vault:swept,pool_updated};emit!(e);emit_cpi!(e);Ok(())"
POS={'E0':(" let a=&ctx.accounts;let mint=a.mint.key();"," let a=&ctx.accounts;{D}let mint=a.mint.key();"),
     'E1':(" let signer_seeds:&[&[&[u8]]]="," {D}let signer_seeds:&[&[&[u8]]]="),
     'E2':(" let (old_creator,old_fee)={"," {D}let (old_creator,old_fee)={"),
     'E3':(" let pool_updated="," {D}let pool_updated="),
     'E4':(" let e=AdminCtoEvent{"," {D}let e=AdminCtoEvent{")}
def body(h):
    s=lambda name,ty,val: (f"{name}={val};" if name in h else f"let {name}{ty}={val};")
    b=s('authority_info','',"ctx.accounts.event_authority.to_account_info()")+"let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;"
    b+=s('inner_data','',"anchor_lang::Event::data(&e)")
    b+=s('ix_data',':Vec<u8>',"disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect()")
    b+=s('ix','',"anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)])")
    if 'fe_signers' in h:
        b+="let event_inner:&[&[u8]]=&[b\"__event_authority\",&[authority_bump]];fe_signers=[event_inner];anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&fe_signers).map_err(anchor_lang::error::Error::from)?;"
    else:
        b+="anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b\"__event_authority\",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;"
    return FE_OLD.replace("emit_cpi!(e);","{"+b+"}")
DECL={'fe_signers':"let fe_signers:[&[&[u8]];1];",'authority_info':"let authority_info:AccountInfo;",'inner_data':"let inner_data:Vec<u8>;",
      'ix_data':"let ix_data:Vec<u8>;",'ix':"let ix:Instruction;"}
GENES={}
for t,d in DECL.items():
    for p,(o,n) in POS.items():
        GENES[f'h_{t}_{p}']=[(o,n.replace('{D}',d)),(FE_OLD,body({t}))]
