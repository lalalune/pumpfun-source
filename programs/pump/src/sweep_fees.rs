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

// layout-pad(117): aligns the next Source site with the original line






























































































 require_keys_neq!(a.recipient.key(),Pubkey::default(),PumpError::NotAuthorized);




















 
 match creator as i32{1=>{let expected=Pubkey::find_program_address(&[b"creator-vault",a.bonding_curve.creator.as_ref()],&crate::ID).0;if !keys_eq(&a.recipient.key(),&expected){return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.recipient.key(),expected)));}
 }_=>{crate::legacy_sell::fee_recipient::validate_fee_recipient(&a.recipient,&a.global,&a.bonding_curve)?;
 }}
 let amount=if creator{let v=a.bonding_curve.creator_fee;a.bonding_curve.creator_fee=0;v}else{let v=a.bonding_curve.protocol_fees;a.bonding_curve.protocol_fees=0;v};

 if amount==0{msg!("Nothing to sweep for fee bucket {}",creator as u8);return Ok(());}
 let native=quote_is_native(&a.bonding_curve);
 match (creator,native){
  (true,true)=>ensure_rent_exempt(a,a.recipient.as_ref())?,



  (_,false)=>{
  let quote_mint=a.quote_mint.key();let quote_token_program=a.quote_token_program.key();let quote_mint_info=a.quote_mint.to_account_info();let quote_token_program_info=a.quote_token_program.to_account_info();
  crate::buy_v2::admit_associated_token_account(a.associated_quote_bonding_curve.as_ref(),&a.bonding_curve.to_account_info(),quote_mint,quote_token_program,&quote_mint_info,&quote_token_program_info,false,a.payer.as_ref(),a.system_program.as_ref())?;
  crate::buy_v2::admit_associated_token_account(a.associated_quote_recipient.as_ref(),a.recipient.as_ref(),quote_mint,quote_token_program,&quote_mint_info,&quote_token_program_info,true,a.payer.as_ref(),a.system_program.as_ref())?;
  }
  (false,true)=>{}
 }
 pay_owned(
  native,&a.base_mint,a.bonding_curve.as_ref(),
  a.recipient.to_account_info(),amount,a,
  &a.quote_mint,
  if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())},
  if native{None}else{Some(a.associated_quote_recipient.as_ref())},
  ctx.bumps.bonding_curve,
 )?;
 let event=SweepBondingCurveFeeEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.base_mint.key(),bonding_curve:a.bonding_curve.key(),quote_mint:a.bonding_curve.quote_mint,recipient:a.recipient.key(),amount,bucket:if creator{1}else{0}};emit!(event);emit_cpi!(event);Ok(())
}
fn ensure_rent_exempt<'info>(a:&SweepFees<'info>,destination:&AccountInfo<'info>)->Result<()>{
 let minimum=Rent::get()?.minimum_balance(0);
 if destination.lamports()<minimum{crate::legacy_buy::native_payments::transfer(a.system_program.as_ref(),&a.payer,destination,minimum)}else{Ok(())}
}
fn pay_owned<'info>(native:bool,base_mint:&InterfaceAccount<'info,anchor_spl::token_interface::Mint>,curve:&Account<'info,BondingCurve>,destination:AccountInfo<'info>,amount:u64,a:&SweepFees<'info>,quote_mint:&InterfaceAccount<'info,anchor_spl::token_interface::Mint>,quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,bump:u8)->Result<()>{crate::trade::quote_payments::transfer_to_owned(native,AsRef::<AccountInfo<'info>>::as_ref(base_mint),curve,destination,amount,&a.quote_token_program,quote_mint.decimals,AsRef::<AccountInfo<'info>>::as_ref(quote_mint),quote_source,quote_destination,bump)}
fn quote_is_native(curve:&BondingCurve)->bool{curve.quote_mint==Pubkey::default()}
fn keys_eq(a:&Pubkey,b:&Pubkey)->bool{a==b}
