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
    let accounts = &mut *ctx.accounts;
    let now = Clock::get()?.unix_timestamp;
    super::volume_accumulator::update(&mut accounts.global_volume_accumulator, &mut accounts.user_volume_accumulator, now, 0, &accounts.user.key())?;
    let amount = accounts.user_volume_accumulator.total_unclaimed_tokens;
    if amount == 0 {
        msg!("No tokens to claim");
        return Ok(());
    }
    { let token_program = accounts.token_program.as_ref();
        let authority = accounts.global_volume_accumulator.to_account_info(); let signer_seeds: &[&[&[u8]]] = &[&[b"global_volume_accumulator", &[ctx.bumps.global_volume_accumulator]]];
        fn transfer<'info>(decimals: u8, token_program: &AccountInfo<'info>, mint: &AccountInfo<'info>, from: &AccountInfo<'info>, to: &AccountInfo<'info>, authority: &AccountInfo<'info>, signer_seeds: &[&[&[u8]]], amount: u64) -> Result<()> {
            token_interface::transfer_checked(
                CpiContext::new_with_signer(
                    token_program.clone(),
                    TransferChecked { from: from.clone(), mint: mint.clone(), to: to.clone(), authority: authority.clone() },
                    signer_seeds,
                ),
                amount,
                decimals,
            )
        }
 
 
        transfer(accounts.mint.decimals, token_program, accounts.mint.as_ref(), accounts.global_incentive_token_account.as_ref(), accounts.user_ata.as_ref(), &authority, signer_seeds, amount)?;
    }
    let user = &mut accounts.user_volume_accumulator;
    super::volume_accumulator::record_claim(user, now);
    let event = ClaimTokenIncentivesEvent {
        user: accounts.user.key(),
        mint: accounts.mint.key(),
        amount,
        timestamp: now,
        total_claimed_tokens: user.total_claimed_tokens,
        current_sol_volume: user.current_sol_volume,
    };



    emit!(event);
    emit_cpi!(event);
















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
  let user_volume_accumulator=&mut ctx.accounts.user_volume_accumulator;let timestamp=Clock::get()?.unix_timestamp;let min=Rent::get()?.minimum_balance(user_volume_accumulator.to_account_info().data_len());let amount=user_volume_accumulator.get_lamports().saturating_sub(min);if amount==0{msg!("No cashback to claim");return Ok(());}
// layout-pad(99): aligns the next Source site with the original line

































































































  user_volume_accumulator.sub_lamports(amount)?;ctx.accounts.user.add_lamports(amount)?;
  user_volume_accumulator.total_cashback_claimed=user_volume_accumulator.total_cashback_claimed.checked_add(amount).ok_or(error!(PumpError::Overflow))?;
  let total_cashback_earned=user_volume_accumulator.cashback_earned;
  let event=ClaimCashbackEvent{user:ctx.accounts.user.key(),amount,timestamp,total_claimed:user_volume_accumulator.total_cashback_claimed,total_cashback_earned};emit!(event);emit_cpi!(event);Ok(())
 }
 pub fn claim_v2(ctx:Context<ClaimCashbackV2>)->Result<()>{
  let user=&mut ctx.accounts.user;let user_volume_accumulator=&mut ctx.accounts.user_volume_accumulator;let timestamp=Clock::get()?.unix_timestamp;let native=ctx.accounts.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
// layout-pad(52): aligns the next Source site with the original line













































  let amount=if native{let min=Rent::get()?.minimum_balance(user_volume_accumulator.to_account_info().data_len());let amount=user_volume_accumulator.get_lamports().saturating_sub(min);if amount==0{msg!("No cashback to claim");return Ok(());}user_volume_accumulator.sub_lamports(amount)?;user.add_lamports(amount)?;amount}else{
   require!(ctx.accounts.quote_token_program.key()==anchor_spl::token::ID||ctx.accounts.quote_token_program.key()==anchor_spl::token_2022::ID,PumpError::InvalidQuoteTokenProgram);




   require_keys_eq!(*ctx.accounts.quote_mint.to_account_info().owner,ctx.accounts.quote_token_program.key(),PumpError::AccountTypeNotSupported);
   if ctx.accounts.associated_user_volume_accumulator.data_is_empty(){msg!("No cashback to claim");return Ok(());}let amount={let data=ctx.accounts.associated_user_volume_accumulator.try_borrow_data()?;TokenAccount::try_deserialize(&mut &data[..])?.amount};if amount==0{msg!("No cashback to claim");return Ok(());}



   

// layout-pad(16): aligns the next Source site with the original line















   require_keys_eq!(*ctx.accounts.associated_quote_user.to_account_info().owner,ctx.accounts.quote_token_program.key(),PumpError::AccountTypeNotSupported);
// layout-pad(8): aligns the next Source site with the original line







   let recipient={let data=ctx.accounts.associated_quote_user.try_borrow_data()?;TokenAccount::try_deserialize(&mut &data[..])?.owner};require_keys_eq!(recipient,user.key(),PumpError::InvalidCashbackRecipient);
   let mint={let data=ctx.accounts.quote_mint.try_borrow_data()?;Mint::try_deserialize(&mut &data[..])?};let user=user.key();let bump=ctx.bumps.user_volume_accumulator;let signer_seeds:&[&[&[u8]]]=&[&[b"user_volume_accumulator",user.as_ref(),&[bump]]];
   token_interface::transfer_checked(CpiContext::new_with_signer(ctx.accounts.quote_token_program.to_account_info(),TransferChecked{from:ctx.accounts.associated_user_volume_accumulator.to_account_info(),mint:ctx.accounts.quote_mint.to_account_info(),to:ctx.accounts.associated_quote_user.to_account_info(),authority:user_volume_accumulator.to_account_info()},signer_seeds),amount,mint.decimals)?;

   amount};
  crate::token_incentives::volume_accumulator::record_cashback_claim(user_volume_accumulator,amount,native)?;
  let total_claimed=user_volume_accumulator.total_cashback_claimed;let total_cashback_earned=user_volume_accumulator.cashback_earned;let event=ClaimCashbackEvent{user:user.key(),amount,timestamp,total_claimed,total_cashback_earned};emit!(event);emit_cpi!(event);Ok(())
 }
}
#[event_cpi]
#[derive(Accounts)]
pub struct CloseUserVolume<'info>{
 #[account(mut)] pub user:Signer<'info>,
 #[account(mut,close=user,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]
 pub user_volume_accumulator:Account<'info,crate::UserVolumeAccumulator>,
}
