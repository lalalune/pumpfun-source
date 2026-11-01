use anchor_lang::prelude::*;
use crate::business_error_codes::ErrorCode as Code;
macro_rules! jupiter_error {($code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:"programs/contracts/src/cpi/jupiter.rs",line:$line})),compared_values:None})};}
pub fn invoke_jupiter<'info>(program:Pubkey,authority:Pubkey,remaining:&[AccountInfo<'info>],data:Vec<u8>,seeds:Option<&[&[&[u8]]]>)->Result<()> {
 let metas=remaining.iter().map(|a|anchor_lang::solana_program::instruction::AccountMeta {pubkey:*a.key,is_signer:a.key==&authority,is_writable:a.is_writable}).collect();
 let infos=remaining.iter().cloned().collect::<Vec<_>>();
 let ix=anchor_lang::solana_program::instruction::Instruction {program_id:program,accounts:metas,data};
 match seeds {Some(seeds)=>anchor_lang::solana_program::program::invoke_signed(&ix,&infos,seeds)?,None=>anchor_lang::solana_program::program::invoke(&ix,&infos)?};Ok(())
}
pub fn swap_observed<'info>(program:&AccountInfo<'info>,authority:Pubkey,input:&mut anchor_lang::accounts::interface_account::InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>,output:&mut anchor_lang::accounts::interface_account::InterfaceAccount<'info,anchor_spl::token_interface::TokenAccount>,remaining:&[AccountInfo<'info>],data:Vec<u8>,seeds:&[&[&[u8]]],expected:u64)->Result<u64> {
 let before_input=input.amount;let before_output=output.amount;
 invoke_jupiter(program.key(),authority,remaining,data,Some(seeds))?;
 input.reload()?;output.reload()?;
 let spent=before_input.checked_sub(input.amount).ok_or(Code::ArithmeticOverflow)?;
 if spent!=expected {return Err(jupiter_error!(InputAmountMismatch,92).with_values((spent,expected)));}
 let delta=output.amount.checked_sub(before_output).ok_or(Code::ArithmeticOverflow)?;
 if delta==0 {return Err(jupiter_error!(OutputAmountMustBeGreaterThanZero,103));}Ok(delta)
}
