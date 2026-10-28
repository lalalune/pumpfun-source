use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,Mint,TokenAccount,TokenInterface,TransferChecked};
use crate::{Global,PumpError};
use crate::trade_types::{TradeEvent,BondingCurve};
use crate::legacy_sell::{LegacyFeeConfig,LegacyFeesProgram};
const FEE_PROGRAM:Pubkey=anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
const WSOL:Pubkey=anchor_lang::solana_program::pubkey!("So11111111111111111111111111111111111111112");
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
 if exact{execute_inner::<true>(ctx,input,limit,partial)}else{execute_inner::<false>(ctx,input,limit,partial)}
}
#[inline(never)]
fn execute_inner<'info,const EXACT:bool>(ctx:Context<'_,'_,'_,'info,BuyV2<'info>>,mut input:u64,limit:u64,partial:bool)->Result<()>{
 let exact=EXACT;
 let a=&mut *ctx.accounts;
 require!(!a.bonding_curve.complete,PumpError::BondingCurveComplete);
 if exact{require_gt!(limit,0,PumpError::BuyZeroAmount);require_gt!(input,0,PumpError::BuyNotEnoughSolToCoverFees);}else{
  if partial{input=input.min(a.bonding_curve.real_token_reserves);}
  require_gt!(input,0,PumpError::BuyZeroAmount);
  require_gte!(a.bonding_curve.real_token_reserves,input,PumpError::NotEnoughTokensToBuy);
 }
 crate::legacy_sell::fee_recipient::validate_fee_recipient(&a.fee_recipient,&a.global,&a.bonding_curve)?;
 require_keys_neq!(a.buyback_fee_recipient.key(),Pubkey::default(),PumpError::BuybackFeeRecipientMissing);
 require!(a.global.buyback_fee_recipients.contains(&a.buyback_fee_recipient.key()),PumpError::BuybackFeeRecipientNotAuthorized);
 if a.user_volume_accumulator.user==Pubkey::default(){a.user_volume_accumulator.user=a.user.key();}
 if a.bonding_curve.quote_mint!=Pubkey::default(){
  admit_associated_token_account(a.associated_quote_bonding_curve.as_ref(),&a.bonding_curve.to_account_info(),&a.quote_mint.key(),&a.quote_token_program.key(),a.user.as_ref(),&a.quote_mint.to_account_info(),false,a.system_program.as_ref(),a.quote_token_program.as_ref())?;
  require_keys_eq!(*a.associated_quote_user.owner,a.quote_token_program.key(),PumpError::AccountTypeNotSupported);
  check_token(&a.associated_quote_user,a.quote_mint.key(),a.user.key())?;{let d=a.associated_quote_user.try_borrow_data()?;let t=TokenAccount::try_deserialize(&mut &d[..])?;require_keys_eq!(t.owner,a.user.key(),PumpError::AccountTypeNotSupported);}
  for (destination,authority) in [(a.associated_creator_vault.to_account_info(),a.creator_vault.to_account_info()),(a.associated_user_volume_accumulator.to_account_info(),a.user_volume_accumulator.to_account_info()),(a.associated_quote_fee_recipient.to_account_info(),a.fee_recipient.to_account_info()),(a.associated_quote_buyback_fee_recipient.to_account_info(),a.buyback_fee_recipient.to_account_info())]{
   admit_associated_token_account(&destination,&authority,&a.quote_mint.key(),&a.quote_token_program.key(),a.user.as_ref(),&a.quote_mint.to_account_info(),true,a.system_program.as_ref(),a.quote_token_program.as_ref())?;
  }
 }




 let c=&a.bonding_curve;let native=c.quote_mint==Pubkey::default();
 let available=if exact && !native{sub(input,crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),input,false)?)?}else{input};
 if exact{require_gt!(available,0,PumpError::BuyNotEnoughSolToCoverFees);}
 let quoted_amount=if exact{0}else{input.min(c.real_token_reserves)};
 let pre_quote=if exact{0}else{add(narrow(quoted_amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128-quoted_amount as u128))?,1)?};
 let pre_quote_transfer_fee=if !exact && !native{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),pre_quote,true)?}else{0};
 let (initial_protocol_fee,initial_creator_fee,protocol_fee_bps,creator_fee_bps)=if a.user.key()==a.global.whitelist_pda{(0,0,0,0)}else{crate::legacy_sell::fee_cpi::trade_fees(
  &a.global,&a.bonding_curve,&a.base_mint,&a.fee_config,&a.fee_program,a.program.as_ref(),if exact{available}else{pre_quote}
 )?};
 let cb=if c.creator==Pubkey::default(){0}else{creator_fee_bps};
 let raw_quote=if exact{let total_bps=protocol_fee_bps.checked_add(cb).ok_or(PumpError::Overflow)?;let denominator=10000u128+total_bps as u128;narrow(available as u128*10000/denominator)?}else{0};
 let adjusted=if exact && add(add(raw_quote,ceil_fee(raw_quote,protocol_fee_bps)?)?,ceil_fee(raw_quote,cb)?)?>available{sub(raw_quote,1)?}else{raw_quote};
 let computed=if exact{require_gt!(raw_quote,0,PumpError::BuyNotEnoughSolToCoverFees);require_gt!(adjusted,0,PumpError::BuySlippageBelowMinTokensOut);let e=adjusted.saturating_sub(1);narrow(c.virtual_token_reserves as u128*e as u128/(c.virtual_quote_reserves as u128+e as u128))?}else{input};
 if !partial{require_gte!(c.real_token_reserves,computed,PumpError::NotEnoughTokensToBuy);}let amount=computed.min(c.real_token_reserves);
 let quote=if !exact{pre_quote}else if computed<=c.real_token_reserves{adjusted}else{add(narrow(amount as u128*c.virtual_quote_reserves as u128/(c.virtual_token_reserves as u128-amount as u128))?,1)?};
 let fq=if exact && computed<=c.real_token_reserves{raw_quote}else{quote};let pf=if exact{ceil_fee(fq,protocol_fee_bps)?}else{initial_protocol_fee};let cf=if exact{ceil_fee(fq,cb)?}else{initial_creator_fee};
 let quote_transfer_fee=if !exact{pre_quote_transfer_fee}else if native{0}else{crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),quote,true)?};
 let gross_quote=add(quote,quote_transfer_fee)?;
 if exact{if !(partial && computed>c.real_token_reserves){require_gte!(amount,limit,PumpError::BuySlippageBelowMinTokensOut);}}else{require_gte!(limit,add(add(gross_quote,pf)?,cf)?,PumpError::TooMuchSolRequired);}
 let vb=sub(c.virtual_token_reserves,amount)?;let vq=add(c.virtual_quote_reserves,quote)?;let rb=sub(c.real_token_reserves,amount)?;let rq=add(c.real_quote_reserves,quote)?;
 let mint=a.base_mint.key();let bump=[ctx.bumps.bonding_curve];let seeds:&[&[u8]]=&[b"bonding-curve",mint.as_ref(),&bump];
 token_transfers::transfer_curve_tokens(&a.base_token_program,&a.associated_base_bonding_curve,&a.associated_base_user,&a.bonding_curve,a.base_mint.decimals,a.base_mint.as_ref().as_ref(),amount,&[seeds])?;
 let bb=&a.buyback_fee_recipient;
 let bbps=if c.is_mayhem_mode{0}else{a.global.buyback_basis_points};
 let cashback_coin=c.is_cashback_coin;
 if cf>0 && !cashback_coin{native_payments::ensure_rent_exempt(0,&a.system_program,&a.user,&a.creator_vault)?;}
 if cf>0 {
  let creator_destination=if cashback_coin{a.user_volume_accumulator.to_account_info()}else{a.creator_vault.to_account_info()};
  let creator_quote_destination=if native{None}else if cashback_coin{Some(a.associated_user_volume_accumulator.as_ref())}else{Some(a.associated_creator_vault.as_ref())};
  crate::user_quote_payments::transfer_from_user_owned(
   native,a.system_program.as_ref(),&a.user,creator_destination,cf,&a.quote_token_program,
   a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),
   if native{None}else{Some(a.associated_quote_user.as_ref())},creator_quote_destination,
  )?;
 }
 if cashback_coin{crate::token_incentives::volume_accumulator::record_cashback_earned(&mut a.user_volume_accumulator,cf,native)?;}
 crate::trade::user_quote_payments::transfer_from_user(
  native,a.system_program.as_ref(),&a.user,a.bonding_curve.as_ref(),
  if native{quote}else{gross_quote},&a.quote_token_program,a.quote_mint.decimals,
  a.quote_mint.as_ref().as_ref(),
  if native{None}else{Some(a.associated_quote_user.as_ref())},
  if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())},
 )?;
 let (bf,protocol_fee)=recipient_payments::split_protocol_fee(&a.global,pf,c.is_mayhem_mode);
 let buyback_received=if native{bf}else{sub(bf,crate::trade::quote_transfer_fee(&a.quote_mint.to_account_info(),bf,false)?)?};
 for (recipient,quote_recipient,amount) in [(&a.fee_recipient,&a.associated_quote_fee_recipient,protocol_fee),(bb,&a.associated_quote_buyback_fee_recipient,bf)].iter() {
  crate::user_quote_payments::transfer_from_user_recipient(
   native,a.system_program.as_ref(),&a.user,recipient,*amount,&a.quote_token_program,
   a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),
   if native{None}else{Some(a.associated_quote_user.as_ref())},
   if native{None}else{Some(quote_recipient.as_ref())},
  )?;
 }
 let shareholders={let d=a.sharing_config.try_borrow_data()?;crate::SharingConfig::try_deserialize(&mut &d[..]).map(|s|s.shareholders).unwrap_or_default()};
 let ev=TradeEvent{mint:a.base_mint.key(),sol_amount:if native{quote}else{0},token_amount:amount,is_buy:true,user:a.user.key(),timestamp:Clock::get()?.unix_timestamp,virtual_sol_reserves:if native{vq}else{0},virtual_token_reserves:vb,real_sol_reserves:if native{rq}else{0},real_token_reserves:rb,fee_recipient:a.fee_recipient.key(),fee_basis_points:protocol_fee_bps,fee:pf,creator:c.creator,creator_fee_basis_points:if c.is_cashback_coin{0}else{creator_fee_bps},creator_fee:if c.is_cashback_coin{0}else{cf},track_volume:false,total_unclaimed_tokens:a.user_volume_accumulator.total_unclaimed_tokens,total_claimed_tokens:a.user_volume_accumulator.total_claimed_tokens,current_sol_volume:a.user_volume_accumulator.current_sol_volume,last_update_timestamp:a.user_volume_accumulator.last_update_timestamp,ix_name:if exact{"buy_exact_quote_in".into()}else{"buy".into()},mayhem_mode:c.is_mayhem_mode,cashback_fee_basis_points:if c.is_cashback_coin{creator_fee_bps}else{0},cashback:if c.is_cashback_coin{cf}else{0},buyback_fee_basis_points:bbps,buyback_fee:buyback_received,shareholders,quote_mint:c.quote_mint,quote_amount:quote,virtual_quote_reserves:vq,real_quote_reserves:rq,holder_rewards_bps:if c.is_holder_reward{cb}else{0},holder_rewards:if c.is_holder_reward{cf}else{0},creator_fee_unclaimed:c.creator_fee,unparsed_trailing_field:quote_transfer_fee};
 let c=&mut a.bonding_curve;c.virtual_token_reserves=vb;c.virtual_quote_reserves=vq;c.real_token_reserves=rb;c.real_quote_reserves=rq;
 let complete=if rb==0{c.complete=true;Some(crate::trade_types::CompleteEvent{user:a.user.key(),mint:a.base_mint.key(),bonding_curve:a.bonding_curve.key(),timestamp:Clock::get()?.unix_timestamp,quote_mint:ev.quote_mint})}else{None};
 emit!(ev.clone());emit_cpi!(ev);if let Some(event)=complete{emit!(event.clone());emit_cpi!(event);}
 let a=&mut *ctx.accounts;
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;
Ok(())
}
use crate::legacy_sell::fee_cpi::fee as ceil_fee;

fn check_token(info:&AccountInfo,mint:Pubkey,owner:Pubkey)->Result<()>{let d=info.try_borrow_data()?;let t=TokenAccount::try_deserialize(&mut &d[..])?;require_keys_eq!(t.mint,mint,PumpError::MintDoesNotMatchBondingCurve);let _=owner;Ok(())}

#[path="v2_native_payments.rs"]
pub(crate) mod native_payments;

#[path="v2_token_transfers.rs"]
mod token_transfers;

#[path="v2_recipient_payments.rs"]
pub(crate) mod recipient_payments;

// Shared main-program admission for an ATA, including the optional idempotent creation.
#[inline(never)]
pub fn admit_associated_token_account<'info>(account:&AccountInfo<'info>,authority:&AccountInfo<'info>,mint:&Pubkey,token_program:&Pubkey,payer:&AccountInfo<'info>,mint_info:&AccountInfo<'info>,allow_create:bool,system_program:&AccountInfo<'info>,token_program_info:&AccountInfo<'info>)->Result<()>{
 let expected=anchor_spl::associated_token::get_associated_token_address_with_program_id(&authority.key(),mint,token_program);
 require_keys_eq!(account.key(),expected,anchor_lang::error::ErrorCode::ConstraintSeeds);
 if account.owner==&anchor_lang::system_program::ID {
  require!(allow_create,anchor_lang::error::ErrorCode::AccountNotInitialized);
  let instruction=anchor_spl::associated_token::spl_associated_token_account::instruction::create_associated_token_account_idempotent(payer.key,authority.key,mint,token_program);
  let account_infos=[payer.clone(),account.clone(),authority.clone(),mint_info.clone(),system_program.clone(),token_program_info.clone()];
  anchor_lang::solana_program::program::invoke(&instruction,&account_infos)?;
 }
 require_keys_eq!(*account.owner,*token_program,PumpError::AccountTypeNotSupported);
 let data=account.try_borrow_data()?;
 let token=TokenAccount::try_deserialize_unchecked(&mut &data[..])?;
 require_keys_eq!(token.mint,*mint,PumpError::MintDoesNotMatchBondingCurve);
 Ok(())
}
