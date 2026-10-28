//! Claim of Token-2022 incentives using the shared volume accumulator worker.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::{
    instruction::{AccountMeta, Instruction},
    program::invoke_signed,
};
use anchor_lang::Event;
use anchor_spl::associated_token::AssociatedToken;
use anchor_spl::token_interface::{self, Mint, TokenAccount, TokenInterface, TransferChecked};

use crate::{GlobalVolumeAccumulator, UserVolumeAccumulator};

const EVENT_CPI_DISCRIMINATOR: [u8; 8] = [228, 69, 165, 46, 81, 203, 154, 29];

#[derive(Accounts)]
pub struct ClaimTokenIncentives<'info> {
    /// CHECK: The user key names its ATA and volume PDA; it is not a signer.
    pub user: AccountInfo<'info>,
    #[account(init_if_needed, payer = payer, associated_token::mint = mint,
        associated_token::authority = user,
        associated_token::token_program = token_program)]
    pub user_ata: InterfaceAccount<'info, TokenAccount>,
    #[account(seeds = [b"global_volume_accumulator"], bump,
        has_one = mint @ crate::PumpError::InvalidIncentiveMint)]
    pub global_volume_accumulator: Account<'info, GlobalVolumeAccumulator>,
    #[account(mut, associated_token::mint = mint,
        associated_token::authority = global_volume_accumulator,
        associated_token::token_program = token_program)]
    pub global_incentive_token_account: InterfaceAccount<'info, TokenAccount>,
    #[account(mut, seeds = [b"user_volume_accumulator", user.key().as_ref()], bump)]
    pub user_volume_accumulator: Account<'info, UserVolumeAccumulator>,
    pub mint: InterfaceAccount<'info, Mint>,
    pub token_program: Interface<'info, TokenInterface>,
    pub system_program: Program<'info, System>,
    pub associated_token_program: Program<'info, AssociatedToken>,
    /// CHECK: This is the program's event CPI signer PDA.
    #[account(seeds = [b"__event_authority"], bump)]
    pub event_authority: AccountInfo<'info>,
    pub program: Program<'info, crate::program::PumpRecovered>,
    #[account(mut)]
    pub payer: Signer<'info>,
}

#[event]
#[derive(Clone)]
pub struct ClaimTokenIncentivesEvent {
    pub user: Pubkey,
    pub mint: Pubkey,
    pub amount: u64,
    pub timestamp: i64,
    pub total_claimed_tokens: u64,
    pub current_sol_volume: u64,
}

pub fn claim(ctx: Context<ClaimTokenIncentives>) -> Result<()> {
    let now = Clock::get()?.unix_timestamp;
    let global = &mut ctx.accounts.global_volume_accumulator;
    let user = &mut ctx.accounts.user_volume_accumulator;
    super::volume_accumulator::update(global, user, now, 0, &ctx.accounts.user.key())?;
    let amount = user.total_unclaimed_tokens;
    if amount == 0 {
        msg!("No tokens to claim");
        return Ok(());
    }
    let bump = [ctx.bumps.global_volume_accumulator];
    let signer: &[&[u8]] = &[b"global_volume_accumulator", &bump];
    let transfer = TransferChecked {
        from: ctx
            .accounts
            .global_incentive_token_account
            .to_account_info(),
        mint: ctx.accounts.mint.to_account_info(),
        to: ctx.accounts.user_ata.to_account_info(),
        authority: global.to_account_info(),
    };
    token_interface::transfer_checked(
        CpiContext::new_with_signer(
            ctx.accounts.token_program.to_account_info(),
            transfer,
            &[signer],
        ),
        amount,
        ctx.accounts.mint.decimals,
    )?;
    super::volume_accumulator::record_claim(user, now);
    let event = ClaimTokenIncentivesEvent {
        user: ctx.accounts.user.key(),
        mint: ctx.accounts.mint.key(),
        amount,
        timestamp: now,
        total_claimed_tokens: user.total_claimed_tokens,
        current_sol_volume: user.current_sol_volume,
    };
    emit!(event.clone());
    let mut data = EVENT_CPI_DISCRIMINATOR.to_vec();
    data.extend_from_slice(&event.data());
    let ix = Instruction {
        program_id: crate::ID,
        accounts: vec![AccountMeta::new_readonly(
            ctx.accounts.event_authority.key(),
            true,
        )],
        data,
    };
    let event_bump = [ctx.bumps.event_authority];
    let event_signer: &[&[u8]] = &[b"__event_authority", &event_bump];
    invoke_signed(
        &ix,
        &[ctx.accounts.event_authority.to_account_info()],
        &[event_signer],
    )?;
    Ok(())
}

pub mod cashback {
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
// layout-pad(99): aligns the next Source site with the original line


































































































  a.user_volume_accumulator.total_cashback_claimed=a.user_volume_accumulator.total_cashback_claimed.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
  a.user_volume_accumulator.sub_lamports(amount)?;a.user.add_lamports(amount)?;
  let event=ClaimCashbackEvent{user:a.user.key(),amount,timestamp:Clock::get()?.unix_timestamp,total_claimed:a.user_volume_accumulator.total_cashback_claimed,total_cashback_earned:a.user_volume_accumulator.cashback_earned};emit!(event.clone());emit_cpi!(event);Ok(())
 }
 pub fn claim_v2(ctx:Context<ClaimCashbackV2>)->Result<()>{
  let a=&mut *ctx.accounts;let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
// layout-pad(52): aligns the next Source site with the original line



















































  if !native{require_keys_eq!(*a.quote_mint.owner,a.quote_token_program.key(),PumpError::AccountTypeNotSupported);}
  let amount=if native{a.user_volume_accumulator.to_account_info().lamports().saturating_sub(Rent::get()?.minimum_balance(a.user_volume_accumulator.to_account_info().data_len()))}else{let data=a.associated_user_volume_accumulator.try_borrow_data()?;if data.is_empty(){0}else{TokenAccount::try_deserialize(&mut &data[..])?.amount}};
  if amount==0{return Ok(());}
  if native{a.user_volume_accumulator.sub_lamports(amount)?;a.user.add_lamports(amount)?;}
  else{
   
   let mint=Mint::try_deserialize(&mut &a.quote_mint.try_borrow_data()?[..])?;
// layout-pad(16): aligns the next Source site with the original line















   require_keys_eq!(*a.associated_quote_user.owner,a.quote_token_program.key(),PumpError::AccountTypeNotSupported);
// layout-pad(8): aligns the next Source site with the original line







   let recipient=TokenAccount::try_deserialize(&mut &a.associated_quote_user.try_borrow_data()?[..])?;require_keys_eq!(recipient.owner,a.user.key(),PumpError::InvalidCashbackRecipient);
   let user=a.user.key();let bump=[ctx.bumps.user_volume_accumulator];let seeds:&[&[u8]]=&[b"user_volume_accumulator",user.as_ref(),&bump];
   token_interface::transfer_checked(CpiContext::new_with_signer(a.quote_token_program.to_account_info(),TransferChecked{from:a.associated_user_volume_accumulator.to_account_info(),mint:a.quote_mint.to_account_info(),to:a.associated_quote_user.to_account_info(),authority:a.user_volume_accumulator.to_account_info()},&[seeds]),amount,mint.decimals)?;

  }
  crate::token_incentives::volume_accumulator::record_cashback_claim(&mut a.user_volume_accumulator,amount,native)?;
  let event=ClaimCashbackEvent{user:a.user.key(),amount,timestamp:Clock::get()?.unix_timestamp,total_claimed:a.user_volume_accumulator.total_cashback_claimed,total_cashback_earned:a.user_volume_accumulator.cashback_earned};emit!(event.clone());emit_cpi!(event);Ok(())
 }
}
