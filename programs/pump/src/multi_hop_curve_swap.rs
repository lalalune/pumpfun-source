//! Reconstructed multi-hop curve trading.
//! Signed original-runtime probes cover ordinary trades, completion, and quote adapters.
use anchor_lang::prelude::*;
use anchor_lang::solana_program::{instruction::{Instruction,AccountMeta},program::{invoke,invoke_signed},program_error::ProgramError};
use anchor_spl::{token::Token,token_2022::Token2022,token_interface::{Mint,TokenAccount}};
use crate::{Global,PumpError};
use crate::trade_types::{BondingCurve,FeeConfig,TradeEvent};
const FEES:Pubkey=anchor_lang::solana_program::pubkey!("pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ");
const AMM:Pubkey=anchor_lang::solana_program::pubkey!("pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA");
const WSOL:Pubkey=anchor_spl::token::spl_token::native_mint::ID;
#[derive(Accounts)]
pub struct MultiHopCurve<'info>{
 #[account(seeds=[b"global"],bump)]pub global:Box<Account<'info,Global>>,
 #[account(seeds=[b"fee_config",crate::ID.as_ref()],bump=fee_config.bump,seeds::program=FEES)]pub fee_config:Box<Account<'info,crate::pump_fees::accounts::FeeConfig>>,
 #[account(seeds=[b"global_config"],bump,seeds::program=AMM)]pub pump_amm_global_config:Signer<'info>,
 #[account(mut)]pub user:Signer<'info>,
 pub source_authority:Signer<'info>,
 #[account(mut)]pub source:Box<InterfaceAccount<'info,TokenAccount>>,
 #[account(mut)]pub destination:Box<InterfaceAccount<'info,TokenAccount>>,
 /// CHECK: Slot 7 is writable raw AccountInfo; no local owner/mint/membership constraint.
 #[account(mut)]pub buyback_fee_recipient:UncheckedAccount<'info>,
 pub token_program:Program<'info,Token>,
 pub token_2022_program:Program<'info,Token2022>,
 pub system_program:Program<'info,System>,
 /// CHECK: event-signing PDA.
 #[account(seeds=[b"__event_authority"],bump)]
 pub event_authority:AccountInfo<'info>,
 pub program:Program<'info,crate::program::PumpRecovered>,
}
#[derive(Accounts)]
pub struct CurveHop<'info>{
 pub base_mint:Box<InterfaceAccount<'info,Mint>>,
 pub quote_mint:Box<InterfaceAccount<'info,Mint>>,
 #[account(mut,seeds=[b"bonding-curve",base_mint.key().as_ref()],bump,
 constraint=quote_mint.key()==bonding_curve.quote_mint || (bonding_curve.quote_mint==Pubkey::default() && quote_mint.key()==WSOL) @ PumpError::MintDoesNotMatchBondingCurve)]
 pub bonding_curve:Box<Account<'info,BondingCurve>>,
 #[account(mut)]pub associated_base_bonding_curve:Box<InterfaceAccount<'info,TokenAccount>>,
 /// CHECK: Address and native quote branch checked before transfer.
 #[account(mut)]pub associated_quote_bonding_curve:UncheckedAccount<'info>,
}
#[derive(AnchorSerialize,AnchorDeserialize,Clone)]
pub struct CurveRunResult{pub amount_out:u64,pub buyback_fee:u64}

// D01: Decode every field before context PDA constraints and handler shape checks.
// Keep the decoded vectors; account length controls selection, never decoding.
#[derive(Clone)]
pub struct RouteFeeConfig(pub FeeConfig);
impl Owner for RouteFeeConfig { fn owner() -> Pubkey { FEES } }
impl AccountSerialize for RouteFeeConfig {}
impl AccountDeserialize for RouteFeeConfig {
    fn try_deserialize(buf: &mut &[u8]) -> Result<Self> {
        if buf.len() < 8 { return err!(anchor_lang::error::ErrorCode::AccountDiscriminatorNotFound); }
        if buf[..8] != [143,52,146,187,219,123,76,155] {
            return err!(anchor_lang::error::ErrorCode::AccountDiscriminatorMismatch);
        }
        Self::try_deserialize_unchecked(buf)
    }
    fn try_deserialize_unchecked(buf: &mut &[u8]) -> Result<Self> {
        let mut cursor = buf.get(8..).ok_or_else(|| error!(anchor_lang::error::ErrorCode::AccountDidNotDeserialize))?;
        FeeConfig::deserialize(&mut cursor).map(Self)
            .map_err(|_| error!(anchor_lang::error::ErrorCode::AccountDidNotDeserialize))
    }
}








// layout-pad(46): aligns the next Source site with the original line














































// T01: Exact four AccountInfos; program identity is in the instruction.
#[inline(always)] fn transfer_tokens<'info>(program: &AccountInfo<'info>, from: &impl ToAccountInfo<'info>, to: &AccountInfo<'info>, authority: &impl ToAccountInfo<'info>,
    mint: &AccountInfo<'info>, amount: u64, decimals: u8, seeds: &[&[&[u8]]]) -> Result<()> {
    if amount == 0 { return Ok(()); }
    anchor_spl::token_2022::transfer_checked(CpiContext::new_with_signer(program.clone(), anchor_spl::token_2022::TransferChecked { from: from.to_account_info(), to: to.clone(), authority: authority.to_account_info(), mint: mint.clone() }, seeds), amount, decimals)
}



pub struct PreviousHop<'info> {
    base_mint: Pubkey,
    output_vault: AccountInfo<'info>,
    authority: AccountInfo<'info>,
    bump: u8,
}














// Base address admission precedes quote admission; native quote checks only its address.
#[inline(always)] fn admit_vaults<'info>(
    h: &CurveHop<'info>,
    a: &MultiHopCurve<'info>,
    base_token_program: &AccountInfo<'info>,
    quote_token_program: &AccountInfo<'info>, native: bool, curve_key: &Pubkey,
    require_ata: fn(&Pubkey,&Pubkey,&Pubkey,&Pubkey)->Result<()>,
) -> Result<()> {
    require_ata(&h.associated_base_bonding_curve.key(), curve_key,
        &h.base_mint.key(), &base_token_program.key())?;
    if !native {
        crate::buy_v2::admit_associated_token_account(
            h.associated_quote_bonding_curve.as_ref(), &h.bonding_curve.to_account_info(),
            h.quote_mint.key(), quote_token_program.key(),
            &h.quote_mint.to_account_info(), quote_token_program,
            false, a.user.as_ref(), a.system_program.as_ref(),
        )?;
    } else { require_ata(&h.associated_quote_bonding_curve.key(), curve_key, &h.quote_mint.key(), &quote_token_program.key())?; }
    Ok(())
}
































pub fn execute<'info>(mut ctx: Context<'_,'_,'info,'info,MultiHopCurve<'info>>,
    amount_in: u64, hop_fees: Vec<u8>) -> Result<CurveRunResult> {





    let mut current_mint;
    require_gt!(amount_in, 0, PumpError::BuyZeroAmount);
    let remaining_accounts = ctx.remaining_accounts; let count = remaining_accounts.len() / 5;




    if remaining_accounts.len() < 5 || count * 5 != remaining_accounts.len() { return err!(PumpError::NotEnoughRemainingAccounts); }



    require!(hop_fees.len() == count && hop_fees.iter().all(|f| *f < 4), PumpError::MultiHopHopFeesMismatch);
    let a = &mut *ctx.accounts; current_mint = a.source.mint; let mut amount = amount_in; let mut total_buyback = 0u64; let mut previous = None;
    for index in 0..count {










        let start = index * 5; let mut accounts =
            &remaining_accounts[start..start.saturating_add(5)];
        let mut bumps = CurveHopBumps::default();
        let mut h = CurveHop::try_accounts(&crate::ID,&mut accounts,&[],&mut bumps,&mut std::collections::BTreeSet::new())?;
        let out = swap_hop(a,ctx.bumps.event_authority,&mut h,bumps.bonding_curve,&current_mint,amount,previous.as_ref(),index + 1 == count,hop_fees[index])?;
        h.exit(&crate::ID)?;
        previous = Some(PreviousHop { output_vault: out.vault, authority: h.bonding_curve.to_account_info(), base_mint: h.base_mint.key(), bump: bumps.bonding_curve });
        current_mint = out.mint;
        amount = out.amount;



















        total_buyback = total_buyback.checked_add(out.buyback_fee).ok_or_else(|| error!(PumpError::Overflow))?;
    }

    require_keys_eq!(current_mint, a.destination.mint, PumpError::MultiHopDiscontinuousPath);
    Ok(CurveRunResult { amount_out: amount, buyback_fee: total_buyback }) } macro_rules! route_event { ($a:expr, $event:expr, $bump:expr) => {{ let a = $a; let event = $event; anchor_lang::solana_program::log::sol_log_data(&[&anchor_lang::Event::data(event)]); let authority_info = a.event_authority.to_account_info(); let authority_bump = $bump; let disc = anchor_lang::event::EVENT_IX_TAG_LE; let inner_data = anchor_lang::Event::data(event); let ix_data: Vec<u8> = disc.into_iter().map(|b| *b).chain(inner_data.into_iter()).collect(); let ix = Instruction::new_with_bytes(crate::ID, &ix_data, vec![AccountMeta::new_readonly(*authority_info.key, true)]); invoke_signed(&ix, &[authority_info], &[&[b"__event_authority", &[authority_bump]]]).map_err(anchor_lang::error::Error::from)?; }}; }

// layout-pad(219): aligns the next Source site with the original line























        fn pool_before(global: &Global, curve: &BondingCurve, curve_base: u64, is_sol: bool, amount: u64, quote: u64) -> Result<(u64, u64)> { crate::trade::v3_pool_before(curve.real_quote_reserves, global.pool_migration_fee, curve_base, is_sol, amount, quote) }
        #[inline(never)]
        fn complete_fill(global: &Global, fee_config: &crate::pump_fees::accounts::FeeConfig, fee_config_len: usize, market_cap: u128,
            bonding_curve: &Account<BondingCurve>, associated_base_bonding_curve: &Box<InterfaceAccount<TokenAccount>>, flag: u8,
            protocol_fee_bps: u64, creator_fee_bps: u64, budget: u64) -> Result<Option<(crate::trade::TradeFees, u64, crate::trade::PostComplete)>> {
            let quote = u64::try_from(crate::buy_quote(bonding_curve, bonding_curve.real_token_reserves)?)
                .map_err(|_| error!(PumpError::Truncation))?;
            let fees = crate::legacy_sell::fee_math::get_fees(global, bonding_curve, fee_config, fee_config_len, market_cap, quote)?;
            let fees = crate::trade::TradeFees {
                protocol_fee: if flag & 1 != 0 { fees.protocol_fee } else { 0 },
                creator_fee: if flag & 2 != 0 { fees.creator_fee } else { 0 },
                protocol_fee_bps: if flag & 1 != 0 { fees.protocol_fee_bps } else { 0 },
                creator_fee_bps: if flag & 2 != 0 { fees.creator_fee_bps } else { 0 } };
            let total = crate::trade::add3(quote, fees.protocol_fee, fees.creator_fee)?;
            let remaining = match budget.checked_sub(total) { Some(r) if r > 0 => r, _ => return Ok(None) };

            let (pool_base, pool_quote) = pool_before(global, bonding_curve,
                associated_base_bonding_curve.amount, bonding_curve.quote_mint == Pubkey::default(), bonding_curve.real_token_reserves, quote)?;
            Ok(crate::trade::estimate_post_complete(&bonding_curve.creator, pool_base, pool_quote, protocol_fee_bps, creator_fee_bps,
                remaining, true)?.map(|post| (fees, quote, post)))
        }











































        #[inline(never)]
        fn token_program_for<'info>(token_program: &AccountInfo<'info>, token_2022_program: &AccountInfo<'info>,
            mint: &AccountInfo<'info>) -> Result<AccountInfo<'info>> {
            let owner = mint.to_account_info().owner;
            if owner == &anchor_spl::token_2022::ID { return Ok(token_2022_program.to_account_info()); }
            if owner == &anchor_spl::token::ID { return Ok(token_program.to_account_info()); }
            err!(PumpError::AccountTypeNotSupported)
        }






        #[inline(never)]
        fn require_ata(key:&Pubkey,owner:&Pubkey,mint:&Pubkey,program:&Pubkey)->Result<()>{
            require_keys_eq!(*key,anchor_spl::associated_token::get_associated_token_address_with_program_id(owner,mint,program),anchor_lang::error::ErrorCode::ConstraintSeeds);
            Ok(())
        }


pub fn native_buyback<'info>(a: &MultiHopCurve<'info>, event_bump: u8, curve: &Account<'info, BondingCurve>, amount: u64) -> Result<()> {
    if amount == 0 { return Ok(()); }
    let to = a.buyback_fee_recipient.to_account_info();
    let curve_info = curve.to_account_info();
    crate::trade::quote_payments::pay_out_native(curve, to.clone(), amount)?;
    invoke_signed(&Instruction { program_id: crate::ID, accounts: vec![AccountMeta::new_readonly(a.event_authority.key(), true), AccountMeta::new(curve_info.key(), false), AccountMeta::new(to.key(), false)], data: anchor_lang::event::EVENT_IX_TAG_LE.to_vec() },
        &[a.event_authority.to_account_info(), curve_info, to.clone()], &[&[b"__event_authority", &[event_bump]]])?;
    invoke(&anchor_spl::token::spl_token::instruction::sync_native(&anchor_spl::token::spl_token::id(), to.key)?, &[to])?;
    Ok(())
}

pub fn transfer_input<'info>(a: &MultiHopCurve<'info>, previous: Option<&PreviousHop<'info>>, token_program: &AccountInfo<'info>, to: &AccountInfo<'info>, decimals: u8, mint: &AccountInfo<'info>, amount: u64) -> Result<()> {
    match previous {
        None => {
            transfer_tokens(token_program, &*a.source, to, &a.source_authority, mint, amount, decimals, &[])
        }
        Some(p) => {
            if p.output_vault.key() == to.key() { return Ok(()); }
            transfer_tokens(token_program, &p.output_vault, to, &p.authority, mint, amount, decimals, &[&[b"bonding-curve", p.base_mint.as_ref(), &[p.bump]]])
        }
    }
}


















































































#[inline(never)] fn swap_hop<'info>(a: &mut MultiHopCurve<'info>, event_bump: u8, h: &mut CurveHop<'info>, curve_bump: u8, current_mint: &Pubkey, amount: u64, previous: Option<&PreviousHop<'info>>, last: bool, flag: u8) -> Result<HopOutput<'info>> {
        prepare_curve(a,h)?;
        crate::trade::validate_trade(h.bonding_curve.complete as u8,h.bonding_curve.is_cashback_coin as u64,(flag & 2 == 0) as u64)?;



        require!(!h.bonding_curve.is_mayhem_mode,PumpError::MultiHopMayhemCurveNotSupported);
        let native = h.bonding_curve.quote_mint == Pubkey::default(); let quote_fee = if native { None } else { crate::transfer_fee_recovered::get_transfer_fee(&h.quote_mint.to_account_info())? }; let base_token_program = token_program_for(&a.token_program, &a.token_2022_program, h.base_mint.as_ref().as_ref())?; let quote_token_program = token_program_for(&a.token_program, &a.token_2022_program, h.quote_mint.as_ref().as_ref())?; let curve_key = h.bonding_curve.key(); admit_vaults(h,a,&base_token_program,&quote_token_program,native,&curve_key,require_ata)?;
        if flag & 1 != 0 {
            crate::trade::validate_buyback_fee_recipient_account(&a.global,a.buyback_fee_recipient.as_ref(),false,
                &h.quote_mint.key(),&quote_token_program.key())?;
        }

// layout-pad(55): aligns the next Source site with the original line






















































        let buy = if *current_mint == h.quote_mint.key() { true } else if *current_mint == h.base_mint.key() { false } else { return err!(PumpError::MultiHopDiscontinuousPath) };
        let mint_key = h.base_mint.to_account_info().key; let seeds: &[&[&[u8]];1] = &[&[b"bonding-curve",mint_key.as_ref(),&[curve_bump]]];
        let c = &h.bonding_curve;
        let fee_config_len = a.fee_config.to_account_info().data_len(); let cap = crate::buy_fee_market_cap(c,&h.base_mint)?;
        let trade_amount = if buy {
            crate::transfer_fee_recovered::post_fee_amount(&quote_fee,amount)?
        }else{amount};
// layout-pad(18): aligns the next Source site with the original line

















        let buy_transfer_fee = amount.checked_sub(trade_amount).ok_or_else(|| error!(PumpError::Overflow))?;


        let post_fill;
        let (fees,base_amount,quote_amount,output,adapter_difference) = if buy {
            let selected = crate::legacy_sell::fee_math::get_fees(&a.global,c,&a.fee_config,fee_config_len,cap,trade_amount)?;
            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };
            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };
            let (_,crate::trade::TradeFees{protocol_fee:pf,creator_fee:cf,..}) = crate::trade::net_quote_for_budget(&c.creator,p_rate,c_rate,trade_amount)?;
            let q = crate::trade::sub3(trade_amount,pf,cf)?;


// layout-pad(6): aligns the next Source site with the original line





            let base = u64::try_from(crate::constant_product::tokens_for_quote(c,q)?).map_err(|_| error!(PumpError::Truncation))?;
            require_gt!(base,0,PumpError::BuyZeroAmount);

            let (base_amount,quote_amount,pf,cf,post_out) = if base > c.real_token_reserves {






                let user = a.user.key(); require!(!c.is_mayhem_mode && user!=a.global.whitelist_pda,PumpError::NotEnoughTokensToBuy);
                if let Some((fees, quote, post)) = complete_fill(&a.global,&a.fee_config,fee_config_len,cap,c,
                    &h.associated_base_bonding_curve,flag,p_rate,c_rate,trade_amount)? {
                    post_fill=Some(post);
                    (c.real_token_reserves,quote,fees.protocol_fee,fees.creator_fee,post.base_out)
                }else{post_fill=None;(c.real_token_reserves,q,pf,cf,0)}
            }else{post_fill=None;(base,q,pf,cf,0)};


















            let raw_output = base_amount.checked_add(post_out).ok_or_else(|| error!(PumpError::Overflow))?;


// layout-pad(45): aligns the next Source site with the original line
            if native { crate::user_quote_payments::transfer_native(a.system_program.as_ref(),&a.user,h.bonding_curve.as_ref(),amount)?; } else { transfer_input(a,previous,&quote_token_program,&h.associated_quote_bonding_curve,h.quote_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.quote_mint),amount)?; }
            h.bonding_curve.apply_buy(base_amount,quote_amount)?;
            if last && raw_output != 0 { transfer_base_out(&base_token_program,&h.associated_base_bonding_curve,&a.destination,&h.bonding_curve,h.base_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.base_mint),raw_output,seeds)?; }
            (crate::trade::TradeFees{protocol_fee:pf,creator_fee:cf,protocol_fee_bps:p_rate,creator_fee_bps:c_rate},base_amount,quote_amount,raw_output,buy_transfer_fee)








































        } else {
            let gross_sell = u64::try_from(c.sell_quote(amount)?).map_err(|_| error!(PumpError::Truncation))?;
            let selected = crate::legacy_sell::fee_math::get_fees(&a.global,c,&a.fee_config,fee_config_len,cap,gross_sell)?;
            let p_rate = if flag & 1 != 0 { selected.protocol_fee_bps } else { 0 };
            let c_rate = if flag & 2 != 0 { selected.creator_fee_bps } else { 0 };
            let pf = if flag & 1 != 0 { selected.protocol_fee } else { 0 };
            let cf = if flag & 2 != 0 { selected.creator_fee } else { 0 };
            let net = crate::trade::sub3(gross_sell,pf,cf)?;
// layout-pad(6): aligns the next Source site with the original line





            require_gt!(net,0,PumpError::SellZeroAmount);
            let output = crate::transfer_fee_recovered::post_fee_amount(&quote_fee,net)?;




            let sell_transfer_fee = net.checked_sub(output).ok_or_else(|| error!(PumpError::Overflow))?;
            transfer_input(a,previous,&base_token_program,&h.associated_base_bonding_curve.to_account_info(),h.base_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.base_mint),amount)?;
            h.bonding_curve.apply_sell(amount,gross_sell)?;
            if last && !native && net != 0 { transfer_quote_out(&quote_token_program,&h.associated_quote_bonding_curve,&a.destination,&h.bonding_curve,h.quote_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.quote_mint),net,seeds)?; }
            post_fill=None; (crate::trade::TradeFees{protocol_fee:pf,creator_fee:cf,protocol_fee_bps:p_rate,creator_fee_bps:c_rate},amount,gross_sell,output,sell_transfer_fee)
        };


        // A02: Input succeeded; each checked operation immediately precedes its store.






















        let buyback_raw = h.bonding_curve.accrue_fees(&a.global,fees.protocol_fee,fees.creator_fee)?;
        let post_buyback_raw = if let Some(post)=post_fill.as_ref() {
            h.bonding_curve.post_complete_base_out=post.base_out;
            h.bonding_curve.post_complete_quote_in=post.quote_in;
            h.bonding_curve.accrue_fees(&a.global,post.fees.protocol_fee,post.fees.creator_fee)?
        }else{0};






        let paid_buyback=buyback_raw.checked_add(post_buyback_raw).ok_or_else(
            ||error!(PumpError::Overflow))?;let received_buyback=crate::transfer_fee_recovered::post_fee_amount(&quote_fee,paid_buyback)?;
        let post_buyback=crate::transfer_fee_recovered::post_fee_amount(&quote_fee,post_buyback_raw)?;






        let buyback=received_buyback.checked_sub(post_buyback).ok_or_else(||error!(PumpError::Overflow))?;






        // One quote transfer pays both buybacks; the receipt is assigned to the first fill before the post fill.
        if flag & 1 != 0 {
            if native {
                native_buyback(a,event_bump,&h.bonding_curve,paid_buyback)?;
            } else if paid_buyback != 0 {
                transfer_buyback_out(&quote_token_program,&h.associated_quote_bonding_curve,&a.buyback_fee_recipient,
                    &h.bonding_curve,h.quote_mint.decimals,AsRef::<AccountInfo>::as_ref(&*h.quote_mint),
                    paid_buyback,seeds)?;
            }
        }
        if native && !buy && last {
            crate::trade::quote_payments::pay_out_native(&h.bonding_curve,a.user.to_account_info(),output)?;
        }
        let c = &h.bonding_curve;
        let timestamp = Clock::get()?.unix_timestamp; let event = trade_event(c,&a.global,&crate::UserVolumeAccumulator::default(),&a.user.key(),&h.base_mint.key(),buy,base_amount,quote_amount,&fees,buyback,adapter_difference,"multi_hop_swap",timestamp);
















        route_event!(&*a,&event,event_bump);
        let completed=h.bonding_curve.real_token_reserves==0; if completed { h.bonding_curve.complete=true;
            let completion=crate::trade_types::CompleteEvent { mint:h.base_mint.key(),user:a.user.key(),
                bonding_curve:h.bonding_curve.key(),timestamp,quote_mint:h.bonding_curve.quote_mint };
            route_event!(&*a,&completion,event_bump);

        if let Some(post)=post_fill {
            let post_event=crate::trade::post_complete_buy_event(&post,a.user.key(),h.base_mint.key(),
                h.bonding_curve.key(),h.bonding_curve.quote_mint,timestamp,post_buyback)?;




            route_event!(&*a,&post_event,event_bump);
        } } Ok(HopOutput { mint: if buy { h.base_mint.key() } else { h.quote_mint.key() }, amount: output, buyback_fee: received_buyback, vault: if buy { h.associated_base_bonding_curve.to_account_info() } else { h.associated_quote_bonding_curve.to_account_info() } }) }


















pub use crate::payments::mhc_transfer_quote_out as transfer_quote_out;
// layout-pad
// layout-pad
// layout-pad






pub use crate::payments::trade_event;
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
pub use crate::payments::mhc_transfer_base_out as transfer_base_out;
// layout-pad
// layout-pad
// layout-pad
// layout-pad
pub use crate::payments::mhc_transfer_buyback_out as transfer_buyback_out;
// layout-pad
// layout-pad
// layout-pad
// layout-pad

// N01: Native interface hypotheses use pinned SDK APIs, not newly recovered processors.
fn prepare_curve<'info>(a: &MultiHopCurve<'info>, h: &CurveHop<'info>) -> Result<()> {
    crate::trade_types::prepare_bonding_curve(&h.bonding_curve, &a.system_program, &a.user)
}







































pub struct HopOutput<'info> { mint: Pubkey, amount: u64, buyback_fee: u64, vault: AccountInfo<'info> }









// S01: General iteration; fee flags and last-hop transfer are independent.
