use anchor_lang::prelude::*;

use crate::trade_types::{BondingCurve, Fees};
use anchor_spl::token_interface::Mint;

/// Checked normal-buy quote calculation precedes the fee CPI.
pub fn buy_quote(curve: &BondingCurve, amount: u64) -> Result<u64> {
    let denominator = curve.virtual_token_reserves.checked_sub(amount)
        .ok_or_else(|| error!(crate::PumpError::Overflow))?;
    require!(denominator != 0, crate::PumpError::DivisionByZero);
    let quote = u128::from(amount) * u128::from(curve.virtual_quote_reserves)
        / u128::from(denominator) + 1;
    u64::try_from(quote).map_err(|_| error!(crate::PumpError::Truncation))
}

/// Shared fee query and accounting. Account clones are created here before
/// the fallible market-cap calculation, as in the original outer helper.
pub fn trade_fees<'info>(
    global: &Account<'info, crate::Global>,
    curve: &Account<'info, BondingCurve>,
    mint: &InterfaceAccount<'info, Mint>,
    fee_config: &Account<'info, super::LegacyFeeConfig>,
    fee_program: &Program<'info, super::LegacyFeesProgram>,
    program: &AccountInfo<'info>,
    quote_amount: u64,
) -> Result<(u64, u64, u64, u64)> {
    let ctx = CpiContext::new(
        fee_program.to_account_info(),
        GetFeesWithQuoteMint {
            fee_config: fee_config.to_account_info(),
            config_program_id: program.clone(),
        },
    );
    let cap = market_cap(curve, mint)?;
    let fees = get_fees_with_quote_mint(ctx, true, cap, curve.quote_mint)?.get();
    let creator_fee_bps = if global.creator_fee_configurable && curve.creator_fee_bps > 0 {
        curve.creator_fee_bps
    } else {
        fees.creator_fee_bps
    };
    let protocol_fee = fee(quote_amount, fees.protocol_fee_bps)?;
    let creator_fee = if curve.creator == Pubkey::default() {
        0
    } else {
        fee(quote_amount, creator_fee_bps)?
    };
    Ok((protocol_fee, creator_fee, fees.protocol_fee_bps, creator_fee_bps))
}

pub use super::fee_math::{checked_ceil_div, fee};

#[inline(never)]
fn market_cap(curve: &BondingCurve, mint: &Mint) -> Result<u128> {
    require!(curve.virtual_token_reserves != 0, crate::PumpError::DivisionByZero);
    let supply = if curve.is_mayhem_mode {
        curve.token_total_supply
    } else {
        mint.supply
    };
    Ok(u128::from(supply) * u128::from(curve.virtual_quote_reserves)
        / u128::from(curve.virtual_token_reserves))
}

// Keep existing caller paths while using the root external-interface API.
pub(crate) use crate::pump_fees::cpi::accounts::GetFeesWithQuoteMint;
pub use crate::pump_fees::cpi::{get_fees_with_quote_mint, Return};
