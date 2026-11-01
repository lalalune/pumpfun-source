use anchor_lang::prelude::*; use anchor_spl::{associated_token::AssociatedToken,token::{Mint,Token,TokenAccount}}; use crate::anchor_framework::*;
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
// Historical text preceding this macro is unknown.
#[event_cpi]
#[derive(Accounts)]
#[instruction(source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32])]
pub struct RecoverBridgePaymentV1<'info> {
 #[account(init,payer=payer,space=8,seeds=[b"bridge_source_v1",source_id.as_ref()],bump)]
 pub source_marker:Account<'info,BridgeSourceV1>,
 #[account(init,payer=payer,space=8,seeds=[b"bridge_payment_v1",payment_id.as_ref()],bump)]
 pub payment_marker:Account<'info,BridgePaymentV1>,
 /// CHECK: PDA receiver, one per source id; signs the recovery transfer.
 #[account(seeds=[b"bridge_receiver_v1",source_id.as_ref()],bump)]
 pub receiver:UncheckedAccount<'info>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=receiver,associated_token::token_program=token_program)]
 pub receiver_token_account:Account<'info,TokenAccount>,
 /// CHECK: owner of the destination token account.
 #[account(constraint=destination_owner.key()!=Pubkey::default() && destination_owner.key()!=receiver.key() @ crate::business_error_codes::ErrorCode::InvalidOwner)]
 pub destination_owner:UncheckedAccount<'info>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=destination_owner,associated_token::token_program=token_program)]
 pub destination_token_account:Account<'info,TokenAccount>,
 #[account(address=Pubkey::new_from_array(crate::codec::constants::SETTLEMENT))]
 pub mint:Account<'info,Mint>,
 #[account(constraint=program_data.upgrade_authority_address==Some(authority.key()) @ crate::business_error_codes::ErrorCode::InvalidAdmin)]
 pub program_data:Account<'info,ProgramData>,
 pub authority:Signer<'info>,
 #[account(mut)]
 pub payer:Signer<'info>,
 pub token_program:Program<'info,Token>,
 pub associated_token_program:Program<'info,AssociatedToken>,
 pub system_program:Program<'info,System>,
}
use anchor_lang::solana_program::bpf_loader_upgradeable::UpgradeableLoaderState;
use crate::business_error_codes::ErrorCode as Code;
macro_rules! bridge_error {($file:literal,$code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:$file,line:$line})),compared_values:None})};}

pub fn recover_bridge_payment<'info>(accounts:&mut RecoverBridgePaymentV1<'info>,source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32],amount:u64,receiver_bump:u8)->Result<BridgePaymentRecoveredV1Event> {
 if accounts.program.key()!=crate::ID {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InvalidAdmin,56).with_pubkeys((accounts.program.key(),crate::ID)));}
 if !accounts.program.executable {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InvalidAdmin,57));}
 if *accounts.program.owner!=anchor_lang::solana_program::bpf_loader_upgradeable::ID {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InvalidAdmin,58).with_pubkeys((*accounts.program.owner,anchor_lang::solana_program::bpf_loader_upgradeable::ID)));}
 let state=UpgradeableLoaderState::try_deserialize_unchecked(&mut &accounts.program.try_borrow_data()?[..])?;
 let linked=matches!(state,UpgradeableLoaderState::Program {programdata_address} if programdata_address==accounts.program_data.key());
 if !linked {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InvalidAdmin,66));}
 if amount==0 {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",OutputAmountMustBeGreaterThanZero,71));}
 let receiver_before=accounts.receiver_token_account.amount;let destination_before=accounts.destination_token_account.amount;
 let seeds:&[&[u8]]=&[b"bridge_receiver_v1",source_id.as_ref(),&[receiver_bump]];
 anchor_spl::token::transfer_checked(CpiContext::new_with_signer(accounts.token_program.to_account_info(),anchor_spl::token::TransferChecked {from:accounts.receiver_token_account.to_account_info(),mint:accounts.mint.to_account_info(),to:accounts.destination_token_account.to_account_info(),authority:accounts.receiver.to_account_info()},&[seeds]),amount,accounts.mint.decimals)?;
 accounts.receiver_token_account.reload()?;accounts.destination_token_account.reload()?;
 if receiver_before.checked_sub(amount)!=Some(accounts.receiver_token_account.amount) || destination_before.checked_add(amount)!=Some(accounts.destination_token_account.amount) {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InputAmountMismatch,95));}
 Ok(BridgePaymentRecoveredV1Event {daas_event_discriminator:DaasEventDiscriminator::BridgePaymentRecoveredV1,source_id,source_commitment,payment_id,mint:accounts.mint.key(),receiver_token_account:accounts.receiver_token_account.key(),destination_owner:accounts.destination_owner.key(),destination_token_account:accounts.destination_token_account.key(),amount,authority:accounts.authority.key()})
}
