use anchor_lang::prelude::*;
use anchor_spl::token_interface::{self, Mint, TokenAccount, TokenInterface, TransferChecked};
use crate::{Global, PumpError};
#[path="v3_native_transfer_fee.rs"] pub mod native_transfer_fee;
use crate::trade_types::{BondingCurve, TradeEvent};
const FEE_PROGRAM: Pubkey = anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
const WSOL: Pubkey = anchor_lang::solana_program::pubkey!("So11111111111111111111111111111111111111112");
// layout-pad(30): aligns the next Source site with the original line





























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
    #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump=fee_config.bump,seeds::program=FEE_PROGRAM)]
    pub fee_config: Box<Account<'info, crate::pump_fees::accounts::FeeConfig>>,
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



fn v3_buyback_split(protocol_fee:u64,buyback_bps:u64)->(u64,u64) {
    let buyback_fee=u64::try_from(protocol_fee as u128*buyback_bps as u128/10000)
        .expect("buyback fee is at most protocol_fee");
    let retained=protocol_fee.checked_sub(buyback_fee)
        .expect("buyback_fee never exceeds protocol_fee");
    (buyback_fee,retained)
}
// layout-pad(15): aligns the next Source site with the original line














// layout-pad(44): aligns the next Source site with the original line











































/// Validate the shared curve flags before quote or amount-specific checks.
#[inline(never)]
pub fn validate_trade(complete:u8,cashback:u64,allow_cashback:u64)->Result<()> {
    require!(complete==0,PumpError::BondingCurveComplete);
    require!(allow_cashback!=0 || cashback as u8==0,PumpError::CashbackCoinNotSupported);
    Ok(())
}
// layout-pad(131): aligns the next Source site with the original line














/// Buyback fee recipient admission (native: global membership of the account key; token: owner program, mint, membership of the token owner, canonical ATA).
pub fn validate_buyback_fee_recipient_account(global:&Global,recipient:&AccountInfo,is_native:bool,quote_mint:&Pubkey,quote_token_program:&Pubkey)->Result<()>{
 if is_native{return global.validate_buyback_fee_recipient(&recipient.key());}

 require_keys_eq!(*recipient.owner,*quote_token_program,PumpError::AccountTypeNotSupported);
 let owner={
  let data=recipient.try_borrow_data()?;
  let mut slice:&[u8]=&data;
  let token=TokenAccount::try_deserialize_unchecked(&mut slice)?;



  require_keys_eq!(token.mint,*quote_mint,PumpError::MintDoesNotMatchBondingCurve);
  token.owner
 };
 global.validate_buyback_fee_recipient(&owner)?;




 require_keys_eq!(recipient.key(),anchor_spl::associated_token::get_associated_token_address_with_program_id(&owner,quote_mint,quote_token_program),anchor_lang::error::ErrorCode::ConstraintSeeds);
 Ok(())
}
fn check_quote(a:&SellV3)->Result<(bool,Option<crate::trade::native_transfer_fee::Fee>)>{
 let is_native=quote_is_native(&a.bonding_curve);
 let quote_mint=a.quote_mint.key();
 let quote_token_program=a.quote_token_program.key();
 if !is_native{
  crate::buy_v2::admit_associated_token_account(a.associated_quote_bonding_curve.as_ref(),&a.bonding_curve.to_account_info(),quote_mint,quote_token_program,&a.quote_mint.to_account_info(),&a.quote_token_program.to_account_info(),false,a.user.as_ref(),a.system_program.as_ref())?;
  crate::buy_v2::check_token_account(a.associated_quote_user.as_ref(),a.user.as_ref(),quote_mint,quote_token_program)?;
 }
 validate_buyback_fee_recipient_account(&a.global,a.buyback_fee_recipient.as_ref(),is_native,&quote_mint,&quote_token_program)?;
 const NO_FEE:Option<crate::trade::native_transfer_fee::Fee>=None;let fee=if is_native{NO_FEE}else{crate::transfer_fee_recovered::get_transfer_fee(&a.quote_mint.to_account_info())?};
 Ok((is_native,fee))
}

#[inline(never)]
fn v3_trade_fees(a:&SellV3,amount:u64)->Result<TradeFees>{
    if a.global.whitelist_pda==a.user.key(){return Ok(TradeFees::default());}
    let curve:&BondingCurve=&a.bonding_curve;
    crate::legacy_sell::fee_math::get_fees(&a.global,curve,&a.fee_config,a.fee_config.to_account_info().data_len(),buy_fee_market_cap(curve,&a.base_mint)?,amount)
}










































































#[inline(never)]
pub(crate) fn add3(a:u64,b:u64,c:u64)->Result<u64>{a.checked_add(b).and_then(|x|x.checked_add(c)).ok_or_else(||error!(PumpError::Overflow))}
// layout-pad(7): aligns the next Source site with the original line






#[inline(never)]
pub(crate) fn sub3(a:u64,b:u64,c:u64)->Result<u64>{a.checked_sub(b).and_then(|x|x.checked_sub(c)).ok_or_else(||error!(PumpError::Overflow))}
// layout-pad(14): aligns the next Source site with the original line














#[inline(never)]
pub(crate) fn net_quote_for_budget(creator:&Pubkey,protocol_fee_bps:u64,creator_fee_bps:u64,budget:u64)->Result<(u64,TradeFees)>{
    let creator_bps=if *creator==Pubkey::default(){0}else{creator_fee_bps};
    let total_bps=protocol_fee_bps.checked_add(creator_bps).ok_or(PumpError::Overflow)?;
    let mut net=if total_bps==0{budget}else if budget==0{0}else{(budget as u128*10_000/(10_000+total_bps as u128)) as u64};


    require_gt!(net,0,PumpError::BuyNotEnoughSolToCoverFees);
    let protocol_fee=crate::legacy_sell::fee_math::fee(net,protocol_fee_bps)?;
    let creator_fee=crate::legacy_sell::fee_math::fee(net,creator_bps)?;
    let total=net.saturating_add(protocol_fee).saturating_add(creator_fee);
    if total>budget{
        let excess=total.saturating_sub(budget);
        net=net.checked_sub(excess).ok_or(PumpError::Overflow)?;


        require_gt!(net,0,PumpError::BuySlippageBelowMinTokensOut);
    }
    Ok((net,TradeFees{protocol_fee,creator_fee,protocol_fee_bps,creator_fee_bps}))
}


































#[inline(never)]
fn v3_buy_costs(buyback_bps:u64,is_mayhem:u8,quote_fee:&Option<native_transfer_fee::Fee>,quote:u64,protocol_fee:u64,creator_fee:u64,post:Option<&PostComplete>)->Result<(u64,u64,u64)>{
    let buyback=crate::protocol_fee_split(buyback_bps,protocol_fee,is_mayhem!=0).0; let post_buyback=match post{Some(p)=>crate::protocol_fee_split(buyback_bps,p.fees.protocol_fee,is_mayhem!=0).0,None=>0};



    let total_buyback=buyback.checked_add(post_buyback)
        .ok_or_else(||error!(PumpError::Overflow))?;
    let first=add3(quote,protocol_fee,creator_fee)?;
    let second=if let Some(p)=post{add3(p.quote_in,p.fees.protocol_fee,p.fees.creator_fee)?}else{0};
    let (pool_quote,net)=first.checked_add(second).and_then(|sum|sum.checked_sub(total_buyback))
        .ok_or_else(||error!(PumpError::Overflow)).and_then(|net|crate::transfer_fee_recovered::pre_fee_amount(quote_fee,net).map(|g|(g,net)))?;
    let quote_transfer_fee=pool_quote.checked_sub(net).ok_or_else(gross_up_quote_error)?; Ok((pool_quote,total_buyback,quote_transfer_fee))
}
/// Gross-up of the pool-side quote by the quote mint's transfer fee; the fee is re-derived from the gross.
#[inline(always)]
fn gross_up_quote(quote_fee:&Option<native_transfer_fee::Fee>,net:u64)->Result<(u64,u64)>{let gross=crate::transfer_fee_recovered::pre_fee_amount(quote_fee,net)?;let quote_transfer_fee=gross.checked_sub(net).ok_or_else(gross_up_quote_error)?;Ok((gross,quote_transfer_fee))}
#[inline(never)]
pub fn gross_up_quote_error()->anchor_lang::error::Error{error!(PumpError::Overflow)}


// layout-pad(5): aligns the next Source site with the original line




fn add(a:u64,b:u64)->Result<u64>{a.checked_add(b).ok_or_else(||error!(PumpError::Overflow))}

/// Buy-side fee amounts and basis points for one quote amount (zero for the fee-exempt whitelist PDA).
pub use crate::legacy_sell::fee_math::TradeFees;

/// Post-complete (crossing) fill: its fees, base out / quote in and the pool reserves before it.
#[derive(Clone,Copy)]
pub struct PostComplete{pub fees:TradeFees,pub base_out:u64,pub quote_in:u64,pub pool_base_before:u64,pub pool_quote_before:u64}







// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad



















// layout-pad(62): aligns the next Source site with the original line
#[inline(always)] fn v3_fee_exempt(global:&Global,curve:&BondingCurve,user:&Pubkey)->bool{curve.is_mayhem_mode || *user==global.whitelist_pda}
fn v3_can_cross(global:&Global,curve:&BondingCurve,user:&Pubkey)->bool{!v3_fee_exempt(global,curve,user)}



/// PostCompleteBuyEvent for a post-complete fill (pool reserves after = before -/+ the fill).
pub fn post_complete_buy_event(post:&PostComplete,user:Pubkey,mint:Pubkey,bonding_curve:Pubkey,quote_mint:Pubkey,timestamp:i64,buyback_fee:u64)->Result<PostCompleteBuyEvent>{




    let pool_base_reserves_after=post.pool_base_before.checked_sub(post.base_out).ok_or_else(||error!(PumpError::Overflow))?;



    let pool_quote_reserves_after=post.pool_quote_before.checked_add(post.quote_in).ok_or_else(||error!(PumpError::Overflow))?;
    Ok(PostCompleteBuyEvent{user,mint,bonding_curve,quote_mint,timestamp,
        base_out:post.base_out,quote_in:post.quote_in,fee_basis_points:post.fees.protocol_fee_bps,fee:post.fees.protocol_fee,creator_fee_basis_points:post.fees.creator_fee_bps,creator_fee:post.fees.creator_fee,buyback_fee,
        pool_base_reserves_before:post.pool_base_before,pool_quote_reserves_before:post.pool_quote_before,pool_base_reserves_after,pool_quote_reserves_after})
}









































#[inline(never)]
pub(crate) fn v3_pool_before(real_quote:u64,migration_fee:u64,curve_base:u64,is_sol:bool,amount:u64,quote:u64)->Result<(u64,u64)>{
    let pool_base=curve_base.checked_sub(amount).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad(3): aligns the next Source site with the original line


    let pool_quote=real_quote.checked_add(quote).ok_or_else(||error!(PumpError::Overflow))?;
// layout-pad(3): aligns the next Source site with the original line


    let pool_quote=if is_sol{pool_quote.checked_sub(migration_fee).ok_or_else(||error!(PumpError::Overflow))?}else{pool_quote};
// layout-pad(3): aligns the next Source site with the original line


    require_gt!(pool_base,0,PumpError::NotEnoughTokensToBuy);
    require_gt!(pool_quote,0,PumpError::Overflow);
    Ok((pool_base,pool_quote))
}
// layout-pad(6): aligns the next Source site with the original line





#[inline(never)]
fn v3_post_complete(a:&SellV3,pool_base:u64,pool_quote:u64,excess:u64)->Result<PostComplete>{
    require_gt!(pool_base,excess,PumpError::NotEnoughTokensToBuy);

// layout-pad(6): aligns the next Source site with the original line





    let quote_in=u64::try_from(crate::legacy_sell::fee_cpi::checked_ceil_div(excess as u128*pool_quote as u128,(pool_base-excess) as u128)?).map_err(|_|error!(PumpError::Truncation))?;
    let fees=v3_trade_fees(a,quote_in)?;
    Ok(PostComplete{fees,base_out:excess,quote_in,pool_base_before:pool_base,pool_quote_before:pool_quote})
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
// layout-pad(132): aligns the next Source site with the original line



#[inline(never)]
pub fn estimate_post_complete(creator:&Pubkey,pool_base_before:u64,pool_quote_before:u64,protocol_fee_bps:u64,creator_fee_bps:u64,budget:u64,exact_budget:bool)->Result<Option<PostComplete>>{
    let creator_bps=if *creator==Pubkey::default(){0}else{creator_fee_bps};
    let total_bps=protocol_fee_bps.checked_add(creator_bps).ok_or(PumpError::Overflow)?;
    let net=if total_bps==0{budget}else if budget==0{0}else{(budget as u128*10_000/(10_000+total_bps as u128)) as u64};
    if net<2{return Ok(None);}
    let (net,fees)=net_quote_for_budget(creator,protocol_fee_bps,creator_fee_bps,budget)?;
    let quote_in=if exact_budget{sub3(budget,fees.protocol_fee,fees.creator_fee)?}else{net};
    let build=|base_out|PostComplete{fees,base_out,quote_in,pool_base_before,pool_quote_before};
    let base_out=exact_input_tokens(quote_in,pool_base_before,pool_quote_before)?;
    if base_out==0{return Ok(None);}
    Ok(Some(build(base_out)))
}















#[inline(never)] pub fn exact_input_tokens(quote_in:u64,token_reserves:u64,quote_reserves:u64)->Result<u64>{
    let effective=quote_in.checked_sub(1).ok_or(PumpError::Overflow)?;
    let tokens=crate::constant_product::output(effective as u128,quote_reserves as u128,token_reserves as u128)?;
    u64::try_from(tokens).map_err(|_|error!(PumpError::Truncation))
}







#[inline(never)]
pub fn fit_post_complete(buyback_bps:u64,is_mayhem:bool,quote_fee:&Option<native_transfer_fee::Fee>,quote:u64,protocol_fee:u64,creator_fee:u64,post:&mut PostComplete,budget:u64)->Result<(Option<PostComplete>,(u64,u64,u64))>{
    loop{
        let costs=v3_buy_costs(buyback_bps,is_mayhem as u8,quote_fee,quote,protocol_fee,creator_fee,Some(post))?;
        let total=add(costs.0,costs.1)?;
        if total<=budget{return Ok((Some(*post),costs));}
        let Some(q)=post.quote_in.checked_sub(total-budget).filter(|q|*q>1) else {return Ok((None,v3_buy_costs(buyback_bps,is_mayhem as u8,quote_fee,quote,protocol_fee,creator_fee,None)?));};
        post.quote_in=q;
        post.base_out=exact_input_tokens(post.quote_in,post.pool_base_before,post.pool_quote_before)?;
        if post.base_out==0{return Ok((None,v3_buy_costs(buyback_bps,is_mayhem as u8,quote_fee,quote,protocol_fee,creator_fee,None)?));}
    }
}












































































#[inline(never)]
fn v3_execute_buy<'info>(a:&mut SellV3<'info>,curve_bump:u8,is_sol:bool,amount:u64,quote:u64,protocol_fee:u64,creator_fee:u64,post:Option<&PostComplete>,pool_quote:u64,total_buyback:u64,quote_fee:&Option<native_transfer_fee::Fee>)->Result<(u64,u64)>{
    let (base_token_program,quote_token_program)=(&a.base_token_program,&a.quote_token_program); a.bonding_curve.apply_buy(amount,quote)?;
    transfer_curve_mint_tokens(base_token_program,&a.base_mint,&a.associated_base_user,&a.associated_base_bonding_curve,&a.bonding_curve,amount.checked_add(match post{Some(p)=>p.base_out,None=>0}).ok_or_else(||error!(PumpError::Overflow))?,&[&[b"bonding-curve",a.base_mint.key().as_ref(),&[curve_bump]]])?;
    


    if a.user.key()==a.global.whitelist_pda{
        a.associated_base_bonding_curve.reload()?;
        a.associated_base_user.reload()?;
        let quote_mint=a.bonding_curve.quote_mint;
        a.bonding_curve.sync_virtual_quote_reserves(a.associated_base_bonding_curve.amount,a.associated_base_user.amount,&quote_mint)?;
    }
    init_volume_user(&mut a.user_volume_accumulator,&a.user);
    let buyback=a.bonding_curve.accrue_fees(&a.global,protocol_fee,creator_fee)?;
    let post_buyback=match post{Some(p)=>{a.bonding_curve.post_complete_base_out=p.base_out;a.bonding_curve.post_complete_quote_in=p.quote_in;a.bonding_curve.accrue_fees(&a.global,p.fees.protocol_fee,p.fees.creator_fee)?},None=>0};
// layout-pad(17): aligns the next Source site with the original line
















    let total=buyback.checked_add(post_buyback).ok_or_else(||error!(PumpError::Overflow))?;
    {
        let user_quote_in=if is_sol{add(pool_quote,total_buyback)?}else{pool_quote};
        let (user_quote,curve_quote)=if is_sol{(None,None)}else{let curve_quote=Some(a.associated_quote_bonding_curve.as_ref());(Some(a.associated_quote_user.as_ref()),curve_quote)};
        user_quote_payments::transfer_from_user(is_sol,a.system_program.as_ref(),&a.user,&a.bonding_curve,user_quote_in,quote_token_program,a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),user_quote,curve_quote)?;
    }
    if is_sol{quote_payments::pay_out_native(&a.bonding_curve,a.buyback_fee_recipient.to_account_info(),total)?;}
    else{crate::collect_v2::transfer_user_quote_tokens(quote_token_program,&a.associated_quote_user,&a.buyback_fee_recipient,a.user.as_ref(),a.quote_mint.decimals,a.quote_mint.as_ref().as_ref(),total)?;}
    let total_net=crate::transfer_fee_recovered::post_fee_amount(quote_fee,total)?;
    let post_net=crate::transfer_fee_recovered::post_fee_amount(quote_fee,post_buyback)?;
// layout-pad(36): aligns the next Source site with the original line



































    let main_net=total_net.checked_sub(post_net).ok_or_else(||error!(PumpError::Overflow))?;
    Ok((main_net,post_net))
}
pub fn buy(mut ctx:Context<SellV3>,amount:u64,max_sol_cost:u64,partial_fill:bool)->Result<()> {
    let a=&mut *ctx.accounts;
    crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;
    validate_trade(a.bonding_curve.complete as u8,a.bonding_curve.is_cashback_coin as u64,0)?;
    let real=a.bonding_curve.real_token_reserves;
    let can_cross=v3_can_cross(&a.global,&a.bonding_curve,&a.user.key());let (amount,excess)=if amount>real && can_cross{(real,amount-real)}else{(if partial_fill{amount.min(real)}else{amount},0)};

// layout-pad(24): aligns the next Source site with the original line























    require_gt!(amount,0,PumpError::BuyZeroAmount);
    require_gte!(real,amount,PumpError::NotEnoughTokensToBuy);
    let (is_sol,quote_fee)=check_quote(a)?;
// layout-pad(7): aligns the next Source site with the original line






    let quote=u64::try_from(crate::buy_quote(&a.bonding_curve,amount)?).map_err(|_|error!(PumpError::Truncation))?;
    let fees=v3_trade_fees(a,quote)?;
    let post=if excess>0{let (pool_base,pool_quote)={let (base,real,fee)=(a.associated_base_bonding_curve.amount,a.bonding_curve.real_quote_reserves,a.global.pool_migration_fee);v3_pool_before(real,fee,base,is_sol,amount,quote)}?;Some(v3_post_complete(a,pool_base,pool_quote,excess)?)}else{None};
    let (pool_quote,total_buyback,quote_transfer_fee)=v3_buy_costs(a.global.buyback_basis_points,a.bonding_curve.is_mayhem_mode as u8,&quote_fee,quote,fees.protocol_fee,fees.creator_fee,post.as_ref())?;
// layout-pad(27): aligns the next Source site with the original line


























    require_gte!(max_sol_cost,add(pool_quote,total_buyback)?,PumpError::TooMuchSolRequired);
    let (buyback,post_buyback)=v3_execute_buy(a,ctx.bumps.bonding_curve,is_sol,amount,quote,fees.protocol_fee,fees.creator_fee,post.as_ref(),pool_quote,total_buyback,&quote_fee)?;
    v3_emit_buy(&mut ctx,amount,quote,&fees,buyback,quote_transfer_fee,"buy",&post,post_buyback)
}
// layout-pad(26): aligns the next Source site with the original line

























pub fn buy_exact_quote(ctx:Context<SellV3>,spendable_quote_in:u64,min_tokens_out:u64,partial_fill:bool)->Result<()> {buy_exact_quote_body(ctx,spendable_quote_in,min_tokens_out,partial_fill)} #[inline(always)] fn buy_exact_quote_body(mut ctx:Context<SellV3>,spendable_quote_in:u64,min_tokens_out:u64,partial_fill:bool)->Result<()> {
    let a=&mut *ctx.accounts;
    crate::trade_types::prepare_bonding_curve(&a.bonding_curve,&a.system_program,&a.user)?;
    validate_trade(a.bonding_curve.complete as u8,a.bonding_curve.is_cashback_coin as u64,0)?;





    require_gt!(min_tokens_out,0,PumpError::BuyZeroAmount);
    require_gt!(spendable_quote_in,0,PumpError::BuyNotEnoughSolToCoverFees);
    let (is_sol,quote_fee);(is_sol,quote_fee)=check_quote(a)?;
    let available=crate::transfer_fee_recovered::post_fee_amount(&quote_fee,spendable_quote_in)?;






    require_neq!(available,0,PumpError::BuyNotEnoughSolToCoverFees);
    let fees=v3_trade_fees(a,available)?;
    let curve=&a.bonding_curve;
    let (tokens,net,protocol_fee,creator_fee,protocol_fee_bps,creator_fee_bps)=if a.global.whitelist_pda==a.user.key(){









        let tokens=u64::try_from(crate::constant_product::tokens_for_quote(curve,available)?).map_err(|_|error!(PumpError::Truncation))?;
        (tokens,available,fees.protocol_fee,fees.creator_fee,fees.protocol_fee_bps,fees.creator_fee_bps)
    }else{
        let (net,TradeFees{protocol_fee,creator_fee,protocol_fee_bps,creator_fee_bps})=net_quote_for_budget(&curve.creator,fees.protocol_fee_bps,fees.creator_fee_bps,available)?;



        let tokens=u64::try_from(crate::constant_product::tokens_for_quote(curve,net)?).map_err(|_|error!(PumpError::Truncation))?;
        (tokens,net,protocol_fee,creator_fee,protocol_fee_bps,creator_fee_bps)
    };
    let (amount,quote,fees,post,costs)=if tokens>curve.real_token_reserves{
        let can_cross=v3_can_cross(&a.global,curve,&a.user.key());










        require!(can_cross||partial_fill,PumpError::NotEnoughTokensToBuy);
        let amount=curve.real_token_reserves;


        let quote=u64::try_from(crate::buy_quote(curve,amount)?).map_err(|_|error!(PumpError::Truncation))?;
        let curve_fees=v3_trade_fees(a,quote)?;
        let costs=v3_buy_costs(a.global.buyback_basis_points,curve.is_mayhem_mode as u8,&quote_fee,quote,curve_fees.protocol_fee,curve_fees.creator_fee,None)?;


        require_gte!(spendable_quote_in,add(costs.0,costs.1)?,PumpError::TooMuchSolRequired);
        let first=add3(quote,curve_fees.protocol_fee,curve_fees.creator_fee)?;let rest=available.saturating_sub(first);
        let (post,costs)=if can_cross & (available>first){
            let (pool_base,pool_quote)=v3_pool_before(curve.real_quote_reserves,a.global.pool_migration_fee,a.associated_base_bonding_curve.amount,is_sol,amount,quote)?;
            match estimate_post_complete(&curve.creator,pool_base,pool_quote,fees.protocol_fee_bps,fees.creator_fee_bps,rest,false)?{
                Some(mut post)=>fit_post_complete(a.global.buyback_basis_points,curve.is_mayhem_mode,&quote_fee,quote,curve_fees.protocol_fee,curve_fees.creator_fee,&mut post,spendable_quote_in)?,
                None=>(None,costs),
            }
        }else{(None,costs)};
        if can_cross{

























            let base_out=amount.checked_add(match &post{Some(p)=>p.base_out,None=>0}).ok_or_else(||error!(PumpError::Overflow))?;
            require_gte!(base_out,min_tokens_out,PumpError::BuySlippageBelowMinTokensOut);
        }
        (amount,quote,curve_fees,post,costs)
    }else{
        let (mut tokens,mut net)=(tokens,net);
        let mut costs=v3_buy_costs(a.global.buyback_basis_points,curve.is_mayhem_mode as u8,&quote_fee,net,protocol_fee,creator_fee,None)?;
        let total=add(costs.0,costs.1)?;
        if total>spendable_quote_in{
            net=net.checked_sub(total-spendable_quote_in).ok_or(PumpError::BuyNotEnoughSolToCoverFees)?;













            require_gt!(net,0,PumpError::BuySlippageBelowMinTokensOut);



            tokens=u64::try_from(crate::constant_product::tokens_for_quote(curve,net)?).map_err(|_|error!(PumpError::Truncation))?;
            costs=v3_buy_costs(a.global.buyback_basis_points,curve.is_mayhem_mode as u8,&quote_fee,net,protocol_fee,creator_fee,None)?;
        }

        require_gte!(tokens,min_tokens_out,PumpError::BuySlippageBelowMinTokensOut);
        (tokens,net,TradeFees{protocol_fee,creator_fee,protocol_fee_bps,creator_fee_bps},None,costs)
    };
    let (buyback,post_buyback)=v3_execute_buy(a,ctx.bumps.bonding_curve,is_sol,amount,quote,fees.protocol_fee,fees.creator_fee,post.as_ref(),costs.0,costs.1,&quote_fee)?;
    v3_emit_buy(&mut ctx,amount,quote,&fees,buyback,costs.2,"buy_exact_quote_in",&post,post_buyback)
}
#[inline(never)]
fn v3_emit_buy(ctx:&mut Context<SellV3>,amount:u64,quote:u64,fees:&TradeFees,buyback_fee:u64,quote_transfer_fee:u64,ix_name:&str,post:&Option<PostComplete>,post_buyback_fee:u64)->Result<()>{
    let timestamp=Clock::get()?.unix_timestamp;
    let event=crate::multi_hop_curve::trade_event(&ctx.accounts.bonding_curve,&ctx.accounts.global,&ctx.accounts.user_volume_accumulator,&ctx.accounts.user.key(),&ctx.accounts.base_mint.key(),true,amount,quote,fees,buyback_fee,quote_transfer_fee,ix_name,timestamp);
    emit!(event);emit_cpi!(event);
    if ctx.accounts.bonding_curve.real_token_reserves==0{ctx.accounts.bonding_curve.complete=true;
        let completion=crate::trade_types::CompleteEvent{mint:ctx.accounts.base_mint.key(),user:ctx.accounts.user.key(),bonding_curve:ctx.accounts.bonding_curve.key(),timestamp,quote_mint:ctx.accounts.bonding_curve.quote_mint};
        emit!(completion);emit_cpi!(completion);
    if let Some(p)=post{let post_event=post_complete_buy_event(p,ctx.accounts.user.key(),ctx.accounts.base_mint.key(),ctx.accounts.bonding_curve.key(),ctx.accounts.bonding_curve.quote_mint,timestamp,post_buyback_fee)?;
        emit!(post_event);emit_cpi!(post_event);}}
    Ok(())
}








pub fn sell(ctx:Context<SellV3>,amount:u64,min_sol_output:u64)->Result<()> {sell_body(ctx,amount,min_sol_output)} #[inline(always)] fn sell_body(ctx:Context<SellV3>,amount:u64,min_sol_output:u64)->Result<()> {
    let a=&mut *ctx.accounts;

    crate::trade_types::prepare_bonding_curve(&a.bonding_curve, &a.system_program, &a.user)?;
    validate_trade(a.bonding_curve.complete as u8,a.bonding_curve.is_cashback_coin as u64,0)?;
// layout-pad(94): aligns the next Source site with the original line





























































































    require_gt!(amount,0,PumpError::SellZeroAmount);
    require_gte!(a.associated_base_user.amount,amount,PumpError::NotEnoughTokensToSell);
    let (is_sol,quote_fee)=check_quote(a)?;


    let curve=&a.bonding_curve;
// layout-pad(8): aligns the next Source site with the original line







    let quote=u64::try_from(curve.sell_quote(amount)?).map_err(|_|error!(PumpError::Truncation))?;
    let fees=v3_trade_fees(a,quote)?;
    let protocol_fee=fees.protocol_fee;let creator_fee=fees.creator_fee;


    let user_output=sub3(quote,protocol_fee,creator_fee)?;
    let net_output=crate::transfer_fee_recovered::post_fee_amount(&quote_fee,user_output)?;

    require_gte!(net_output,min_sol_output,PumpError::TooLittleSolReceived);






    let quote_transfer_fee=user_output.checked_sub(net_output).ok_or_else(||error!(PumpError::Overflow))?;
    a.bonding_curve.apply_sell(amount,quote)?;




    crate::sell_v2::user_token_transfers::transfer_user_tokens(&a.base_token_program,&a.associated_base_user,&a.associated_base_bonding_curve,a.user.as_ref(),a.base_mint.decimals,a.base_mint.as_ref().as_ref(),amount)?;
    if a.user.key()==a.global.whitelist_pda{a.associated_base_bonding_curve.reload()?;a.associated_base_user.reload()?;let quote_mint=a.bonding_curve.quote_mint;a.bonding_curve.sync_virtual_quote_reserves(a.associated_base_bonding_curve.amount,a.associated_base_user.amount,&quote_mint)?;}
    init_volume_user(&mut a.user_volume_accumulator,&a.user);
    
    pay_user(is_sol,&a.base_mint,a.bonding_curve.as_ref(),a.user.as_ref(),user_output,&a.quote_token_program,&a.quote_mint,if is_sol{None}else{Some(a.associated_quote_bonding_curve.as_ref())},if is_sol{None}else{Some(a.associated_quote_user.as_ref())},ctx.bumps.bonding_curve)?;



    let buyback_fee=a.bonding_curve.accrue_fees(&a.global,protocol_fee,creator_fee)?;


    
    pay_owned(
        is_sol,&a.base_mint,a.bonding_curve.as_ref(),a.buyback_fee_recipient.to_account_info(),
        buyback_fee,&a.quote_token_program,&a.quote_mint,
        if is_sol{None}else{Some(a.associated_quote_bonding_curve.as_ref())},if is_sol{None}else{Some(a.buyback_fee_recipient.as_ref())},ctx.bumps.bonding_curve,
    )?;



    let event=sell_event(&a.bonding_curve,&a.global,&a.user_volume_accumulator,&a.user.key(),&a.base_mint.key(),amount,quote,fees,crate::transfer_fee_recovered::post_fee_amount(&quote_fee,buyback_fee)?,quote_transfer_fee,Clock::get()?.unix_timestamp);








    emit!(event);
    emit_cpi!(event);
    Ok(())
}

// layout-pad(14): aligns the next Source site with the original line
















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
fn quote_is_native(curve:&BondingCurve)->bool{curve.quote_mint==Pubkey::default()}  fn sell_event(curve:&BondingCurve,global:&Global,volume:&crate::UserVolumeAccumulator,user:&Pubkey,mint:&Pubkey,amount:u64,quote:u64,fees:TradeFees,buyback_fee:u64,quote_transfer_fee:u64,timestamp:i64)->TradeEvent{crate::multi_hop_curve::trade_event(curve,global,volume,user,mint,false,amount,quote,&fees,buyback_fee,quote_transfer_fee,"sell",timestamp)}








// Token-2022 transfer-fee math on the quote amount, mirroring the original's
// epoch fee selection. `inverse` grosses up an amount the pool must RECEIVE net;
// otherwise it returns the fee withheld from a sent amount. SOL / SPL-Token quotes
// carry no transfer fee.
fn quote_fee_snapshot(mint:&AccountInfo)->Result<Option<(u64,u64,u64)>>{Ok(crate::transfer_fee_recovered::get_transfer_fee(mint)?.map(|f|(f.epoch,f.maximum_fee,f.basis_points as u64)))}





































pub(crate) fn quote_transfer_fee(mint:&AccountInfo,amount:u64,inverse:bool)->Result<u64>{
    let snapshot=quote_fee_snapshot(mint)?;
    quote_fee_for_amount(&snapshot,amount,inverse)
}

fn quote_fee_for_amount(snapshot:&Option<(u64,u64,u64)>,amount:u64,inverse:bool)->Result<u64>{
 let fee=snapshot.map(|(epoch,maximum_fee,basis_points)|native_transfer_fee::Fee{epoch,maximum_fee,basis_points:basis_points as u16});
 if inverse{let gross=crate::transfer_fee_recovered::pre_fee_amount(&fee,amount)?;crate::transfer_fee_recovered::calculate_fee(&fee,gross)}else{crate::transfer_fee_recovered::calculate_fee(&fee,amount)}
}


pub use crate::PostCompleteBuyEvent;


// Buy-side pretrade fee basis recovered from the original mode selector.
use crate::buy_fee_market_cap;#[inline(always)] fn pay_user<'info>(native:bool,base_mint:&InterfaceAccount<'info,Mint>,curve:&Account<'info,BondingCurve>,destination:&AccountInfo<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,quote_mint:&InterfaceAccount<'info,Mint>,quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,bump:u8)->Result<()>{quote_payments::transfer_to_user(native,base_mint.as_ref(),curve,destination,amount,token_program,quote_mint.decimals,quote_mint.as_ref(),quote_source,quote_destination,bump)}#[inline(always)] fn pay_owned<'info>(native:bool,base_mint:&InterfaceAccount<'info,Mint>,curve:&Account<'info,BondingCurve>,destination:AccountInfo<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,quote_mint:&InterfaceAccount<'info,Mint>,quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,bump:u8)->Result<()>{quote_payments::transfer_to_owned(native,base_mint.as_ref(),curve,destination,amount,token_program,quote_mint.decimals,quote_mint.as_ref(),quote_source,quote_destination,bump)}


pub use crate::quote_payments;

pub use crate::user_quote_payments;

fn init_volume_user(uva:&mut crate::UserVolumeAccumulator,user:&Signer){if uva.user==Pubkey::default(){uva.user=user.key();}}






#[inline(always)]
fn transfer_curve_mint_tokens<'info>(token_program:&Interface<'info,TokenInterface>,mint:&InterfaceAccount<'info,Mint>,destination:&InterfaceAccount<'info,TokenAccount>,source:&InterfaceAccount<'info,TokenAccount>,authority:&Account<'info,BondingCurve>,amount:u64,signer_seeds:&[&[&[u8]];1])->Result<()>{
    crate::buy_v2::token_transfers::transfer_curve_tokens(token_program,source,destination,authority,mint.decimals,mint.as_ref(),amount,signer_seeds)
}
