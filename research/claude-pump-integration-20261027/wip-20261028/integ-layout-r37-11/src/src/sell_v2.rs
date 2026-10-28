use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,Mint,TokenAccount,TokenInterface,TransferChecked};
use crate::{Global,PumpError};
const FEE_PROGRAM:Pubkey=anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
use crate::trade_types::{TradeEvent,BondingCurve};
use crate::legacy_sell::{LegacyFeeConfig,LegacyFeesProgram};
const WSOL:Pubkey=anchor_lang::solana_program::pubkey!("So11111111111111111111111111111111111111112");
// layout-pad(24): aligns the next Source site with the original line























#[derive(Accounts)]
pub struct SellV2<'info>{
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,
 pub base_mint:Box<InterfaceAccount<'info,Mint>>,
 pub quote_mint:Box<InterfaceAccount<'info,Mint>>,
 pub base_token_program:Interface<'info,TokenInterface>,
 pub quote_token_program:Interface<'info,TokenInterface>,
 pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
 /// CHECK: handler checks membership.
 #[account(mut)]pub fee_recipient:UncheckedAccount<'info>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[fee_recipient.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_quote_fee_recipient:UncheckedAccount<'info>,
 /// CHECK: handler checks membership.
 #[account(mut)]pub buyback_fee_recipient:UncheckedAccount<'info>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[buyback_fee_recipient.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_quote_buyback_fee_recipient:UncheckedAccount<'info>,
 #[account(mut,seeds=[b"bonding-curve",base_mint.key().as_ref()],bump,constraint=quote_mint.key()==bonding_curve.quote_mint || (bonding_curve.quote_mint==Pubkey::default() && quote_mint.key()==WSOL) @ PumpError::MintDoesNotMatchBondingCurve)]pub bonding_curve:Box<Account<'info,BondingCurve>>,
 #[account(mut,associated_token::mint=base_mint,associated_token::authority=bonding_curve,associated_token::token_program=base_token_program)]pub associated_base_bonding_curve:Box<InterfaceAccount<'info,TokenAccount>>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[bonding_curve.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_quote_bonding_curve:UncheckedAccount<'info>,
 #[account(mut)]pub user:Signer<'info>,
 #[account(mut,token::mint=base_mint)]pub associated_base_user:Box<InterfaceAccount<'info,TokenAccount>>,
 /// CHECK: quote ATA.
 #[account(mut)]pub associated_quote_user:UncheckedAccount<'info>,
 /// CHECK: PDA.
 #[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[creator_vault.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_creator_vault:UncheckedAccount<'info>,
 /// CHECK: sharing validation later.
 #[account(seeds=[b"sharing-config",base_mint.key().as_ref()],bump,seeds::program=FEE_PROGRAM)]pub sharing_config:UncheckedAccount<'info>,
 /// CHECK: volume state validated when used.
 #[account(init_if_needed,payer=user,space=137,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]pub user_volume_accumulator:Box<Account<'info,crate::UserVolumeAccumulator>>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[user_volume_accumulator.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_user_volume_accumulator:UncheckedAccount<'info>,
 #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump,seeds::program=fee_program.key())]pub fee_config:Account<'info,LegacyFeeConfig>,
 pub fee_program:Program<'info,LegacyFeesProgram>,
 pub system_program:Program<'info,System>,
 /// CHECK: event PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
}
fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}
fn sub(a:u64,b:u64)->Result<u64>{a.checked_sub(b).ok_or_else(||error!(PumpError::Overflow))}
fn narrow(a:u128)->Result<u64>{u64::try_from(a).map_err(|_|error!(PumpError::Truncation))}
pub fn execute(ctx:Context<SellV2>,amount:u64,minimum:u64)->Result<()>{
 let a=&mut *ctx.accounts;
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;


let c=&a.bonding_curve;let native=c.quote_mint==Pubkey::default();
// layout-pad(161): aligns the next Source site with the original line
































































































































































 require!(!c.complete,PumpError::BondingCurveComplete);
// layout-pad(1): aligns the next Source site with the original line
 require_gt!(amount,0,PumpError::SellZeroAmount);
// layout-pad(1): aligns the next Source site with the original line
 require_gte!(a.associated_base_user.amount,amount,PumpError::NotEnoughTokensToSell);
 crate::legacy_sell::fee_recipient::validate_fee_recipient(&a.fee_recipient,&a.global,&a.bonding_curve)?;
 let bb=&a.buyback_fee_recipient;a.global.validate_buyback_fee_recipient(*bb.key)?;
 if a.user_volume_accumulator.user==Pubkey::default(){a.user_volume_accumulator.user=a.user.key();}
 if a.bonding_curve.quote_mint!=Pubkey::default(){
  crate::buy_v2::admit_associated_token_account(a.associated_quote_bonding_curve.as_ref(),&a.bonding_curve.to_account_info(),&a.quote_mint.key(),&a.quote_token_program.key(),a.user.as_ref(),&a.quote_mint.to_account_info(),false,a.system_program.as_ref(),a.quote_token_program.as_ref())?;
  require_keys_eq!(*a.associated_quote_user.owner,a.quote_token_program.key(),PumpError::AccountTypeNotSupported);
  check_token(&a.associated_quote_user,a.quote_mint.key(),a.user.key())?;{let d=a.associated_quote_user.try_borrow_data()?;let t=TokenAccount::try_deserialize(&mut &d[..])?;require_keys_eq!(t.owner,a.user.key(),PumpError::AccountTypeNotSupported);}
  for (destination,authority) in [(a.associated_creator_vault.to_account_info(),a.creator_vault.to_account_info()),(a.associated_user_volume_accumulator.to_account_info(),a.user_volume_accumulator.to_account_info()),(a.associated_quote_fee_recipient.to_account_info(),a.fee_recipient.to_account_info()),(a.associated_quote_buyback_fee_recipient.to_account_info(),a.buyback_fee_recipient.to_account_info())]{
   crate::buy_v2::admit_associated_token_account(&destination,&authority,&a.quote_mint.key(),&a.quote_token_program.key(),a.user.as_ref(),&a.quote_mint.to_account_info(),true,a.system_program.as_ref(),a.quote_token_program.as_ref())?;
  }
 }

// layout-pad(81): aligns the next Source site with the original line
















































































 let quote=u64::try_from(c.sell_quote(amount)?).map_err(|_|error!(PumpError::Truncation))?;
 let (initial_protocol_fee,initial_creator_fee,protocol_fee_bps,creator_fee_bps)=if a.user.key()==a.global.whitelist_pda{(0,0,0,0)}else{crate::legacy_sell::fee_cpi::trade_fees(
  &a.global,&a.bonding_curve,&a.base_mint,&a.fee_config,&a.fee_program,a.program.as_ref(),quote
 )?};
 let cb=if c.creator==Pubkey::default(){0}else{creator_fee_bps};let pf=initial_protocol_fee;let cf=initial_creator_fee;
// layout-pad(19): aligns the next Source site with the original line


















 let output=quote.checked_sub(pf)
  .ok_or_else(||error!(PumpError::Overflow))?
  .checked_sub(cf)
  .ok_or_else(||error!(PumpError::Overflow))?;
 let quote_transfer_fee=if native{0}else{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),output,false)?};
 let net_output=sub(output,quote_transfer_fee)?;
// layout-pad(8): aligns the next Source site with the original line







 require_gte!(net_output,minimum,PumpError::TooLittleSolReceived);
// layout-pad(6): aligns the next Source site with the original line





 let quote_transfer_fee=output.checked_sub(net_output).ok_or_else(||error!(PumpError::Overflow))?;
 let vb=add(c.virtual_token_reserves,amount)?;let vq=sub(c.virtual_quote_reserves,quote)?;let rb=add(c.real_token_reserves,amount)?;let rq=sub(c.real_quote_reserves,quote)?;
 user_token_transfers::transfer_user_tokens(&a.base_token_program,&a.associated_base_user,&a.associated_base_bonding_curve,a.user.as_ref(),a.base_mint.decimals,a.base_mint.as_ref().as_ref(),amount)?;
 let cashback_coin=c.is_cashback_coin;
 if cf>0 && !cashback_coin{crate::buy_v2::native_payments::ensure_rent_exempt(0,&a.system_program,&a.user,&a.creator_vault)?;}
 let bbps=if c.is_mayhem_mode{0}else{a.global.buyback_basis_points};
 let mint=a.base_mint.key();let bump=[ctx.bumps.bonding_curve];let seeds:&[&[u8]]=&[b"bonding-curve",mint.as_ref(),&bump];
 if native{
  if cf>0{a.bonding_curve.sub_lamports(cf)?;if cashback_coin{a.user_volume_accumulator.add_lamports(cf)?;}else{a.creator_vault.add_lamports(cf)?;}}
  if cashback_coin{crate::token_incentives::volume_accumulator::record_cashback_earned(&mut a.user_volume_accumulator,cf,true)?;}
  if output>0{a.bonding_curve.sub_lamports(output)?;a.user.add_lamports(output)?;}
 }else{
  let to=if cashback_coin{a.associated_user_volume_accumulator.to_account_info()}else{a.associated_creator_vault.to_account_info()};
  if cf>0{quote_token_transfers::transfer_quote_tokens(&a.quote_token_program,a.associated_quote_bonding_curve.as_ref(),&to,a.bonding_curve.to_account_info(),a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),cf,&[seeds])?;}
  if cashback_coin{crate::token_incentives::volume_accumulator::record_cashback_earned(&mut a.user_volume_accumulator,cf,false)?;}
  if output>0{quote_token_transfers::transfer_quote_tokens(&a.quote_token_program,a.associated_quote_bonding_curve.as_ref(),a.associated_quote_user.as_ref(),a.bonding_curve.to_account_info(),a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),output,&[seeds])?;}
 }
 let (bf,protocol_fee)=crate::buy_v2::recipient_payments::split_protocol_fee(&a.global,pf,c.is_mayhem_mode);
 let quote_source=if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())};
 let buyback_quote=if native{None}else{Some(a.associated_quote_buyback_fee_recipient.as_ref())};
 let fee_quote=if native{None}else{Some(a.associated_quote_fee_recipient.as_ref())};
 let fee_recipient=&a.fee_recipient;
 crate::trade::quote_payments::transfer_to_recipient(
  native,a.base_mint.as_ref().as_ref(),a.bonding_curve.as_ref(),&bb,bf,
  &a.quote_token_program,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),
  quote_source,buyback_quote,ctx.bumps.bonding_curve,
 )?;
 crate::trade::quote_payments::transfer_to_recipient(
  native,a.base_mint.as_ref().as_ref(),a.bonding_curve.as_ref(),&fee_recipient,protocol_fee,
  &a.quote_token_program,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),
  quote_source,fee_quote,ctx.bumps.bonding_curve,
 )?;
 let buyback_received=if native{bf}else{sub(bf,crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),bf,false)?)?};
 let shareholders=crate::distribution::sharing_config_shareholders(&a.sharing_config)?.unwrap_or_default();
 let ev=TradeEvent{mint:a.base_mint.key(),sol_amount:if native{quote}else{0},token_amount:amount,is_buy:false,user:a.user.key(),timestamp:Clock::get()?.unix_timestamp,virtual_sol_reserves:if native{vq}else{0},virtual_token_reserves:vb,real_sol_reserves:if native{rq}else{0},real_token_reserves:rb,fee_recipient:a.fee_recipient.key(),fee_basis_points:protocol_fee_bps,fee:pf,creator:c.creator,creator_fee_basis_points:if c.is_cashback_coin{0}else{creator_fee_bps},creator_fee:if c.is_cashback_coin{0}else{cf},track_volume:false,total_unclaimed_tokens:0,total_claimed_tokens:0,current_sol_volume:0,last_update_timestamp:0,ix_name:"sell".into(),mayhem_mode:c.is_mayhem_mode,cashback_fee_basis_points:if c.is_cashback_coin{cb}else{0},cashback:if c.is_cashback_coin{cf}else{0},buyback_fee_basis_points:bbps,buyback_fee:buyback_received,shareholders,quote_mint:c.quote_mint,quote_amount:quote,virtual_quote_reserves:vq,real_quote_reserves:rq,holder_rewards_bps:if c.is_holder_reward{cb}else{0},holder_rewards:if c.is_holder_reward{cf}else{0},creator_fee_unclaimed:c.creator_fee,unparsed_trailing_field:quote_transfer_fee};
 let c=&mut a.bonding_curve;c.virtual_token_reserves=vb;c.virtual_quote_reserves=vq;c.real_token_reserves=rb;c.real_quote_reserves=rq;emit!(ev.clone());emit_cpi!(ev);Ok(())
}

fn check_token(info:&AccountInfo,mint:Pubkey,owner:Pubkey)->Result<()>{let d=info.try_borrow_data()?;let t=TokenAccount::try_deserialize(&mut &d[..])?;require_keys_eq!(t.mint,mint,PumpError::MintDoesNotMatchBondingCurve);let _=owner;Ok(())}

#[path="v2_user_token_transfers.rs"]
pub mod user_token_transfers;

#[path="v2_quote_token_transfers.rs"]
pub mod quote_token_transfers;
