EDITS=[("""         let event_inner:&[&[u8]]=&[b"__event_authority",&[authority_bump]];
         event_signers=[event_inner];
         anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&event_signers).map_err(anchor_lang::error::Error::from)?;""",
"""

         anchor_lang::solana_program::program::invoke_signed(&ix,&[authority_info],&[&[b"__event_authority",&[authority_bump]]]).map_err(anchor_lang::error::Error::from)?;"""),
("let event_signers:[&[&[u8]];1];if let Some((collected","if let Some((collected")]
