use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,TokenAccount,Mint,TransferChecked};
use crate::{UserVolumeAccumulator,PumpError};
#[derive(Accounts)]
pub struct ClaimCashback<'info>{
 /// CHECK: recipient is constrained by the accumulator PDA.
 #[account(mut)]pub user:AccountInfo<'info>,
 #[account(mut,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]pub user_volume_accumulator:Account<'info,UserVolumeAccumulator>,
 pub system_program:Program<'info,System>,
 /// CHECK: constrained event authority PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
}
#[derive(Accounts)]
pub struct ClaimCashbackV2<'info>{
 /// CHECK: recipient is constrained by the accumulator PDA.
 #[account(mut)]pub user:AccountInfo<'info>,
 #[account(mut,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]pub user_volume_accumulator:Account<'info,UserVolumeAccumulator>,
 /// CHECK: native path ignores mint data; token branch checks owner and decodes.
 pub quote_mint:UncheckedAccount<'info>,
 /// CHECK: CPI target on token branch only.
 pub quote_token_program:UncheckedAccount<'info>,
 pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
 /// CHECK: PDA constrained; token program validates transfer source.
 #[account(mut,seeds=[user_volume_accumulator.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub associated_user_volume_accumulator:UncheckedAccount<'info>,
 /// CHECK: token branch checks token program owner and user authority.
 #[account(mut)]pub associated_quote_user:UncheckedAccount<'info>,
 pub system_program:Program<'info,System>,
 /// CHECK: constrained event authority PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
}
#[event]
#[derive(Clone)]
pub struct ClaimCashbackEvent{pub user:Pubkey,pub amount:u64,pub timestamp:i64,pub total_claimed:u64,pub total_cashback_earned:u64}
pub fn claim(ctx:Context<ClaimCashback>)->Result<()>{
 let a=&mut *ctx.accounts;let amount=a.user_volume_accumulator.to_account_info().lamports().saturating_sub(Rent::get()?.minimum_balance(a.user_volume_accumulator.to_account_info().data_len()));if amount==0{return Ok(());}
 a.user_volume_accumulator.total_cashback_claimed=a.user_volume_accumulator.total_cashback_claimed.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
 a.user_volume_accumulator.sub_lamports(amount)?;a.user.add_lamports(amount)?;
 let event=ClaimCashbackEvent{user:a.user.key(),amount,timestamp:Clock::get()?.unix_timestamp,total_claimed:a.user_volume_accumulator.total_cashback_claimed,total_cashback_earned:a.user_volume_accumulator.cashback_earned};emit!(event.clone());emit_cpi!(event);Ok(())
}
pub fn claim_v2(ctx:Context<ClaimCashbackV2>)->Result<()>{
 let a=&mut *ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
 if !native{require_keys_eq!(*a.quote_mint.owner,a.quote_token_program.key(),PumpError::AccountTypeNotSupported);}
 let amount=if native{a.user_volume_accumulator.to_account_info().lamports().saturating_sub(Rent::get()?.minimum_balance(a.user_volume_accumulator.to_account_info().data_len()))}else{let data=a.associated_user_volume_accumulator.try_borrow_data()?;if data.is_empty(){0}else{TokenAccount::try_deserialize(&mut &data[..])?.amount}};
 if amount==0{return Ok(());}
 if native{a.user_volume_accumulator.sub_lamports(amount)?;a.user.add_lamports(amount)?;}
 else{
  
  let mint=Mint::try_deserialize(&mut &a.quote_mint.try_borrow_data()?[..])?;
  require_keys_eq!(*a.associated_quote_user.owner,a.quote_token_program.key(),PumpError::AccountTypeNotSupported);
  let recipient=TokenAccount::try_deserialize(&mut &a.associated_quote_user.try_borrow_data()?[..])?;require_keys_eq!(recipient.owner,a.user.key(),PumpError::InvalidCashbackRecipient);
  let user=a.user.key();let bump=[ctx.bumps.user_volume_accumulator];let seeds:&[&[u8]]=&[b"user_volume_accumulator",user.as_ref(),&bump];
  token_interface::transfer_checked(CpiContext::new_with_signer(a.quote_token_program.to_account_info(),TransferChecked{from:a.associated_user_volume_accumulator.to_account_info(),mint:a.quote_mint.to_account_info(),to:a.associated_quote_user.to_account_info(),authority:a.user_volume_accumulator.to_account_info()},&[seeds]),amount,mint.decimals)?;

 }
 crate::token_incentives::volume_accumulator::record_cashback_claim(&mut a.user_volume_accumulator,amount,native)?;
 let event=ClaimCashbackEvent{user:a.user.key(),amount,timestamp:Clock::get()?.unix_timestamp,total_claimed:a.user_volume_accumulator.total_cashback_claimed,total_cashback_earned:a.user_volume_accumulator.cashback_earned};emit!(event.clone());emit_cpi!(event);Ok(())
}
