//! Typed close-epoch body. Privileged runtime success is not inferred from parser tests.
use anchor_lang::prelude::*;
use crate::anchor_framework::*;
use crate::business_error_codes::ErrorCode as Code;
macro_rules! close_error {($code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:"programs/contracts/src/instructions/v1/relayer_only/close_donation_epoch.rs",line:$line})),compared_values:None})};}


macro_rules! just_error {($code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:"programs/contracts/src/instructions/v1/relayer_only/distribute/just_swap.rs",line:$line})),compared_values:None})};}

pub use crate::cpi::jupiter::{invoke_jupiter,swap_observed};
pub use crate::tools::distribution::shared::{BurnCloseContext,burn_and_close};

macro_rules! distribution_error {($file:literal,$code:ident,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:$file,line:$line})),compared_values:None})};}


pub fn close_epoch(accounts:&mut CloseDonationEpochV1,args:crate::codec::wire::CloseDonationEpochV1,distribution_bump:u8)->Result<DonationEpochClosedV1Event> {
 let epoch=accounts.epoch_tracker.current_epoch;
 let gross=accounts.debouncer.total_amount;
 if gross==0 {return Err(close_error!(InvalidBalance,91));}
 if epoch!=args.epoch {return Err(close_error!(EpochAlreadyClosed,95));}
 accounts.distribution.set_inner(DistributionV1 {bump:distribution_bump,state:DistributionV1State::Initialized,config_id:accounts.debouncer.config_id,mint:accounts.debouncer.mint,epoch,total_amount:gross});
 let signer_seeds:&[&[&[u8]];1]=&[&[b"debouncer_v1",accounts.debouncer.config_id.as_ref(),accounts.debouncer.mint.as_ref(),&[accounts.debouncer.bump]]];
 anchor_spl::token_interface::transfer_checked(CpiContext::new(accounts.token_program.to_account_info(),anchor_spl::token_interface::TransferChecked {
  from:accounts.debouncer_token_account.to_account_info(),mint:accounts.mint.to_account_info(),to:accounts.distribution_token_account.to_account_info(),authority:accounts.debouncer.to_account_info(),
 }).with_signer(signer_seeds),gross,accounts.mint.decimals)?;
 accounts.debouncer.total_amount=0;
 accounts.epoch_tracker.increment()?;
 Ok(DonationEpochClosedV1Event {daas_event_discriminator:DaasEventDiscriminator::DonationEpochClosedV1,config_id:accounts.debouncer.config_id,mint:accounts.debouncer.mint,epoch,gross_epoch_amount:gross})
}

#[inline(never)]
pub(crate) fn distribute_after_prechecks(accounts:&DistributeAfterJustSwappingV1<'_>)->Result<()> {
 if !(accounts.distribution.epoch<accounts.epoch_tracker.current_epoch) {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_after_just_swapping.rs",EpochNotClosed,88));}
 if accounts.distribution.state!=DistributionV1State::Initialized {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_after_just_swapping.rs",InvalidState,93));}
 if accounts.debouncer.mint!=accounts.distribution.mint {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_after_just_swapping.rs",InvalidMint,98).with_pubkeys((accounts.debouncer.mint,accounts.distribution.mint)));}
 Ok(())
}

pub fn distribute_after<'info>(accounts:&mut DistributeAfterJustSwappingV1<'info>,args:crate::codec::wire::DistributeAfterJustSwappingV1,remaining:&'info [AccountInfo<'info>])->Result<DonationEpochProcessedV1Event> {
 let crate::codec::wire::DistributeAfterJustSwappingV1 {shares}=args;
 distribute_after_prechecks(accounts)?;
 crate::tools::checks::admit_shares(shares.iter().map(|share|share.bps))?;
 let total=accounts.swap_receipt.swap_output_amount;
 if total==0 {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_after_just_swapping.rs",InvalidBalance,116));}
 if accounts.output_distribution_token_account.amount<total {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_after_just_swapping.rs",InvalidBalance,118));}
 if remaining.len()<shares.len() {return Err(Code::InsufficientRemainingAccounts.into());}
 let remaining=&remaining[..shares.len()];
 let config=accounts.distribution.config_id;let mint=accounts.distribution.mint;let epoch=accounts.distribution.epoch.to_le_bytes();let bump=accounts.distribution.bump;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"distribution_v1",config.as_ref(),mint.as_ref(),&epoch,&[bump]]];
 let transfers=crate::shared_distribution::distribute(crate::shared_distribution::DistributionContext {remaining,source:accounts.output_distribution_token_account.to_account_info(),mint:accounts.output_mint.to_account_info(),program:accounts.output_mint_program.to_account_info(),authority:accounts.distribution.to_account_info()},crate::shared_distribution::DistributionArgs::new(&shares,signer_seeds,total,accounts.output_mint_program.key,accounts.output_mint.decimals))?;
 distribute_after_finish(accounts,signer_seeds)?;
 Ok(DonationEpochProcessedV1Event {daas_event_discriminator:DaasEventDiscriminator::DonationEpochProcessedV1,config_id:accounts.distribution.config_id,mint:accounts.distribution.mint,epoch:accounts.distribution.epoch,settled_amount:total,settlement_mint:accounts.output_mint.key(),transfers})
}

#[inline(never)]
pub(crate) fn distribute_after_finish<'info>(accounts:&mut DistributeAfterJustSwappingV1<'info>,signer_seeds:&[&[&[u8]];1])->Result<()> {
 accounts.output_distribution_token_account.reload()?;
 burn_and_close(BurnCloseContext {token:accounts.output_distribution_token_account.to_account_info(),mint:accounts.output_mint.to_account_info(),authority:accounts.distribution.to_account_info(),destination:accounts.signer.to_account_info(),program:accounts.output_mint_program.to_account_info()},accounts.output_distribution_token_account.amount,signer_seeds)
}

#[inline(never)]
pub(crate) fn distribute_non_swap_prechecks(accounts:&DistributeNonSwapOutputMintV1<'_>)->Result<()> {
 if !(accounts.distribution.epoch<accounts.epoch_tracker.current_epoch) {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_non_swap_output_mint.rs",EpochNotClosed,80));}
 if accounts.distribution.state!=DistributionV1State::Initialized {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_non_swap_output_mint.rs",InvalidState,85));}
 if accounts.distribution.mint!=accounts.mint.key() {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_non_swap_output_mint.rs",InvalidMint,91).with_pubkeys((accounts.distribution.mint,accounts.mint.key())));}
 if accounts.debouncer.mint!=accounts.mint.key() {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_non_swap_output_mint.rs",InvalidMint,96).with_pubkeys((accounts.debouncer.mint,accounts.mint.key())));}
 Ok(())
}

pub fn distribute_non_swap<'info>(accounts:&mut DistributeNonSwapOutputMintV1<'info>,args:crate::codec::wire::DistributeNonSwapOutputMintV1,remaining:&'info [AccountInfo<'info>])->Result<DonationEpochProcessedV1Event> {
 let crate::codec::wire::DistributeNonSwapOutputMintV1 {shares}=args;
 distribute_non_swap_prechecks(accounts)?;
 crate::tools::checks::admit_shares(shares.iter().map(|share|share.bps))?;
 let total=accounts.distribution.total_amount;
 if accounts.distribution_token_account.amount<total {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/distribute_non_swap_output_mint.rs",InvalidBalance,117));}
 if remaining.len()<shares.len() {return Err(Code::InsufficientRemainingAccounts.into());}
 let remaining=&remaining[..shares.len()];
 let config=accounts.distribution.config_id;let mint=accounts.distribution.mint;let epoch=accounts.distribution.epoch.to_le_bytes();let bump=accounts.distribution.bump;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"distribution_v1",config.as_ref(),mint.as_ref(),&epoch,&[bump]]];
 let transfers=crate::shared_distribution::distribute(crate::shared_distribution::DistributionContext {remaining,source:accounts.distribution_token_account.to_account_info(),mint:accounts.mint.to_account_info(),program:accounts.token_program.to_account_info(),authority:accounts.distribution.to_account_info()},crate::shared_distribution::DistributionArgs::new(&shares,signer_seeds,total,accounts.token_program.key,accounts.mint.decimals))?;
 distribute_non_swap_finish(accounts,signer_seeds)?;
 Ok(DonationEpochProcessedV1Event {daas_event_discriminator:DaasEventDiscriminator::DonationEpochProcessedV1,config_id:accounts.distribution.config_id,mint:accounts.distribution.mint,epoch:accounts.distribution.epoch,settled_amount:total,settlement_mint:accounts.mint.key(),transfers})
}

#[inline(never)]
pub(crate) fn distribute_non_swap_finish<'info>(accounts:&mut DistributeNonSwapOutputMintV1<'info>,signer_seeds:&[&[&[u8]];1])->Result<()> {
 accounts.distribution_token_account.reload()?;
 burn_and_close(BurnCloseContext {token:accounts.distribution_token_account.to_account_info(),mint:accounts.mint.to_account_info(),authority:accounts.distribution.to_account_info(),destination:accounts.signer.to_account_info(),program:accounts.token_program.to_account_info()},accounts.distribution_token_account.amount,signer_seeds)
}

pub fn just_swap<'info>(accounts:&mut JustSwapV1<'info>,args:crate::codec::wire::JustSwapV1,remaining:&[AccountInfo<'info>],receipt_bump:u8)->Result<DonationEpochJustSwappedV1Event> {
 let crate::codec::wire::JustSwapV1 {jupiter_swap_ix_data:data}=args;
 if !(accounts.distribution.epoch<accounts.epoch_tracker.current_epoch) {return Err(just_error!(EpochNotClosed,110));}
 if accounts.distribution.state!=DistributionV1State::Initialized {return Err(just_error!(InvalidState,115));}
 if accounts.debouncer.mint!=accounts.distribution.mint {return Err(just_error!(InvalidMint,120).with_pubkeys((accounts.debouncer.mint,accounts.distribution.mint)));}
 if accounts.distribution.mint==Pubkey::new_from_array(crate::codec::constants::SETTLEMENT) {return Err(just_error!(InvalidMint,126).with_pubkeys((accounts.distribution.mint,Pubkey::new_from_array(crate::codec::constants::SETTLEMENT))));}
 let total=accounts.distribution.total_amount;
 let config=accounts.distribution.config_id;let mint=accounts.distribution.mint;
 let epoch=accounts.distribution.epoch.to_le_bytes();
 let bump=accounts.distribution.bump;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"distribution_v1",config.as_ref(),mint.as_ref(),&epoch,&[bump]]];
 let output=swap_observed(&accounts.jupiter_program,accounts.distribution.key(),&mut accounts.distribution_token_account,&mut accounts.output_distribution_token_account,remaining,data,signer_seeds,total)?;
 accounts.swap_receipt.set_inner(SwapReceiptV1 {bump:receipt_bump,distribution:accounts.distribution.key(),swap_output_amount:output});
 accounts.distribution_token_account.reload()?;
 burn_and_close(BurnCloseContext {token:accounts.distribution_token_account.to_account_info(),mint:accounts.mint.to_account_info(),authority:accounts.distribution.to_account_info(),destination:accounts.signer.to_account_info(),program:accounts.token_program.to_account_info()},accounts.distribution_token_account.amount,signer_seeds)?;
 Ok(DonationEpochJustSwappedV1Event {daas_event_discriminator:DaasEventDiscriminator::DonationEpochJustSwappedV1,config_id:accounts.distribution.config_id,mint:accounts.distribution.mint,epoch:accounts.distribution.epoch,distribution:accounts.distribution.key(),swap_receipt:accounts.swap_receipt.key(),output_token_account:accounts.output_distribution_token_account.key(),swap_output_amount:output,settlement_mint:accounts.output_mint.key()})
}

pub fn swap_then_distribute<'info>(accounts:&mut SwapThenDistributeV1<'info>,args:crate::codec::wire::SwapThenDistributeV1,remaining:&'info [AccountInfo<'info>])->Result<DonationEpochProcessedV1Event> {
 let crate::codec::wire::SwapThenDistributeV1 {jupiter_swap_ix_data:data,shares}=args;
 if !(accounts.distribution.epoch<accounts.epoch_tracker.current_epoch) {return Err(distribution_error!("programs/contracts/src/instructions/v1/relayer_only/distribute/swap_then_distribute.rs",EpochNotClosed,110));}
 crate::tools::checks::admit_shares(shares.iter().map(|share|share.bps))?;
 if remaining.len()<shares.len() {return Err(Code::InsufficientRemainingAccounts.into());}
 let (recipients,jupiter_accounts)=remaining.split_at(shares.len());
 let expected_input=accounts.distribution.total_amount;
 let config=accounts.distribution.config_id;let mint=accounts.distribution.mint;let epoch=accounts.distribution.epoch.to_le_bytes();let bump=accounts.distribution.bump;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"distribution_v1",config.as_ref(),mint.as_ref(),&epoch,&[bump]]];
 let total=swap_observed(&accounts.jupiter_program,accounts.distribution.key(),&mut accounts.distribution_token_account,&mut accounts.output_distribution_token_account,jupiter_accounts,data,signer_seeds,expected_input)?;
 let transfers=crate::shared_distribution::distribute(crate::shared_distribution::DistributionContext {remaining:recipients,source:accounts.output_distribution_token_account.to_account_info(),mint:accounts.output_mint.to_account_info(),program:accounts.output_mint_program.to_account_info(),authority:accounts.distribution.to_account_info()},crate::shared_distribution::DistributionArgs::new(&shares,signer_seeds,total,accounts.output_mint_program.key,accounts.output_mint.decimals))?;
 accounts.distribution_token_account.reload()?;
 burn_and_close(BurnCloseContext {token:accounts.distribution_token_account.to_account_info(),mint:accounts.mint.to_account_info(),authority:accounts.distribution.to_account_info(),destination:accounts.signer.to_account_info(),program:accounts.token_program.to_account_info()},accounts.distribution_token_account.amount,signer_seeds)?;
 anchor_spl::token_interface::close_account(CpiContext::new_with_signer(accounts.output_mint_program.to_account_info(),anchor_spl::token_interface::CloseAccount {account:accounts.output_distribution_token_account.to_account_info(),destination:accounts.signer.to_account_info(),authority:accounts.distribution.to_account_info()},signer_seeds))?;
 Ok(DonationEpochProcessedV1Event {daas_event_discriminator:DaasEventDiscriminator::DonationEpochProcessedV1,config_id:accounts.distribution.config_id,mint:accounts.distribution.mint,epoch:accounts.distribution.epoch,settled_amount:total,settlement_mint:accounts.output_mint.key(),transfers})
}

pub fn distribute_exact_non_swap<'info>(accounts:&mut DistributeNonSwapOutputMintV1<'info>,transfers:Vec<ExactTransfer>,remaining:&'info [AccountInfo<'info>])->Result<DonationEpochProcessedExactV1Event> {
 distribute_non_swap_prechecks(accounts)?;
 let total=accounts.distribution.total_amount;
 let config=accounts.distribution.config_id;let mint=accounts.distribution.mint;let epoch=accounts.distribution.epoch.to_le_bytes();let bump=accounts.distribution.bump;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"distribution_v1",config.as_ref(),mint.as_ref(),&epoch,&[bump]]];
 crate::shared_distribution::distribute_exact(crate::shared_distribution::DistributionContext {remaining,source:accounts.distribution_token_account.to_account_info(),mint:accounts.mint.to_account_info(),program:accounts.token_program.to_account_info(),authority:accounts.distribution.to_account_info()},&transfers,signer_seeds,total,accounts.token_program.key(),accounts.mint.decimals)?;
 distribute_non_swap_finish(accounts,signer_seeds)?;
 Ok(DonationEpochProcessedExactV1Event {daas_event_discriminator:DaasEventDiscriminator::DonationEpochProcessedExactV1,config_id:accounts.distribution.config_id,mint:accounts.distribution.mint,epoch:accounts.distribution.epoch,settled_amount:total,settlement_mint:accounts.mint.key(),transfers})
}

pub fn distribute_exact_after<'info>(accounts:&mut DistributeAfterJustSwappingV1<'info>,transfers:Vec<ExactTransfer>,remaining:&'info [AccountInfo<'info>])->Result<DonationEpochProcessedExactV1Event> {
 distribute_after_prechecks(accounts)?;
 let total=accounts.swap_receipt.swap_output_amount;
 let config=accounts.distribution.config_id;let mint=accounts.distribution.mint;let epoch=accounts.distribution.epoch.to_le_bytes();let bump=accounts.distribution.bump;
 let signer_seeds:&[&[&[u8]];1]=&[&[b"distribution_v1",config.as_ref(),mint.as_ref(),&epoch,&[bump]]];
 crate::shared_distribution::distribute_exact(crate::shared_distribution::DistributionContext {remaining,source:accounts.output_distribution_token_account.to_account_info(),mint:accounts.output_mint.to_account_info(),program:accounts.output_mint_program.to_account_info(),authority:accounts.distribution.to_account_info()},&transfers,signer_seeds,total,accounts.output_mint_program.key(),accounts.output_mint.decimals)?;
 distribute_after_finish(accounts,signer_seeds)?;
 Ok(DonationEpochProcessedExactV1Event {daas_event_discriminator:DaasEventDiscriminator::DonationEpochProcessedExactV1,config_id:accounts.distribution.config_id,mint:accounts.distribution.mint,epoch:accounts.distribution.epoch,settled_amount:total,settlement_mint:accounts.output_mint.key(),transfers})
}
