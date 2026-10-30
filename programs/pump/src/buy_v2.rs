use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,Mint,TokenAccount,TokenInterface,TransferChecked};
use crate::{Global,PumpError};
use crate::trade_types::{TradeEvent,BondingCurve};
use crate::legacy_sell::{LegacyFeeConfig,LegacyFeesProgram};
const FEE_PROGRAM:Pubkey=anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
const WSOL:Pubkey=anchor_lang::solana_program::pubkey!("So11111111111111111111111111111111111111112");
// Shared main-program admission for an ATA, including the optional idempotent creation.
#[inline(never)]
pub fn admit_associated_token_account<'info>(account:&AccountInfo<'info>,authority:&AccountInfo<'info>,mint:Pubkey,token_program:Pubkey,mint_info:&AccountInfo<'info>,token_program_info:&AccountInfo<'info>,allow_create:bool,payer:*const AccountInfo<'info>,system_program:&AccountInfo<'info>)->Result<()>{
 let expected=anchor_spl::associated_token::get_associated_token_address_with_program_id(&authority.key(),&mint,&token_program);
// layout-pad(43): aligns the next Source site with the original line










































 require_keys_eq!(account.key(),expected,anchor_lang::error::ErrorCode::ConstraintSeeds);
// layout-pad(3): aligns the next Source site with the original line


 let needs_create=account.owner==&anchor_lang::system_program::ID; if needs_create {
  require!(allow_create,anchor_lang::error::ErrorCode::AccountNotInitialized);
  let payer=unsafe{&*payer}; let instruction=anchor_spl::associated_token::spl_associated_token_account::instruction::create_associated_token_account_idempotent(&payer.key(),&authority.key(),&mint,&token_program);
  let account_infos=[payer.clone(),account.clone(),authority.clone(),mint_info.clone(),system_program.clone(),token_program_info.clone()];
  anchor_lang::solana_program::program::invoke(&instruction,&account_infos)?;
 }
// layout-pad(16): aligns the next Source site with the original line















 require_keys_eq!(*account.owner,token_program,PumpError::AccountTypeNotSupported);
 let data=account.try_borrow_data()?;
 let token=TokenAccount::try_deserialize_unchecked(&mut &data[..])?;
// layout-pad(4): aligns the next Source site with the original line



 require_keys_eq!(token.mint,mint,PumpError::MintDoesNotMatchBondingCurve);
 Ok(())
}
// layout-pad(14): aligns the next Source site with the original line













// Existing token-account admission: owner program, mint, authority.
#[inline(never)]
pub fn check_token_account<'info>(account:&AccountInfo<'info>,authority:&AccountInfo<'info>,mint:Pubkey,token_program:Pubkey)->Result<()>{

 require_keys_eq!(*account.owner,token_program,PumpError::AccountTypeNotSupported);
 let data=account.try_borrow_data()?;
 let mut slice:&[u8]=&data;let token=TokenAccount::try_deserialize_unchecked(&mut slice)?;




 require_keys_eq!(token.mint,mint,PumpError::MintDoesNotMatchBondingCurve);




 require_keys_eq!(token.owner,authority.key(),PumpError::AccountTypeNotSupported);
 Ok(())
}





#[derive(Accounts)]
pub struct BuyV2<'info>{
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,
 pub base_mint:Box<InterfaceAccount<'info,Mint>>,
 pub quote_mint:Box<InterfaceAccount<'info,Mint>>,
 pub base_token_program:Interface<'info,TokenInterface>,
 pub quote_token_program:Interface<'info,TokenInterface>,
 pub associated_token_program:Program<'info,anchor_spl::associated_token::AssociatedToken>,
 /// CHECK: handler checks membership.
 #[account(mut)]pub fee_recipient:UncheckedAccount<'info>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[fee_recipient.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_quote_fee_recipient:UncheckedAccount<'info>,
 /// CHECK: handler checks membership.
 #[account(mut)]pub buyback_fee_recipient:UncheckedAccount<'info>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[buyback_fee_recipient.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_quote_buyback_fee_recipient:UncheckedAccount<'info>,
 #[account(mut,seeds=[b"bonding-curve",base_mint.key().as_ref()],bump,constraint=quote_mint.key()==bonding_curve.quote_mint || (bonding_curve.quote_mint==Pubkey::default() && quote_mint.key()==WSOL) @ PumpError::MintDoesNotMatchBondingCurve)]pub bonding_curve:Box<Account<'info,BondingCurve>>,
 #[account(mut,associated_token::mint=base_mint,associated_token::authority=bonding_curve,associated_token::token_program=base_token_program)]pub associated_base_bonding_curve:Box<InterfaceAccount<'info,TokenAccount>>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[bonding_curve.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_quote_bonding_curve:UncheckedAccount<'info>,
 #[account(mut)]pub user:Signer<'info>,
 #[account(mut,token::mint=base_mint)]pub associated_base_user:Box<InterfaceAccount<'info,TokenAccount>>,
 /// CHECK: quote ATA.
 #[account(mut)]pub associated_quote_user:UncheckedAccount<'info>,
 /// CHECK: PDA.
 #[account(mut,seeds=[b"creator-vault",bonding_curve.creator.as_ref()],bump)]pub creator_vault:AccountInfo<'info>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[creator_vault.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_creator_vault:UncheckedAccount<'info>,
 /// CHECK: sharing validation later.
 #[account(seeds=[b"sharing-config",base_mint.key().as_ref()],bump,seeds::program=FEE_PROGRAM)]pub sharing_config:UncheckedAccount<'info>,
 #[account(seeds=[b"global_volume_accumulator"],bump)]pub global_volume_accumulator:Box<Account<'info,crate::GlobalVolumeAccumulator>>,
 /// CHECK: volume state validated when used.
 #[account(init_if_needed,payer=user,space=137,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]pub user_volume_accumulator:Box<Account<'info,crate::UserVolumeAccumulator>>,
 /// CHECK: quote ATA.
 #[account(mut,seeds=[user_volume_accumulator.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]pub associated_user_volume_accumulator:UncheckedAccount<'info>,
 #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump,seeds::program=fee_program.key())]pub fee_config:Account<'info,LegacyFeeConfig>,
 pub fee_program:Program<'info,LegacyFeesProgram>,
 pub system_program:Program<'info,System>,
 /// CHECK: event PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:AccountInfo<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
}
fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}
fn sub(a:u64,b:u64)->Result<u64>{a.checked_sub(b).ok_or_else(||error!(PumpError::Overflow))}
fn narrow(a:u128)->Result<u64>{u64::try_from(a).map_err(|_|error!(PumpError::Truncation))}
#[inline(always)]
pub fn execute<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,input:u64,limit:u64,partial:bool,exact:bool)->Result<()>{
 if exact{buy_exact_quote_in_handler(ctx,input,limit,partial)}else{buy_handler(ctx,input,limit,partial)}
}
#[inline(never)]
fn buy_handler<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,mut input:u64,limit:u64,partial:bool)->Result<()>{
 let a=&mut *ctx.accounts;let fee_recipient=&a.fee_recipient;let buyback_fee_recipient=&a.buyback_fee_recipient;let (base_token_program,base_mint)=(&a.base_token_program,&a.base_mint);
// layout-pad(164): aligns the next Source site with the original line



































































































































































 require!(!a.bonding_curve.complete,PumpError::BondingCurveComplete);
 if partial{input=input.min(a.bonding_curve.real_token_reserves);}
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
 require_gt!(input,0,PumpError::BuyZeroAmount);
// layout-pad
 require_gte!(a.bonding_curve.real_token_reserves,input,PumpError::NotEnoughTokensToBuy);
 crate::legacy_sell::fee_recipient::validate_fee_recipient(&a.fee_recipient,&a.global,&a.bonding_curve)?;
 a.global.validate_buyback_fee_recipient(&a.buyback_fee_recipient.key())?;
 const NO_FEE:Option<crate::trade::native_transfer_fee::Fee>=None;let native=a.bonding_curve.quote_mint==Pubkey::default();
 if !native{
  let quote_mint=a.quote_mint.key();let quote_token_program=a.quote_token_program.key();
  {let mint_info=a.quote_mint.to_account_info();let token_program_info=a.quote_token_program.to_account_info();
  admit_associated_token_account(&a.associated_quote_bonding_curve,&a.bonding_curve.to_account_info(),quote_mint,quote_token_program,&mint_info,&token_program_info,false,a.user.as_ref(),&a.system_program)?;
  check_token_account(&a.associated_quote_user,&a.user,quote_mint,quote_token_program)?;
  admit_associated_token_account(&a.associated_creator_vault,&a.creator_vault,quote_mint,quote_token_program,&mint_info,&token_program_info,true,a.user.as_ref(),&a.system_program)?;
  admit_associated_token_account(&a.associated_user_volume_accumulator,&a.user_volume_accumulator.to_account_info(),quote_mint,quote_token_program,&mint_info,&token_program_info,true,a.user.as_ref(),&a.system_program)?;
  admit_associated_token_account(&a.associated_quote_fee_recipient,&a.fee_recipient.to_account_info(),quote_mint,quote_token_program,&mint_info,&token_program_info,true,a.user.as_ref(),&a.system_program)?;admit_associated_token_account(&a.associated_quote_buyback_fee_recipient,&a.buyback_fee_recipient.to_account_info(),quote_mint,quote_token_program,&mint_info,&token_program_info,true,a.user.as_ref(),&a.system_program)?;}
  }let fee=if !native{crate::transfer_fee_recovered::get_transfer_fee(&a.quote_mint.to_account_info())?
 }else{require!(a.quote_mint.key()==WSOL,PumpError::UnsupportedQuoteMint);NO_FEE};
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
 let quote=u64::try_from(crate::buy_quote(&a.bonding_curve,input)?).map_err(|_|error!(PumpError::Truncation))?;
 let gross=crate::transfer_fee_recovered::pre_fee_amount(&fee,quote)?;
// layout-pad
// layout-pad
 let quote_transfer_fee=gross.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;
 let whitelisted=a.global.whitelist_pda==a.user.key();let (pf,cf,protocol_fee_bps,creator_fee_bps)=if whitelisted{Ok((0,0,0,0))}else{crate::legacy_sell::fee_cpi::trade_fees(
  &a.global,&a.bonding_curve,&a.base_mint,&a.fee_config,&a.fee_program,a.program.as_ref(),quote
 )}?;
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
 require_gte!(limit,gross.checked_add(pf)
// layout-pad
// layout-pad
// layout-pad
  .ok_or_else(||error!(PumpError::Overflow))?
  .checked_add(cf)
  .ok_or_else(||error!(PumpError::Overflow))?,PumpError::TooMuchSolRequired);
 a.bonding_curve.apply_buy(input,quote)?;
// layout-pad
  move_curve_tokens(base_token_program,&a.associated_base_bonding_curve,&a.associated_base_user,&a.bonding_curve,base_mint,input,&[&[b"bonding-curve",base_mint.key().as_ref(),&[ctx.bumps.bonding_curve]]])?;
  if a.user.key()==a.global.whitelist_pda{a.associated_base_bonding_curve.reload()?;a.associated_base_user.reload()?;let quote_mint=a.bonding_curve.quote_mint;a.bonding_curve.sync_virtual_quote_reserves(a.associated_base_bonding_curve.amount,a.associated_base_user.amount,&quote_mint)?;}
  if a.user_volume_accumulator.user==Pubkey::default(){a.user_volume_accumulator.user=a.user.key();}
 let system_program=&a.system_program;
 if cf>0{
   if !a.bonding_curve.is_cashback_coin{
    native_payments::ensure_rent_exempt(0,&a.system_program,&a.user,&a.creator_vault)?;
    pay_from_user_owned(native,system_program,&a.user,a.creator_vault.to_account_info(),cf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_creator_vault.as_ref())})?;
   }else{
    pay_from_user_owned(native,system_program,&a.user,a.user_volume_accumulator.to_account_info(),cf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_user_volume_accumulator.as_ref())})?;
    crate::token_incentives::volume_accumulator::record_cashback_earned(&mut a.user_volume_accumulator,cf,native)?;
   }
  }
  pay_from_user(native,system_program,&a.user,a.bonding_curve.as_ref(),gross,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())})?;
  let (bf,protocol_fee)=recipient_payments::split_protocol_fee(&a.global,pf,a.bonding_curve.is_mayhem_mode);
  pay_from_user_recipient(native,system_program,&a.user,&fee_recipient,protocol_fee,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_quote_fee_recipient.as_ref())})?;
  pay_from_user_recipient(native,system_program,&a.user,&buyback_fee_recipient,bf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_quote_buyback_fee_recipient.as_ref())})?;
 let c=&a.bonding_curve;let virtual_token_reserves=c.virtual_token_reserves;let virtual_quote_reserves=c.virtual_quote_reserves;let real_token_reserves=c.real_token_reserves;let real_quote_reserves=c.real_quote_reserves;
 let creator=c.creator;let mut quote_mint=Pubkey::default();snapshot_quote_mint(&c.quote_mint,&mut quote_mint);let timestamp=Clock::get()?.unix_timestamp;
 let uva=&a.user_volume_accumulator;let total_unclaimed_tokens=uva.total_unclaimed_tokens;let total_claimed_tokens=uva.total_claimed_tokens;let current_sol_volume=uva.current_sol_volume;let last_update_timestamp=uva.last_update_timestamp;let shareholders=crate::distribution::sharing_config_shareholders(&a.sharing_config.to_account_info())?.unwrap_or_default();
 let c=&a.bonding_curve;let is_sol=quote_mint==Pubkey::default();
  let ev=TradeEvent{user:a.user.key(),mint:a.base_mint.key(),sol_amount:if is_sol{quote}else{0},token_amount:input,is_buy:true,timestamp,real_sol_reserves:if is_sol{real_quote_reserves}else{0},virtual_token_reserves,virtual_sol_reserves:if is_sol{virtual_quote_reserves}else{0},real_token_reserves,fee_recipient:a.fee_recipient.key(),fee_basis_points:protocol_fee_bps,fee:pf,creator,creator_fee_basis_points:if c.is_cashback_coin{0}else{creator_fee_bps},creator_fee:if c.is_cashback_coin{0}else{cf},holder_rewards_bps:if c.is_holder_reward{creator_fee_bps}else{0},holder_rewards:if c.is_holder_reward{cf}else{0},track_volume:false,total_unclaimed_tokens,total_claimed_tokens,current_sol_volume,last_update_timestamp,ix_name:"buy".to_string(),mayhem_mode:c.is_mayhem_mode,cashback_fee_basis_points:if c.is_cashback_coin{creator_fee_bps}else{0},cashback:if c.is_cashback_coin{cf}else{0},buyback_fee:crate::transfer_fee_recovered::post_fee_amount(&fee,bf)?,buyback_fee_basis_points:if c.is_mayhem_mode{0}else{a.global.buyback_basis_points},shareholders,quote_mint:c.quote_mint,quote_amount:quote,virtual_quote_reserves,real_quote_reserves,creator_fee_unclaimed:c.creator_fee,unparsed_trailing_field:quote_transfer_fee};
  emit!(ev);emit_cpi!(ev);
  complete_and_prepare(ctx,timestamp)?;



Ok(())
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
}
#[inline(never)]
fn buy_exact_quote_in_handler<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,input:u64,limit:u64,partial:bool)->Result<()>{
 let a=&mut *ctx.accounts;let fee_recipient=&a.fee_recipient;let buyback_fee_recipient=&a.buyback_fee_recipient;let (base_token_program,base_mint)=(&a.base_token_program,&a.base_mint);
// layout-pad(220): aligns the next Source site with the original line



























































































































































































































 require!(!a.bonding_curve.complete,PumpError::BondingCurveComplete);
// layout-pad(1): aligns the next Source site with the original line
 require_gt!(limit,0,PumpError::BuyZeroAmount);

 require_gt!(input,0,PumpError::BuyNotEnoughSolToCoverFees); crate::legacy_sell::fee_recipient::validate_fee_recipient(fee_recipient,&a.global,&a.bonding_curve)?;
 a.global.validate_buyback_fee_recipient(&buyback_fee_recipient.key())?;
 const NO_FEE:Option<crate::trade::native_transfer_fee::Fee>=None;let native=a.bonding_curve.quote_mint==Pubkey::default();
 if !native{
  {let quote_mint=a.quote_mint.key();let quote_token_program=a.quote_token_program.key();let mint_info=a.quote_mint.to_account_info();let token_program_info=a.quote_token_program.to_account_info();
  admit_associated_token_account(a.associated_quote_bonding_curve.as_ref(),&a.bonding_curve.to_account_info(),quote_mint,quote_token_program,&mint_info,&token_program_info,false,a.user.as_ref(),a.system_program.as_ref())?;check_token_account(&a.associated_quote_user,a.user.as_ref(),quote_mint,quote_token_program)?;
  admit_associated_token_account(a.associated_creator_vault.as_ref(),&a.creator_vault,quote_mint,quote_token_program,&mint_info,&token_program_info,true,a.user.as_ref(),a.system_program.as_ref())?;admit_associated_token_account(a.associated_user_volume_accumulator.as_ref(),&a.user_volume_accumulator.to_account_info(),quote_mint,quote_token_program,&mint_info,&token_program_info,true,a.user.as_ref(),a.system_program.as_ref())?;
  admit_associated_token_account(a.associated_quote_fee_recipient.as_ref(),&fee_recipient.to_account_info(),quote_mint,quote_token_program,&mint_info,&token_program_info,true,a.user.as_ref(),a.system_program.as_ref())?;admit_associated_token_account(a.associated_quote_buyback_fee_recipient.as_ref(),&buyback_fee_recipient.to_account_info(),quote_mint,quote_token_program,&mint_info,&token_program_info,true,a.user.as_ref(),a.system_program.as_ref())?;
  }}let transfer_fee=if !native{crate::transfer_fee_recovered::get_transfer_fee(&a.quote_mint.to_account_info())?
 }else{require!(a.quote_mint.key()==WSOL,PumpError::UnsupportedQuoteMint);NO_FEE};






 let c=&a.bonding_curve;
 let available=crate::transfer_fee_recovered::post_fee_amount(&transfer_fee,input)?;
// layout-pad(84): aligns the next Source site with the original line



















































































 require_gt!(available,0,PumpError::BuyNotEnoughSolToCoverFees);
 let (quote,pf,cf,computed,protocol_fee_bps,creator_fee_bps)=if a.global.whitelist_pda==a.user.key(){






  let computed=u64::try_from(crate::constant_product::tokens_for_quote(c,available)?).map_err(|_|error!(PumpError::Truncation))?;(available,0,0,computed,0,0)
 }else{
  let (_,_,protocol_fee_bps,creator_fee_bps)=crate::legacy_sell::fee_cpi::trade_fees(&a.global,&a.bonding_curve,&a.base_mint,&a.fee_config,&a.fee_program,a.program.as_ref(),available)?;
  let total_bps=protocol_fee_bps.checked_add(if c.creator==Pubkey::default(){0}else{creator_fee_bps}).ok_or(PumpError::Overflow)?;
  let raw_quote=if total_bps==0{available}else{(available as u128*10000/(10000+total_bps as u128)) as u64};





















  require_gt!(raw_quote,0,PumpError::BuyNotEnoughSolToCoverFees);
  let pf=ceil_fee(raw_quote,protocol_fee_bps)?;
  let cf=if c.creator!=Pubkey::default(){ceil_fee(raw_quote,creator_fee_bps)?}else{0};
  let total=raw_quote.saturating_add(pf).saturating_add(cf);
  let mut quote=raw_quote;if total>available{
   quote=raw_quote.checked_sub(total.saturating_sub(available)).ok_or(PumpError::Overflow)?;








   require_gt!(quote,0,PumpError::BuySlippageBelowMinTokensOut);}





  let computed=u64::try_from(crate::constant_product::tokens_for_quote(c,quote)?).map_err(|_|error!(PumpError::Truncation))?;
  (quote,pf,cf,computed,protocol_fee_bps,creator_fee_bps)};




















 let gross_total=|quote:u64,pf:u64,cf:u64|->Result<(u64,u64)>{let gross=crate::transfer_fee_recovered::pre_fee_amount(&transfer_fee,quote)?;Ok((gross,gross.checked_add(pf).and_then(|t|t.checked_add(cf)).ok_or_else(||error!(PumpError::Overflow))?))};
 let (amount,quote,pf,cf,gross_quote)=if computed>c.real_token_reserves && partial{
  let amount=c.real_token_reserves;







  let quote=u64::try_from(crate::buy_quote(c,amount)?).map_err(|_|error!(PumpError::Truncation))?;
  let pf=ceil_fee(quote,protocol_fee_bps)?;
  let cf=if c.creator!=Pubkey::default(){ceil_fee(quote,creator_fee_bps)?}else{0};
  let (gross,total)=gross_total(quote,pf,cf)?;




  require_gte!(input,total,PumpError::TooMuchSolRequired);
  (amount,quote,pf,cf,gross)
 }else{
  let (mut gross,total)=gross_total(quote,pf,cf)?;let mut quote=quote;let mut amount=computed;
  if total>input{
   quote=quote.checked_sub(total.saturating_sub(input)).ok_or(PumpError::BuyNotEnoughSolToCoverFees)?;






   require_gt!(quote,0,PumpError::BuySlippageBelowMinTokensOut);



   amount=u64::try_from(crate::constant_product::tokens_for_quote(c,quote)?).map_err(|_|error!(PumpError::Truncation))?;gross=gross_total(quote,pf,cf)?.0;
  }

  require_gte!(amount,limit,PumpError::BuySlippageBelowMinTokensOut);
  (amount,quote,pf,cf,gross)};







 let quote_transfer_fee=gross_quote.checked_sub(quote).ok_or_else(||error!(PumpError::Overflow))?;
 let _=&c;
 require_gte!(c.real_token_reserves,amount,PumpError::NotEnoughTokensToBuy);a.bonding_curve.apply_buy(amount,quote)?;
  move_curve_tokens(base_token_program,&a.associated_base_bonding_curve,&a.associated_base_user,&a.bonding_curve,base_mint,amount,&[&[b"bonding-curve",base_mint.key().as_ref(),&[ctx.bumps.bonding_curve]]])?;
  if a.user.key()==a.global.whitelist_pda{a.associated_base_bonding_curve.reload()?;a.associated_base_user.reload()?;let quote_mint=a.bonding_curve.quote_mint;a.bonding_curve.sync_virtual_quote_reserves(a.associated_base_bonding_curve.amount,a.associated_base_user.amount,&quote_mint)?;}
  if a.user_volume_accumulator.user==Pubkey::default(){a.user_volume_accumulator.user=a.user.key();}
 if cf>0{
   if a.bonding_curve.is_cashback_coin{
    pay_from_user_owned(native,&a.system_program,&a.user,a.user_volume_accumulator.to_account_info(),cf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_user_volume_accumulator.as_ref())})?;
    crate::token_incentives::volume_accumulator::record_cashback_earned(&mut a.user_volume_accumulator,cf,native)?;
   }else{
    native_payments::ensure_rent_exempt(0,&a.system_program,&a.user,&a.creator_vault)?;
    pay_from_user_owned(native,&a.system_program,&a.user,a.creator_vault.to_account_info(),cf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_creator_vault.as_ref())})?;
   }
  }
  pay_from_user(native,&a.system_program,&a.user,a.bonding_curve.as_ref(),gross_quote,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())})?;
  let (bf,protocol_fee)=recipient_payments::split_protocol_fee(&a.global,pf,a.bonding_curve.is_mayhem_mode);
  pay_from_user_recipient(native,&a.system_program,&a.user,&fee_recipient,protocol_fee,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_quote_fee_recipient.as_ref())})?;
  pay_from_user_recipient(native,&a.system_program,&a.user,&buyback_fee_recipient,bf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_user.as_ref())},if native{None}else{Some(a.associated_quote_buyback_fee_recipient.as_ref())})?;
 let c=&a.bonding_curve;let virtual_token_reserves=c.virtual_token_reserves;let virtual_quote_reserves=c.virtual_quote_reserves;let real_token_reserves=c.real_token_reserves;let real_quote_reserves=c.real_quote_reserves;let creator=c.creator;let mut quote_mint=Pubkey::default();snapshot_quote_mint(&c.quote_mint,&mut quote_mint);let timestamp=Clock::get()?.unix_timestamp;let total_unclaimed_tokens=a.user_volume_accumulator.total_unclaimed_tokens;let total_claimed_tokens=a.user_volume_accumulator.total_claimed_tokens;let current_sol_volume=a.user_volume_accumulator.current_sol_volume;let last_update_timestamp=a.user_volume_accumulator.last_update_timestamp;let shareholders=crate::distribution::sharing_config_shareholders(&a.sharing_config.to_account_info())?.unwrap_or_default();let is_sol=quote_mint==Pubkey::default();
  let ev=TradeEvent{user:a.user.key(),mint:a.base_mint.key(),sol_amount:if is_sol{quote}else{0},token_amount:amount,is_buy:true,timestamp,virtual_sol_reserves:if is_sol{virtual_quote_reserves}else{0},virtual_token_reserves,real_sol_reserves:if is_sol{real_quote_reserves}else{0},real_token_reserves,fee_recipient:fee_recipient.key(),fee_basis_points:protocol_fee_bps,fee:pf,creator,creator_fee_basis_points:if c.is_cashback_coin{0}else{creator_fee_bps},creator_fee:if c.is_cashback_coin{0}else{cf},holder_rewards_bps:if c.is_holder_reward{creator_fee_bps}else{0},holder_rewards:if c.is_holder_reward{cf}else{0},track_volume:false,total_unclaimed_tokens,total_claimed_tokens,current_sol_volume,last_update_timestamp,ix_name:"buy_exact_quote_in".into(),mayhem_mode:c.is_mayhem_mode,cashback_fee_basis_points:if c.is_cashback_coin{creator_fee_bps}else{0},cashback:if c.is_cashback_coin{cf}else{0},buyback_fee:crate::transfer_fee_recovered::post_fee_amount(&transfer_fee,bf)?,buyback_fee_basis_points:if c.is_mayhem_mode{0}else{a.global.buyback_basis_points},shareholders,quote_mint:c.quote_mint,quote_amount:quote,virtual_quote_reserves,real_quote_reserves,creator_fee_unclaimed:c.creator_fee,unparsed_trailing_field:quote_transfer_fee};
  emit!(ev);emit_cpi!(ev);
  complete_and_prepare(ctx,timestamp)?;



















Ok(())
}
use crate::legacy_sell::fee_cpi::fee as ceil_fee;




pub use crate::v2_native_payments as native_payments;

#[path="v2_token_transfers.rs"]
pub mod token_transfers;

#[path="v2_recipient_payments.rs"]
pub(crate) mod recipient_payments;

fn pay_from_user<'info>(native:bool,system_program:&Program<'info,System>,user:&Signer<'info>,to:&Account<'info,BondingCurve>,amount:u64,token_program:&Interface<'info,TokenInterface>,mint:&InterfaceAccount<'info,Mint>,from:Option<&AccountInfo<'info>>,dst:Option<&AccountInfo<'info>>)->Result<()>{crate::trade::user_quote_payments::transfer_from_user(native,system_program.as_ref(),user,to,amount,token_program,mint.decimals,AsRef::<AccountInfo<'info>>::as_ref(mint),from,dst)}
fn pay_from_user_owned<'info>(native:bool,system_program:&Program<'info,System>,user:&Signer<'info>,to:AccountInfo<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,mint:&InterfaceAccount<'info,Mint>,from:Option<&AccountInfo<'info>>,dst:Option<&AccountInfo<'info>>)->Result<()>{crate::user_quote_payments::transfer_from_user_owned(native,system_program.as_ref(),user,to,amount,token_program,mint.decimals,AsRef::<AccountInfo<'info>>::as_ref(mint),from,dst)}
fn pay_from_user_recipient<'info>(native:bool,system_program:&Program<'info,System>,user:&Signer<'info>,to:&&UncheckedAccount<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,mint:&InterfaceAccount<'info,Mint>,from:Option<&AccountInfo<'info>>,dst:Option<&AccountInfo<'info>>)->Result<()>{crate::user_quote_payments::transfer_from_user_recipient(native,system_program.as_ref(),user,to,amount,token_program,mint.decimals,AsRef::<AccountInfo<'info>>::as_ref(mint),from,dst)}
fn move_curve_tokens<'info>(token_program:&Interface<'info,TokenInterface>,source:&InterfaceAccount<'info,TokenAccount>,destination:&InterfaceAccount<'info,TokenAccount>,authority:&Account<'info,BondingCurve>,mint:&InterfaceAccount<'info,Mint>,amount:u64,signer_seeds:&[&[&[u8]];1])->Result<()>{token_transfers::transfer_curve_tokens(token_program,source,destination,authority,mint.decimals,AsRef::<AccountInfo<'info>>::as_ref(mint),amount,signer_seeds)}

#[inline(always)]
fn complete_and_prepare<'info>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,timestamp:i64)->Result<()>{
  let a=&mut *ctx.accounts;if a.bonding_curve.real_token_reserves==0{a.bonding_curve.complete=true;let event=crate::trade_types::CompleteEvent{mint:a.base_mint.key(),user:a.user.key(),bonding_curve:a.bonding_curve.key(),quote_mint:a.bonding_curve.quote_mint,timestamp};emit!(event);emit_cpi!(event);}
  let a=&mut *ctx.accounts;crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;Ok(())
}

// Separate fixed-size copies reproduce the original's interleaved load/store order.
// Returning a Pubkey temporary instead hoists all loads before the stores.
#[inline(always)]
fn snapshot_quote_mint(key: &Pubkey, target: &mut Pubkey) {
    let src = key.as_ref();
    let out = target.as_mut();
    out[0..8].copy_from_slice(&src[0..8]);
    out[8..16].copy_from_slice(&src[8..16]);
    out[16..24].copy_from_slice(&src[16..24]);
    out[24..32].copy_from_slice(&src[24..32]);
}
