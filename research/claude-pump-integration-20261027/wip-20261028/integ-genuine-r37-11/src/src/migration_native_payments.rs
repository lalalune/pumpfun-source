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

pub(crate) fn boost_enabled(config: &AccountInfo) -> bool {
    let Ok(data) = config.try_borrow_data() else { return false };
    let mut buf: &[u8] = &data;
    crate::pump_amm::accounts::GlobalConfig::try_deserialize(&mut buf).map_or(false, |global_config| global_config.boost_enabled)
}
