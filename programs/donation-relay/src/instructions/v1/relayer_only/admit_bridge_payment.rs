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
// Historical text preceding this macro is unknown.
#[event_cpi]
#[derive(Accounts)]
#[instruction(source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32],config_id:[u8;32])]
pub struct AdmitBridgePaymentV1<'info> {
 #[account(init,payer=signer,space=8,seeds=[b"bridge_source_v1",source_id.as_ref()],bump)]
 pub source_marker:Account<'info,BridgeSourceV1>,
 #[account(init,payer=signer,space=8,seeds=[b"bridge_payment_v1",payment_id.as_ref()],bump)]
 pub payment_marker:Account<'info,BridgePaymentV1>,
 /// CHECK: PDA receiver, one per source id; signs the donation transfer.
 #[account(seeds=[b"bridge_receiver_v1",source_id.as_ref()],bump)]
 pub receiver:UncheckedAccount<'info>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=receiver,associated_token::token_program=token_program)]
 pub receiver_token_account:Account<'info,TokenAccount>,
 #[account(seeds=[b"epoch_tracker_v1",config_id.as_ref(),mint.key().as_ref()],bump,init_if_needed,payer=signer,space=90)]
 pub epoch_tracker:Account<'info,EpochTrackerV1>,
 #[account(seeds=[b"debouncer_v1",config_id.as_ref(),mint.key().as_ref()],bump,init_if_needed,payer=signer,space=82)]
 pub debouncer:Account<'info,DebouncerV1>,
 #[account(init_if_needed,payer=signer,associated_token::mint=mint,associated_token::authority=debouncer,associated_token::token_program=token_program)]
 pub debouncer_token_account:Account<'info,TokenAccount>,
 #[account(address=Pubkey::new_from_array(crate::codec::constants::SETTLEMENT))]
 pub mint:Account<'info,Mint>,
 #[account(mut)]
 pub signer:Signer<'info>,
 pub token_program:Program<'info,Token>,
 pub associated_token_program:Program<'info,AssociatedToken>,
 pub system_program:Program<'info,System>,
}
use crate::business_error_codes::ErrorCode as Code;
macro_rules! bridge_error {($file:literal,$code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:$file,line:$line})),compared_values:None})};}

pub fn admit_bridge_payment<'info>(accounts:&mut AdmitBridgePaymentV1<'info>,source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32],config_id:[u8;32],amount:u64,minimum_amount:u64,tip_bps:u16,receiver_bump:u8,epoch_tracker_bump:u8,debouncer_bump:u8)->Result<BridgeDonationAdmittedV1Event> {
 if amount==0 {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",OutputAmountMustBeGreaterThanZero,57));}
 if amount<minimum_amount {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",InputAmountMismatch,58));}
 crate::tools::checks::check_bps(tip_bps)?;
 let amounts=crate::tools::donate::shared::donate_with_seeds(crate::tools::donate::shared::SignedDonationContext {epoch_tracker:&mut accounts.epoch_tracker,debouncer:&mut accounts.debouncer,debouncer_token_account:accounts.debouncer_token_account.to_account_info(),mint:accounts.mint.to_account_info(),from_token_account:accounts.receiver_token_account.to_account_info(),from:accounts.receiver.to_account_info(),token_program:accounts.token_program.to_account_info()},crate::tools::donate::shared::SignedDonationArgs {config_id,amount,tip_bps,epoch_tracker_bump,debouncer_bump},&[&[b"bridge_receiver_v1",source_id.as_ref(),&[receiver_bump]]])?;
 if amounts.gross_amount!=amount {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",InputAmountMismatch,83).with_values((amounts.gross_amount,amount)));}
 Ok(BridgeDonationAdmittedV1Event {daas_event_discriminator:DaasEventDiscriminator::BridgeDonationAdmittedV1,source_id:source_id,source_commitment:source_commitment,payment_id:payment_id,config_id:config_id,mint:accounts.mint.key(),epoch:amounts.epoch,gross_amount:amounts.gross_amount,tip:amounts.tip})
}
