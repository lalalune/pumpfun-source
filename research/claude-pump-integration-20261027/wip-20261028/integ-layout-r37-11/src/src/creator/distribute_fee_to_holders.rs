use anchor_lang::prelude::*;
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed,system_instruction};
use anchor_spl::{token_interface::{Mint,TokenAccount,TokenInterface},associated_token::AssociatedToken};
use crate::{Global,PumpError};
#[event_cpi]
#[derive(Accounts)]
pub struct DistributeFeeToHolders<'info>{
 #[account(seeds=[b"global"],bump,has_one=holder_reward_claim_authority @ PumpError::NotAuthorized)]pub global:Box<Account<'info,Global>>,
 #[account(mut)]pub holder_reward_claim_authority:Signer<'info>,
 /// CHECK: mint key identifies the rewards PDA.
 pub mint:UncheckedAccount<'info>,
 /// CHECK: System transfers enforce the source account ownership.
 #[account(mut,seeds=[b"holder-rewards",mint.key().as_ref()],bump)]pub holder_rewards:UncheckedAccount<'info>,
 #[account(mut,token::authority=holder_rewards,token::mint=quote_mint,token::token_program=quote_token_program)]pub holder_rewards_token_account:Option<Box<InterfaceAccount<'info,TokenAccount>>>,
 pub quote_mint:Box<InterfaceAccount<'info,Mint>>,
 pub quote_token_program:Interface<'info,TokenInterface>,
 pub associated_token_program:Program<'info,AssociatedToken>,
 pub system_program:Program<'info,System>,
}
#[event]#[derive(Clone)]pub struct DistributeFeeToHoldersEvent{pub timestamp:i64,pub mint:Pubkey,pub quote_mint:Pubkey,pub recipients:u64,pub total:u64}
pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,DistributeFeeToHolders<'info>>,amounts:Vec<u64>)->Result<()>{
 let a=&ctx.accounts;let mint=a.mint.key();let bump=[ctx.bumps.holder_rewards];let seeds:&[&[u8]]=&[b"holder-rewards",mint.as_ref(),&bump];let signer=&[seeds];
 let native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
// layout-pad(58): aligns the next Source site with the original line

























































 require!(ctx.remaining_accounts.len()==amounts.len()*2,PumpError::HolderRewardRecipientsMismatch);
 if let Some(source)=&a.holder_rewards_token_account {
  if native {anchor_spl::token_interface::close_account(CpiContext::new_with_signer(a.quote_token_program.to_account_info(),anchor_spl::token_interface::CloseAccount{account:source.to_account_info(),destination:a.holder_rewards.to_account_info(),authority:a.holder_rewards.to_account_info()},signer))?;}
 }
 let mut total=0u64;
 for (amount,pair) in amounts.iter().zip(ctx.remaining_accounts.chunks_exact(2)){
  if native {
   if *amount!=0 {invoke_signed(&system_instruction::transfer(&a.holder_rewards.key(),pair[0].key,*amount),&[a.holder_rewards.to_account_info(),pair[0].clone(),a.system_program.to_account_info()],signer)?;}
// layout-pad(29): aligns the next Source site with the original line




























  }else{
   let source=a.holder_rewards_token_account.as_ref().ok_or_else(||error!(PumpError::HolderRewardTokenAccountMissing))?;
// layout-pad(1): aligns the next Source site with the original line
   require_keys_eq!(*pair[1].key,anchor_spl::associated_token::get_associated_token_address_with_program_id(pair[0].key,&a.quote_mint.key(),&a.quote_token_program.key()),PumpError::HolderRewardRecipientsMismatch);
   if pair[1].data_is_empty(){let ix=Instruction{program_id:a.associated_token_program.key(),accounts:vec![AccountMeta::new(a.holder_reward_claim_authority.key(),true),AccountMeta::new(*pair[1].key,false),AccountMeta::new_readonly(*pair[0].key,false),AccountMeta::new_readonly(a.quote_mint.key(),false),AccountMeta::new_readonly(a.system_program.key(),false),AccountMeta::new_readonly(a.quote_token_program.key(),false)],data:vec![0]};invoke_signed(&ix,&[a.holder_reward_claim_authority.to_account_info(),pair[1].clone(),pair[0].clone(),a.quote_mint.to_account_info(),a.system_program.to_account_info(),a.quote_token_program.to_account_info(),a.associated_token_program.to_account_info()],&[])?;}
   if *amount!=0 {anchor_spl::token_interface::transfer_checked(CpiContext::new_with_signer(a.quote_token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{from:source.to_account_info(),mint:a.quote_mint.to_account_info(),to:pair[1].clone(),authority:a.holder_rewards.to_account_info()},signer),*amount,a.quote_mint.decimals)?;}
  }
// layout-pad(31): aligns the next Source site with the original line






























  total=total.checked_add(*amount).ok_or_else(||error!(PumpError::Overflow))?;
 }
// layout-pad(5): aligns the next Source site with the original line




 if native {let balance=a.holder_rewards.lamports();require!(balance==0||balance>=Rent::get()?.minimum_balance(0),PumpError::HolderRewardsRentFloor);}
 let e=DistributeFeeToHoldersEvent{timestamp:Clock::get()?.unix_timestamp,mint,quote_mint:if native {Pubkey::default()}else{a.quote_mint.key()},recipients:amounts.len() as u64,total};emit!(e.clone());emit_cpi!(e);Ok(())
}
