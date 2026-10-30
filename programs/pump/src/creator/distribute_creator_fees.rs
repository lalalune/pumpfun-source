use anchor_lang::prelude::*;#[path = "distribute_creator_fee_v2.rs"] mod v2;
use crate::{PumpError,trade_types::{Shareholder,BondingCurve}};
pub const FEES:Pubkey=anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
pub use crate::pump_fees::{accounts::SharingConfig, types::ConfigStatus};
// Legacy curve layouts omit trailing fields. Keep this read-only view separate from trade state.
pub use crate::migrate::DistributionCurve;
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
#[derive(Accounts)]
pub struct DistributeCreatorFeesV2<'info>{
 #[account(mut)]pub payer:Signer<'info>,
 pub mint:InterfaceAccount<'info,anchor_spl::token_interface::Mint>,
 #[account(seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.creator==sharing_config.key() @ PumpError::BondingCurveAndSharingConfigCreatorMismatch)]pub bonding_curve:Account<'info,BondingCurve>,
 #[account(seeds=[b"sharing-config",mint.key().as_ref()],bump,seeds::program=FEES,has_one=mint @ PumpError::MintDoesNotMatchBondingCurve)]pub sharing_config:Account<'info,SharingConfig>,
 /// CHECK: Native vault address validated by PDA seeds.
 #[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 pub system_program:Program<'info,System>,
 /// CHECK: Event authority.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
 /// CHECK: Nonlegacy branch parses token data manually.
 #[account(mut,seeds=[creator_vault.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub creator_vault_quote_token_account:UncheckedAccount<'info>,
 #[account(constraint=quote_mint.key()==bonding_curve.quote_mint||(bonding_curve.quote_mint==Pubkey::default()&&quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID) @ PumpError::MintDoesNotMatchBondingCurve)]
 pub quote_mint:Box<InterfaceAccount<'info,anchor_spl::token_interface::Mint>>,
 pub quote_token_program:Interface<'info,anchor_spl::token_interface::TokenInterface>,
 pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
}
#[derive(Accounts)]
pub struct DistributeCreatorFees<'info>{
 pub mint:InterfaceAccount<'info,anchor_spl::token_interface::Mint>,
 #[account(seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.quote_mint==Pubkey::default() @ PumpError::UnsupportedQuoteMint,constraint=bonding_curve.creator==sharing_config.key() @ PumpError::BondingCurveAndSharingConfigCreatorMismatch)]pub bonding_curve:Account<'info,BondingCurve>,
 #[account(seeds=[b"sharing-config",mint.key().as_ref()],bump,seeds::program=FEES,has_one=mint @ PumpError::MintDoesNotMatchBondingCurve)]pub sharing_config:Account<'info,SharingConfig>,
 #[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 pub system_program:Program<'info,System>,
 /// CHECK: event PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
}

fn validate_shareholder_recipient(shareholder:&Shareholder,recipient:&AccountInfo)->Result<()>{
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
 require!(recipient.key()==shareholder.address,PumpError::ShareholdersAndRemainingAccountsMismatch);
 if recipient.executable{
  msg!("Unable to distribute to {}. Shareholder is a program account, use pump_fees::update_fee_shares to remove the shareholder from the team",recipient.key().to_string());
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
  return err!(PumpError::UnableToDistributeCreatorFeesToExecutableRecipient);
 }
 Ok(())
}

pub(crate) fn get_distribution_amounts<'info>(rent:&Rent,shares:&[Shareholder],recipients:&[AccountInfo<'info>],creator_vault:&AccountInfo<'info>)->Result<(Vec<(u64,u64)>,u64,u64,u64)>{
 let reserve=rent.minimum_balance(0);
 let available=creator_vault.lamports().saturating_sub(reserve);
 let mut transfers=Vec::with_capacity(shares.len());let mut minimum=0u64;
 for (i,share) in shares.iter().enumerate(){
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
  let recipient=recipients.get(i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
  validate_shareholder_recipient(share,recipient)?;
// layout-pad
// layout-pad
// layout-pad
  require!(share.share_bps>0,PumpError::InvalidShareBps);
  let share_bps=u64::from(share.share_bps);
  let deficit=rent.minimum_balance(recipient.data_len()).saturating_sub(recipient.lamports());
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
  let threshold=deficit.checked_mul(10000).and_then(|v|v.checked_add(share_bps.saturating_sub(1))).ok_or_else(||error!(PumpError::Overflow))?/share_bps;
  minimum=minimum.max(threshold);
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
  let amount=available.checked_mul(share_bps).ok_or_else(||error!(PumpError::Overflow))?/10000;
  transfers.push((amount,deficit));
 }
 Ok((transfers,minimum,minimum.saturating_add(reserve),available))
}

pub mod minimum{use anchor_lang::prelude::*;
use crate::{PumpError,distribution::{FEES,SharingConfig},trade_types::BondingCurve};
#[derive(Accounts)]
pub struct GetMinimumDistributableFee<'info>{
 pub mint:InterfaceAccount<'info,anchor_spl::token_interface::Mint>,
 #[account(seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.creator==sharing_config.key() @ PumpError::BondingCurveAndSharingConfigCreatorMismatch)]pub bonding_curve:Account<'info,BondingCurve>,
 #[account(seeds=[b"sharing-config",mint.key().as_ref()],bump,seeds::program=FEES,has_one=mint @ PumpError::MintDoesNotMatchBondingCurve)]pub sharing_config:Account<'info,SharingConfig>,
 /// CHECK: only seeds and available lamports are used by this readonly query.
 #[account(seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
}
#[event]
#[derive(Clone)]
pub struct MinimumDistributableFeeEvent{pub minimum_required:u64,pub distributable_fees:u64,pub can_distribute:bool}
pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,GetMinimumDistributableFee<'info>>)->Result<MinimumDistributableFeeEvent>{
 let a=ctx.accounts;
 let rent=Rent::get()?;
 let (_,minimum_distributable,minimum_required,distributable_fees)=crate::distribution::get_distribution_amounts(&rent,&a.sharing_config.shareholders,ctx.remaining_accounts,&a.creator_vault)?;
 let event=MinimumDistributableFeeEvent{minimum_required,distributable_fees,can_distribute:distributable_fees>=minimum_distributable};emit!(event.clone());Ok(event)
}}
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
#[event]
#[derive(Clone)]pub struct DistributeCreatorFeesEvent{pub timestamp:i64,pub mint:Pubkey,pub bonding_curve:Pubkey,pub sharing_config:Pubkey,pub admin:Pubkey,pub shareholders:Vec<Shareholder>,pub distributed:u64,pub quote_mint:Pubkey}
pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,DistributeCreatorFees<'info>>)->Result<DistributeCreatorFeesEvent>{
 let sharing_config=&ctx.accounts.sharing_config;
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
 require!(matches!(sharing_config.status, ConfigStatus::Active),PumpError::SharingConfigNotActive);
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
 require!(ctx.accounts.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);
 let rent=Rent::get()?;
 let (transfers,minimum_distributable,minimum_vault_balance,available)=get_distribution_amounts(&rent,&sharing_config.shareholders,ctx.remaining_accounts,&ctx.accounts.creator_vault)?;
 if available<minimum_distributable{
  msg!("Insufficient fees for distribution. Minimum vault balance needed: {} lamports. Use get_minimum_distributable_fee instruction to check the minimum distributable amount.",minimum_vault_balance);
  return Ok(DistributeCreatorFeesEvent{timestamp:Clock::get()?.unix_timestamp,mint:ctx.accounts.mint.key(),bonding_curve:ctx.accounts.bonding_curve.key(),sharing_config:sharing_config.key(),admin:sharing_config.admin,shareholders:sharing_config.shareholders.to_vec(),distributed:0,quote_mint:Pubkey::default()});
 }
 let distributed=distribute_native(sharing_config,&ctx.accounts.creator_vault.to_account_info(),&ctx.accounts.system_program,ctx.remaining_accounts,&transfers,ctx.bumps.creator_vault)?;
 let event=DistributeCreatorFeesEvent{timestamp:Clock::get()?.unix_timestamp,mint:ctx.accounts.mint.key(),bonding_curve:ctx.accounts.bonding_curve.key(),sharing_config:sharing_config.key(),admin:sharing_config.admin,shareholders:sharing_config.shareholders.to_vec(),distributed,quote_mint:Pubkey::default()};
 emit!(event);
 emit_cpi!(event);
 Ok(event)
}

pub fn distribute_native<'info>(sharing_config:&Account<'info,SharingConfig>,creator_vault:&AccountInfo<'info>,system_program:&Program<'info,System>,remaining_accounts:&[AccountInfo<'info>],transfers:&[(u64,u64)],creator_vault_bump:u8)->Result<u64>{
 let sharing_config_key=sharing_config.key();
 let creator_vault=creator_vault.to_account_info();
 let mut distributed=0u64;
 for (i,_shareholder) in sharing_config.shareholders.iter().enumerate(){
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
  let recipient=remaining_accounts.get(i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
// layout-pad
        let amount = transfers[i].0; crate::collect_v2::transfer_native(system_program.as_ref(),&creator_vault,recipient,amount,&[&[b"creator-vault",sharing_config_key.as_ref(),&[creator_vault_bump]]])?;
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
  distributed=distributed.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
 }
 Ok(distributed)
}


pub use self::v2::{execute_v2, get_token_distribution_amounts};

pub use crate::payments::sharing_config_shareholders;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
