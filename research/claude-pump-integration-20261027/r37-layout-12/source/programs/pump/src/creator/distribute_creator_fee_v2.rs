use anchor_lang::prelude::*;
use crate::{PumpError, trade_types::Shareholder};
use super::{ConfigStatus, DistributeCreatorFeesV2, DistributeCreatorFeesEvent, get_distribution_amounts};

pub fn execute_v2<'info>(ctx:Context<'_, '_, '_, 'info,DistributeCreatorFeesV2<'info>>,initialize_ata:bool)->Result<DistributeCreatorFeesEvent>{
 let a=&ctx.accounts;
 require!(matches!(a.sharing_config.status, ConfigStatus::Active),PumpError::SharingConfigNotActive);
 require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);
 let native=a.bonding_curve.quote_mint==Pubkey::default() || a.bonding_curve.quote_mint==anchor_spl::token::spl_token::native_mint::ID;
 let count=a.sharing_config.shareholders.len();
 let mut distributed=0u64;let bump=[ctx.bumps.creator_vault];let seeds:&[&[u8]]=&[b"creator-vault",a.bonding_curve.creator.as_ref(),&bump];
 let eligible;
 if native{
  let rent=Rent::get()?;
  let (transfers,minimum_distributable,_,available)=get_distribution_amounts(&rent,&a.sharing_config.shareholders,ctx.remaining_accounts,&a.creator_vault)?;
  eligible=available>=minimum_distributable;
  if eligible{distributed=crate::distribution::execute_native_distribution(transfers,ctx.remaining_accounts,&a.creator_vault,&a.system_program,seeds)?;}
 }else{
  let data=a.creator_vault_quote_token_account.try_borrow_data()?;
  let source=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut data.as_ref())?;drop(data);
  let (transfers,_source_amount)=get_token_distribution_amounts(&a.sharing_config.shareholders,ctx.remaining_accounts,&source,&a.quote_mint,initialize_ata)?;
  eligible=true;
  for (i,(amount,needs_initialize)) in transfers.into_iter().enumerate(){
   let recipient=&ctx.remaining_accounts[i];let ata=&ctx.remaining_accounts[count+i];
   if needs_initialize{
    anchor_spl::associated_token::create(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.payer.to_account_info(),associated_token:ata.clone(),authority:recipient.clone(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}))?;
   }
   crate::collect_v2::transfer_tokens(&a.quote_token_program,a.creator_vault_quote_token_account.as_ref(),ata,&a.creator_vault,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),amount,&[seeds])?;
   distributed=distributed.checked_add(amount).ok_or(error!(PumpError::Overflow))?;
  }
 }
 let event=DistributeCreatorFeesEvent{timestamp:Clock::get()?.unix_timestamp,mint:a.mint.key(),bonding_curve:a.bonding_curve.key(),sharing_config:a.sharing_config.key(),admin:a.sharing_config.admin,shareholders:a.sharing_config.shareholders.clone(),distributed,quote_mint:if native{Pubkey::default()}else{a.quote_mint.key()}};if eligible{emit!(event.clone());emit_cpi!(event.clone());}Ok(event)
}

#[inline(never)]
pub fn get_token_distribution_amounts(shares:&[Shareholder],recipients:&[AccountInfo],source:&anchor_spl::token_interface::TokenAccount,quote_mint:&InterfaceAccount<anchor_spl::token_interface::Mint>,initialize_ata:bool)->Result<(Vec<(u64,bool)>,u64)>{
 let source_amount=source.amount;
 let mut transfers=Vec::with_capacity(shares.len());
 for (i,share) in shares.iter().enumerate(){
  let recipient=recipients.get(i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
  let ata=recipients.get(shares.len()+i).ok_or_else(||error!(PumpError::NotEnoughRemainingAccounts))?;
  {
   let quote_mint_info=quote_mint.to_account_info();
   require!(share.address==recipient.key(),PumpError::ShareholdersAndRemainingAccountsMismatch);
   let expected=anchor_spl::associated_token::get_associated_token_address_with_program_id(&share.address,&quote_mint_info.key(),quote_mint_info.owner);
   require!(ata.key()==expected,PumpError::ShareholdersAndRemainingAccountsMismatch);
   if recipient.executable{
    msg!("Unable to distribute to {}. Shareholder is a program account, use pump_fees::update_fee_shares to remove the shareholder from the team",recipient.key().to_string());
    return err!(PumpError::UnableToDistributeCreatorFeesToExecutableRecipient);
   }
  }
  require!(share.share_bps>0,PumpError::InvalidShareBps);
  let amount=source_amount.checked_mul(u64::from(share.share_bps)).ok_or_else(||error!(PumpError::Overflow))?/10000;
  let needs_initialize=ata.to_account_info().data_len()==0;
  require!(!needs_initialize||initialize_ata,PumpError::UnableToDistributeCreatorFeesToUninitializedAccount);
  transfers.push((amount,needs_initialize));
 }
 Ok((transfers,source_amount))
}
