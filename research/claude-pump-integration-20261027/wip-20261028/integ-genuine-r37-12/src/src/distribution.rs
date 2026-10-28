use anchor_lang::prelude::*;
use crate::{PumpError,trade_types::{Shareholder,BondingCurve}};
pub const FEES:Pubkey=anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
pub use crate::pump_fees::{accounts::SharingConfig, types::ConfigStatus};
// Legacy curve layouts omit trailing fields. Keep this read-only view separate from trade state.
#[derive(Clone)]pub struct DistributionCurve{pub creator:Pubkey,pub quote_mint:Pubkey}
impl Owner for DistributionCurve{fn owner()->Pubkey{crate::ID}}
impl AccountSerialize for DistributionCurve{}
impl AccountDeserialize for DistributionCurve{
 fn try_deserialize(buf:&mut &[u8])->Result<Self>{Self::try_deserialize_unchecked(buf)}
 fn try_deserialize_unchecked(buf:&mut &[u8])->Result<Self>{
  if buf.len()<49 || buf[..8]!=[23,183,248,55,96,216,172,96]{return Err(anchor_lang::solana_program::program_error::ProgramError::InvalidAccountData.into());}
  for offset in [48usize,81,82,123,124]{if buf.len()>offset{let _=bool::deserialize(&mut &buf[offset..offset+1])?;}}
  let creator=if buf.len()>=81{Pubkey::new_from_array(buf[49..81].try_into().unwrap())}else{Pubkey::default()};
  let quote_mint=if buf.len()>=115{Pubkey::new_from_array(buf[83..115].try_into().unwrap())}else{Pubkey::default()};Ok(Self{creator,quote_mint})
 }
}
#[event]
#[derive(Clone)]pub struct DistributeCreatorFeesEvent{pub timestamp:i64,pub mint:Pubkey,pub bonding_curve:Pubkey,pub sharing_config:Pubkey,pub admin:Pubkey,pub shareholders:Vec<Shareholder>,pub distributed:u64,pub quote_mint:Pubkey}
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
pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,DistributeCreatorFees<'info>>)->Result<DistributeCreatorFeesEvent>{
 let a=&ctx.accounts;
 require!(matches!(a.sharing_config.status, ConfigStatus::Active),PumpError::SharingConfigNotActive);
 require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);
 let rent=Rent::get()?;
 let (transfers,minimum_distributable,_,available)=get_distribution_amounts(&rent,&a.sharing_config.shareholders,ctx.remaining_accounts,&a.creator_vault)?;
 let eligible=available>=minimum_distributable;let mut distributed=0u64;
 let bump=[ctx.bumps.creator_vault];let seeds:&[&[u8]]=&[b"creator-vault",a.bonding_curve.creator.as_ref(),&bump];
 if eligible{distributed=crate::distribution::execute_native_distribution(transfers,ctx.remaining_accounts,&a.creator_vault,&a.system_program,seeds)?;}
 let event=DistributeCreatorFeesEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),sharing_config:a.sharing_config.key(),admin:a.sharing_config.admin,shareholders:a.sharing_config.shareholders.clone(),distributed,quote_mint:Pubkey::default()};if eligible{emit!(event.clone());emit_cpi!(event.clone());}Ok(event)
}

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


fn execute_native_distribution<'info>(
 transfers:Vec<(u64,u64)>,recipients:&[AccountInfo<'info>],creator_vault:&AccountInfo<'info>,
 system_program:&Program<'info,System>,seeds:&[&[u8]],
)->Result<u64>{
 let mut distributed=0u64;
 for ((amount,_),recipient) in transfers.into_iter().zip(recipients){
  crate::collect_v2::transfer_native(system_program.as_ref(),creator_vault,recipient,amount,&[seeds])?;
  distributed=distributed.checked_add(amount).ok_or(error!(PumpError::Overflow))?;
 }
 Ok(distributed)
}

pub(crate) fn get_distribution_amounts<'info>(rent:&Rent,shares:&[Shareholder],recipients:&[AccountInfo<'info>],creator_vault:&AccountInfo<'info>)->Result<(Vec<(u64,u64)>,u64,u64,u64)>{
 let reserve=rent.minimum_balance(0);
 let available=creator_vault.lamports().saturating_sub(reserve);
 let mut transfers=Vec::with_capacity(shares.len());let mut minimum=0u64;
 for (i,share) in shares.iter().enumerate(){
  let recipient=recipients.get(i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
  require!(share.address==recipient.key(),PumpError::ShareholdersAndRemainingAccountsMismatch);
  if recipient.executable{
   msg!("Unable to distribute to {}. Shareholder is a program account, use pump_fees::update_fee_shares to remove the shareholder from the team",recipient.key().to_string());
   return err!(PumpError::UnableToDistributeCreatorFeesToExecutableRecipient);
  }
  require!(share.share_bps>0,PumpError::InvalidShareBps);
  let share_bps=u64::from(share.share_bps);
  let deficit=rent.minimum_balance(recipient.data_len()).saturating_sub(recipient.lamports());
  let threshold=deficit.checked_mul(10000).ok_or_else(||error!(PumpError::Overflow))?.checked_add(share_bps.saturating_sub(1)).ok_or_else(||error!(PumpError::Overflow))?/share_bps;
  minimum=minimum.max(threshold);
  let amount=available.checked_mul(share_bps).ok_or_else(||error!(PumpError::Overflow))?/10000;
  transfers.push((amount,deficit));
 }
 Ok((transfers,minimum,reserve.saturating_add(minimum),available))
}
#[path = "creator/distribute_creator_fee_v2.rs"]
mod v2;
pub use self::v2::{execute_v2, get_token_distribution_amounts};

/// Shareholders of an optional fee-sharing config; empty or undecodable data reads as none.
#[inline(never)]
pub fn sharing_config_shareholders(account:&AccountInfo)->Result<Option<Vec<Shareholder>>>{
 if account.data_is_empty(){return Ok(None);}
 let data=account.try_borrow_data()?;
 match SharingConfig::try_deserialize(&mut &data[..]){Ok(config)=>Ok(Some(config.shareholders)),Err(_)=>Ok(None)}
}
