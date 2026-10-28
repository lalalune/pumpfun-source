use anchor_lang::prelude::*;

#[inline(never)]
pub fn transfer_native<'info>(
    system_program: &AccountInfo<'info>, payer: &Signer<'info>,
    destination: &UncheckedAccount<'info>, amount: u64,
) -> Result<()> {
    if amount == 0 { return Ok(()); }
    anchor_lang::system_program::transfer(
        CpiContext::new(system_program.clone(), anchor_lang::system_program::Transfer {
            from: payer.to_account_info(), to: destination.to_account_info(),
        }), amount,
    )
}

#[derive(AnchorDeserialize)]
struct AmmConfigBase {
    admin: Pubkey,
    lp_fee_basis_points: u64,
    protocol_fee_basis_points: u64,
    disable_flags: u8,
    protocol_fee_recipients: [Pubkey; 8],
    coin_creator_fee_basis_points: u64,
    admin_set_coin_creator_authority: Pubkey,
    whitelist_pda: Pubkey,
    reserved_fee_recipient: Pubkey,
    mayhem_mode_enabled: bool,
    reserved_fee_recipients: [Pubkey; 7],
    is_cashback_enabled: bool,
    buyback_fee_recipients: [Pubkey; 8],
    buyback_basis_points: u64,
}

fn decode_boost_enabled(data: &[u8]) -> Option<bool> {
    if data.len() < 907 || data[..8] != [149, 8, 156, 202, 160, 252, 176, 217] { return None; }
    let mut body = &data[8..];
    let _base = AmmConfigBase::deserialize(&mut body).ok()?;
    if data.len() < 940 { return Some(false); }
    let _boost_authority = Pubkey::deserialize(&mut body).ok()?;
    let enabled = bool::deserialize(&mut body).ok()?;
    if data.len() >= 949 {
        let _creator_fee_configurable = bool::deserialize(&mut body).ok()?;
        let _max_configurable_creator_fee_bps = u64::deserialize(&mut body).ok()?;
    }
    Some(enabled)
}

pub(crate) fn boost_enabled(config: &AccountInfo) -> bool {
    config.try_borrow_data().ok().and_then(|data|decode_boost_enabled(&data)).unwrap_or(false)
}
