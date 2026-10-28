use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self, Mint, TokenAccount, TokenInterface, TransferChecked};
use crate::{Global, PumpError};
#[path="v3_native_transfer_fee.rs"] pub mod native_transfer_fee;
use crate::trade_types::{BondingCurve, FeeConfig, Fees, TradeEvent};
const FEE_PROGRAM: Pubkey = anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
const WSOL: Pubkey = anchor_lang::solana_program::pubkey!("So11111111111111111111111111111111111111112");
#[derive(Accounts)]
pub struct SellV3<'info> {
    #[account(seeds=[b"global"],bump)]
    pub global: Box<Account<'info, Global>>,
    pub base_mint: Box<InterfaceAccount<'info, Mint>>,
    pub quote_mint: Box<InterfaceAccount<'info, Mint>>,
    pub base_token_program: Interface<'info, TokenInterface>,
    pub quote_token_program: Interface<'info, TokenInterface>,
    #[account(mut,seeds=[b"bonding-curve",base_mint.key().as_ref()],bump,
        constraint=quote_mint.key()==bonding_curve.quote_mint || (bonding_curve.quote_mint==Pubkey::default() && quote_mint.key()==WSOL) @ PumpError::MintDoesNotMatchBondingCurve)]
    pub bonding_curve: Box<Account<'info, BondingCurve>>,
    #[account(mut,associated_token::mint=base_mint,associated_token::authority=bonding_curve,associated_token::token_program=base_token_program)]
    pub associated_base_bonding_curve: Box<InterfaceAccount<'info, TokenAccount>>,
    /// CHECK: PDA seeds are checked here; the quote branch validates token data.
    #[account(mut,seeds=[bonding_curve.key().as_ref(),quote_token_program.key().as_ref(),quote_mint.key().as_ref()],bump,seeds::program=anchor_spl::associated_token::ID)]
    pub associated_quote_bonding_curve: UncheckedAccount<'info>,
    #[account(mut)]
    pub user: Signer<'info>,
    #[account(mut,token::mint=base_mint)]
    pub associated_base_user: Box<InterfaceAccount<'info, TokenAccount>>,
    /// CHECK: token-quote checks validate owner, mint and relevant authority/address.
    #[account(mut)]
    pub associated_quote_user: UncheckedAccount<'info>,
    /// The original initializes this account on first use even when volume tracking is disabled.
    #[account(init_if_needed,payer=user,space=137,seeds=[b"user_volume_accumulator",user.key().as_ref()],bump)]
    pub user_volume_accumulator: Box<Account<'info,crate::UserVolumeAccumulator>>,
    /// CHECK: cross-program FeeConfig owner, address and serialization checked.
    #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump=fee_config.0.bump,seeds::program=FEE_PROGRAM)]
    pub fee_config: Box<Account<'info, crate::multi_hop_curve::RouteFeeConfig>>,
    /// CHECK: membership in global buyback recipients is checked in handler.
    #[account(mut)]
    pub buyback_fee_recipient: UncheckedAccount<'info>,
    pub system_program: Program<'info, System>,
    /// CHECK: PDA for signed event emission.
    #[account(seeds=[b"__event_authority"],bump)]
    pub event_authority: AccountInfo<'info>,
    pub program: Program<'info,crate::program::PumpRecovered>,
}
fn sub(a:u64,b:u64)->Result<u64>{a.checked_sub(b).ok_or_else(||error!(PumpError::Overflow))}
fn narrow(a:u128)->Result<u64>{u64::try_from(a).map_err(|_|error!(PumpError::Truncation))}
fn fee(a:u64,b:u64)->Result<u64>{narrow((a as u128*b as u128+9999)/10000)}

fn v3_buyback_split(protocol_fee:u64,buyback_bps:u64)->(u64,u64) {
    let buyback_fee=u64::try_from(protocol_fee as u128*buyback_bps as u128/10000)
        .expect("buyback fee is at most protocol_fee");
    let retained=protocol_fee.checked_sub(buyback_fee)
        .expect("buyback_fee never exceeds protocol_fee");
    (buyback_fee,retained)
}
fn selected(config:&FeeConfig,cap:u128,quote:Pubkey)->Result<Fees>{
    let tiers=if quote==Pubkey::default() || quote==WSOL || quote==QUOTE_2 {
        &config.fee_tiers
    }else if quote==USDC {
        &config.stable_fee_tiers
    }else{
        let fees=&config.exotic_flat_fees;
        return Ok(if fees.lp_fee_bps!=0 || fees.protocol_fee_bps!=0 || fees.creator_fee_bps!=0 {
            fees.clone()
        }else{config.flat_fees.clone()});
    };
    let first=tiers.first().ok_or_else(||error!(PumpError::FeeTiersEmpty))?;
    if cap<first.market_cap_lamports_threshold{return Ok(first.fees.clone())}
    Ok(tiers.iter().rev().find(|t|t.market_cap_lamports_threshold<=cap).unwrap_or(first).fees.clone())
}
/// Validate the shared curve flags before quote or amount-specific checks.
#[inline(never)]
pub fn validate_trade(complete:u8,cashback:u64,allow_cashback:u64)->Result<()> {
    require!(complete==0,PumpError::BondingCurveComplete);
    require!(allow_cashback!=0 || cashback as u8==0,PumpError::CashbackCoinNotSupported);
    Ok(())
}
#[inline(never)]
fn add3(a:u64,b:u64,c:u64)->Result<u64>{a.checked_add(b).and_then(|x|x.checked_add(c)).ok_or_else(||error!(PumpError::Overflow))}
#[inline(never)]
fn sub3(a:u64,b:u64,c:u64)->Result<u64>{a.checked_sub(b).and_then(|x|x.checked_sub(c)).ok_or_else(||error!(PumpError::Overflow))}
/// Gross-up of the pool-side quote by the quote mint's transfer fee; the fee is re-derived from the gross.
#[inline(always)]
fn gross_up_quote(quote_fee:&Option<(u64,u64,u64)>,is_sol:bool,net:u64)->Result<(u64,u64)>{
    let gross=add(net,if is_sol{0}else{quote_fee_for_amount(quote_fee,net,true)?})?;
    let quote_transfer_fee=gross.checked_sub(net).ok_or_else(||error!(PumpError::Overflow))?;
    Ok((gross,quote_transfer_fee))
}
fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}

pub fn buy(ctx:Context<SellV3>,amount:u64,max_sol_cost:u64,partial_fill:bool)->Result<()> {
    let a=&mut *ctx.accounts;
    if a.user_volume_accumulator.user==Pubkey::default(){a.user_volume_accumulator.user=a.user.key();}
    crate::trade_types::prepare_bonding_curve(&a.bonding_curve, &a.system_program, &a.user)?;
    validate_trade(a.bonding_curve.complete as u8,a.bonding_curve.is_cashback_coin as u64,0)?;
    let requested_amount=amount;
    let amount=amount.min(a.bonding_curve.real_token_reserves);
    require_gt!(amount,0,PumpError::BuyZeroAmount);
    let (quote_decimals,quote_fee)=check_quote(a)?;
    let is_sol=quote_decimals.is_none();
    if is_sol{a.global.validate_buyback_fee_recipient(a.buyback_fee_recipient.key())?;}
    let curve=&a.bonding_curve;
    let is_fee_exempt=a.user.key()==a.global.whitelist_pda;
    let exceeds=requested_amount>amount;
    if (curve.is_mayhem_mode || is_fee_exempt) && !partial_fill{require_gte!(curve.real_token_reserves,requested_amount,PumpError::NotEnoughTokensToBuy);}
    let crossing=exceeds && !curve.is_mayhem_mode && !is_fee_exempt;
    let denominator=(curve.virtual_token_reserves as u128).checked_sub(amount as u128).ok_or_else(||error!(PumpError::Overflow))?;
    let quotient=(amount as u128*curve.virtual_quote_reserves as u128).checked_div(denominator).ok_or_else(||error!(PumpError::DivisionByZero))?;
    let quote=u64::try_from(quotient.checked_add(1).ok_or_else(||error!(PumpError::Overflow))?).map_err(|_|error!(PumpError::Truncation))?;
    let (fees,creator_bps)=if is_fee_exempt {
        (Fees{lp_fee_bps:0,protocol_fee_bps:0,creator_fee_bps:0},0)
    }else{
        let cap=buy_fee_market_cap(curve, &a.base_mint)?;
        let config_info=a.fee_config.to_account_info();
        let config_data=config_info.try_borrow_data()?;
        let config=read_config(&config_data)?;
        drop(config_data);
        let mut fees=selected(&config,cap,curve.quote_mint)?;
        if a.global.creator_fee_configurable && curve.creator_fee_bps>0{fees.creator_fee_bps=curve.creator_fee_bps;}
        let creator_bps=if curve.creator==Pubkey::default(){0}else{fees.creator_fee_bps};
        (fees,creator_bps)
    };
    let protocol_fee=fee(quote,fees.protocol_fee_bps)?;
    let creator_fee=fee(quote,creator_bps)?;
    let buyback_bps=if curve.is_mayhem_mode {0}else{a.global.buyback_basis_points};
    let pool_base_before=if crossing{sub(a.associated_base_bonding_curve.amount,amount)?}else{0};
    let pool_quote_before=if crossing{sub(add(curve.real_quote_reserves,quote)?,if is_sol{a.global.pool_migration_fee}else{0})?}else{0};
    if crossing{require_gt!(pool_base_before,0,PumpError::NotEnoughTokensToBuy);require_gt!(pool_quote_before,0,PumpError::Overflow);}
    let post_base=if crossing{sub(requested_amount,amount)?}else{0};
    let post_quote=if crossing{
        require_gt!(pool_base_before,post_base,PumpError::NotEnoughTokensToBuy);
        let numerator=post_base as u128*pool_quote_before as u128;
        let denominator=(pool_base_before-post_base) as u128;
        narrow(crate::legacy_sell::fee_cpi::checked_ceil_div(numerator,denominator)?)?
    }else{0};
    let post_protocol=if crossing{fee(post_quote,fees.protocol_fee_bps)?}else{0};
    let post_creator=if crossing{fee(post_quote,creator_bps)?}else{0};
    let (buyback_fee,retained)=v3_buyback_split(protocol_fee,buyback_bps);
    let (post_buyback,post_retained)=v3_buyback_split(post_protocol,buyback_bps);
    let transfer_base=add(amount,post_base)?;
    let total_buyback=add(buyback_fee,post_buyback)?;
    let first_cost=add3(quote,protocol_fee,creator_fee)?;
    let user_output=add(first_cost,add(add(post_quote,post_protocol)?,post_creator)?)?;
    let net_pool_quote=sub(user_output,total_buyback)?;
    let buyback_received=if is_sol{buyback_fee}else{sub(buyback_fee,quote_fee_for_amount(&quote_fee,buyback_fee,false)?)?};
    let (pool_quote,quote_transfer_fee)=gross_up_quote(&quote_fee,is_sol,net_pool_quote)?;
    require_gte!(max_sol_cost,add(pool_quote,total_buyback)?,PumpError::TooMuchSolRequired);
    let next_base=sub(curve.virtual_token_reserves,amount)?;
    let next_quote=add(curve.virtual_quote_reserves,quote)?;
    let next_real_base=sub(curve.real_token_reserves,amount)?;
    let next_real_quote=add(curve.real_quote_reserves,quote)?;
    let next_creator=add(add(curve.creator_fee,creator_fee)?,post_creator)?;
    let next_protocol=add(add(curve.protocol_fees,retained)?,post_retained)?;
    let mint_key=a.base_mint.key();let bump=[ctx.bumps.bonding_curve];
    let seeds:&[&[u8]]=&[b"bonding-curve",mint_key.as_ref(),&bump];
    token_interface::transfer_checked(CpiContext::new_with_signer(a.base_token_program.to_account_info(),TransferChecked{
        from:a.associated_base_bonding_curve.to_account_info(),mint:a.base_mint.to_account_info(),to:a.associated_base_user.to_account_info(),authority:a.bonding_curve.to_account_info()
    },&[seeds]),transfer_base,a.base_mint.decimals)?;
    user_quote_payments::transfer_from_user(
        is_sol,a.system_program.as_ref(),&a.user,a.bonding_curve.as_ref(),
        if is_sol{user_output}else{pool_quote},&a.quote_token_program,
        quote_decimals.unwrap_or_default(),a.quote_mint.as_ref().as_ref(),
        if is_sol{None}else{Some(a.associated_quote_user.as_ref())},
        if is_sol{None}else{Some(a.associated_quote_bonding_curve.as_ref())},
    )?;
    if let Some(decimals)=quote_decimals {
      crate::collect_v2::transfer_user_quote_tokens(&a.quote_token_program,&a.associated_quote_user,&a.buyback_fee_recipient,a.user.as_ref(),decimals,a.quote_mint.as_ref().as_ref(),total_buyback)?;
    }else{
      a.bonding_curve.sub_lamports(total_buyback)?;a.buyback_fee_recipient.add_lamports(total_buyback)?;
    }
    let curve=&mut a.bonding_curve;
    curve.apply_buy(amount,quote)?;
    let _=curve.accrue_fees(&a.global,protocol_fee,creator_fee)?;let _=curve.accrue_fees(&a.global,post_protocol,post_creator)?;
    if crossing{curve.post_complete_base_out=post_base;curve.post_complete_quote_in=post_quote;}
    let event=TradeEvent{
        mint:a.base_mint.key(),sol_amount:if is_sol{quote}else{0},token_amount:amount,is_buy:true,user:a.user.key(),timestamp:Clock::get()?.unix_timestamp,
        virtual_sol_reserves:if is_sol{next_quote}else{0},virtual_token_reserves:next_base,real_sol_reserves:if is_sol{next_real_quote}else{0},real_token_reserves:next_real_base,
        fee_recipient:Pubkey::default(),fee_basis_points:fees.protocol_fee_bps,fee:protocol_fee,creator:curve.creator,creator_fee_basis_points:fees.creator_fee_bps,creator_fee,
        track_volume:false,total_unclaimed_tokens:0,total_claimed_tokens:0,current_sol_volume:0,last_update_timestamp:0,ix_name:"buy".into(),mayhem_mode:curve.is_mayhem_mode,
        cashback_fee_basis_points:0,cashback:0,buyback_fee_basis_points:buyback_bps,buyback_fee:buyback_received,shareholders:vec![],quote_mint:curve.quote_mint,
        quote_amount:quote,virtual_quote_reserves:next_quote,real_quote_reserves:next_real_quote,holder_rewards_bps:if curve.is_holder_reward{fees.creator_fee_bps}else{0},holder_rewards:if curve.is_holder_reward{creator_fee}else{0},creator_fee_unclaimed:next_creator,
        unparsed_trailing_field:quote_transfer_fee,
    };
    let completion=if next_real_base==0 {
        a.bonding_curve.complete=true;
        Some(crate::trade_types::CompleteEvent{user:a.user.key(),mint:a.base_mint.key(),bonding_curve:a.bonding_curve.key(),timestamp:Clock::get()?.unix_timestamp,quote_mint:a.bonding_curve.quote_mint})
    }else{None};
    let post_event=if crossing{Some(PostCompleteBuyEvent{user:a.user.key(),mint:a.base_mint.key(),bonding_curve:a.bonding_curve.key(),quote_mint:a.bonding_curve.quote_mint,timestamp:Clock::get()?.unix_timestamp,base_out:post_base,quote_in:post_quote,fee_basis_points:fees.protocol_fee_bps,fee:post_protocol,creator_fee_basis_points:fees.creator_fee_bps,creator_fee:post_creator,buyback_fee:post_buyback,pool_base_reserves_before:pool_base_before,pool_quote_reserves_before:pool_quote_before,pool_base_reserves_after:sub(pool_base_before,post_base)?,pool_quote_reserves_after:add(pool_quote_before,post_quote)?})}else{None};
    emit!(event.clone());emit_cpi!(event);
    if let Some(completion)=completion {emit!(completion.clone());emit_cpi!(completion);}
    if let Some(post_event)=post_event{emit!(post_event.clone());emit_cpi!(post_event);}
    Ok(())
}

pub fn buy_exact_quote(ctx:Context<SellV3>,spendable_quote_in:u64,min_tokens_out:u64,partial_fill:bool)->Result<()> {
    let a=&mut *ctx.accounts;
    if a.user_volume_accumulator.user==Pubkey::default(){a.user_volume_accumulator.user=a.user.key();}
    crate::trade_types::prepare_bonding_curve(&a.bonding_curve, &a.system_program, &a.user)?;
    validate_trade(a.bonding_curve.complete as u8,a.bonding_curve.is_cashback_coin as u64,0)?;
    require_gt!(min_tokens_out,0,PumpError::BuyZeroAmount);
    require_gt!(spendable_quote_in,0,PumpError::BuyNotEnoughSolToCoverFees);
    let (quote_decimals,quote_fee)=check_quote(a)?;
    let is_sol=quote_decimals.is_none();
    if is_sol{a.global.validate_buyback_fee_recipient(a.buyback_fee_recipient.key())?;}
    let available=if is_sol{spendable_quote_in}else{quote_post_fee_amount(&quote_fee,spendable_quote_in)?};
    let curve=&a.bonding_curve;
    let is_fee_exempt=a.user.key()==a.global.whitelist_pda;
    let (fees,creator_bps)=if is_fee_exempt {
        (Fees{lp_fee_bps:0,protocol_fee_bps:0,creator_fee_bps:0},0)
    }else{
        let cap=buy_fee_market_cap(curve, &a.base_mint)?;
        let config_info=a.fee_config.to_account_info();
        let config_data=config_info.try_borrow_data()?;
        if config_data.len()<8{return Err(error!(anchor_lang::error::ErrorCode::AccountDiscriminatorNotFound));}
        require!(config_data[..8]==[143,52,146,187,219,123,76,155],anchor_lang::error::ErrorCode::AccountDiscriminatorMismatch);
        let mut config=FeeConfig::deserialize(&mut &config_data[8..]).map_err(|_|error!(anchor_lang::error::ErrorCode::AccountDidNotDeserialize))?;
        if config_data.len()<4073{config.stable_fee_tiers.clear();}
        if config_data.len()<4097{config.exotic_flat_fees=Fees{lp_fee_bps:0,protocol_fee_bps:0,creator_fee_bps:0};}
        require!(config_data.len()>=2512,PumpError::FeeConfigTooShort);
        drop(config_data);
        let mut fees=selected(&config,cap,curve.quote_mint)?;
        if a.global.creator_fee_configurable && curve.creator_fee_bps>0{fees.creator_fee_bps=curve.creator_fee_bps;}
        let creator_bps=if curve.creator==Pubkey::default(){0}else{fees.creator_fee_bps};
        (fees,creator_bps)
    };
    let _=fee(available,fees.protocol_fee_bps)?;
    let _=fee(available,creator_bps)?;
    let quote_budget=net_quote(available,fees.protocol_fee_bps,creator_bps)?;
    let raw_quote=narrow(available as u128*10000/(10000u128+fees.protocol_fee_bps as u128+creator_bps as u128))?;require_gt!(raw_quote,0,PumpError::BuyNotEnoughSolToCoverFees);
    require_gt!(quote_budget,0,PumpError::BuySlippageBelowMinTokensOut);
    let effective=quote_budget.saturating_sub(1);
    let computed_amount=if is_fee_exempt{u64::try_from(curve.virtual_token_reserves as u128*effective as u128/(curve.virtual_quote_reserves as u128+effective as u128)).map_err(|_|error!(PumpError::Truncation))?}
        else{u64::try_from(crate::constant_product::tokens_for_quote(curve,quote_budget)?).map_err(|_|error!(PumpError::Truncation))?};
    let amount=computed_amount.min(curve.real_token_reserves);
    let exceeds=computed_amount>curve.real_token_reserves;
    require!(!exceeds || !(curve.is_mayhem_mode || is_fee_exempt) || partial_fill,PumpError::NotEnoughTokensToBuy);
    let crossing=exceeds && !curve.is_mayhem_mode && !is_fee_exempt;
    let quote=if exceeds{u64::try_from(curve.real_token_reserves as u128*curve.virtual_quote_reserves as u128/(curve.virtual_token_reserves as u128-curve.real_token_reserves as u128)).map_err(|_|error!(PumpError::Truncation))?.checked_add(1).ok_or(error!(PumpError::Overflow))?}else{quote_budget};
    let fee_quote=if exceeds{quote}else{narrow(available as u128*10000/(10000u128+fees.protocol_fee_bps as u128+creator_bps as u128))?};
    let protocol_fee=fee(fee_quote,fees.protocol_fee_bps)?;
    let creator_fee=fee(fee_quote,creator_bps)?;
    let buyback_bps=if curve.is_mayhem_mode {0}else{a.global.buyback_basis_points};
    let first_cost=add(add(quote,protocol_fee)?,creator_fee)?;
    let pool_base_before=if crossing{sub(a.associated_base_bonding_curve.amount,amount)?}else{0};
    let pool_quote_before=if crossing{sub(add(curve.real_quote_reserves,quote)?,if is_sol{a.global.pool_migration_fee}else{0})?}else{0};
    if crossing {
        require_gt!(pool_base_before,0,PumpError::NotEnoughTokensToBuy);
        require_gt!(pool_quote_before,0,PumpError::Overflow);
    }
    let estimated_post_quote=if crossing{net_quote(sub(available,first_cost)?,fees.protocol_fee_bps,creator_bps)?}else{0};
    let post_base=if estimated_post_quote>0{narrow(pool_base_before as u128*(estimated_post_quote-1) as u128/(pool_quote_before as u128+(estimated_post_quote-1) as u128))?}else{0};
    let post_active=crossing && post_base>0;
    let post_quote=if post_active{estimated_post_quote}else{0};
    let post_fee_quote=if crossing{narrow(sub(available,first_cost)? as u128*10000/(10000u128+fees.protocol_fee_bps as u128+creator_bps as u128))?}else{0};
    let post_protocol_raw=fee(post_fee_quote,fees.protocol_fee_bps)?;let post_creator_raw=fee(post_fee_quote,creator_bps)?;
    let post_protocol=if post_active{post_protocol_raw}else{0};let post_creator=if post_active{post_creator_raw}else{0};
    let (buyback_fee,retained)=v3_buyback_split(protocol_fee,buyback_bps);
    let (post_buyback,post_retained)=v3_buyback_split(post_protocol,buyback_bps);
    let transfer_base=amount.checked_add(post_base).ok_or_else(||error!(PumpError::Overflow))?;
    if !(exceeds && (curve.is_mayhem_mode || is_fee_exempt) && partial_fill){require_gte!(transfer_base,min_tokens_out,PumpError::BuySlippageBelowMinTokensOut);};
    let user_output=add(first_cost,add(add(post_quote,post_protocol)?,post_creator)?)?;

    let next_base=sub(curve.virtual_token_reserves,amount)?;
    let next_quote=add(curve.virtual_quote_reserves,quote)?;
    let next_real_base=sub(curve.real_token_reserves,amount)?;
    let next_real_quote=add(curve.real_quote_reserves,quote)?;
    let next_creator=add(add(curve.creator_fee,creator_fee)?,post_creator)?;
    let next_protocol=add(add(curve.protocol_fees,retained)?,post_retained)?;
    let total_buyback=add(buyback_fee,post_buyback)?;
    let net_pool_quote=sub(user_output,total_buyback)?;
    // Main-event buyback_fee reports the net of the first-fill buyback only; any
    // post-complete buyback is carried separately by PostCompleteBuyEvent.
    let buyback_received=if is_sol{buyback_fee}else{sub(buyback_fee,quote_fee_for_amount(&quote_fee,buyback_fee,false)?)?};
    let (pool_quote,quote_transfer_fee)=gross_up_quote(&quote_fee,is_sol,net_pool_quote)?;
    let mint_key=a.base_mint.key();let bump=[ctx.bumps.bonding_curve];
    let seeds:&[&[u8]]=&[b"bonding-curve",mint_key.as_ref(),&bump];
    token_interface::transfer_checked(CpiContext::new_with_signer(a.base_token_program.to_account_info(),TransferChecked{
        from:a.associated_base_bonding_curve.to_account_info(),mint:a.base_mint.to_account_info(),to:a.associated_base_user.to_account_info(),authority:a.bonding_curve.to_account_info()
    },&[seeds]),transfer_base,a.base_mint.decimals)?;
    user_quote_payments::transfer_from_user(
        is_sol,a.system_program.as_ref(),&a.user,a.bonding_curve.as_ref(),
        if is_sol{user_output}else{pool_quote},&a.quote_token_program,
        quote_decimals.unwrap_or_default(),a.quote_mint.as_ref().as_ref(),
        if is_sol{None}else{Some(a.associated_quote_user.as_ref())},
        if is_sol{None}else{Some(a.associated_quote_bonding_curve.as_ref())},
    )?;
    if let Some(decimals)=quote_decimals {
      crate::collect_v2::transfer_user_quote_tokens(&a.quote_token_program,&a.associated_quote_user,&a.buyback_fee_recipient,a.user.as_ref(),decimals,a.quote_mint.as_ref().as_ref(),total_buyback)?;
    }else{
      a.bonding_curve.sub_lamports(add(buyback_fee,post_buyback)?)?;a.buyback_fee_recipient.add_lamports(add(buyback_fee,post_buyback)?)?;
    }
    let curve=&mut a.bonding_curve;
    curve.apply_buy(amount,quote)?;
    let _=curve.accrue_fees(&a.global,protocol_fee,creator_fee)?;let _=curve.accrue_fees(&a.global,post_protocol,post_creator)?;
    if post_active{curve.post_complete_base_out=post_base;curve.post_complete_quote_in=post_quote;}
    let event=TradeEvent{
        mint:a.base_mint.key(),sol_amount:if is_sol{quote}else{0},token_amount:amount,is_buy:true,user:a.user.key(),timestamp:Clock::get()?.unix_timestamp,
        virtual_sol_reserves:if is_sol{next_quote}else{0},virtual_token_reserves:next_base,real_sol_reserves:if is_sol{next_real_quote}else{0},real_token_reserves:next_real_base,
        fee_recipient:Pubkey::default(),fee_basis_points:fees.protocol_fee_bps,fee:protocol_fee,creator:curve.creator,creator_fee_basis_points:fees.creator_fee_bps,creator_fee,
        track_volume:false,total_unclaimed_tokens:0,total_claimed_tokens:0,current_sol_volume:0,last_update_timestamp:0,ix_name:"buy_exact_quote_in".into(),mayhem_mode:curve.is_mayhem_mode,
        cashback_fee_basis_points:0,cashback:0,buyback_fee_basis_points:buyback_bps,buyback_fee:buyback_received,shareholders:vec![],quote_mint:curve.quote_mint,
        quote_amount:quote,virtual_quote_reserves:next_quote,real_quote_reserves:next_real_quote,holder_rewards_bps:if curve.is_holder_reward{fees.creator_fee_bps}else{0},holder_rewards:if curve.is_holder_reward{creator_fee}else{0},creator_fee_unclaimed:next_creator,
        unparsed_trailing_field:quote_transfer_fee,
    };
    let completion=if next_real_base==0 {
        a.bonding_curve.complete=true;
        Some(crate::trade_types::CompleteEvent{user:a.user.key(),mint:a.base_mint.key(),bonding_curve:a.bonding_curve.key(),timestamp:Clock::get()?.unix_timestamp,quote_mint:a.bonding_curve.quote_mint})
    }else{None};
    let post_event=if post_active{Some(PostCompleteBuyEvent{user:a.user.key(),mint:a.base_mint.key(),bonding_curve:a.bonding_curve.key(),quote_mint:a.bonding_curve.quote_mint,timestamp:Clock::get()?.unix_timestamp,base_out:post_base,quote_in:post_quote,fee_basis_points:fees.protocol_fee_bps,fee:post_protocol,creator_fee_basis_points:fees.creator_fee_bps,creator_fee:post_creator,buyback_fee:post_buyback,pool_base_reserves_before:pool_base_before,pool_quote_reserves_before:pool_quote_before,pool_base_reserves_after:sub(pool_base_before,post_base)?,pool_quote_reserves_after:add(pool_quote_before,post_quote)?})}else{None};
    emit!(event.clone());emit_cpi!(event);
    if let Some(completion)=completion {emit!(completion.clone());emit_cpi!(completion);}
    if let Some(post_event)=post_event{emit!(post_event.clone());emit_cpi!(post_event);}
    Ok(())
}

pub fn sell(ctx:Context<SellV3>,amount:u64,min_sol_output:u64)->Result<()> {
    let a=&mut *ctx.accounts;
    if a.user_volume_accumulator.user==Pubkey::default(){a.user_volume_accumulator.user=a.user.key();}
    crate::trade_types::prepare_bonding_curve(&a.bonding_curve, &a.system_program, &a.user)?;
    validate_trade(a.bonding_curve.complete as u8,a.bonding_curve.is_cashback_coin as u64,0)?;
    require_gt!(amount,0,PumpError::SellZeroAmount);
    let (quote_decimals,quote_fee)=check_quote(a)?;
    let is_sol=quote_decimals.is_none();
    require_gte!(a.associated_base_user.amount,amount,PumpError::NotEnoughTokensToSell);
    if is_sol{a.global.validate_buyback_fee_recipient(a.buyback_fee_recipient.key())?;}
    let curve=&a.bonding_curve;
    let quote=u64::try_from(curve.sell_quote(amount)?).map_err(|_|error!(PumpError::Truncation))?;
    let (fees,creator_bps)=if a.user.key()==a.global.whitelist_pda {
        (Fees{lp_fee_bps:0,protocol_fee_bps:0,creator_fee_bps:0},0)
    }else{
        let cap=buy_fee_market_cap(curve, &a.base_mint)?;
        let config_info=a.fee_config.to_account_info();
        let config_data=config_info.try_borrow_data()?;
        let config=read_config(&config_data)?;
        drop(config_data);
        let mut fees=selected(&config,cap,curve.quote_mint)?;
        if a.global.creator_fee_configurable && curve.creator_fee_bps>0{fees.creator_fee_bps=curve.creator_fee_bps;}
        let creator_bps=if curve.creator==Pubkey::default(){0}else{fees.creator_fee_bps};
        (fees,creator_bps)
    };
    let protocol_fee=fee(quote,fees.protocol_fee_bps)?;
    let creator_fee=fee(quote,creator_bps)?;
    let buyback_bps=if curve.is_mayhem_mode {0}else{a.global.buyback_basis_points};
    let user_output=sub3(quote,protocol_fee,creator_fee)?;
    let quote_transfer_fee=if is_sol{0}else{quote_fee_for_amount(&quote_fee,user_output,false)?};
    let net_output=sub(user_output,quote_transfer_fee)?;
    require_gte!(net_output,min_sol_output,PumpError::TooLittleSolReceived);
    let quote_transfer_fee=user_output.checked_sub(net_output).ok_or_else(||error!(PumpError::Overflow))?;
    let next_base=add(curve.virtual_token_reserves,amount)?;
    let next_quote=sub(curve.virtual_quote_reserves,quote)?;
    let next_real_base=add(curve.real_token_reserves,amount)?;
    let next_real_quote=sub(curve.real_quote_reserves,quote)?;
    let next_creator=add(curve.creator_fee,creator_fee)?;
    crate::sell_v2::user_token_transfers::transfer_user_tokens(&a.base_token_program,&a.associated_base_user,&a.associated_base_bonding_curve,a.user.as_ref(),a.base_mint.decimals,a.base_mint.as_ref().as_ref(),amount)?;
    let source_quote=if is_sol{None}else{Some(a.associated_quote_bonding_curve.as_ref())};
    let user_quote=if is_sol{None}else{Some(a.associated_quote_user.as_ref())};
    quote_payments::transfer_to_user(
        is_sol,a.base_mint.as_ref().as_ref(),a.bonding_curve.as_ref(),a.user.as_ref(),
        user_output,&a.quote_token_program,quote_decimals.unwrap_or_default(),a.quote_mint.as_ref().as_ref(),
        source_quote,user_quote,ctx.bumps.bonding_curve,
    )?;
    let (buyback_fee,retained)=v3_buyback_split(protocol_fee,buyback_bps);
    let next_protocol=add(curve.protocol_fees,retained)?;
    let buyback_received=if is_sol{buyback_fee}else{sub(buyback_fee,quote_fee_for_amount(&quote_fee,buyback_fee,false)?)?};
    let buyback_quote=if is_sol{None}else{Some(a.buyback_fee_recipient.as_ref())};
    quote_payments::transfer_to_owned(
        is_sol,a.base_mint.as_ref().as_ref(),a.bonding_curve.as_ref(),a.buyback_fee_recipient.to_account_info(),
        buyback_fee,&a.quote_token_program,quote_decimals.unwrap_or_default(),a.quote_mint.as_ref().as_ref(),
        source_quote,buyback_quote,ctx.bumps.bonding_curve,
    )?;
    let curve=&mut a.bonding_curve;
    curve.apply_sell(amount,quote)?;
    let _=curve.accrue_fees(&a.global,protocol_fee,creator_fee)?;
    let event=TradeEvent{
        mint:a.base_mint.key(),sol_amount:if is_sol{quote}else{0},token_amount:amount,is_buy:false,user:a.user.key(),timestamp:Clock::get()?.unix_timestamp,
        virtual_sol_reserves:if is_sol{next_quote}else{0},virtual_token_reserves:next_base,real_sol_reserves:if is_sol{next_real_quote}else{0},real_token_reserves:next_real_base,
        fee_recipient:Pubkey::default(),fee_basis_points:fees.protocol_fee_bps,fee:protocol_fee,creator:curve.creator,creator_fee_basis_points:fees.creator_fee_bps,creator_fee,
        track_volume:false,total_unclaimed_tokens:0,total_claimed_tokens:0,current_sol_volume:0,last_update_timestamp:0,ix_name:"sell".into(),mayhem_mode:curve.is_mayhem_mode,
        cashback_fee_basis_points:0,cashback:0,buyback_fee_basis_points:buyback_bps,buyback_fee:buyback_received,shareholders:vec![],quote_mint:curve.quote_mint,
        quote_amount:quote,virtual_quote_reserves:next_quote,real_quote_reserves:next_real_quote,holder_rewards_bps:if curve.is_holder_reward{fees.creator_fee_bps}else{0},holder_rewards:if curve.is_holder_reward{creator_fee}else{0},creator_fee_unclaimed:next_creator,
        unparsed_trailing_field:quote_transfer_fee,
    };
    emit!(event.clone());
    emit_cpi!(event);
    Ok(())
}

fn read_config(data:&[u8])->Result<FeeConfig>{
 use anchor_lang::error::ErrorCode;
 if data.len()<8{return Err(error!(ErrorCode::AccountDiscriminatorNotFound))}
 if data[..8]!=[143,52,146,187,219,123,76,155]{return Err(error!(ErrorCode::AccountDiscriminatorMismatch))}
 let mut input=&data[8..];
 let decode=(||->std::io::Result<FeeConfig>{
  let bump=u8::deserialize(&mut input)?;let admin=Pubkey::deserialize(&mut input)?;
  let flat_fees=Fees::deserialize(&mut input)?;let fee_tiers=Vec::<crate::trade_types::FeeTier>::deserialize(&mut input)?;
  let stable_fee_tiers=if data.len()>=4073{Vec::<crate::trade_types::FeeTier>::deserialize(&mut input)?}else{vec![]};
  let exotic_flat_fees=if data.len()>=4097{Fees::deserialize(&mut input)?}else{Fees{lp_fee_bps:0,protocol_fee_bps:0,creator_fee_bps:0}};
  Ok(FeeConfig{bump,admin,flat_fees,fee_tiers,stable_fee_tiers,exotic_flat_fees})
 })().map_err(|_|error!(ErrorCode::AccountDidNotDeserialize))?;
 require!(data.len()>=2512,PumpError::FeeConfigTooShort);Ok(decode)
}

const QUOTE_2:Pubkey=Pubkey::new_from_array([131,13,252,159,222,95,230,184,170,124,4,164,118,233,30,138,198,187,38,74,173,144,250,25,201,223,73,216,92,62,91,94]);
const USDC:Pubkey=anchor_lang::solana_program::pubkey!("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v");
fn check_quote(a:&SellV3)->Result<(Option<u8>,Option<(u64,u64,u64)>)>{
 if a.bonding_curve.quote_mint==Pubkey::default(){return Ok((None,None))}
 require!(*a.quote_mint.to_account_info().owner==a.quote_token_program.key(),anchor_lang::error::ErrorCode::AccountOwnedByWrongProgram);
 let decimals=a.quote_mint.decimals;
 for (role,info) in [(0,a.associated_quote_bonding_curve.to_account_info()),(1,a.associated_quote_user.to_account_info()),(2,a.buyback_fee_recipient.to_account_info())]{
  require_keys_eq!(*info.owner,a.quote_token_program.key(),PumpError::AccountTypeNotSupported);
  let token=TokenAccount::try_deserialize(&mut &info.try_borrow_data()?[..])?;
  require_keys_eq!(token.mint,a.quote_mint.key(),PumpError::MintDoesNotMatchBondingCurve);
  if role==1{require_keys_eq!(token.owner,a.user.key(),PumpError::AccountTypeNotSupported)}
  if role==2{a.global.validate_buyback_fee_recipient(token.owner)?}
  if role!=1 {
   let authority=if role==0{a.bonding_curve.key()}else{token.owner};
   let expected=anchor_spl::associated_token::get_associated_token_address_with_program_id(&authority,&a.quote_mint.key(),&a.quote_token_program.key());
   require_keys_eq!(info.key(),expected,anchor_lang::error::ErrorCode::ConstraintSeeds);
  }
 }
 let fee=quote_fee_snapshot(&a.quote_mint.to_account_info())?;
 Ok((Some(decimals),fee))
}

fn net_quote(spend:u64,pb:u64,cb:u64)->Result<u64>{let total=pb.checked_add(cb).ok_or(PumpError::Overflow)?;let mut quote=narrow(spend as u128*10000/(10000u128+total as u128))?;if quote>0 && add(add(quote,fee(quote,pb)?)?,fee(quote,cb)?)?>spend{quote-=1;}Ok(quote)}
// Token-2022 transfer-fee math on the quote amount, mirroring the original's
// epoch fee selection. `inverse` grosses up an amount the pool must RECEIVE net;
// otherwise it returns the fee withheld from a sent amount. SOL / SPL-Token quotes
// carry no transfer fee.
fn quote_fee_snapshot(mint:&AccountInfo)->Result<Option<(u64,u64,u64)>>{
    use anchor_spl::token_2022::spl_token_2022::{extension::{BaseStateWithExtensions,ExtensionType,StateWithExtensions,transfer_fee::TransferFeeConfig},state::Mint as SplMint};
    if mint.owner==&anchor_spl::token::ID{return Ok(None);}
    let data=mint.try_borrow_data()?;
    let parsed=StateWithExtensions::<SplMint>::unpack(&data)?;
    // TLV tags are forward compatible. Validate every declared payload while
    // finding a single transfer-fee config, including across unknown tags.
    let tlv=parsed.get_tlv_data();
    let mut cursor=0usize;
    let mut selected=None;
    while cursor<tlv.len() {
        if tlv.len()-cursor<2 {break;}
        let tag=u16::from_le_bytes([tlv[cursor],tlv[cursor+1]]);
        if tag==0 {break;}
        if tlv.len()-cursor<4 {return err!(PumpError::UnsupportedQuoteMint);}
        let length=u16::from_le_bytes([tlv[cursor+2],tlv[cursor+3]]) as usize;
        let begin=cursor+4;
        let end=begin.checked_add(length).ok_or_else(||error!(PumpError::UnsupportedQuoteMint))?;
        let value=tlv.get(begin..end).ok_or_else(||error!(PumpError::UnsupportedQuoteMint))?;
        if tag==ExtensionType::TransferFeeConfig as u16 {
            if selected.is_some() {return err!(PumpError::UnsupportedQuoteMint);}
            let prefix=value.get(..std::mem::size_of::<TransferFeeConfig>())
                .ok_or_else(||error!(PumpError::UnsupportedQuoteMint))?;
            selected=Some(anchor_lang::__private::bytemuck::try_from_bytes::<TransferFeeConfig>(prefix)
                .map_err(|_|error!(PumpError::UnsupportedQuoteMint))?);
        }
        cursor=end;
    }
    Ok(match selected {
        Some(fees)=>{
            let epoch=Clock::get()?.epoch;
            let selected=fees.get_epoch_fee(epoch);
            Some((u64::from(selected.epoch),u64::from(selected.maximum_fee),u16::from(selected.transfer_fee_basis_points) as u64))
        }
        None=>None,
    })
}

pub(crate) fn quote_transfer_fee(mint:&AccountInfo,amount:u64,inverse:bool)->Result<u64>{
    let snapshot=quote_fee_snapshot(mint)?;
    quote_fee_for_amount(&snapshot,amount,inverse)
}

fn quote_fee_for_amount(snapshot:&Option<(u64,u64,u64)>,amount:u64,inverse:bool)->Result<u64>{
 let fee=snapshot.map(|(epoch,maximum_fee,basis_points)|native_transfer_fee::Fee{epoch,maximum_fee,basis_points:basis_points as u16});
 if inverse{let gross=crate::transfer_fee_recovered::pre_fee_amount(&fee,amount)?;crate::transfer_fee_recovered::calculate_fee(&fee,gross)}else{crate::transfer_fee_recovered::calculate_fee(&fee,amount)}
}
#[inline(always)] fn quote_post_fee_amount(snapshot:&Option<(u64,u64,u64)>,amount:u64)->Result<u64>{let fee=snapshot.map(|(epoch,maximum_fee,basis_points)|native_transfer_fee::Fee{epoch,maximum_fee,basis_points:basis_points as u16});crate::transfer_fee_recovered::post_fee_amount(&fee,amount)}

#[event]
#[derive(Clone)]pub struct PostCompleteBuyEvent{pub user:Pubkey,pub mint:Pubkey,pub bonding_curve:Pubkey,pub quote_mint:Pubkey,pub timestamp:i64,pub base_out:u64,pub quote_in:u64,pub fee_basis_points:u64,pub fee:u64,pub creator_fee_basis_points:u64,pub creator_fee:u64,pub buyback_fee:u64,pub pool_base_reserves_before:u64,pub pool_quote_reserves_before:u64,pub pool_base_reserves_after:u64,pub pool_quote_reserves_after:u64}

// Buy-side pretrade fee basis recovered from the original mode selector.
use crate::buy_fee_market_cap;

#[path="curve_quote_payments.rs"]
pub mod quote_payments;

pub use crate::user_quote_payments;
