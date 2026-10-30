# Variant library for w14a28-cto-evauthlit. Each variant: list of (old,new) exact edits on admin_cto.rs (line count preserved).
EA='ctx.accounts.event_authority'
F={'K':'key:{p}.key','L':'lamports:{p}.lamports.clone()','D':'data:{p}.data.clone()','O':'owner:{p}.owner',
   'R':'rent_epoch:{p}.rent_epoch','S':'is_signer:{p}.is_signer','W':'is_writable:{p}.is_writable','E':'executable:{p}.executable'}
def lit(order,p):
    return 'AccountInfo{'+','.join(F[c].format(p=p) for c in order)+'}'
W_OLD='let authority_info=ctx.accounts.event_authority.to_account_info();'
T_OLD='emit!(e);emit_cpi!(e);Ok(())'
def tail(auth='ctx.accounts.event_authority.to_account_info()',form='macro'):
    if form=='macro':   # anchor 0.31 emit_cpi! text
        body=('{let authority_info='+auth+';let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;'
              'let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();'
              'let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);'
              'anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b"__event_authority",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;}')
    elif form=='wallet':  # same statement form as the landed wallet block
        body=('{let event_signers:[&[&[u8]];1];let authority_info='+auth+';let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;'
              'let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();'
              'let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);'
              'let event_infos=[authority_info];({let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];event_signers=[event_inner];'
              'anchor_lang::solana_program::program::invoke_signed(&ix,&event_infos,&event_signers)}).map_err(anchor_lang::error::Error::from)?;}')
    elif form=='arrfirst':  # [authority_info] array bound right after the clone, before the event data
        body=('{let authority_info='+auth+';let authority_bump=ctx.bumps.event_authority;let disc=anchor_lang::event::EVENT_IX_TAG_LE;'
              'let inner_data=anchor_lang::Event::data(&e);let ix_data:Vec<u8>=disc.into_iter().map(|b|*b).chain(inner_data.into_iter()).collect();'
              'let ix=anchor_lang::solana_program::instruction::Instruction::new_with_bytes(crate::ID,&ix_data,vec![anchor_lang::solana_program::instruction::AccountMeta::new_readonly(*authority_info.key,true)]);'
              'let event_infos=[authority_info];anchor_lang::solana_program::program::invoke_signed(&ix,&event_infos,&[&[b"__event_authority",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;}')
    return [(T_OLD,'emit!(e);'+body+'Ok(())')]
V={}
# tail site
V['t0']=tail()                                            # control: hand expansion of emit_cpi!
V['tw']=tail(form='wallet')
V['ta']=tail(form='arrfirst')
V['tlK_thru']=tail(auth=lit('KRLSDOWE',EA))             # literal, #3260 order, through-path reads
V['tlL_thru']=tail(auth=lit('KLDORSWE',EA))             # literal, declaration order, through-path reads
V['tlL_x']=tail(auth='{let x:&AccountInfo=&'+EA+';'+lit('KLDORSWE','x')+'}')
V['tlLD_thru']=tail(auth=lit('LDKORSWE',EA))            # #3267 sharing order (lamports,data first)
# wallet site
V['wlK_thru']=[(W_OLD,'let authority_info='+lit('KRLSDOWE',EA)+';')]
V['wlLD_thru']=[(W_OLD,'let authority_info='+lit('LDKORSWE',EA)+';')]
V['wlL_thru']=[(W_OLD,'let authority_info='+lit('KLDORSWE',EA)+';')]
