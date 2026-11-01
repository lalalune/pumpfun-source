use crate::business_error_codes::ErrorCode as Code;
macro_rules! source_error {
 ($code:ident,$file:literal,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:$file,line:$line})),compared_values:None,
 })};
}
use anchor_lang::prelude::*;
pub fn native_program_supported(program:&Pubkey)->bool {
 program.to_bytes()==crate::codec::constants::TOKEN || program.to_bytes()==crate::codec::constants::TOKEN2022
}
pub fn native_mint_for_program(program:&Pubkey)->Result<Pubkey> {
 if program.to_bytes()==crate::codec::constants::TOKEN {Ok(Pubkey::new_from_array(crate::codec::constants::NATIVE))}
 else if program.to_bytes()==crate::codec::constants::TOKEN2022 {Ok(Pubkey::new_from_array(crate::codec::constants::NATIVE2022))}
 else {Err(crate::business_error_codes::ErrorCode::InvalidTokenProgram.into())}
}
pub fn native_mint_pair(mint:&Pubkey,program:&Pubkey)->bool {
 native_mint_for_program(program).map(|expected|expected==*mint).unwrap_or_default()
}
pub fn check_message(message:&str)->Result<()> {
 if !(message.len()<256) {return Err(source_error!(InvalidMessageLength,"programs/contracts/src/tools/checks.rs",55));}Ok(())
}
// Preserve the independently observed call boundary; original annotation unknown.
#[inline(never)]
pub(crate) fn check_relayer(signer:&Signer<'_>) -> Result<()> {
    let key=signer.key;
    if *key!=Pubkey::new_from_array(crate::codec::constants::RELAYER) {
        return Err(anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
            error_name:crate::business_error_codes::ErrorCode::SignerIsNotRelayer.name(),error_code_number:crate::business_error_codes::ErrorCode::SignerIsNotRelayer.into(),error_msg:crate::business_error_codes::ErrorCode::SignerIsNotRelayer.to_string(),
            error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {
                filename:"programs/contracts/src/tools/checks.rs",line:80})),
            compared_values:None,
        }).with_pubkeys((*key,Pubkey::new_from_array(crate::codec::constants::RELAYER))));
    }
    Ok(())
}























































pub fn typed_mint_safe(info:&AccountInfo)->anchor_lang::Result<bool> {
 use spl_token_2022::{state::{Mint as SplMint,AccountState},extension::{BaseStateWithExtensions,StateWithExtensions,
 transfer_fee::TransferFeeConfig,transfer_hook::TransferHook,permanent_delegate::PermanentDelegate,
 mint_close_authority::MintCloseAuthority,default_account_state::DefaultAccountState,non_transferable::NonTransferable}};
           let data=info.data.borrow();
 let state=StateWithExtensions::<SplMint>::unpack(&data)?;
 if state.base.mint_authority.is_some() || state.base.freeze_authority.is_some() {return Ok(false);}
 if info.owner.to_bytes()==crate::codec::constants::TOKEN2022 {
  if let Ok(fee)=state.get_extension::<TransferFeeConfig>() {
   if Option::<Pubkey>::from(fee.transfer_fee_config_authority).is_some() {return Ok(false);}
   if (u16::from(fee.older_transfer_fee.transfer_fee_basis_points),u16::from(fee.newer_transfer_fee.transfer_fee_basis_points)) != (0,0) {return Ok(false);}
  }
  if let Ok(hook)=state.get_extension::<TransferHook>() {
   if Option::<Pubkey>::from(hook.authority).is_some() || Option::<Pubkey>::from(hook.program_id).is_some() {return Ok(false);}
  }
  if state.get_extension::<PermanentDelegate>().is_ok() {return Ok(false);}
  if let Ok(close)=state.get_extension::<MintCloseAuthority>() {
   if Option::<Pubkey>::from(close.close_authority).is_some() {return Ok(false);}
  }
  if let Ok(default)=state.get_extension::<DefaultAccountState>() {
   if default.state!=AccountState::Initialized as u8 {return Ok(false);}
  }
  if state.get_extension::<NonTransferable>().is_ok() {return Ok(false);}
 }
 Ok(true)
}

pub fn check_bps(bps:u16)->Result<()> {
 if !(bps<=10000) {return Err(source_error!(InvalidBps,"programs/contracts/src/tools/checks.rs",192));}Ok(())
}

#[inline]
pub(crate) fn admit_shares(bps:impl Iterator<Item=u16>)->Result<()> {
 let mut sum=0u32;for bps in bps {sum=sum.checked_add(u32::from(bps)).ok_or_else(||anchor_lang::error::Error::from(Code::ArithmeticOverflow))?;}
 if sum!=10000 {return Err(source_error!(BpsSumDoesNotEqualTenThousand,"programs/contracts/src/tools/checks.rs",204).with_values((sum,10000u32)));}
 Ok(())
}
