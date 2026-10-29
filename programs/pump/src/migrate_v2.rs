use crate::*;
use anchor_lang::Event;
use anchor_spl::{token_interface::{Mint,TokenAccount,TokenInterface},token_2022::Token2022,associated_token::AssociatedToken};
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::invoke_signed,program_error::ProgramError};
#[event_cpi]
#[derive(Accounts)]
pub struct MigrateV2<'info>{
 #[account(seeds=[b"global"],bump,has_one=withdraw_authority @ PumpError::NotAuthorized)]pub global:Box<Account<'info,Global>>,
 /// CHECK: global relation.
 #[account(mut)]pub withdraw_authority:UncheckedAccount<'info>,
 pub base_mint:Box<InterfaceAccount<'info,Mint>>,
 pub quote_mint:Box<InterfaceAccount<'info,Mint>>,
 #[account(mut,seeds=[b"bonding-curve",base_mint.key().as_ref()],bump,constraint=quote_mint.key()==bonding_curve.quote_mint||(bonding_curve.quote_mint==Pubkey::default()&&quote_mint.key()==anchor_spl::token::spl_token::native_mint::ID) @ PumpError::MintDoesNotMatchBondingCurve)]pub bonding_curve:Box<Account<'info,crate::trade_types::BondingCurve>>,
 #[account(mut,associated_token::mint=base_mint,associated_token::authority=bonding_curve,associated_token::token_program=base_token_program)]pub associated_base_bonding_curve:Box<InterfaceAccount<'info,TokenAccount>>,
 /// CHECK: canonical quote ATA.
 #[account(mut,seeds=[bonding_curve.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub associated_quote_bonding_curve:UncheckedAccount<'info>,
 #[account(mut)]pub user:Signer<'info>,
 pub system_program:Program<'info,System>,
 pub pump_amm:Program<'info,crate::pump_amm::program::PumpAmm>,
 /// CHECK: canonical PDA.
 #[account(mut,seeds=[b"pool",&0u16.to_le_bytes(),pool_authority.key().as_ref(),base_mint.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=pump_amm.key())]pub pool:UncheckedAccount<'info>,
 /// CHECK: canonical PDA.
 #[account(mut,seeds=[b"pool-authority",base_mint.key().as_ref()],bump)]pub pool_authority:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),base_token_program.key().as_ref(),base_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_authority_mint_account:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_authority_quote_account:UncheckedAccount<'info>,
 /// CHECK: canonical AMM config.
 #[account(seeds=[b"global_config"],bump,seeds::program=pump_amm.key())]pub amm_global_config:UncheckedAccount<'info>,

 /// CHECK: canonical LP base_mint.
 #[account(mut,seeds=[b"pool_lp_mint",pool.key().as_ref()],bump,seeds::program=pump_amm.key())]pub lp_mint:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool_authority.key().as_ref(),token_2022_program.key().as_ref(),lp_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub user_pool_token_account:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool.key().as_ref(),base_token_program.key().as_ref(),base_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_base_token_account:UncheckedAccount<'info>,
 /// CHECK: canonical ATA.
 #[account(mut,seeds=[pool.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=associated_token_program.key())]pub pool_quote_token_account:UncheckedAccount<'info>,
 pub base_token_program:Interface<'info,TokenInterface>,
 pub quote_token_program:Interface<'info,TokenInterface>,
 pub token_2022_program:Program<'info,Token2022>,
 pub associated_token_program:Program<'info,AssociatedToken>,
 /// CHECK: canonical AMM event PDA.
 pub pump_amm_event_authority:UncheckedAccount<'info>,
 /// CHECK: constrained sysvar address.
 #[account(address=anchor_lang::solana_program::sysvar::rent::ID)]pub rent:UncheckedAccount<'info>,
}







































pub use pump_token_ext::required_quote_account_len;




















#[inline(always)]fn transfer_from_curve<'info>(a:&MigrateV2<'info>,from:&InterfaceAccount<'info,TokenAccount>,mint:&InterfaceAccount<'info,Mint>,authority:&Account<'info,crate::trade_types::BondingCurve>,amount:u64,signer_seeds:&[&[&[u8]]])->Result<()>{if amount==0{return Ok(())}let decimals=mint.decimals;anchor_spl::token_2022::transfer_checked(CpiContext::new_with_signer(a.base_token_program.to_account_info(),anchor_spl::token_2022::TransferChecked{from:from.to_account_info(),to:a.pool_authority_mint_account.to_account_info(),authority:authority.to_account_info(),mint:mint.to_account_info()},signer_seeds),amount,decimals)}fn amount(a:&AccountInfo)->Result<u64>{Ok(u64::from_le_bytes(a.try_borrow_data()?[64..72].try_into().unwrap()))}
#[inline(always)]fn burn_with_seeds<'info>(a:&MigrateV2<'info>,amount:u64,signer_seeds:&[&[&[u8]]])->Result<()>{anchor_spl::token_2022::burn(CpiContext::new_with_signer(a.token_2022_program.to_account_info(),anchor_spl::token_2022::Burn{mint:a.lp_mint.to_account_info(),from:a.user_pool_token_account.to_account_info(),authority:a.pool_authority.to_account_info()},signer_seeds),amount)}






























































































































pub fn execute<'info>(ctx:Context<'_, '_, '_, 'info,MigrateV2<'info>>)->Result<()>{
 let a=&ctx.accounts;
 crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;
 let (expected_event_authority,_)=Pubkey::find_program_address(&[b"__event_authority"],&pump_amm::ID);



 require_keys_eq!(a.pump_amm_event_authority.key(),expected_event_authority,anchor_lang::error::ErrorCode::ConstraintSeeds);





 require!(a.bonding_curve.complete,PumpError::BondingCurveNotComplete);
 let migrated=a.bonding_curve.real_quote_reserves==0&&a.bonding_curve.virtual_quote_reserves==0&&a.bonding_curve.real_token_reserves==0&&a.bonding_curve.virtual_token_reserves==0;if migrated{msg!("Bonding curve already migrated");return Ok(());}
 let native=a.bonding_curve.quote_mint==Pubkey::default();
 let fee=a.global.pool_migration_fee;
 pay_migration_fee(a,&a.pool_authority,native,fee)?;
 let bump=ctx.bumps.pool_authority;
 create_token_account_v2(&ctx,&a.pool_base_token_account,&a.pool,&a.base_mint,native,&a.base_token_program)?;
 create_token_account_v2(&ctx,&a.pool_quote_token_account,&a.pool,&a.quote_mint,native,&a.quote_token_program)?;
 create_token_account_v2(&ctx,&a.pool_authority_mint_account,&a.pool_authority,&a.base_mint,native,&a.base_token_program)?;
 let quote_account_created=a.pool_authority_quote_account.owner==&anchor_lang::system_program::ID;
 create_token_account_v2(&ctx,&a.pool_authority_quote_account,&a.pool_authority,&a.quote_mint,native,&a.quote_token_program)?;
 transfer_base_to_pool_authority(a,ctx.bumps.bonding_curve)?;
 let base=pool_authority_mint_token_account(a)?.amount;














































 let quote=a.bonding_curve.real_quote_reserves.checked_add(a.bonding_curve.post_complete_quote_in)
  .ok_or_else(||error!(PumpError::Overflow))?;



 let quote=if native{quote.checked_sub(fee).ok_or_else(||error!(PumpError::Overflow))?}else{quote};
 let quote_before=quote_amount(&a.pool_authority_quote_account)?;
 fund_quote_token_account_v2(&ctx,quote,native)?;










 let quote=quote_amount(&a.pool_authority_quote_account)?.checked_sub(quote_before).ok_or_else(||error!(PumpError::Overflow))?;
 create_pool(&ctx,base,quote)?;
 init_pump_amm_boost_v2(&ctx)?;
 close_pool_authority_account(a,bump,&a.pool_authority_mint_account,&a.base_token_program)?;
 if quote_account_created{
  if crate::transfer_fee_recovered::get_transfer_fee(&a.quote_mint.to_account_info())?.is_some(){



   require!(a.quote_mint.to_account_info().is_writable,PumpError::QuoteMintNotWritable);
   harvest_withheld_tokens_to_mint(&a.quote_token_program.to_account_info(),&a.quote_mint.to_account_info(),&a.pool_authority_quote_account)?;
  }
  close_pool_authority_account(a,bump,&a.pool_authority_quote_account,&a.quote_token_program)?;
 }
 burn_lp_tokens(&ctx,bump)?;
 close_lp_account(a,bump,&a.user_pool_token_account)?;
 refund_pool_authority(a,bump,&a.withdraw_authority,a.pool_authority.lamports())?;
 {let c:&mut crate::trade_types::BondingCurve=&mut ctx.accounts.bonding_curve;c.real_quote_reserves=0;c.real_token_reserves=0;c.virtual_quote_reserves=0;c.virtual_token_reserves=0;}
 let a=&ctx.accounts;
 let event=CompletePumpAmmMigrationEvent{user:a.user.key(),mint:a.base_mint.key(),mint_amount:base,sol_amount:quote,pool_migration_fee:fee,bonding_curve:a.bonding_curve.key(),timestamp:Clock::get()?.unix_timestamp,pool:a.pool.key(),quote_mint:a.bonding_curve.quote_mint};
 emit!(event);emit_cpi!(event);
 Ok(())
}









// The original migration skips an empty refund before constructing signer seeds.
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad

// Original: standalone pub helper wrapping anchor_spl's Token-2022 harvest CPI (window 0x95610 calls
// anchor_spl::token_2022_extensions::harvest_withheld_tokens_to_mint @0x184e38 with vec![source]).
pub use crate::withheld::harvest_withheld_tokens_to_mint as harvest_withheld_tokens_to_mint;
#[inline(never)]
fn create_token_account_v2<'info>(ctx:&Context<'_,'_,'_,'info,MigrateV2<'info>>,account:&AccountInfo<'info>,wallet:&AccountInfo<'info>,mint:&Box<InterfaceAccount<'info,Mint>>,native:bool,token_program:&AccountInfo<'info>)->Result<()>{
 let bump=ctx.bumps.pool_authority;let a=&ctx.accounts;let token_program=token_program.clone();let tp=&token_program;
 if native{
  cta_signed(a,&a.bonding_curve,account,wallet,mint,token_program,&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]])?;
 }else{
  let mint_info:&AccountInfo<'info>;anchor_lang::solana_program::program::invoke(&Instruction{program_id:anchor_spl::associated_token::ID,accounts:vec![AccountMeta::new(a.user.key(),true),AccountMeta::new(account.key(),false),AccountMeta::new_readonly(wallet.key(),false),AccountMeta::new_readonly({mint_info=mint.as_ref().as_ref();mint_info.key()},false),AccountMeta::new_readonly(a.system_program.key(),false),AccountMeta::new_readonly(tp.key(),false)],data:anchor_lang::prelude::borsh::to_vec(&1u8).unwrap()},&[a.user.to_account_info(),account.clone(),wallet.clone(),mint_info.clone(),a.system_program.to_account_info(),token_program])?;
 }
 Ok(())
}
#[inline(never)]fn transfer_base_to_pool_authority<'info>(a:&MigrateV2<'info>,bump:u8)->Result<()>{transfer_from_curve(a,&a.associated_base_bonding_curve,&a.base_mint,&a.bonding_curve,a.associated_base_bonding_curve.amount,&[&[b"bonding-curve",a.base_mint.key().as_ref(),&[bump]]])}
// layout-pad

// layout-pad
// layout-pad
// layout-pad

#[inline(always)]
fn close_token_account<'info>(a:&MigrateV2<'info>,account:&AccountInfo<'info>,signer_seeds:&[&[&[u8]]],token_program:&AccountInfo<'info>)->Result<()>{
 anchor_spl::token_2022::close_account(CpiContext::new_with_signer(token_program.clone(),anchor_spl::token_2022::CloseAccount{account:account.clone(),destination:a.withdraw_authority.to_account_info(),authority:a.pool_authority.to_account_info()},signer_seeds))
}

// Original: standalone pool-creation helper (window 0x502f0) calling the generated pump_amm client (Round46 form).
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
#[inline(never)]
fn fund_quote_token_account_v2<'info>(ctx:&Context<'_,'_,'_,'info,MigrateV2<'info>>,amount:u64,native:bool)->Result<()>{
 let a=&ctx.accounts;
 if native{
  a.bonding_curve.sub_lamports(amount)?;a.pool_authority_quote_account.add_lamports(amount)?;
  anchor_lang::solana_program::program::invoke(&Instruction{program_id:anchor_spl::token::ID,accounts:vec![AccountMeta::new(a.pool_authority_quote_account.key(),false),AccountMeta::new_readonly(a.rent.key(),false),AccountMeta::new(a.bonding_curve.key(),false)],data:anchor_spl::token::spl_token::instruction::TokenInstruction::SyncNative.pack()},&[a.pool_authority_quote_account.to_account_info(),a.rent.to_account_info(),a.bonding_curve.to_account_info()])?;
 }else{
  tq(a,&a.quote_mint,&a.associated_quote_bonding_curve,&a.bonding_curve,amount,&[&[b"bonding-curve",a.base_mint.key().as_ref(),&[ctx.bumps.bonding_curve]]])?;
 }
 Ok(())
}
#[inline(always)]
fn tq<'info>(a:&MigrateV2<'info>,mint:&InterfaceAccount<'info,Mint>,from:&AccountInfo<'info>,authority:&Account<'info,crate::trade_types::BondingCurve>,amount:u64,signer_seeds:&[&[&[u8]]])->Result<()>{
 if amount==0{return Ok(())}
 let decimals=mint.decimals;let mint_info:&AccountInfo<'info>=mint.as_ref();
 anchor_spl::token_2022::transfer_checked(CpiContext::new_with_signer(a.quote_token_program.to_account_info(),anchor_spl::token_2022::TransferChecked{from:from.clone(),to:a.pool_authority_quote_account.to_account_info(),authority:authority.to_account_info(),mint:mint_info.clone()},signer_seeds),amount,decimals)
}
fn create_pool<'info>(ctx:&Context<'_,'_,'_,'info,MigrateV2<'info>>,base:u64,quote:u64)->Result<()>{
 let bump=ctx.bumps.pool_authority;let a=&ctx.accounts;
 let create=move |signer_seeds:&[&[&[u8]];1]|pump_amm::cpi::create_pool(CpiContext::new_with_signer(a.pump_amm.to_account_info(),pump_amm::cpi::accounts::CreatePool{pool:a.pool.to_account_info(),global_config:a.amm_global_config.to_account_info(),creator:a.pool_authority.to_account_info(),base_mint:a.base_mint.to_account_info(),quote_mint:a.quote_mint.to_account_info(),lp_mint:a.lp_mint.to_account_info(),user_base_token_account:a.pool_authority_mint_account.to_account_info(),user_quote_token_account:a.pool_authority_quote_account.to_account_info(),user_pool_token_account:a.user_pool_token_account.to_account_info(),pool_base_token_account:a.pool_base_token_account.to_account_info(),pool_quote_token_account:a.pool_quote_token_account.to_account_info(),system_program:a.system_program.to_account_info(),token_2022_program:a.token_2022_program.to_account_info(),base_token_program:a.base_token_program.to_account_info(),quote_token_program:a.quote_token_program.to_account_info(),associated_token_program:a.associated_token_program.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()},signer_seeds),0,base,quote,a.bonding_curve.creator,a.bonding_curve.is_mayhem_mode,pump_amm::types::OptionBool(a.bonding_curve.is_cashback_coin),pump_amm::types::OptionU64(a.bonding_curve.creator_fee_bps),pump_amm::types::OptionBool(a.bonding_curve.can_edit_creator_fee),pump_amm::types::OptionBool(a.bonding_curve.is_holder_reward));
 create(&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]])
}
pub(crate) fn boost_enabled(config: &AccountInfo) -> bool {
    let Ok(data) = config.try_borrow_data() else { return false };
    let mut buf: &[u8] = &data;
    crate::pump_amm::accounts::GlobalConfig::try_deserialize(&mut buf).map_or(false, |global_config| global_config.boost_enabled)
}
#[inline(always)]
fn cta_signed<'info>(a:&MigrateV2<'info>,curve:&Account<'info,crate::trade_types::BondingCurve>,account:&AccountInfo<'info>,wallet:&AccountInfo<'info>,mint:&InterfaceAccount<'info,Mint>,token_program:AccountInfo<'info>,signer_seeds:&[&[&[u8]]])->anchor_lang::solana_program::entrypoint::ProgramResult{
 let ix=Instruction{program_id:anchor_spl::associated_token::ID,accounts:vec![AccountMeta::new(a.pool_authority.key(),true),AccountMeta::new(account.key(),false),AccountMeta::new_readonly(wallet.key(),false),AccountMeta::new_readonly(mint.key(),false),AccountMeta::new_readonly(a.system_program.key(),false),AccountMeta::new_readonly(token_program.key(),false),AccountMeta::new_readonly(curve.key(),false)],data:anchor_lang::prelude::borsh::to_vec(&1u8).unwrap()};
 invoke_signed(&ix,&[a.pool_authority.to_account_info(),account.clone(),wallet.clone(),mint.to_account_info(),a.system_program.to_account_info(),token_program,curve.to_account_info()],signer_seeds)
}
































































































































































































































#[inline(never)]
pub fn init_pump_amm_boost_v2<'info>(ctx:&Context<'_,'_,'_,'info,MigrateV2<'info>>)->Result<()>{
 let a=&ctx.accounts;
 if a.bonding_curve.is_mayhem_mode{return Ok(());}
 let [boost,vault]=ctx.remaining_accounts else {
  require!(!crate::migrate::native_payments::boost_enabled(&a.amm_global_config),PumpError::NotEnoughRemainingAccounts);
  return Ok(());
 };
 let initial_balance=a.pool_authority.lamports();
 let funding=Rent::get()?.minimum_balance(qsize(ctx)?);
 crate::migrate::native_payments::transfer_native(a.system_program.as_ref(),&a.user,&a.pool_authority,funding)?;
 let bump=ctx.bumps.pool_authority;{let init=move||(move|signer_seeds:&[&[&[u8]];1]|pump_amm::cpi::init_boost(CpiContext::new_with_signer(a.pump_amm.to_account_info(),pump_amm::cpi::accounts::InitBoost{pool:a.pool.to_account_info(),global_config:a.amm_global_config.to_account_info(),creator:a.pool_authority.to_account_info(),base_mint:a.base_mint.to_account_info(),quote_mint:a.quote_mint.to_account_info(),pool_base_token_account:a.pool_base_token_account.to_account_info(),pool_quote_token_account:a.pool_quote_token_account.to_account_info(),boost_vault_authority:boost.clone(),boost_vault:vault.clone(),quote_token_program:a.quote_token_program.to_account_info(),system_program:a.system_program.to_account_info(),associated_token_program:a.associated_token_program.to_account_info(),event_authority:a.pump_amm_event_authority.to_account_info(),program:a.pump_amm.to_account_info()},signer_seeds)))(&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]]);init()?;}
 let after_balance=a.pool_authority.lamports();let user=a.user.to_account_info();
 refund_pool_authority(a,bump,&user,after_balance.saturating_sub(initial_balance))?;
 crate::migrate::native_payments::transfer_native(a.system_program.as_ref(),&a.user,&a.pool_authority,initial_balance.saturating_sub(after_balance))?;
 Ok(())
}











































































fn qsize<'info>(ctx:&Context<'_,'_,'_,'info,MigrateV2<'info>>)->Result<usize>{
 let a=&ctx.accounts;if a.quote_token_program.key()==anchor_spl::token::ID{return Ok(165)}
 required_quote_account_len(&a.quote_mint.to_account_info().try_borrow_data()?).ok_or_else(||error!(PumpError::UnsupportedQuoteMint))
}

fn pay_migration_fee<'info>(a:&MigrateV2<'info>,pool_authority:&UncheckedAccount<'info>,native:bool,fee:u64)->Result<()>{
 if native{a.bonding_curve.sub_lamports(fee)?;pool_authority.add_lamports(fee)?;}else{crate::migrate::native_payments::transfer_native(a.system_program.as_ref(),&a.user,pool_authority,fee)?;}
 Ok(())
}
// layout-pad(62): aligns the next Source site with the original line
#[inline(never)]
pub fn pool_authority_mint_token_account(a:&MigrateV2)->Result<TokenAccount>{
 let data=a.pool_authority_mint_account.try_borrow_data()?;
 TokenAccount::try_deserialize_unchecked(&mut &data[..])
}
fn quote_amount(a:&AccountInfo)->Result<u64>{let d=a.try_borrow_data()?;let t=TokenAccount::try_deserialize(&mut &d[..])?;Ok(t.amount)}
pub fn close_pool_authority_account<'info>(a:&MigrateV2<'info>,bump:u8,account:&AccountInfo<'info>,token_program:&Interface<'info,TokenInterface>)->Result<()>{
 close_token_account(a,account,&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]],token_program)
}
pub fn close_lp_account<'info>(a:&MigrateV2<'info>,bump:u8,account:&AccountInfo<'info>)->Result<()>{
 close_token_account(a,account,&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]],&a.token_2022_program)
}

















































#[inline(never)]
fn burn_lp_tokens<'info>(ctx:&Context<'_,'_,'_,'info,MigrateV2<'info>>,bump:u8)->Result<()>{
 let a=&ctx.accounts;
 let amount={
  let data=a.user_pool_token_account.data.borrow();
  anchor_spl::token_2022::spl_token_2022::extension::StateWithExtensions::<anchor_spl::token_2022::spl_token_2022::state::Account>::unpack(&data)?.base.amount};
 burn_with_seeds(a,amount,&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]])}
#[inline(never)]
fn refund_pool_authority<'info>(a:&MigrateV2<'info>,bump:u8,destination:&AccountInfo<'info>,amount:u64)->Result<()>{
 if amount==0{return Ok(());}
 let transfer=|signer_seeds:&[&[&[u8]];1]|crate::migrate::transfer_native(a.system_program.as_ref(),&a.pool_authority,destination,amount,signer_seeds);
 transfer(&[&[b"pool-authority",a.base_mint.key().as_ref(),&[bump]]])
}
