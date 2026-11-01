//! Bridge payment handlers read from the deployed program; shape still to be fitted function by function.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::bpf_loader_upgradeable::UpgradeableLoaderState;
use crate::anchor_framework::*;
use crate::business_error_codes::ErrorCode as Code;
macro_rules! bridge_error {($file:literal,$code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:$file,line:$line})),compared_values:None})};}

pub fn admit_bridge_payment<'info>(accounts:&mut AdmitBridgePaymentV1<'info>,source_id:[u8;32],source_commitment:[u8;32],payment_id:[u8;32],config_id:[u8;32],amount:u64,minimum_amount:u64,tip_bps:u16,receiver_bump:u8,epoch_tracker_bump:u8,debouncer_bump:u8)->Result<BridgeDonationAdmittedV1Event> {
 if amount==0 {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",OutputAmountMustBeGreaterThanZero,57));}
 if amount<minimum_amount {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",InputAmountMismatch,58));}
 crate::tools::checks::check_bps(tip_bps)?;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"bridge_receiver_v1",source_id.as_ref(),&[receiver_bump]]];
 let amounts=crate::tools::donate::shared::donate_with_seeds(crate::tools::donate::shared::SignedDonationContext {epoch_tracker:&mut accounts.epoch_tracker,debouncer:&mut accounts.debouncer,debouncer_token_account:accounts.debouncer_token_account.to_account_info(),mint:accounts.mint.to_account_info(),from_token_account:accounts.receiver_token_account.to_account_info(),from:accounts.receiver.to_account_info(),token_program:accounts.token_program.to_account_info()},crate::tools::donate::shared::DonationArgs {config_id,amount,message:String::new(),tip_bps,epoch_tracker_bump,debouncer_bump},signer_seeds)?;
 if amounts.gross_amount!=amount {return Err(bridge_error!("programs/contracts/src/instructions/v1/relayer_only/admit_bridge_payment.rs",InputAmountMismatch,83));}
 Ok(BridgeDonationAdmittedV1Event {daas_event_discriminator:DaasEventDiscriminator::BridgeDonationAdmittedV1,source_id:source_id,source_commitment:source_commitment,payment_id:payment_id,config_id:config_id,mint:accounts.mint.key(),epoch:amounts.epoch,gross_amount:amounts.gross_amount,tip:amounts.tip})
}

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
