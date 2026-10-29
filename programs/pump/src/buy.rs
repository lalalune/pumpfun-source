use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,Mint,TokenAccount,TokenInterface,TransferChecked};
use crate::{Global,PumpError};
use crate::trade_types::{BondingCurve,TradeEvent};
use crate::LegacyBuy;
use crate::legacy_sell::fee_cpi::fee as ceil_fee;
pub use crate::legacy_native_payments as native_payments;

#[inline] pub fn buy_exact_sol_in<'info>(ctx:Context<'_,'_,'_,'info,LegacyBuy<'info>>,spendable_sol_in:u64,min_tokens_out:u64,track_volume:crate::OptionBool,partial_fill:crate::OptionBool)->Result<()>{
 let fee_recipient=&ctx.accounts.fee_recipient;
 let bonding_curve=&mut ctx.accounts.bonding_curve;let (associated_bonding_curve,associated_user,token_program)=(&ctx.accounts.associated_bonding_curve,&ctx.accounts.associated_user,&ctx.accounts.token_program);
 crate::trade_types::prepare_bonding_curve(bonding_curve,&ctx.accounts.system_program,&ctx.accounts.user)?;
 crate::legacy_sell::fee_recipient::validate_fee_recipient(fee_recipient,&ctx.accounts.global,bonding_curve)?;
 let buyback_fee_recipient=crate::legacy_sell::buyback_fee_recipient(ctx.remaining_accounts,&ctx.accounts.global,1)?;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
 require!(!bonding_curve.complete,PumpError::BondingCurveComplete);
// layout-pad
// layout-pad
// layout-pad
 require_gt!(min_tokens_out,0,PumpError::BuyZeroAmount);
// layout-pad
 require_gt!(spendable_sol_in,0,PumpError::BuyNotEnoughSolToCoverFees);
 let (protocol_fee_bps,creator_fee_bps)={let fees=crate::legacy_sell::fee_cpi::trade_fees(
  &ctx.accounts.global,bonding_curve,&ctx.accounts.mint,&ctx.accounts.fee_config,&ctx.accounts.fee_program,ctx.accounts.program.as_ref(),spendable_sol_in
 )?;if ctx.accounts.user.key()==ctx.accounts.global.whitelist_pda{(0,0)}else{(fees.2,fees.3)}};
 let cb=if bonding_curve.creator==Pubkey::default(){0}else{creator_fee_bps};
 let total_fee_bps=protocol_fee_bps.checked_add(cb).ok_or(PumpError::Overflow)?;
 let raw_quote=if total_fee_bps==0{spendable_sol_in}else{(spendable_sol_in as u128*10000/(10000+total_fee_bps as u128)) as u64};
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
 require_gt!(raw_quote,0,PumpError::BuyNotEnoughSolToCoverFees);
 let protocol_fee=ceil_fee(raw_quote,protocol_fee_bps)?;
 let creator_fee=if bonding_curve.creator!=Pubkey::default(){ceil_fee(raw_quote,creator_fee_bps)?}else{0};
 let total=raw_quote.saturating_add(protocol_fee).saturating_add(creator_fee);
 let mut quote=raw_quote;if total>spendable_sol_in{quote=raw_quote.checked_sub(total.saturating_sub(spendable_sol_in)).ok_or(PumpError::Overflow)?;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
 require_gt!(quote,0,PumpError::BuySlippageBelowMinTokensOut);}
 let amount=u64::try_from(crate::constant_product::tokens_for_quote(bonding_curve,quote)?).map_err(|_|PumpError::Truncation)?;
 let (amount,quote,protocol_fee,creator_fee)=if amount>bonding_curve.real_token_reserves&&partial_fill.0{
  let amount=bonding_curve.real_token_reserves;
  let quote=u64::try_from(crate::legacy_sell::fee_cpi::buy_quote(bonding_curve,amount)?).map_err(|_|PumpError::Truncation)?;
  let protocol_fee=ceil_fee(quote,protocol_fee_bps)?;
  let creator_fee=if bonding_curve.creator!=Pubkey::default(){ceil_fee(quote,creator_fee_bps)?}else{0};
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
  require_gte!(spendable_sol_in,quote.checked_add(protocol_fee).ok_or(PumpError::Overflow)?.checked_add(creator_fee).ok_or(PumpError::Overflow)?,PumpError::TooMuchSolRequired);
  (amount,quote,protocol_fee,creator_fee)
 }else{
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
  require_gte!(amount,min_tokens_out,PumpError::BuySlippageBelowMinTokensOut);
  (amount,quote,protocol_fee,creator_fee)
 };
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
 require_gte!(bonding_curve.real_token_reserves,amount,PumpError::NotEnoughTokensToBuy);
 bonding_curve.virtual_token_reserves=bonding_curve.virtual_token_reserves.checked_sub(amount).ok_or(PumpError::Overflow)?;
 bonding_curve.virtual_quote_reserves=bonding_curve.virtual_quote_reserves.checked_add(quote).ok_or(PumpError::Overflow)?;
 bonding_curve.real_token_reserves-=amount;
 bonding_curve.real_quote_reserves=bonding_curve.real_quote_reserves.checked_add(quote).ok_or(PumpError::Overflow)?;
 let transfer=|signer_seeds:&[&[&[u8]];1]|crate::buy_v2::token_transfers::transfer_curve_tokens_ref(token_program,associated_bonding_curve,associated_user,&bonding_curve,ctx.accounts.mint.decimals,ctx.accounts.mint.as_ref(),amount,signer_seeds);transfer(&[&[b"bonding-curve",ctx.accounts.mint.key().as_ref(),&[ctx.bumps.bonding_curve]]])?;
 if ctx.accounts.user.key()==ctx.accounts.global.whitelist_pda{
  ctx.accounts.associated_bonding_curve.reload()?;
  ctx.accounts.associated_user.reload()?;
  let quote_mint=bonding_curve.quote_mint;
  bonding_curve.sync_virtual_quote_reserves(ctx.accounts.associated_bonding_curve.amount,ctx.accounts.associated_user.amount,&quote_mint)?;
 }
 if ctx.accounts.user_volume_accumulator.user==Pubkey::default(){ctx.accounts.user_volume_accumulator.user=ctx.accounts.user.key();}
 let mint=ctx.accounts.mint.key();
 let mut cashback=false;
 if creator_fee!=0{
  crate::legacy_sell::check_bonding_curve_v2(ctx.remaining_accounts,&mint)?;
  if bonding_curve.is_cashback_coin{
   #[inline(always)] fn pay_owned<'info>(to:AccountInfo<'info>,system_program:&AccountInfo<'info>,user:&Signer<'info>,amount:u64)->Result<()>{crate::user_quote_payments::transfer_native_owned(system_program,user,to,amount)}
   pay_owned(ctx.accounts.user_volume_accumulator.to_account_info(),ctx.accounts.system_program.as_ref(),&ctx.accounts.user,creator_fee)?;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
   ctx.accounts.user_volume_accumulator.cashback_earned=ctx.accounts.user_volume_accumulator.cashback_earned.checked_add(creator_fee).ok_or(error!(PumpError::Overflow))?;
   cashback=true;
  }else{
   crate::legacy_buy::native_payments::ensure_rent_exempt(&ctx.accounts.system_program,&ctx.accounts.user,&ctx.accounts.creator_vault)?;
   crate::user_quote_payments::transfer_native_unchecked(ctx.accounts.system_program.as_ref(),&ctx.accounts.user,&ctx.accounts.creator_vault,creator_fee)?;
  }
 }
 crate::user_quote_payments::transfer_native_curve(ctx.accounts.system_program.as_ref(),&ctx.accounts.user,&bonding_curve,quote)?;
 let (buyback_fee,remaining)=crate::buy_v2::recipient_payments::split_protocol_fee(&ctx.accounts.global,protocol_fee,bonding_curve.is_mayhem_mode);
 if buyback_fee!=0{crate::user_quote_payments::transfer_native_curve_unchecked(ctx.accounts.system_program.as_ref(),&ctx.accounts.user,&buyback_fee_recipient,buyback_fee)?;}
 crate::user_quote_payments::transfer_native_recipient(ctx.accounts.system_program.as_ref(),&ctx.accounts.user,&fee_recipient,remaining)?;




 let virtual_token_reserves=bonding_curve.virtual_token_reserves;
 let virtual_quote_reserves=bonding_curve.virtual_quote_reserves;
 let real_token_reserves=bonding_curve.real_token_reserves;
 let real_quote_reserves=bonding_curve.real_quote_reserves;
 let creator=bonding_curve.creator;
 let timestamp=Clock::get()?.unix_timestamp;
 let event=crate::trade_types::TradeEvent{
 total_unclaimed_tokens:ctx.accounts.user_volume_accumulator.total_unclaimed_tokens,
 total_claimed_tokens:ctx.accounts.user_volume_accumulator.total_claimed_tokens,
 current_sol_volume:ctx.accounts.user_volume_accumulator.current_sol_volume,
 last_update_timestamp:ctx.accounts.user_volume_accumulator.last_update_timestamp,
 user:ctx.accounts.user.key(),
 mint,
 sol_amount:quote,
 token_amount:amount,
 is_buy:true,
 timestamp,
 virtual_sol_reserves:virtual_quote_reserves,
 virtual_token_reserves,
 real_sol_reserves:real_quote_reserves,
 real_token_reserves,
 fee_recipient:fee_recipient.key(),
 fee_basis_points:protocol_fee_bps,
 fee:protocol_fee,
 creator,
 creator_fee_basis_points:if cashback{0}else{creator_fee_bps},
 creator_fee:if cashback{0}else{creator_fee},
 track_volume:track_volume.0,
 holder_rewards_bps:if bonding_curve.is_holder_reward{creator_fee_bps}else{0},
 holder_rewards:if bonding_curve.is_holder_reward{creator_fee}else{0},
 ix_name:"buy_exact_sol_in".to_string(),
 mayhem_mode:bonding_curve.is_mayhem_mode,
 cashback_fee_basis_points:if cashback{creator_fee_bps}else{0},
 cashback:if cashback{creator_fee}else{0},
 buyback_fee_basis_points:if bonding_curve.is_mayhem_mode{0}else{ctx.accounts.global.buyback_basis_points},
 buyback_fee,
 shareholders:vec![],
 quote_mint:bonding_curve.quote_mint,
 quote_amount:quote,
 virtual_quote_reserves,
 real_quote_reserves,
 creator_fee_unclaimed:bonding_curve.creator_fee,
 unparsed_trailing_field:0,
 };
 emit!(event);
 emit_cpi!(event);
 if ctx.accounts.bonding_curve.real_token_reserves==0{
 ctx.accounts.bonding_curve.complete=true;
 let event=crate::trade_types::CompleteEvent{mint,user:ctx.accounts.user.key(),bonding_curve:ctx.accounts.bonding_curve.key(),timestamp,quote_mint:ctx.accounts.bonding_curve.quote_mint};
 emit!(event);
 emit_cpi!(event);
 }
 Ok(())
}
