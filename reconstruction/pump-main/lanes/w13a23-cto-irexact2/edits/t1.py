EDITS=[("""         let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];
         event_signers=[event_inner];
         anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&event_signers).map_err(anchor_lang::error::Error::from)?;""",
"""         let r;let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];
         event_signers=[event_inner];
         r=anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&event_signers);r.map_err(anchor_lang::error::Error::from)?;""")]
