use anchor_lang::prelude::*;

// layout-pad(8): aligns the next Source site with the original line







/// Shared checked ceiling division, preserving addition/subtraction/division order.
#[inline(never)]
pub fn checked_ceil_div(numerator: u128, denominator: u128) -> Result<u128> {
    let sum = numerator.checked_add(denominator)
        .ok_or_else(|| error!(crate::PumpError::Overflow))?;
    let adjusted = sum.checked_sub(1)
        .ok_or_else(|| error!(crate::PumpError::Overflow))?;
    adjusted.checked_div(denominator)
        .ok_or_else(|| error!(crate::PumpError::DivisionByZero))
}

pub fn fee(quote_amount: u64, basis_points: u64) -> Result<u64> {
    let value = checked_ceil_div(u128::from(quote_amount) * u128::from(basis_points), 10000)?;
// layout-pad(10): aligns the next Source site with the original line









    u64::try_from(value).map_err(|_| error!(crate::PumpError::Truncation))
}

use crate::{trade_types::{BondingCurve,FeeTier},pump_fees::accounts::FeeConfig};
const WSOL_QUOTE:Pubkey=anchor_spl::token::spl_token::native_mint::ID;
const QUOTE_2:Pubkey=Pubkey::new_from_array([131,13,252,159,222,95,230,184,170,124,4,164,118,233,30,138,198,187,38,74,173,144,250,25,201,223,73,216,92,62,91,94]);
const USDC:Pubkey=anchor_lang::solana_program::pubkey!("EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v");
// layout-pad: aligns the next Source site with the original line
/// Shared fee query and accounting. Account clones are created here before
/// the fallible market-cap calculation, as in the original outer helper.
pub fn trade_fees<'info>(
    global: &Account<'info, crate::Global>,
    curve: &Account<'info, BondingCurve>,
    mint: &InterfaceAccount<'info, anchor_spl::token_interface::Mint>,
    fee_config: &Account<'info, crate::legacy_sell::LegacyFeeConfig>,
    fee_program: &Program<'info, crate::legacy_sell::LegacyFeesProgram>,
    program: &AccountInfo<'info>,
    quote_amount: u64,
) -> Result<(u64, u64, u64, u64)> {
    let fees = crate::pump_fees::cpi::get_fees_with_quote_mint(CpiContext::new(
        fee_program.to_account_info(),
        crate::pump_fees::cpi::accounts::GetFeesWithQuoteMint {
            fee_config: fee_config.to_account_info(),
            config_program_id: program.clone(),
        },
    ),
    true, crate::buy_fee_market_cap(curve, mint)?, curve.quote_mint)?.get();

    let (protocol_fee_bps, creator_fee_bps) = (fees.protocol_fee_bps, fees.creator_fee_bps);
    let creator_fee_bps = if global.creator_fee_configurable && curve.creator_fee_bps != 0 { curve.creator_fee_bps } else { creator_fee_bps };
    let protocol_fee = fee(quote_amount, protocol_fee_bps)?;
    let creator_fee = if curve.creator != Pubkey::default() { fee(quote_amount, creator_fee_bps)? } else { 0 };







    return Ok((protocol_fee, creator_fee, protocol_fee_bps, creator_fee_bps));
}





















































































pub fn calculate_fee_tier(fee_tiers: &[FeeTier], market_cap: u128) -> Result<(u64, u64)> {
    // fee tiers must be non-empty
    require!(!fee_tiers.is_empty(), crate::PumpError::FeeTiersEmpty);
    let first_tier = &fee_tiers[0];
    if market_cap < first_tier.market_cap_lamports_threshold {
        return Ok((first_tier.fees.protocol_fee_bps, first_tier.fees.creator_fee_bps));
    }
    let tier = fee_tiers.iter().rev().find(|tier| market_cap >= tier.market_cap_lamports_threshold).unwrap_or(first_tier);
    Ok((tier.fees.protocol_fee_bps, tier.fees.creator_fee_bps))
}











fn is_sol_quote(quote_mint: &Pubkey) -> bool { *quote_mint == Pubkey::default() || *quote_mint == WSOL_QUOTE || *quote_mint == QUOTE_2 }
fn get_fee_basis_points(fee_config: &FeeConfig, fee_config_len: usize, quote_mint: &Pubkey, market_cap: u128) -> Result<(u64, u64)> {
    require!(fee_config_len >= 2512, crate::PumpError::FeeConfigTooShort);
    if is_sol_quote(quote_mint) {
        calculate_fee_tier(&fee_config.fee_tiers, market_cap)
    } else if USDC == *quote_mint {
        calculate_fee_tier(if fee_config_len > 4072 { &fee_config.stable_fee_tiers } else { &[] }, market_cap)
    } else {
            let exotic = &fee_config.exotic_flat_fees;
            let use_exotic = fee_config_len > 4096 && (exotic.lp_fee_bps != 0 || exotic.protocol_fee_bps != 0 || exotic.creator_fee_bps != 0);
            let fees = if use_exotic { exotic } else { &fee_config.flat_fees }; Ok((fees.protocol_fee_bps, fees.creator_fee_bps))
    }
}
#[derive(Clone, Copy, Default)] pub struct TradeFees { pub protocol_fee: u64, pub creator_fee: u64, pub protocol_fee_bps: u64, pub creator_fee_bps: u64 }
pub fn get_fees(global: &crate::Global, bonding_curve: &BondingCurve, fee_config: &FeeConfig, fee_config_len: usize, market_cap: u128, amount: u64) -> Result<TradeFees> {
    let (protocol_fee_bps, creator_fee_bps) = get_fee_basis_points(fee_config, fee_config_len, &bonding_curve.quote_mint, market_cap)?;
    let creator_fee_bps = if global.creator_fee_configurable && bonding_curve.creator_fee_bps != 0 { bonding_curve.creator_fee_bps } else { creator_fee_bps };
    let protocol_fee = fee(amount, protocol_fee_bps)?;
    let creator_fee = if bonding_curve.creator != Pubkey::default() { fee(amount, creator_fee_bps)? } else { 0 };
    Ok(TradeFees { protocol_fee, creator_fee, protocol_fee_bps, creator_fee_bps })
}



