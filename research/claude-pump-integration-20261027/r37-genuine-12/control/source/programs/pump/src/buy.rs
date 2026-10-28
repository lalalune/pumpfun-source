use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,Mint,TokenAccount,TokenInterface,TransferChecked};
use crate::{Global,PumpError};
use crate::trade_types::{BondingCurve,TradeEvent};

use crate::legacy_sell::{LegacyFeeConfig,LegacyFeesProgram};
#[derive(Accounts)]
pub struct LegacyBuy<'info>{
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,
 /// CHECK: handler validates recipient.
 #[account(mut)]pub fee_recipient:UncheckedAccount<'info>,
 pub mint:InterfaceAccount<'info,Mint>,
 #[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.quote_mint==Pubkey::default() @ PumpError::UnsupportedQuoteMint)]pub bonding_curve:Account<'info,BondingCurve>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=bonding_curve,associated_token::token_program=token_program)]pub associated_bonding_curve:InterfaceAccount<'info,TokenAccount>,
 #[account(mut,token::mint=mint)]pub associated_user:InterfaceAccount<'info,TokenAccount>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
 pub token_program:Interface<'info,TokenInterface>,
 /// CHECK: PDA checked.
 #[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 /// CHECK: event authority.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 /// CHECK: self CPI.
 pub program:Program<'info,crate::program::PumpRecovered>,
 #[account(seeds=[b"global_volume_accumulator"],bump)]pub global_volume_accumulator:Box<Account<'info,crate::GlobalVolumeAccumulator>>,
 #[account(init_if_needed,payer=user,space=137,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]pub user_volume_accumulator:Box<Account<'info,crate::UserVolumeAccumulator>>,
 /// CHECK: fee program validates config.
 #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump,seeds::program=fee_program.key())]
 pub fee_config:Account<'info,LegacyFeeConfig>,
 /// CHECK: canonical dependency.
 pub fee_program:Program<'info,LegacyFeesProgram>,
}
fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}
fn sub(a:u64,b:u64)->Result<u64>{a.checked_sub(b).ok_or_else(||error!(PumpError::Overflow))}
fn narrow(a:u128)->Result<u64>{u64::try_from(a).map_err(|_|error!(PumpError::Truncation))}
pub fn execute<'info>(ctx:Context<'_,'_,'_,'info,LegacyBuy<'info>>,input:u64,limit:u64,track:bool,partial:bool,exact:bool)->Result<()>{
 let a=&mut *ctx.accounts;
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;

 let c=&a.bonding_curve;
 crate::legacy_sell::fee_recipient::validate_fee_recipient(&a.fee_recipient,&a.global,&a.bonding_curve)?;
 let rem=ctx.remaining_accounts;
 let bb=rem.get(1).ok_or_else(||error!(PumpError::BuybackFeeRecipientMissing))?;require_keys_neq!(*bb.key,Pubkey::default(),PumpError::BuybackFeeRecipientMissing);require!(a.global.buyback_fee_recipients.contains(bb.key),PumpError::BuybackFeeRecipientNotAuthorized);
 require!(!c.complete,PumpError::BondingCurveComplete);
 if exact{require_gt!(limit,0,PumpError::BuyZeroAmount);require_gt!(input,0,PumpError::BuyNotEnoughSolToCoverFees);}else{require_gt!(input,0,PumpError::BuyZeroAmount);}
 if !exact{if !partial{require_gte!(c.real_token_reserves,input,PumpError::NotEnoughTokensToBuy);}}
 if !exact && partial{require_gt!(input.min(c.real_token_reserves),0,PumpError::BuyZeroAmount);}
 let pre_quote=if exact{0}else{crate::legacy_sell::fee_cpi::buy_quote(c,input.min(c.real_token_reserves))?};
 let (initial_protocol_fee,initial_creator_fee,protocol_fee_bps,creator_fee_bps)={let values=crate::legacy_sell::fee_cpi::trade_fees(
  &a.global,&a.bonding_curve,&a.mint,&a.fee_config,&a.fee_program,a.program.as_ref(),if exact{input}else{pre_quote}
 )?;if a.user.key()==a.global.whitelist_pda{(0,0,0,0)}else{values}};
 let cb=if c.creator==Pubkey::default(){0}else{creator_fee_bps};
 let raw_quote=if exact{let total_bps=protocol_fee_bps.checked_add(cb).ok_or(PumpError::Overflow)?;let denominator=10000u128+total_bps as u128;narrow(input as u128*10000/denominator)?}else{0};
 let adjusted=if exact && add(add(raw_quote,ceil_fee(raw_quote,protocol_fee_bps)?)?,ceil_fee(raw_quote,cb)?)?>input{sub(raw_quote,1)?}else{raw_quote};
 let computed=if exact{require_gt!(raw_quote,0,PumpError::BuyNotEnoughSolToCoverFees);require_gt!(adjusted,0,PumpError::BuySlippageBelowMinTokensOut);let e=adjusted.saturating_sub(1);narrow(c.virtual_token_reserves as u128*e as u128/(c.virtual_quote_reserves as u128+e as u128))?}else{input};
 if !partial{require_gte!(c.real_token_reserves,computed,PumpError::NotEnoughTokensToBuy);}let amount=computed.min(c.real_token_reserves);
 let quote=if !exact{pre_quote}else if computed<=c.real_token_reserves{adjusted}else{add(narrow(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128-amount as u128))?,1)?};
 let fq=if exact && computed<=c.real_token_reserves{raw_quote}else{quote};let pf=if exact{ceil_fee(fq,protocol_fee_bps)?}else{initial_protocol_fee};let cf=if exact{ceil_fee(fq,cb)?}else{initial_creator_fee};
 if exact{if !(partial && computed>c.real_token_reserves){require_gte!(amount,limit,PumpError::BuySlippageBelowMinTokensOut);}}else{require_gte!(limit,add(add(quote,pf)?,cf)?,PumpError::TooMuchSolRequired);}
 let vb=sub(c.virtual_token_reserves,amount)?;let vq=add(c.virtual_quote_reserves,quote)?;let rb=sub(c.real_token_reserves,amount)?;let rq=add(c.real_quote_reserves,quote)?;
 let mint=a.mint.key();let bump=[ctx.bumps.bonding_curve];let seeds:&[&[u8]]=&[b"bonding-curve",mint.as_ref(),&bump];
 if amount>0{token_interface::transfer_checked(CpiContext::new_with_signer(a.token_program.to_account_info(),TransferChecked{from:a.associated_bonding_curve.to_account_info(),mint:a.mint.to_account_info(),to:a.associated_user.to_account_info(),authority:a.bonding_curve.to_account_info()},&[seeds]),amount,a.mint.decimals)?;}
 let v2=rem.get(0).ok_or_else(||error!(PumpError::InvalidBondingCurveV2))?;require!(v2.key()==Pubkey::find_program_address(&[b"bonding-curve-v2",a.mint.key().as_ref()],&crate::ID).0,PumpError::InvalidBondingCurveV2);
 let bbps=if c.is_mayhem_mode{0}else{a.global.buyback_basis_points};
 let cashback_coin=c.is_cashback_coin;
 if cf!=0 && !cashback_coin {crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.user,&a.creator_vault)?;}
 let creator_destination=if cashback_coin{a.user_volume_accumulator.to_account_info()}else{a.creator_vault.to_account_info()};
 if cf>0{anchor_lang::system_program::transfer(CpiContext::new(a.system_program.to_account_info(),anchor_lang::system_program::Transfer{from:a.user.to_account_info(),to:creator_destination}),cf)?;}
 if cashback_coin{a.user_volume_accumulator.cashback_earned=add(a.user_volume_accumulator.cashback_earned,cf)?;}
 if quote>0{anchor_lang::system_program::transfer(CpiContext::new(a.system_program.to_account_info(),anchor_lang::system_program::Transfer{from:a.user.to_account_info(),to:a.bonding_curve.to_account_info()}),quote)?;}
 let (bf,protocol_fee)=crate::buy_v2::recipient_payments::split_protocol_fee(&a.global,pf,c.is_mayhem_mode);
 for (to,amount) in [(bb.clone(),bf),(a.fee_recipient.to_account_info(),protocol_fee)]{if amount>0{anchor_lang::system_program::transfer(CpiContext::new(a.system_program.to_account_info(),anchor_lang::system_program::Transfer{from:a.user.to_account_info(),to}),amount)?;}}
 let ev=TradeEvent{mint:a.mint.key(),sol_amount:quote,token_amount:amount,is_buy:true,user:a.user.key(),timestamp:Clock::get()?.unix_timestamp,virtual_sol_reserves:vq,virtual_token_reserves:vb,real_sol_reserves:rq,real_token_reserves:rb,fee_recipient:a.fee_recipient.key(),fee_basis_points:protocol_fee_bps,fee:pf,creator:c.creator,creator_fee_basis_points:if c.is_cashback_coin{0}else{creator_fee_bps},creator_fee:if c.is_cashback_coin{0}else{cf},track_volume:track,total_unclaimed_tokens:a.user_volume_accumulator.total_unclaimed_tokens,total_claimed_tokens:a.user_volume_accumulator.total_claimed_tokens,current_sol_volume:a.user_volume_accumulator.current_sol_volume,last_update_timestamp:a.user_volume_accumulator.last_update_timestamp,ix_name:if exact{"buy_exact_sol_in".into()}else{"buy".into()},mayhem_mode:c.is_mayhem_mode,cashback_fee_basis_points:if c.is_cashback_coin{cb}else{0},cashback:if c.is_cashback_coin{cf}else{0},buyback_fee_basis_points:bbps,buyback_fee:bf,shareholders:vec![],quote_mint:Pubkey::default(),quote_amount:quote,virtual_quote_reserves:vq,real_quote_reserves:rq,holder_rewards_bps:if c.is_holder_reward{cb}else{0},holder_rewards:if c.is_holder_reward{cf}else{0},creator_fee_unclaimed:c.creator_fee,unparsed_trailing_field:0};
 let c=&mut a.bonding_curve;c.virtual_token_reserves=vb;c.virtual_quote_reserves=vq;c.real_token_reserves=rb;c.real_quote_reserves=rq;
 let complete=if rb==0{c.complete=true;Some(crate::trade_types::CompleteEvent{user:a.user.key(),mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),timestamp:Clock::get()?.unix_timestamp,quote_mint:Pubkey::default()})}else{None};
 emit!(ev.clone());emit_cpi!(ev);if let Some(event)=complete{emit!(event.clone());emit_cpi!(event);}Ok(())
}
use crate::legacy_sell::fee_cpi::fee as ceil_fee;

#[path="legacy_native_payments.rs"]
pub(crate) mod native_payments;
