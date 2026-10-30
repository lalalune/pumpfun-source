use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self,Mint,TokenAccount,TokenInterface,TransferChecked};
use crate::{Global,PumpError};
const FEE_PROGRAM:Pubkey=anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
use crate::trade_types::{TradeEvent,BondingCurve};
use crate::legacy_sell::{LegacyFeeConfig,LegacyFeesProgram};
const WSOL:Pubkey=anchor_lang::solana_program::pubkey!("So11111111111111111111111111111111111111112");
// layout-pad(24): aligns the next Source site with the original line























#[derive(Accounts)]
pub struct SellV2<'info>{
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
const NO_FEE:Option<crate::trade::native_transfer_fee::Fee>=None;fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}
fn sub(a:u64,b:u64)->Result<u64>{a.checked_sub(b).ok_or_else(||error!(PumpError::Overflow))}
fn narrow(a:u128)->Result<u64>{u64::try_from(a).map_err(|_|error!(PumpError::Truncation))}fn is_native_quote(quote_mint:Pubkey)->bool{quote_mint==Pubkey::default()}
#[inline(always)]pub fn execute(ctx:Context<SellV2>,amount:u64,minimum:u64)->Result<()>{
 let a=&mut *ctx.accounts;let fee_recipient=&a.fee_recipient;let buyback_fee_recipient=&a.buyback_fee_recipient;let (base_token_program,base_mint)=(&a.base_token_program,&a.base_mint);
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;


 let c=&a.bonding_curve;

































































































































































 require!(!c.complete,PumpError::BondingCurveComplete);

 require_gt!(amount,0,PumpError::SellZeroAmount);

 require_gte!(a.associated_base_user.amount,amount,PumpError::NotEnoughTokensToSell);
 crate::legacy_sell::fee_recipient::validate_fee_recipient(fee_recipient,&a.global,&a.bonding_curve)?;
 a.global.validate_buyback_fee_recipient(&buyback_fee_recipient.key())?;
 let native=a.bonding_curve.quote_mint==Pubkey::default();
 if !native{
  {let quote_mint=a.quote_mint.key();let quote_token_program=a.quote_token_program.key();let quote_mint_info=a.quote_mint.to_account_info();let quote_token_program_info=a.quote_token_program.to_account_info();
  crate::buy_v2::admit_associated_token_account(a.associated_quote_bonding_curve.as_ref(),&a.bonding_curve.to_account_info(),quote_mint,quote_token_program,&quote_mint_info,&quote_token_program_info,false,a.user.as_ref(),a.system_program.as_ref())?;crate::buy_v2::check_token_account(&a.associated_quote_user,a.user.as_ref(),quote_mint,quote_token_program)?;
  crate::buy_v2::admit_associated_token_account(a.associated_creator_vault.as_ref(),&a.creator_vault,quote_mint,quote_token_program,&quote_mint_info,&quote_token_program_info,true,a.user.as_ref(),a.system_program.as_ref())?;crate::buy_v2::admit_associated_token_account(a.associated_user_volume_accumulator.as_ref(),&a.user_volume_accumulator.to_account_info(),quote_mint,quote_token_program,&quote_mint_info,&quote_token_program_info,true,a.user.as_ref(),a.system_program.as_ref())?;
  crate::buy_v2::admit_associated_token_account(a.associated_quote_fee_recipient.as_ref(),&fee_recipient.to_account_info(),quote_mint,quote_token_program,&quote_mint_info,&quote_token_program_info,true,a.user.as_ref(),a.system_program.as_ref())?;crate::buy_v2::admit_associated_token_account(a.associated_quote_buyback_fee_recipient.as_ref(),&buyback_fee_recipient.to_account_info(),quote_mint,quote_token_program,&quote_mint_info,&quote_token_program_info,true,a.user.as_ref(),a.system_program.as_ref())?;}




 }else{require!(a.quote_mint.key()==WSOL,PumpError::UnsupportedQuoteMint);}
















































































 let quote=u64::try_from(c.sell_quote(amount)?).map_err(|_|error!(PumpError::Truncation))?;
 let (cf,pf,protocol_fee_bps,creator_fee_bps)=if a.global.whitelist_pda==a.user.key(){(0,0,0,0)}else{let (pf,cf,p,c)=crate::legacy_sell::fee_cpi::trade_fees(
  &a.global,&a.bonding_curve,&a.base_mint,&a.fee_config,&a.fee_program,a.program.as_ref(),quote
 )?;(cf,pf,p,c)};




















 let output=quote.checked_sub(pf)
  .ok_or_else(||error!(PumpError::Overflow))?
  .checked_sub(cf)
  .ok_or_else(||error!(PumpError::Overflow))?;
 let transfer_fee=if native{NO_FEE}else{crate::transfer_fee_recovered::get_transfer_fee(&a.quote_mint.to_account_info())?};
 let net_output=crate::transfer_fee_recovered::post_fee_amount(&transfer_fee,output)?;








 require_gte!(net_output,minimum,PumpError::TooLittleSolReceived);






 let quote_transfer_fee=output.checked_sub(net_output).ok_or_else(||error!(PumpError::Overflow))?;
 a.bonding_curve.apply_sell(amount,quote)?;
 user_token_transfers::transfer_user_tokens(base_token_program,&a.associated_base_user,&a.associated_base_bonding_curve,a.user.as_ref(),base_mint.decimals,base_mint.as_ref().as_ref(),amount)?;
  if a.user.key()==a.global.whitelist_pda{a.associated_base_bonding_curve.reload()?;a.associated_base_user.reload()?;let quote_mint=a.bonding_curve.quote_mint;a.bonding_curve.sync_virtual_quote_reserves(a.associated_base_bonding_curve.amount,a.associated_base_user.amount,&quote_mint)?;}
  if a.user_volume_accumulator.user==Pubkey::default(){a.user_volume_accumulator.user=a.user.key();}
 if cf>0{if a.bonding_curve.is_cashback_coin{
 pay_owned(native,&a.base_mint,a.bonding_curve.as_ref(),a.user_volume_accumulator.to_account_info(),cf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())},if native{None}else{Some(a.associated_user_volume_accumulator.as_ref())},ctx.bumps.bonding_curve)?;
 crate::token_incentives::volume_accumulator::record_cashback_earned(&mut a.user_volume_accumulator,cf,native)?;
 }else{crate::buy_v2::native_payments::ensure_rent_exempt(0,&a.system_program,&a.user,&a.creator_vault)?;
 pay_owned(native,&a.base_mint,a.bonding_curve.as_ref(),a.creator_vault.to_account_info(),cf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())},if native{None}else{Some(a.associated_creator_vault.as_ref())},ctx.bumps.bonding_curve)?;
 }}
 pay_user(native,&a.base_mint,a.bonding_curve.as_ref(),a.user.as_ref(),output,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())},if native{None}else{Some(a.associated_quote_user.as_ref())},ctx.bumps.bonding_curve)?;
 let (bf,protocol_fee)=crate::buy_v2::recipient_payments::split_protocol_fee(&a.global,pf,a.bonding_curve.is_mayhem_mode);
 pay_recipient(native,&a.base_mint,a.bonding_curve.as_ref(),&buyback_fee_recipient,bf,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())},if native{None}else{Some(a.associated_quote_buyback_fee_recipient.as_ref())},ctx.bumps.bonding_curve)?;
 pay_recipient(native,&a.base_mint,a.bonding_curve.as_ref(),&fee_recipient,protocol_fee,&a.quote_token_program,&a.quote_mint,if native{None}else{Some(a.associated_quote_bonding_curve.as_ref())},if native{None}else{Some(a.associated_quote_fee_recipient.as_ref())},ctx.bumps.bonding_curve)?;
 let c=&a.bonding_curve;let virtual_token_reserves=c.virtual_token_reserves;let virtual_quote_reserves=c.virtual_quote_reserves;let real_token_reserves=c.real_token_reserves;let real_quote_reserves=c.real_quote_reserves;let creator=c.creator;let quote_mint=c.quote_mint;
 let shareholders=crate::distribution::sharing_config_shareholders(&a.sharing_config.to_account_info())?.unwrap_or_default();let is_sol=is_native_quote(quote_mint);
  let ev=TradeEvent{user:a.user.key(),mint:a.base_mint.key(),sol_amount:if is_sol{quote}else{0},token_amount:amount,is_buy:false,
   virtual_sol_reserves:if is_sol{virtual_quote_reserves}else{0},virtual_token_reserves,real_sol_reserves:if is_sol{real_quote_reserves}else{0},real_token_reserves,timestamp:Clock::get()?.unix_timestamp,
   fee_recipient:fee_recipient.key(),fee_basis_points:protocol_fee_bps,fee:pf,creator,
   creator_fee_basis_points:if c.is_cashback_coin{0}else{creator_fee_bps},creator_fee:if c.is_cashback_coin{0}else{cf},holder_rewards_bps:if c.is_holder_reward{creator_fee_bps}else{0},holder_rewards:if c.is_holder_reward{cf}else{0},
   track_volume:false,total_unclaimed_tokens:0,total_claimed_tokens:0,current_sol_volume:0,last_update_timestamp:0,
   ix_name:"sell".into(),mayhem_mode:c.is_mayhem_mode,cashback_fee_basis_points:if c.is_cashback_coin{creator_fee_bps}else{0},cashback:if c.is_cashback_coin{cf}else{0},
   buyback_fee:crate::transfer_fee_recovered::post_fee_amount(&transfer_fee,bf)?,buyback_fee_basis_points:if c.is_mayhem_mode{0}else{a.global.buyback_basis_points},
   shareholders,
   quote_mint:c.quote_mint,quote_amount:quote,virtual_quote_reserves,real_quote_reserves,
   creator_fee_unclaimed:c.creator_fee,unparsed_trailing_field:quote_transfer_fee};
  emit!(ev);emit_cpi!(ev);Ok(())








}



#[path="v2_user_token_transfers.rs"]
pub mod user_token_transfers;

#[path="v2_quote_token_transfers.rs"]
pub mod quote_token_transfers;
fn pay_user<'info>(native:bool,base_mint:&InterfaceAccount<'info,Mint>,curve:&Account<'info,BondingCurve>,destination:&AccountInfo<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,quote_mint:&InterfaceAccount<'info,Mint>,quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,bump:u8)->Result<()>{crate::trade::quote_payments::transfer_to_user(native,AsRef::<AccountInfo<'info>>::as_ref(base_mint),curve,destination,amount,token_program,quote_mint.decimals,AsRef::<AccountInfo<'info>>::as_ref(quote_mint),quote_source,quote_destination,bump)}
fn pay_owned<'info>(native:bool,base_mint:&InterfaceAccount<'info,Mint>,curve:&Account<'info,BondingCurve>,destination:AccountInfo<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,quote_mint:&InterfaceAccount<'info,Mint>,quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,bump:u8)->Result<()>{crate::trade::quote_payments::transfer_to_owned(native,AsRef::<AccountInfo<'info>>::as_ref(base_mint),curve,destination,amount,token_program,quote_mint.decimals,AsRef::<AccountInfo<'info>>::as_ref(quote_mint),quote_source,quote_destination,bump)}
fn pay_recipient<'info>(native:bool,base_mint:&InterfaceAccount<'info,Mint>,curve:&Account<'info,BondingCurve>,destination:&&UncheckedAccount<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,quote_mint:&InterfaceAccount<'info,Mint>,quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,bump:u8)->Result<()>{crate::trade::quote_payments::transfer_to_recipient(native,AsRef::<AccountInfo<'info>>::as_ref(base_mint),curve,destination,amount,token_program,quote_mint.decimals,AsRef::<AccountInfo<'info>>::as_ref(quote_mint),quote_source,quote_destination,bump)}
#[event_cpi]
#[derive(Accounts)]
pub struct AdminReadonly<'info>{
 #[account(mut,seeds=[b"global"],bump,has_one=authority @ crate::PumpError::NotAuthorized)]
 pub global:Account<'info,crate::Global>,
 pub authority:Signer<'info>,
}
