use crate::*;
use anchor_lang::Event;
use anchor_spl::{token::Token,token_interface::{Mint,TokenAccount},token_2022::Token2022,associated_token::AssociatedToken};
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed,program_error::ProgramError};
#[derive(Accounts)]
pub struct Migrate<'info>{
 #[account(seeds=[b"global"],bump,has_one=withdraw_authority @ PumpError::NotAuthorized)]pub global:Box<Account<'info,Global>>,
 /// CHECK: global relation.
 #[account(mut)]pub withdraw_authority:UncheckedAccount<'info>,
 pub mint:Box<InterfaceAccount<'info,Mint>>,
 #[account(mut,seeds=[b"bonding-curve",mint.key().as_ref()],bump,constraint=bonding_curve.quote_mint==Pubkey::default() @ PumpError::UnsupportedQuoteMint)]pub bonding_curve:Box<Account<'info,crate::trade_types::BondingCurve>>,
 #[account(mut,associated_token::mint=mint,associated_token::authority=bonding_curve,associated_token::token_program=mint.to_account_info().owner)]pub associated_bonding_curve:Box<InterfaceAccount<'info,TokenAccount>>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,pub token_program:Program<'info,Token>,pub pump_amm:Program<'info,crate::pump_amm::program::PumpAmm>,
 /// CHECK: canonical PDA.
 #[account(mut,seeds=[b"pool",&0u16.to_le_bytes(),pool_authority.key().as_ref(),mint.key().as_ref(),wsol_mint.key().as_ref()],bump,seeds::program=pump_amm.key())]pub pool:UncheckedAccount<'info>,
 /// CHECK: canonical PDA.
 #[account(mut,seeds=[b"pool-authority",mint.key().as_ref()],bump)]pub pool_authority:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),mint.to_account_info().owner.as_ref(),mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_authority_mint_account:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),token_program.key().as_ref(),wsol_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_authority_wsol_account:UncheckedAccount<'info>,
 /// CHECK: canonical AMM config.
 #[account(seeds=[b"global_config"],bump,seeds::program=pump_amm.key())]pub amm_global_config:UncheckedAccount<'info>,
 #[account(address=anchor_spl::token::spl_token::native_mint::ID)]pub wsol_mint:Box<InterfaceAccount<'info,Mint>>,
 /// CHECK: canonical LP mint.
 #[account(mut,seeds=[b"pool_lp_mint",pool.key().as_ref()],bump,seeds::program=pump_amm.key())]pub lp_mint:AccountInfo<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),token_2022_program.key().as_ref(),lp_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub user_pool_token_account:AccountInfo<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool.key().as_ref(),mint.to_account_info().owner.as_ref(),mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_base_token_account:AccountInfo<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool.key().as_ref(),token_program.key().as_ref(),wsol_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_quote_token_account:AccountInfo<'info>,
 pub token_2022_program:Program<'info,Token2022>,pub associated_token_program:Program<'info,AssociatedToken>,
 /// CHECK: canonical AMM event PDA.
 #[account(seeds=[b"__event_authority"],bump,seeds::program=pump_amm.key())]pub pump_amm_event_authority:AccountInfo<'info>,
 /// CHECK: canonical event PDA.
 #[account(seeds=[b"__event_authority"],bump)]pub event_authority:UncheckedAccount<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
 /// CHECK: constrained sysvar address.
 #[account(address=anchor_lang::solana_program::sysvar::rent::ID)]pub rent:UncheckedAccount<'info>,
}

// layout-pad: aligns the next Source site with the original line













































































































































































































pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,Migrate<'info>>)->Result<()>{
 let a=&ctx.accounts;crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;require!(a.bonding_curve.complete,PumpError::BondingCurveNotComplete);let migrated=a.bonding_curve.real_quote_reserves==0&&a.bonding_curve.virtual_quote_reserves==0&&a.bonding_curve.real_token_reserves==0&&a.bonding_curve.virtual_token_reserves==0;if migrated{msg!("Bonding curve already migrated");return Ok(());}
 let fee=a.global.pool_migration_fee;
 pay_migration_fee(a,&a.pool_authority,fee)?;
 let bump=ctx.bumps.pool_authority;
 create_pool_token_account(a,bump,&a.pool_base_token_account,&a.pool,&a.mint)?;
 create_pool_token_account(a,bump,&a.pool_quote_token_account,&a.pool,&a.wsol_mint)?;
 create_pool_token_account(a,bump,&a.pool_authority_mint_account,&a.pool_authority,&a.mint)?;
 let wsol_account_created=a.pool_authority_wsol_account.owner==&anchor_lang::system_program::ID;
 create_pool_token_account(a,bump,&a.pool_authority_wsol_account,&a.pool_authority,&a.wsol_mint)?;
 transfer_curve_tokens(&ctx)?;
 let base=pool_authority_mint_token_account(a)?.amount;
// layout-pad: aligns the next Source site with the original line
















 let quote=a.bonding_curve.real_quote_reserves.checked_add(a.bonding_curve.post_complete_quote_in)
  .ok_or_else(||error!(PumpError::Overflow))?
  .checked_sub(fee)
  .ok_or_else(||error!(PumpError::Overflow))?;
 fund_quote_token_account(&ctx,quote)?;
 create_pool(&ctx,base,quote)?;
 init_pump_amm_boost(&ctx)?;
 close_pool_authority_token_account(a,bump,&a.pool_authority_mint_account,&a.mint)?;
 if wsol_account_created{close_pool_authority_token_account(a,bump,&a.pool_authority_wsol_account,&a.wsol_mint)?;}
 burn_pool_authority_lp(&ctx)?;
 close_pool_authority_account(a,bump,&a.user_pool_token_account)?;
 refund_pool_authority(a,bump,&a.withdraw_authority,a.pool_authority.lamports())?;
 {let c:&mut crate::trade_types::BondingCurve=&mut ctx.accounts.bonding_curve;c.real_quote_reserves=0;c.real_token_reserves=0;c.virtual_quote_reserves=0;c.virtual_token_reserves=0;}
 let a=&ctx.accounts;
 let event=CompletePumpAmmMigrationEvent{user:a.user.key(),mint:a.mint.key(),mint_amount:base,sol_amount:quote,pool_migration_fee:fee,bonding_curve:a.bonding_curve.key(),timestamp:Clock::get()?.unix_timestamp,pool:a.pool.key(),quote_mint:a.bonding_curve.quote_mint};
 emit!(event);emit_cpi!(event);
 Ok(())
}
#[event]#[derive(Clone)]pub struct CompletePumpAmmMigrationEvent{pub user:Pubkey,pub mint:Pubkey,pub mint_amount:u64,pub sol_amount:u64,pub pool_migration_fee:u64,pub bonding_curve:Pubkey,pub timestamp:i64,pub pool:Pubkey,pub quote_mint:Pubkey}

#[inline(never)]
pub fn create_pool_token_account<'info>(a:&Migrate<'info>,bump:u8,account:&AccountInfo<'info>,wallet:&AccountInfo<'info>,mint:&InterfaceAccount<'info,Mint>)->Result<()>{
 create_token_account(a,&a.bonding_curve,account,wallet,mint,&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])?;
 Ok(())
}
#[inline(always)]
fn create_token_account<'info>(a:&Migrate<'info>,curve:&Account<'info,crate::trade_types::BondingCurve>,account:&AccountInfo<'info>,wallet:&AccountInfo<'info>,mint:&InterfaceAccount<'info,Mint>,signer_seeds:&[&[&[u8]]])->anchor_lang::solana_program::entrypoint::ProgramResult{
 let token_program=base_token_program(AsRef::<AccountInfo>::as_ref(mint),&a.token_program,&a.token_2022_program);
 let ix=Instruction{program_id:anchor_spl::associated_token::ID,accounts:vec![AccountMeta::new(a.pool_authority.key(),true),AccountMeta::new(account.key(),false),AccountMeta::new_readonly(wallet.key(),false),AccountMeta::new_readonly(mint.key(),false),AccountMeta::new_readonly(a.system_program.key(),false),AccountMeta::new_readonly(token_program.key(),false),AccountMeta::new_readonly(curve.key(),false)],data:anchor_lang::prelude::borsh::to_vec(&1u8).unwrap()};
 invoke_signed(&ix,&[a.pool_authority.to_account_info(),account.clone(),wallet.clone(),mint.to_account_info(),a.system_program.to_account_info(),token_program,curve.to_account_info()],signer_seeds)
}

#[inline(never)]
fn transfer_curve_tokens<'info>(ctx:&Context<'_,'_,'_,'info,Migrate<'info>>)->Result<()>{
 let a=&ctx.accounts; transfer_from_curve(a,base_token_program(AsRef::<AccountInfo>::as_ref(&*a.mint),&a.token_program,&a.token_2022_program),&a.associated_bonding_curve,&a.mint,&a.bonding_curve,a.associated_bonding_curve.amount,&[&[b"bonding-curve",a.mint.key().as_ref(),&[ctx.bumps.bonding_curve]]])
}
#[inline(always)]
fn transfer_from_curve<'info>(a:&Migrate<'info>,token_program:AccountInfo<'info>,from:&InterfaceAccount<'info,TokenAccount>,mint:&InterfaceAccount<'info,Mint>,authority:&Account<'info,crate::trade_types::BondingCurve>,amount:u64,signer_seeds:&[&[&[u8]]])->Result<()>{
 if amount==0{return Ok(())}
 let decimals=mint.decimals;
 anchor_spl::token_2022::transfer_checked(CpiContext::new_with_signer(token_program.clone(),anchor_spl::token_2022::TransferChecked{from:from.to_account_info(),to:a.pool_authority_mint_account.to_account_info(),authority:authority.to_account_info(),mint:mint.to_account_info()},signer_seeds),amount,decimals)
}

#[inline(never)]
fn fund_quote_token_account<'info>(ctx:&Context<'_,'_,'_,'info,Migrate<'info>>,amount:u64)->Result<()>{
 let a=&ctx.accounts; a.bonding_curve.sub_lamports(amount)?;a.pool_authority_wsol_account.add_lamports(amount)?;
 anchor_lang::solana_program::program::invoke(&Instruction{program_id:anchor_spl::token::ID,accounts:vec![AccountMeta::new(a.pool_authority_wsol_account.key(),false),AccountMeta::new_readonly(a.rent.key(),false),AccountMeta::new(a.bonding_curve.key(),false)],data:anchor_spl::token::spl_token::instruction::TokenInstruction::SyncNative.pack()},&[a.pool_authority_wsol_account.to_account_info(),a.rent.to_account_info(),a.bonding_curve.to_account_info()])?;
 Ok(())
}

// Original: standalone pool-creation helper (window 0x43ea0) calling the generated pump_amm client (Round46 form).
fn create_pool<'info>(ctx:&Context<'_,'_,'_,'info,Migrate<'info>>,base:u64,quote:u64)->Result<()>{
 let bump=ctx.bumps.pool_authority;let a=&ctx.accounts;
 let create=move |signer_seeds:&[&[&[u8]];1]|pump_amm::cpi::create_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),pump_amm::cpi::accounts::CreatePool{pool:a.pool.to_account_info(),global_config:a.amm_global_config.to_account_info(),creator:a.pool_authority.to_account_info(),base_mint:a.mint.to_account_info(),quote_mint:a.wsol_mint.to_account_info(),lp_mint:a.lp_mint.to_account_info(),user_base_token_account:a.pool_authority_mint_account.to_account_info(),user_quote_token_account:a.pool_authority_wsol_account.to_account_info(),user_pool_token_account:a.user_pool_token_account.to_account_info(),pool_base_token_account:a.pool_base_token_account.to_account_info(),pool_quote_token_account:a.pool_quote_token_account.to_account_info(),system_program:a.system_program.to_account_info(),token_2022_program:a.token_2022_program.to_account_info(),base_token_program:base_token_program(a.mint.as_ref().as_ref(),&a.token_program,&a.token_2022_program),quote_token_program:a.token_program.to_account_info(),associated_token_program:a.associated_token_program.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()},signer_seeds),0,base,quote,a.bonding_curve.creator,a.bonding_curve.is_mayhem_mode,pump_amm::types::OptionBool(a.bonding_curve.is_cashback_coin),pump_amm::types::OptionU64(a.bonding_curve.creator_fee_bps),pump_amm::types::OptionBool(a.bonding_curve.can_edit_creator_fee),pump_amm::types::OptionBool(a.bonding_curve.is_holder_reward));
 create(&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])
}

#[inline(never)]
// layout-pad: aligns the next Source site with the original line

























































































































































































pub fn init_pump_amm_boost<'info>(ctx:&Context<'_,'_,'_,'info,Migrate<'info>>)->Result<()>{
 let a=&ctx.accounts;
 if a.bonding_curve.is_mayhem_mode{return Ok(());}
 let [boost,vault]=ctx.remaining_accounts else {
  require!(!native_payments::boost_enabled(&a.amm_global_config),PumpError::NotEnoughRemainingAccounts);
  return Ok(());
 };let funding=Rent::get()?.minimum_balance(165);native_payments::transfer_native(a.system_program.as_ref(),&a.user,&a.pool_authority,funding)?;
 let bump=ctx.bumps.pool_authority;let init=move |signer_seeds:&[&[&[u8]];1]|pump_amm::cpi::init_boost(CpiContext::new_with_signer(a.pump_amm.to_account_info(),pump_amm::cpi::accounts::InitBoost{pool:a.pool.to_account_info(),global_config:a.amm_global_config.to_account_info(),creator:a.pool_authority.to_account_info(),base_mint:a.mint.to_account_info(),quote_mint:a.wsol_mint.to_account_info(),pool_base_token_account:a.pool_base_token_account.to_account_info(),pool_quote_token_account:a.pool_quote_token_account.to_account_info(),boost_vault_authority:boost.clone(),boost_vault:vault.clone(),quote_token_program:a.token_program.to_account_info(),system_program:a.system_program.to_account_info(),associated_token_program:a.associated_token_program.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()},signer_seeds));init(&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])
}



// The original migration skips an empty refund before constructing signer seeds.
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

pub use crate::payments::migrate_transfer_native as transfer_native;
// layout-pad
// layout-pad
// layout-pad
// layout-pad

#[path="migration_native_payments.rs"]
pub mod native_payments;

// layout-pad
// layout-pad
// layout-pad

fn close_token_account<'info>(a:&Migrate<'info>,account:&AccountInfo<'info>,signer_seeds:&[&[&[u8]]])->Result<()>{
 anchor_spl::token_2022::close_account(CpiContext::new_with_signer(a.token_2022_program.to_account_info(),anchor_spl::token_2022::CloseAccount{account:account.clone(),destination:a.withdraw_authority.to_account_info(),authority:a.pool_authority.to_account_info()},signer_seeds))
}

#[inline(never)]
pub fn pool_authority_mint_token_account(a:&Migrate)->Result<TokenAccount>{
 let data=a.pool_authority_mint_account.try_borrow_data()?;
 TokenAccount::try_deserialize_unchecked(&mut &data[..])
}

#[inline(never)]
fn base_token_program<'info>(mint:&AccountInfo<'info>,token_program:&AccountInfo<'info>,token_2022_program:&AccountInfo<'info>)->AccountInfo<'info>{
 if mint.to_account_info().owner==&anchor_spl::token::ID{token_program.clone()}else{token_2022_program.clone()}
}

#[inline(never)]
pub fn close_pool_authority_token_account<'info>(a:&Migrate<'info>,bump:u8,account:&AccountInfo<'info>,mint:&InterfaceAccount<'info,Mint>)->Result<()>{
 close_temp_account(a,account,mint,&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])
}
#[inline(always)]
fn close_temp_account<'info>(a:&Migrate<'info>,account:&AccountInfo<'info>,mint:&InterfaceAccount<'info,Mint>,signer_seeds:&[&[&[u8]]])->Result<()>{
 anchor_spl::token_2022::close_account(CpiContext::new_with_signer(base_token_program(AsRef::<AccountInfo>::as_ref(mint),&a.token_program,&a.token_2022_program),anchor_spl::token_2022::CloseAccount{account:account.clone(),destination:a.withdraw_authority.to_account_info(),authority:a.pool_authority.to_account_info()},signer_seeds))
}

pub fn close_pool_authority_account<'info>(a:&Migrate<'info>,bump:u8,account:&AccountInfo<'info>)->Result<()>{
 close_token_account(a,account,&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])
}
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
#[inline(never)]
fn burn_pool_authority_lp<'info>(ctx:&Context<'_,'_,'_,'info,Migrate<'info>>)->Result<()>{
 let a=&ctx.accounts; use anchor_spl::token_2022::spl_token_2022::{extension::StateWithExtensions,state::Account as SplAccount}; let amount={
  let data=a.user_pool_token_account.data.borrow();StateWithExtensions::<SplAccount>::unpack(&data)?.base.amount};
 burn_lp(a,amount,&[&[b"pool-authority",a.mint.key().as_ref(),&[ctx.bumps.pool_authority]]])
}
#[inline(always)]
fn burn_lp<'info>(a:&Migrate<'info>,amount:u64,signer_seeds:&[&[&[u8]]])->Result<()>{
 anchor_spl::token_2022::burn(CpiContext::new_with_signer(a.token_2022_program.to_account_info(),anchor_spl::token_2022::Burn{mint:a.lp_mint.to_account_info(),from:a.user_pool_token_account.to_account_info(),authority:a.pool_authority.to_account_info()},signer_seeds),amount)
}

fn pay_migration_fee<'info>(a:&Migrate<'info>,pool_authority:&UncheckedAccount<'info>,fee:u64)->Result<()>{
 a.bonding_curve.sub_lamports(fee)?;pool_authority.add_lamports(fee)?;
 Ok(())
}
#[derive(Clone)]pub struct DistributionCurve{pub creator:Pubkey,pub quote_mint:Pubkey}
impl Owner for DistributionCurve{fn owner()->Pubkey{crate::ID}}
impl AccountSerialize for DistributionCurve{}
impl AccountDeserialize for DistributionCurve{
 fn try_deserialize(buf:&mut &[u8])->Result<Self>{Self::try_deserialize_unchecked(buf)}
 fn try_deserialize_unchecked(buf:&mut &[u8])->Result<Self>{
  if buf.len()<49 || buf[..8]!=[23,183,248,55,96,216,172,96]{return Err(anchor_lang::solana_program::program_error::ProgramError::InvalidAccountData.into());}
  for offset in [48usize,81,82,123,124]{if buf.len()>offset{let _=bool::deserialize(&mut &buf[offset..offset+1])?;}}
  let creator=if buf.len()>=81{Pubkey::new_from_array(buf[49..81].try_into().unwrap_or_default())}else{Pubkey::default()};
  let quote_mint=if buf.len()>=115{Pubkey::new_from_array(buf[83..115].try_into().unwrap_or_default())}else{Pubkey::default()};Ok(Self{creator,quote_mint})
 }
}
#[inline(never)]
fn refund_pool_authority<'info>(a:&Migrate<'info>,bump:u8,destination:&AccountInfo<'info>,amount:u64)->Result<()>{
 if amount==0{return Ok(());}
 let transfer=|signer_seeds:&[&[&[u8]];1]|crate::migrate::transfer_native(a.system_program.as_ref(),&a.pool_authority,destination,amount,signer_seeds);
 transfer(&[&[b"pool-authority",a.mint.key().as_ref(),&[bump]]])
}
