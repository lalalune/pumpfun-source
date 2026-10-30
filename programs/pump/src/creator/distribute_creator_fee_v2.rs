use anchor_lang::prelude::*;
use crate::{PumpError, trade_types::Shareholder};
use super::{ConfigStatus, DistributeCreatorFeesV2, DistributeCreatorFeesEvent, get_distribution_amounts};

// layout-pad(92): aligns the next Source site with the original line




























































































#[inline]
fn validate_token_recipient(share:&Shareholder,recipient:&AccountInfo,ata:&AccountInfo,mint:&Pubkey,quote_mint_info:&AccountInfo)->Result<()>{

 require!(recipient.key()==share.address,PumpError::ShareholdersAndRemainingAccountsMismatch);
 let expected=anchor_spl::associated_token::get_associated_token_address_with_program_id(&share.address,mint,quote_mint_info.owner);
// layout-pad(8): aligns the next Source site with the original line








 require!(ata.key()==expected,PumpError::ShareholdersAndRemainingAccountsMismatch);
 if recipient.executable{
  msg!("Unable to distribute to {}. Shareholder is a program account, use pump_fees::update_fee_shares to remove the shareholder from the team",recipient.key().to_string());
// layout-pad(9): aligns the next Source site with the original line









  return err!(PumpError::UnableToDistributeCreatorFeesToExecutableRecipient);
 }
 Ok(())
}
// layout-pad(14): aligns the next Source site with the original line














#[inline(never)]
pub fn get_token_distribution_amounts(shares:&[Shareholder],recipients:&[AccountInfo],source:&anchor_spl::token_interface::TokenAccount,quote_mint:&InterfaceAccount<anchor_spl::token_interface::Mint>,initialize_ata:bool)->Result<(Vec<(u64,bool)>,u64)>{
 let source_amount=source.amount;
 let mut transfers=Vec::with_capacity(shares.len());
 for (i,share) in shares.iter().enumerate(){
  let recipient=recipients.get(i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
// layout-pad(1): aligns the next Source site with the original line

  let ata=recipients.get(shares.len()+i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
  validate_token_recipient(share,recipient,ata,&quote_mint.key(),&quote_mint.to_account_info())?;
// layout-pad(8): aligns the next Source site with the original line








  require!(share.share_bps>0,PumpError::InvalidShareBps);
// layout-pad(3): aligns the next Source site with the original line



  let amount=source_amount.checked_mul(u64::from(share.share_bps)).and_then(|a|a.checked_div(10000)).ok_or_else(||error!(PumpError::Overflow))?;
  let needs_initialize=ata.to_account_info().data_len()==0;
// layout-pad(2): aligns the next Source site with the original line


  require!(!needs_initialize||initialize_ata,PumpError::UnableToDistributeCreatorFeesToUninitializedAccount);
  transfers.push((amount,needs_initialize));
 }
 Ok((transfers,source_amount))
}
// layout-pad(24): aligns the next Source site with the original line
























pub fn execute_v2<'info>(ctx:Context<'_, '_, '_, 'info,DistributeCreatorFeesV2<'info>>,initialize_ata:bool)->Result<DistributeCreatorFeesEvent>{
 let a=&ctx.accounts;
 require!(matches!(a.sharing_config.status, ConfigStatus::Active),PumpError::SharingConfigNotActive);
// layout-pad(6): aligns the next Source site with the original line






 require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);
 let native=a.bonding_curve.quote_mint==Pubkey::default();
 if native{
  let rent=Rent::get()?;
  let (transfers,minimum_distributable,minimum_vault_balance,available)=get_distribution_amounts(&rent,&a.sharing_config.shareholders,ctx.remaining_accounts,&a.creator_vault)?;
  if available<minimum_distributable{
   msg!("Insufficient fees for distribution. Minimum vault balance needed: {} lamports. Use get_minimum_distributable_fee instruction to check the minimum distributable amount.",minimum_vault_balance);
   return Ok(DistributeCreatorFeesEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),sharing_config:a.sharing_config.key(),admin:a.sharing_config.admin,shareholders:a.sharing_config.shareholders.to_vec(),distributed:0,quote_mint:Pubkey::default()});
  }
  let distributed=super::distribute_native(&a.sharing_config,&a.creator_vault.to_account_info(),&a.system_program,ctx.remaining_accounts,&transfers,ctx.bumps.creator_vault)?;
  let event=DistributeCreatorFeesEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),sharing_config:a.sharing_config.key(),admin:a.sharing_config.admin,shareholders:a.sharing_config.shareholders.to_vec(),distributed:distributed,quote_mint:Pubkey::default()};
  emit!(event);
  emit_cpi!(event);
  return Ok(event);
 }
 let data=a.creator_vault_quote_token_account.try_borrow_data()?;
 let source=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut data.as_ref())?;drop(data);
 let (transfers,_source_amount)=get_token_distribution_amounts(&a.sharing_config.shareholders,ctx.remaining_accounts,&source,&a.quote_mint,initialize_ata)?;
 let distributed=distribute_tokens(&a.sharing_config,&a.creator_vault.to_account_info(),&a.creator_vault_quote_token_account.to_account_info(),&a.system_program,ctx.remaining_accounts,&transfers,ctx.bumps.creator_vault,&a.payer,a.quote_mint.decimals,&a.quote_mint,&a.quote_token_program,&a.associated_token_program)?;
 let event=DistributeCreatorFeesEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),sharing_config:a.sharing_config.key(),admin:a.sharing_config.admin,shareholders:a.sharing_config.shareholders.to_vec(),distributed:distributed,quote_mint:a.quote_mint.key()};
 emit!(event);
 emit_cpi!(event);
 Ok(event)
}
// layout-pad(98): aligns the next Source site with the original line

































































































pub fn distribute_tokens<'info>(sharing_config:&Account<'info,super::SharingConfig>,creator_vault:&AccountInfo<'info>,creator_vault_quote_token_account:&AccountInfo<'info>,system_program:&Program<'info,System>,remaining_accounts:&[AccountInfo<'info>],transfers:&[(u64,bool)],creator_vault_bump:u8,payer:&Signer<'info>,decimals:u8,quote_mint:&InterfaceAccount<'info,anchor_spl::token_interface::Mint>,quote_token_program:&Interface<'info,anchor_spl::token_interface::TokenInterface>,associated_token_program:&Program<'info,anchor_spl::associated_token::AssociatedToken>)->Result<u64>{
 let sharing_config_key=sharing_config.key();
 let creator_vault=creator_vault.to_account_info();
 let mut distributed=0u64;
 for (i,_shareholder) in sharing_config.shareholders.iter().enumerate(){
  let recipient=remaining_accounts.get(i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
  let (amount,initialize_ata)=
                     transfers[i];
// layout-pad(3): aligns the next Source site with the original line


  let recipient_ata=remaining_accounts.get(transfers.len()+i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
  if initialize_ata{
   anchor_spl::associated_token::create(CpiContext::new(associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:payer.to_account_info(),associated_token:recipient_ata.clone(),authority:recipient.clone(),mint:quote_mint.to_account_info(),system_program:system_program.to_account_info(),token_program:quote_token_program.to_account_info()}))?;
  }
  crate::collect_v2::transfer_tokens(quote_token_program,creator_vault_quote_token_account,recipient_ata,&creator_vault,decimals,AsRef::<AccountInfo>::as_ref(quote_mint),amount,&[&[b"creator-vault",sharing_config_key.as_ref(),&[creator_vault_bump]]])?;
// layout-pad(27): aligns the next Source site with the original line


























  distributed=distributed.checked_add(amount).ok_or_else(||error!(PumpError::Overflow))?;
 }
 Ok(distributed)
}
