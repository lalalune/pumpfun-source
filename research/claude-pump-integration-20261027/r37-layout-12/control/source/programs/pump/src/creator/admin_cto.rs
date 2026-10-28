use anchor_lang::prelude::*;
use crate::{Global,PumpError,CollectCreatorFeeEvent};
use crate::trade_types::BondingCurve;
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed};
pub const AMM:Pubkey=anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
pub const FEES:Pubkey=crate::distribution::FEES;
#[derive(Clone)]pub struct Amm; impl Id for Amm{fn id()->Pubkey{AMM}}
#[derive(Clone)]pub struct Fees; impl Id for Fees{fn id()->Pubkey{FEES}}
#[derive(Accounts)]
pub struct AdminCto<'info>{
#[account(mut)]
/// CHECK: constrained address or handler validation.
pub admin_set_creator_authority:Signer<'info>,
#[account(has_one=admin_set_creator_authority @ PumpError::NotAuthorized,seeds=[&[103,108,111,98,97,108]],bump)]
/// CHECK: constrained address or handler validation.
pub global:Box<Account<'info,Global>>,
/// CHECK: constrained address or handler validation.
pub mint:UncheckedAccount<'info>,
/// CHECK: constrained address or handler validation.
#[account(mint::token_program=quote_token_program,constraint=quote_mint.key()==bonding_curve.quote_mint||(bonding_curve.quote_mint==Pubkey::default()&&quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID) @ PumpError::MintDoesNotMatchBondingCurve)]
pub quote_mint:Box<InterfaceAccount<'info,anchor_spl::token_interface::Mint>>,
/// CHECK: constrained address or handler validation.
pub quote_token_program:Interface<'info,anchor_spl::token_interface::TokenInterface>,
/// CHECK: constrained address or handler validation.
pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
/// CHECK: constrained address or handler validation.
pub system_program:Program<'info,System>,
#[account(mut,seeds=[&[98,111,110,100,105,110,103,45,99,117,114,118,101],mint.key().as_ref()],bump)]
/// CHECK: constrained address or handler validation.
pub bonding_curve:Box<Account<'info,BondingCurve>>,
#[account(address=bonding_curve.creator @ PumpError::InvalidCreator)]
/// CHECK: constrained address or handler validation.
pub current_creator:AccountInfo<'info>,
#[account(mut,seeds=[current_creator.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]
/// CHECK: constrained address or handler validation.
pub current_creator_quote_token_account:UncheckedAccount<'info>,
#[account(mut,seeds=[&[99,114,101,97,116,111,114,45,118,97,117,108,116],current_creator.key().as_ref()],bump)]
/// CHECK: constrained address or handler validation.
pub creator_vault:AccountInfo<'info>,
#[account(mut,seeds=[creator_vault.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]
/// CHECK: constrained address or handler validation.
pub creator_vault_quote_token_account:UncheckedAccount<'info>,
#[account(mut)]
/// CHECK: constrained address or handler validation.
pub holder_creator_vault:AccountInfo<'info>,
#[account(mut,seeds=[holder_creator_vault.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]
/// CHECK: constrained address or handler validation.
pub holder_creator_vault_quote_token_account:UncheckedAccount<'info>,
/// CHECK: constrained address or handler validation.
pub pump_amm:Program<'info,Amm>,
#[account(seeds=[&[103,108,111,98,97,108,95,99,111,110,102,105,103]],bump,seeds::program=pump_amm.key())]
/// CHECK: constrained address or handler validation.
pub amm_global_config:UncheckedAccount<'info>,
#[account(seeds=[&[112,111,111,108,45,97,117,116,104,111,114,105,116,121],mint.key().as_ref()],bump)]
/// CHECK: constrained address or handler validation.
pub pool_authority:UncheckedAccount<'info>,
#[account(mut,seeds=[&[112,111,111,108],&0u16.to_le_bytes(),pool_authority.key().as_ref(),mint.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=pump_amm.key())]
/// CHECK: constrained address or handler validation.
pub pool:UncheckedAccount<'info>,
#[account(seeds=[&[95,95,101,118,101,110,116,95,97,117,116,104,111,114,105,116,121]],bump,seeds::program=pump_amm.key())]
/// CHECK: constrained address or handler validation.
pub pump_amm_event_authority:UncheckedAccount<'info>,
#[account(mut,seeds=[&[99,114,101,97,116,111,114,95,118,97,117,108,116],current_creator.key().as_ref()],bump,seeds::program=pump_amm.key())]
/// CHECK: constrained address or handler validation.
pub coin_creator_vault_authority:UncheckedAccount<'info>,
#[account(mut,seeds=[coin_creator_vault_authority.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]
/// CHECK: constrained address or handler validation.
pub coin_creator_vault_ata:UncheckedAccount<'info>,
#[account(mut,seeds=[&[115,104,97,114,105,110,103,45,99,111,110,102,105,103],mint.key().as_ref()],bump,seeds::program=pump_fees.key())]
/// CHECK: constrained address or handler validation.
pub sharing_config:UncheckedAccount<'info>,
/// CHECK: constrained address or handler validation.
pub pump_fees:Program<'info,Fees>,
#[account(seeds=[&[95,95,101,118,101,110,116,95,97,117,116,104,111,114,105,116,121]],bump,seeds::program=pump_fees.key())]
/// CHECK: constrained address or handler validation.
pub pump_fees_event_authority:UncheckedAccount<'info>,
#[account(seeds=[&[95,95,101,118,101,110,116,95,97,117,116,104,111,114,105,116,121]],bump)]
/// CHECK: constrained address or handler validation.
pub event_authority:AccountInfo<'info>,
/// CHECK: constrained address or handler validation.
pub program:AccountInfo<'info>,
}
#[event]
#[derive(Clone)]
pub struct AdminCtoEvent{
pub timestamp:i64,
pub authority:Pubkey,
pub mint:Pubkey,
pub bonding_curve:Pubkey,
pub old_creator:Pubkey,
pub new_creator:Pubkey,
pub is_holder_reward:bool,
pub is_cashback_coin:bool,
pub old_creator_fee_bps:u64,
pub new_creator_fee_bps:u64,
pub sharing_config_reset:bool,
pub swept_to_holder_vault:u64,
pub pool_updated:bool,
}
pub fn execute(ctx:Context<AdminCto>,holder:Option<bool>,fee:Option<u64>,new:Option<Pubkey>)->Result<()>{
 let a=&ctx.accounts;let old_fee=a.bonding_curve.creator_fee_bps;
 if a.bonding_curve.is_mayhem_mode{return Err(error!(PumpError::CtoNotAllowedForMayhemCoin));}if a.bonding_curve.is_holder_reward&&holder!=Some(true){return Err(error!(PumpError::HolderRewardCreatorImmutable));}
 if holder==Some(true)&&!a.bonding_curve.is_holder_reward&&!a.global.is_holder_reward_enabled{return Err(error!(PumpError::HolderRewardDisabled));}
 let holder=holder.unwrap_or(false);let cashback=!holder&&a.bonding_curve.is_cashback_coin;let old=a.current_creator.key();let mint=a.mint.key();let (holder_key,_)=Pubkey::find_program_address(&[b"holder-rewards",mint.as_ref()],&crate::ID);
 if holder && new.is_some(){return Err(error!(PumpError::CtoNewCreatorNotAllowed));}if !holder && new.is_none(){return Err(error!(PumpError::CtoNewCreatorRequired));}
 let mut target=if holder{holder_key}else{new.unwrap()};if target==Pubkey::default(){return Err(error!(PumpError::CreatorShouldNotBeZero).with_pubkeys((target,Pubkey::default())));}if !holder && (target==holder_key||target==a.sharing_config.key()){return Err(error!(PumpError::InvalidCreator));}
 if fee.is_some()&&(a.bonding_curve.quote_mint==Pubkey::default()||a.bonding_curve.quote_mint==anchor_spl::token::spl_token::native_mint::ID||a.global.whitelisted_quote_mints.contains(&a.bonding_curve.quote_mint)){return Err(error!(PumpError::CreatorFeeNotConfigurableForQuote));}
 if fee.is_some()&&cashback{return Err(error!(PumpError::CreatorFeeNotAllowedForCashbackCoin));}
 if fee.is_some()&&!a.global.creator_fee_configurable{return Err(error!(PumpError::CreatorFeeNotConfigurable));}
 if let Some(f)=fee{if f==0||f>a.global.max_configurable_creator_fee_bps{return Err(error!(PumpError::CreatorFeeBpsOutOfRange));}}
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.admin_set_creator_authority)?;
 require!(a.bonding_curve.creator_fee==0,PumpError::CreatorFeesNotSwept);
 let shared=a.sharing_config.owner==&FEES && !a.sharing_config.data_is_empty() && old==a.sharing_config.key();
 let shared_amm_frozen=shared&&holder&&!a.coin_creator_vault_ata.data_is_empty()&&token_frozen(&a.coin_creator_vault_ata.to_account_info())?;
 if shared_amm_frozen{require!(token_raw_amount(&a.coin_creator_vault_ata.to_account_info())?==0,PumpError::CtoSharedVaultFrozen);}
 if shared&&holder&&!shared_amm_frozen&&!a.coin_creator_vault_ata.data_is_empty(){invoke_signed(&Instruction{program_id:AMM,accounts:vec![AccountMeta::new(a.admin_set_creator_authority.key(),true),AccountMeta::new_readonly(a.quote_mint.key(),false),AccountMeta::new_readonly(a.quote_token_program.key(),false),AccountMeta::new_readonly(a.system_program.key(),false),AccountMeta::new_readonly(a.associated_token_program.key(),false),AccountMeta::new_readonly(a.current_creator.key(),false),AccountMeta::new(a.coin_creator_vault_authority.key(),false),AccountMeta::new(a.coin_creator_vault_ata.key(),false),AccountMeta::new(a.creator_vault.key(),false),AccountMeta::new(a.creator_vault_quote_token_account.key(),false),AccountMeta::new_readonly(a.pump_amm_event_authority.key(),false),AccountMeta::new_readonly(a.pump_amm.key(),false)],data:vec![1,33,78,185,33,67,44,92]},&[a.admin_set_creator_authority.to_account_info(),a.quote_mint.to_account_info(),a.quote_token_program.to_account_info(),a.system_program.to_account_info(),a.associated_token_program.to_account_info(),a.current_creator.to_account_info(),a.coin_creator_vault_authority.to_account_info(),a.coin_creator_vault_ata.to_account_info(),a.creator_vault.to_account_info(),a.creator_vault_quote_token_account.to_account_info(),a.pump_amm_event_authority.to_account_info(),a.pump_amm.to_account_info()],&[])?;}
 let wallet=old!=Pubkey::default()&&!a.current_creator.executable&&a.current_creator.owner==&anchor_lang::system_program::ID;if wallet&&!a.current_creator.is_writable{return Err(error!(PumpError::CtoCreatorAccountNotWritable));}let wallet_frozen=wallet&&!a.current_creator_quote_token_account.data_is_empty()&&token_frozen(&a.current_creator_quote_token_account.to_account_info())?;
 let native=a.bonding_curve.quote_mint==Pubkey::default();let rent=Rent::get()?.minimum_balance(0);let amount=if !(shared&&holder)&&(!wallet||wallet_frozen){0}else if native{a.creator_vault.lamports().saturating_sub(rent)}else if shared&&holder&&!a.creator_vault_quote_token_account.data_is_empty(){let amount=token_raw_amount(&a.creator_vault_quote_token_account.to_account_info())?;let frozen=token_frozen(&a.creator_vault_quote_token_account.to_account_info())?;require!(!frozen||amount==0,PumpError::CtoSharedVaultFrozen);amount}else{0};let bump=[ctx.bumps.creator_vault];let vaultseeds:&[&[u8]]=&[b"creator-vault",old.as_ref(),&bump];let mut swept=0;
 if shared && holder && amount>0{
  let dest=Pubkey::find_program_address(&[b"creator-vault",holder_key.as_ref()],&crate::ID).0;if a.holder_creator_vault.key()!=dest{return Err(error!(anchor_lang::error::ErrorCode::ConstraintSeeds).with_pubkeys((a.holder_creator_vault.key(),dest)));}
  if native{crate::legacy_buy::native_payments::ensure_rent_exempt(&a.system_program,&a.admin_set_creator_authority,&a.holder_creator_vault)?;
  crate::collect_v2::transfer_native(a.system_program.as_ref(),&a.creator_vault,&a.holder_creator_vault,amount,&[vaultseeds])?;}else{pay_token(a,&a.holder_creator_vault.to_account_info(),&a.holder_creator_vault_quote_token_account.to_account_info(),amount,vaultseeds)?;}swept=amount;
 }
 if wallet&&!wallet_frozen{
  let collection_native=a.quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID;
  let source_present=!a.creator_vault_quote_token_account.data_is_empty();
  let source_frozen=!collection_native&&source_present&&token_frozen(a.creator_vault_quote_token_account.as_ref())?;
  if collection_native||source_present||a.coin_creator_vault_ata.data_is_empty(){
   if !collection_native{anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.current_creator_quote_token_account.to_account_info(),authority:a.current_creator.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}))?;}
   if collection_native||(source_present&&!source_frozen){
    if let Some((collected,quote_mint))=crate::collect_v2::collect(&a.current_creator,a.current_creator_quote_token_account.as_ref(),&a.creator_vault,ctx.bumps.creator_vault,a.creator_vault_quote_token_account.as_ref(),a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),&a.quote_token_program,&a.system_program)?{
     let e=CollectCreatorFeeEvent{timestamp:Clock::get()?.unix_timestamp,creator:old,creator_fee:collected,quote_mint};emit!(e.clone());emit_cpi!(e);
    }
   }
  }
 }
 if wallet&&!wallet_frozen&&!a.coin_creator_vault_ata.data_is_empty(){
  let frozen=token_frozen(&a.coin_creator_vault_ata.to_account_info())?;anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:a.current_creator_quote_token_account.to_account_info(),authority:a.current_creator.to_account_info(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}))?;
  let accounts=vec![AccountMeta::new_readonly(a.quote_mint.key(),false),AccountMeta::new_readonly(a.quote_token_program.key(),false),AccountMeta::new_readonly(old,false),AccountMeta::new_readonly(a.coin_creator_vault_authority.key(),false),AccountMeta::new(a.coin_creator_vault_ata.key(),false),AccountMeta::new(a.current_creator_quote_token_account.key(),false),AccountMeta::new_readonly(a.pump_amm_event_authority.key(),false),AccountMeta::new_readonly(AMM,false)];
  if !frozen{invoke_signed(&Instruction{program_id:AMM,accounts,data:vec![160,57,89,42,181,139,43,66]},&[a.quote_mint.to_account_info(),a.quote_token_program.to_account_info(),a.current_creator.to_account_info(),a.coin_creator_vault_authority.to_account_info(),a.coin_creator_vault_ata.to_account_info(),a.current_creator_quote_token_account.to_account_info(),a.pump_amm_event_authority.to_account_info(),a.pump_amm.to_account_info()],&[])?;}
 }
 let pb=[ctx.bumps.pool_authority];let poolseeds:&[&[u8]]=&[b"pool-authority",mint.as_ref(),&pb];
 if shared{
  let mut data=vec![60,100,144,156,64,138,182,37];let val=if holder{None}else{new};val.serialize(&mut data)?;
  let accounts=vec![AccountMeta::new_readonly(a.pool_authority.key(),true),AccountMeta::new_readonly(a.admin_set_creator_authority.key(),true),AccountMeta::new_readonly(a.global.key(),false),AccountMeta::new_readonly(mint,false),AccountMeta::new(a.sharing_config.key(),false),AccountMeta::new_readonly(a.pump_fees_event_authority.key(),false),AccountMeta::new_readonly(FEES,false)];
  invoke_signed(&Instruction{program_id:FEES,accounts,data},&[a.pool_authority.to_account_info(),a.admin_set_creator_authority.to_account_info(),a.global.to_account_info(),a.mint.to_account_info(),a.sharing_config.to_account_info(),a.pump_fees_event_authority.to_account_info(),a.pump_fees.to_account_info()],&[poolseeds])?;
  if !holder{target=old;}
 }
 {
  let curve=&mut ctx.accounts.bonding_curve;
  curve.creator=target;
  curve.is_holder_reward=holder;
  curve.is_cashback_coin=cashback;
  if let Some(f)=fee{curve.creator_fee_bps=f;}
  curve.can_edit_creator_fee=false;
 }
 let a=&ctx.accounts;
 let pool_updated=a.pool.owner==&AMM && !a.pool.data_is_empty();
 if pool_updated{
  let mut data=vec![45,61,165,151,104,0,49,189];target.serialize(&mut data)?;holder.serialize(&mut data)?;fee.serialize(&mut data)?;
  let accounts=vec![AccountMeta::new(a.admin_set_creator_authority.key(),true),AccountMeta::new_readonly(a.amm_global_config.key(),false),AccountMeta::new(a.pool.key(),false),AccountMeta::new_readonly(a.pool_authority.key(),true),AccountMeta::new_readonly(a.system_program.key(),false),AccountMeta::new_readonly(a.pump_amm_event_authority.key(),false),AccountMeta::new_readonly(AMM,false)];
  invoke_signed(&Instruction{program_id:AMM,accounts,data},&[a.admin_set_creator_authority.to_account_info(),a.amm_global_config.to_account_info(),a.pool.to_account_info(),a.pool_authority.to_account_info(),a.system_program.to_account_info(),a.pump_amm_event_authority.to_account_info(),a.pump_amm.to_account_info()],&[poolseeds])?;
 }
 let e=AdminCtoEvent{timestamp:Clock::get()?.unix_timestamp,authority:a.admin_set_creator_authority.key(),mint,bonding_curve:a.bonding_curve.key(),old_creator:old,new_creator:target,is_holder_reward:holder,is_cashback_coin:cashback,old_creator_fee_bps:old_fee,new_creator_fee_bps:fee.unwrap_or(old_fee),sharing_config_reset:shared,swept_to_holder_vault:swept,pool_updated};emit!(e.clone());emit_cpi!(e);Ok(())
}

fn token_frozen(a:&AccountInfo)->Result<bool>{if a.data_is_empty(){return Ok(false);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.is_frozen())}
#[inline(never)]fn pay_token<'info>(a:&AdminCto<'info>,owner:&AccountInfo<'info>,to:&AccountInfo<'info>,amount:u64,seeds:&[&[u8]])->Result<()>{
 anchor_spl::associated_token::create_idempotent(CpiContext::new(a.associated_token_program.to_account_info(),anchor_spl::associated_token::Create{payer:a.admin_set_creator_authority.to_account_info(),associated_token:to.clone(),authority:owner.clone(),mint:a.quote_mint.to_account_info(),system_program:a.system_program.to_account_info(),token_program:a.quote_token_program.to_account_info()}))?;
 if amount>0{anchor_spl::token_interface::transfer_checked(CpiContext::new_with_signer(a.quote_token_program.to_account_info(),anchor_spl::token_interface::TransferChecked{from:a.creator_vault_quote_token_account.to_account_info(),mint:a.quote_mint.to_account_info(),to:to.clone(),authority:a.creator_vault.to_account_info()},&[seeds]),amount,a.quote_mint.decimals)?;}Ok(())}

fn token_raw_amount(a:&AccountInfo)->Result<u64>{if a.data_is_empty(){return Ok(0);}let d=a.try_borrow_data()?;let t=anchor_spl::token_interface::TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.amount)}
