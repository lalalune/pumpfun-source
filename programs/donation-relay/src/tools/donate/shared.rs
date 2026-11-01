//! Common donation context, wire-neutral arguments and result recovered from disassembly.
use anchor_lang::prelude::*;
use anchor_spl::token_interface::{TokenAccount,Mint};
use crate::anchor_framework::{EpochTrackerV1,EpochTrackerV1State,DebouncerV1,DebouncerV1State,MintWhitelistV1};
use crate::business_error_codes::ErrorCode as Code;
pub struct DonationContext<'a,'info> {
 pub epoch_tracker:&'a mut Account<'info,EpochTrackerV1>,pub debouncer:&'a mut Account<'info,DebouncerV1>,
 pub debouncer_token_account:AccountInfo<'info>,pub mint:AccountInfo<'info>,pub from_token_account:AccountInfo<'info>,
 pub from:&'a Signer<'info>,pub token_program:AccountInfo<'info>,pub mint_whitelist:&'a Account<'info,MintWhitelistV1>,
}
pub struct SignedDonationContext<'a,'info> {
 pub epoch_tracker:&'a mut Account<'info,EpochTrackerV1>,pub debouncer:&'a mut Account<'info,DebouncerV1>,
 pub debouncer_token_account:AccountInfo<'info>,pub mint:AccountInfo<'info>,pub from_token_account:AccountInfo<'info>,
 pub from:AccountInfo<'info>,pub token_program:AccountInfo<'info>,
}
pub struct DonationArgs {pub config_id:[u8;32],pub amount:u64,pub message:String,pub tip_bps:u16,pub epoch_tracker_bump:u8,pub debouncer_bump:u8}
pub struct SignedDonationArgs {pub config_id:[u8;32],pub amount:u64,pub tip_bps:u16,pub epoch_tracker_bump:u8,pub debouncer_bump:u8}
pub struct DonationAmounts {pub epoch:u128,pub gross_amount:u64,pub tip:u64}
macro_rules! source_error {
 ($code:ident,$file:literal,$line:literal)=>{anchor_lang::error::Error::from(anchor_lang::error::AnchorError {
 error_name:Code::$code.name(),error_code_number:Code::$code.into(),error_msg:Code::$code.to_string(),
 error_origin:Some(anchor_lang::error::ErrorOrigin::Source(anchor_lang::error::Source {filename:$file,line:$line})),compared_values:None,
 })};
}
pub use crate::tools::checks::{check_message,check_bps};
pub fn deserialize_token_account(info:&AccountInfo)->Result<TokenAccount> {
 let data=info.try_borrow_data()?;
 let result=TokenAccount::try_deserialize(&mut data.as_ref());result
}
pub fn deserialize_mint(info:&AccountInfo)->Result<Mint> {
 let data=info.try_borrow_data()?;
 let result=Mint::try_deserialize(&mut data.as_ref());result
}
pub fn donate_shared(ctx:DonationContext,args:DonationArgs)->Result<DonationAmounts> {
 check_message(&args.message)?;check_bps(args.tip_bps)?;
 check_mint_for_donation(&ctx.mint_whitelist.mints,&ctx.mint)?;
 donate_with_seeds(SignedDonationContext {epoch_tracker:ctx.epoch_tracker,debouncer:ctx.debouncer,debouncer_token_account:ctx.debouncer_token_account,mint:ctx.mint,from_token_account:ctx.from_token_account,from:ctx.from.to_account_info(),token_program:ctx.token_program},SignedDonationArgs {config_id:args.config_id,amount:args.amount,tip_bps:args.tip_bps,epoch_tracker_bump:args.epoch_tracker_bump,debouncer_bump:args.debouncer_bump},&[])
}
pub fn donate_with_seeds(ctx:SignedDonationContext,args:SignedDonationArgs,signer_seeds:&[&[&[u8]]])->Result<DonationAmounts> {
 let mint=*ctx.mint.key;
 if ctx.epoch_tracker.state==EpochTrackerV1State::Uninitialized {
  ctx.epoch_tracker.set_inner(EpochTrackerV1 {bump:args.epoch_tracker_bump,state:EpochTrackerV1State::Initialized,config_id:args.config_id,mint,current_epoch:0});
 }
 if ctx.debouncer.state==DebouncerV1State::Uninitialized {
  ctx.debouncer.set_inner(DebouncerV1 {bump:args.debouncer_bump,state:DebouncerV1State::Initialized,config_id:args.config_id,mint,total_amount:0});
 }
 if !ctx.epoch_tracker.config_id.iter().eq(args.config_id.iter()) {return Err(source_error!(InvalidConfigId,"programs/contracts/src/tools/donate/shared.rs",144));}
 if !ctx.debouncer.config_id.iter().eq(args.config_id.iter()) {return Err(source_error!(InvalidConfigId,"programs/contracts/src/tools/donate/shared.rs",152));}
 if ctx.debouncer.mint!=mint {return Err(source_error!(InvalidMint,"programs/contracts/src/tools/donate/shared.rs",160).with_pubkeys((ctx.debouncer.mint,mint)));}
 if ctx.debouncer.state!=DebouncerV1State::Initialized {return Err(source_error!(InvalidState,"programs/contracts/src/tools/donate/shared.rs",165));}
 if ctx.epoch_tracker.mint!=mint {return Err(source_error!(InvalidMint,"programs/contracts/src/tools/donate/shared.rs",169).with_pubkeys((ctx.epoch_tracker.mint,mint)));}
 if ctx.epoch_tracker.state!=EpochTrackerV1State::Initialized {return Err(source_error!(InvalidState,"programs/contracts/src/tools/donate/shared.rs",174));}
 let before=deserialize_token_account(&ctx.debouncer_token_account)?.amount;
 let decimals=deserialize_mint(&ctx.mint)?.decimals;
 anchor_spl::token_interface::transfer_checked(CpiContext::new(ctx.token_program.clone(),anchor_spl::token_interface::TransferChecked {
  from:ctx.from_token_account.clone(),mint:ctx.mint.clone(),to:ctx.debouncer_token_account.clone(),authority:ctx.from.clone(),
 }).with_signer(signer_seeds),args.amount,decimals)?;
 let after=deserialize_token_account(&ctx.debouncer_token_account)?.amount;
 let delta=after.checked_sub(before).ok_or(Code::ArithmeticOverflow)?;
 let product=delta.checked_mul(u64::from(args.tip_bps)).ok_or(Code::ArithmeticOverflow)?;
 let tip=product/10000;
 increment_total(&mut *ctx.debouncer,delta)?;
 Ok(DonationAmounts {epoch:ctx.epoch_tracker.current_epoch,gross_amount:delta,tip})
}

fn check_mint_for_donation(mints:&[Pubkey],source:&AccountInfo)->Result<()>  {
  let info=source.clone();
  let mint=info.key();let owner=*info.owner;
  if owner.to_bytes()!=crate::codec::constants::TOKEN && owner.to_bytes()!=crate::codec::constants::TOKEN2022 {return Err(Code::InvalidTokenProgram.into());}
  if mint==Pubkey::new_from_array(crate::codec::constants::NATIVE) || mint==Pubkey::new_from_array(crate::codec::constants::NATIVE2022) || mints.contains(&mint) {return Ok(());}
  if !crate::mint_policy::typed_mint_safe(&info)? {return Err(source_error!(MintNotSafeForDonation,"programs/contracts/src/tools/checks.rs",184));}
 Ok(())
 }

fn increment_total(debouncer:&mut DebouncerV1,amount:u64)->Result<()> {
 match debouncer.total_amount.checked_add(amount) {
  Some(total)=>{debouncer.total_amount=total;Ok(())},
  None=>Err(Code::ArithmeticOverflow.into()),
 }
}
