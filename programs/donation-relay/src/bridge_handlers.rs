//! Bridge payment handlers read from the deployed program; shape still to be fitted function by function.
use anchor_lang::prelude::*;
use crate::anchor_framework::*;
use crate::business_error_codes::ErrorCode as Code;
macro_rules! bridge_error {($file:literal,$code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:$file,line:$line})),compared_values:None})};}

pub struct AdmitArgs {pub source_id:[u8;32],pub source_commitment:[u8;32],pub payment_id:[u8;32],pub config_id:[u8;32],pub amount:u64,pub minimum_amount:u64,pub tip_bps:u16}
pub fn admit_bridge_payment<'info>(accounts:&mut AdmitBridgePaymentV1<'info>,args:AdmitArgs,receiver_bump:u8,epoch_tracker_bump:u8,debouncer_bump:u8)->Result<BridgeDonationAdmittedV1Event> {
 if args.amount==0 {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",OutputAmountMustBeGreaterThanZero,57));}
 if args.amount<args.minimum_amount {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",InputAmountMismatch,58));}
 crate::tools::checks::check_bps(args.tip_bps)?;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"bridge_receiver_v1",args.source_id.as_ref(),&[receiver_bump]]];
 let amounts=crate::tools::donate::shared::donate_with_seeds(crate::tools::donate::shared::SignedDonationContext {epoch_tracker:&mut accounts.epoch_tracker,debouncer:&mut accounts.debouncer,debouncer_token_account:accounts.debouncer_token_account.to_account_info(),mint:accounts.mint.to_account_info(),from_token_account:accounts.receiver_token_account.to_account_info(),from:accounts.receiver.to_account_info(),token_program:accounts.token_program.to_account_info()},crate::tools::donate::shared::DonationArgs {config_id:args.config_id,amount:args.amount,message:String::new(),tip_bps:args.tip_bps,epoch_tracker_bump,debouncer_bump},signer_seeds)?;
 if amounts.gross_amount!=args.amount {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",InputAmountMismatch,83));}
 Ok(BridgeDonationAdmittedV1Event {daas_event_discriminator:DaasEventDiscriminator::BridgeDonationAdmittedV1,source_id:args.source_id,source_commitment:args.source_commitment,payment_id:args.payment_id,config_id:args.config_id,mint:accounts.mint.key(),epoch:amounts.epoch,gross_amount:amounts.gross_amount,tip:amounts.tip})
}

pub struct RecoverArgs {pub source_id:[u8;32],pub source_commitment:[u8;32],pub payment_id:[u8;32],pub amount:u64}
pub fn recover_bridge_payment<'info>(accounts:&mut RecoverBridgePaymentV1<'info>,args:RecoverArgs,receiver_bump:u8)->Result<BridgePaymentRecoveredV1Event> {
 if accounts.program.key()!=crate::ID {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InvalidAdmin,56));}
 if !accounts.program.executable {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InvalidAdmin,57));}
 if *accounts.program.owner!=anchor_lang::solana_program::bpf_loader_upgradeable::ID {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InvalidAdmin,58));}
 if accounts.program_data.upgrade_authority_address!=Some(accounts.authority.key()) {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InvalidAdmin,66));}
 if args.amount==0 {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",OutputAmountMustBeGreaterThanZero,71));}
 let receiver_before=accounts.receiver_token_account.amount;let destination_before=accounts.destination_token_account.amount;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"bridge_receiver_v1",args.source_id.as_ref(),&[receiver_bump]]];
 anchor_spl::token::transfer_checked(CpiContext::new_with_signer(accounts.token_program.to_account_info(),anchor_spl::token::TransferChecked {from:accounts.receiver_token_account.to_account_info(),mint:accounts.mint.to_account_info(),to:accounts.destination_token_account.to_account_info(),authority:accounts.receiver.to_account_info()},signer_seeds),args.amount,accounts.mint.decimals)?;
 accounts.receiver_token_account.reload()?;accounts.destination_token_account.reload()?;
 if receiver_before.checked_sub(accounts.receiver_token_account.amount)!=Some(args.amount) || accounts.destination_token_account.amount.checked_sub(destination_before)!=Some(args.amount) {return Err(bridge_error!("programs/contracts/src/instructions/v1/recover_bridge_payment.rs",InputAmountMismatch,95));}
 Ok(BridgePaymentRecoveredV1Event {daas_event_discriminator:DaasEventDiscriminator::BridgePaymentRecoveredV1,source_id:args.source_id,source_commitment:args.source_commitment,payment_id:args.payment_id,mint:accounts.mint.key(),receiver_token_account:accounts.receiver_token_account.key(),destination_owner:accounts.destination_owner.key(),destination_token_account:accounts.destination_token_account.key(),amount:args.amount,authority:accounts.authority.key()})
}
