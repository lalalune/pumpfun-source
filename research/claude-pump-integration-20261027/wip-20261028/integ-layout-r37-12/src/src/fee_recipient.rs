use anchor_lang::prelude::*;
use crate::{Global, PumpError};
use crate::trade_types::BondingCurve;

/// Validate the recipient against the curve's configured fee-recipient family.
pub fn validate_fee_recipient<'info>(
    fee_recipient: &UncheckedAccount<'info>,
    global: &Account<'info, Global>,
    bonding_curve: &Account<'info, BondingCurve>,
) -> Result<()> {
    let key = fee_recipient.key();
    if bonding_curve.is_mayhem_mode {
        if key == global.reserved_fee_recipient || global.reserved_fee_recipients.contains(&key) { return Ok(()); }
// layout-pad(5): aligns the next Source site with the original line




        return err!(PumpError::NotAuthorized);
    }
    if key == global.fee_recipient || global.fee_recipients.binary_search(&key).is_ok() { return Ok(()); }
// layout-pad(13): aligns the next Source site with the original line












    err!(PumpError::NotAuthorized)
}
