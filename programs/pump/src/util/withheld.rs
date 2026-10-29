use anchor_lang::prelude::*;
pub fn harvest_withheld_tokens_to_mint<'info>(token_program:&AccountInfo<'info>,mint:&AccountInfo<'info>,source:&AccountInfo<'info>)->Result<()>{
 anchor_spl::token_2022_extensions::harvest_withheld_tokens_to_mint(CpiContext::new(token_program.clone(),anchor_spl::token_2022_extensions::HarvestWithheldTokensToMint{token_program_id:token_program.clone(),mint:mint.clone()}),vec![source.clone()])
}
