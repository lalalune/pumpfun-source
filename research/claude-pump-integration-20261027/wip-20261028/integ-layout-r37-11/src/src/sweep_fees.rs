use anchor_lang::prelude::*;
use crate::{Global,PumpError};
use crate::trade_types::BondingCurve;
#[event_cpi]
#[derive(Accounts)]
pub struct SweepFees<'info>{
 #[account(mut)]pub payer:Signer<'info>,
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,
 pub base_mint:Box<InterfaceAccount<'info,anchor_spl::token_interface::Mint>>,
 pub quote_mint:Box<InterfaceAccount<'info,anchor_spl::token_interface::Mint>>,
 pub quote_token_program:Interface<'info,anchor_spl::token_interface::TokenInterface>,
 pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
 pub system_program:Program<'info,System>,
 #[account(mut,seeds=[b"bonding-curve",base_mint.key().as_ref()],bump,constraint=quote_mint.key()==bonding_curve.quote_mint || (bonding_curve.quote_mint==Pubkey::default() && quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID) @ PumpError::MintDoesNotMatchBondingCurve)]pub bonding_curve:Box<Account<'info,BondingCurve>>,
 /// CHECK: checked as token data only in the positive token branch.
 #[account(mut,seeds=[bonding_curve.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_quote_bonding_curve:UncheckedAccount<'info>,
 /// CHECK: handler verifies fee recipient or creator vault.
 #[account(mut)]pub recipient:UncheckedAccount<'info>,
 /// CHECK: address checked; token branch creates or parses.
 #[account(mut,seeds=[recipient.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_quote_recipient:UncheckedAccount<'info>,
}
#[event]
#[derive(Clone)]pub struct SweepBondingCurveFeeEvent{pub timestamp:i64,pub mint:Pubkey,pub bonding_curve:Pubkey,pub quote_mint:Pubkey,pub recipient:Pubkey,pub amount:u64,pub bucket:u8}
pub fn execute(ctx:Context<SweepFees>,creator:bool)->Result<()>{
 let a=&mut *ctx.accounts;
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.payer)?;
 let native=a.bonding_curve.quote_mint==Pubkey::default();let cf=a.bonding_curve.creator_fee;let pf=a.bonding_curve.protocol_fees;let info=a.bonding_curve.to_account_info();
// layout-pad(117): aligns the next Source site with the original line




















































































































 if creator{let expected=Pubkey::find_program_address(&[b"creator-vault",a.bonding_curve.creator.as_ref()],&crate::ID).0;require_keys_eq!(a.recipient.key(),expected,anchor_lang::error::ErrorCode::ConstraintSeeds);}
 else{crate::legacy_sell::fee_recipient::validate_fee_recipient(&a.recipient,&a.global,&a.bonding_curve)?;}
 let amount=if creator{cf}else{pf};if amount==0{return Ok(());}
 if native{
  if creator{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.payer,a.recipient.as_ref())?;}
  a.bonding_curve.sub_lamports(amount)?;a.recipient.add_lamports(amount)?;
 }
 else{

  crate::buy_v2::admit_associated_token_account(a.associated_quote_bonding_curve.as_ref(),&a.bonding_curve.to_account_info(),&a.quote_mint.key(),&a.quote_token_program.key(),a.payer.as_ref(),&a.quote_mint.to_account_info(),false,a.system_program.as_ref(),a.quote_token_program.as_ref())?;
  crate::buy_v2::admit_associated_token_account(a.associated_quote_recipient.as_ref(),a.recipient.as_ref(),&a.quote_mint.key(),&a.quote_token_program.key(),a.payer.as_ref(),&a.quote_mint.to_account_info(),true,a.system_program.as_ref(),a.quote_token_program.as_ref())?;
  let mint=a.base_mint.key();let bump=[ctx.bumps.bonding_curve];let seeds:&[&[u8]]=&[b"bonding-curve",mint.as_ref(),&bump];
  crate::sell_v2::quote_token_transfers::transfer_quote_tokens(&a.quote_token_program,a.associated_quote_bonding_curve.as_ref(),a.associated_quote_recipient.as_ref(),info,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&[seeds])?;
 }
 if creator{a.bonding_curve.creator_fee=0;}else{a.bonding_curve.protocol_fees=0;}
 let event=SweepBondingCurveFeeEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.base_mint.key(),bonding_curve:a.bonding_curve.key(),quote_mint:a.bonding_curve.quote_mint,recipient:a.recipient.key(),amount,bucket:if creator{1}else{0}};emit!(event.clone());emit_cpi!(event);Ok(())
}

