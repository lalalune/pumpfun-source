use crate::*;
#[event_cpi]
#[derive(Accounts)]
pub struct ExtendAccount<'info> {
    /// CHECK: this instruction handles raw supported account discriminators.
    #[account(mut,owner=crate::ID)]
    pub account: AccountInfo<'info>,
    #[account(mut)]
    pub user: Signer<'info>,
    pub system_program: Program<'info, System>,
}
#[event]
#[derive(Clone)]
pub struct ExtendAccountEvent {
    pub account: Pubkey,
    pub user: Pubkey,
    pub current_size: u64,
    pub new_size: u64,
    pub timestamp:i64,
}
const GLOBAL_DISCRIMINATOR: &[u8] = &[167, 232, 232, 177, 200, 108, 114, 127];
const BONDING_CURVE_DISCRIMINATOR: &[u8] = &[23, 183, 248, 55, 96, 216, 172, 96];
const GLOBAL_VOLUME_ACCUMULATOR_DISCRIMINATOR: &[u8] = &[202, 42, 246, 43, 142, 190, 30, 255];
const USER_VOLUME_ACCUMULATOR_DISCRIMINATOR: &[u8] = &[86, 255, 112, 14, 102, 53, 154, 250];
fn transfer_lamports(accounts: &ExtendAccount, lamports: u64) -> Result<()> {
    if lamports > 0 {
        anchor_lang::system_program::transfer(
            CpiContext::new(
                accounts.system_program.to_account_info(),
                anchor_lang::system_program::Transfer {
                    from: accounts.user.to_account_info(),
                    to: accounts.account.to_account_info(),
                },
            ),
            lamports,
        )?;
    }
    Ok(())
}
pub fn execute(ctx: Context<ExtendAccount>) -> Result<()> {
    let account = &ctx.accounts.account;
    let current_size = account.data_len();
    let new_size = get_account_size(account)?;
    if current_size == new_size {
        msg!("Account already has the correct size");
        return Ok(());
    }
    if current_size > new_size {
        msg!("Account already has more than {} bytes: {}", new_size, current_size);
        return Ok(());
    }
    let rent = Rent::get()?;
    let delta = rent
        .minimum_balance(new_size)
        .saturating_sub(rent.minimum_balance(current_size));
    transfer_lamports(&ctx.accounts, delta)?;
    account.realloc(new_size, false)?;
    let event = ExtendAccountEvent {
        account: account.key(),
        user: ctx.accounts.user.key(),
        current_size: current_size as u64,
        new_size: new_size as u64,
        timestamp: Clock::get()?.unix_timestamp,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
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
fn get_account_size(account: &AccountInfo) -> Result<usize> {
    require!(account.data_len() >= 8, PumpError::AccountTypeNotSupported);
// layout-pad
// layout-pad
// layout-pad
// layout-pad
    let discriminator_data = &account.try_borrow_data()?[..8];
    let size = if discriminator_data == GLOBAL_DISCRIMINATOR {
        1088
    } else if discriminator_data == BONDING_CURVE_DISCRIMINATOR {
        166
    } else if discriminator_data == GLOBAL_VOLUME_ACCUMULATOR_DISCRIMINATOR {
        600
    } else if discriminator_data == USER_VOLUME_ACCUMULATOR_DISCRIMINATOR {
        137
    } else {
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
// layout-pad
        return err!(PumpError::AccountTypeNotSupported);
    };
    Ok(size)
}

#[inline(never)]
pub fn prepare_bonding_curve<'info>(
    curve: &Account<'info, crate::trade_types::BondingCurve>,
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
) -> Result<()> {
    let current_size = curve.to_account_info().data_len();
    let needs_realloc = current_size < 166;
    let new_size = current_size.max(166);
    fund_bonding_curve_rent(curve, system_program, payer, new_size)?;
    if needs_realloc { curve.to_account_info().realloc(166, false)?; }
    Ok(())
}







#[inline(never)]
pub fn fund_bonding_curve_rent<'info>(
    curve: &Account<'info, crate::trade_types::BondingCurve>,
    system_program: &Program<'info, System>,
    payer: &Signer<'info>,
    size: usize,
) -> Result<()> {
    let native = curve.quote_mint == Pubkey::default(); let reserved = if !native { 0 } else {
        curve.real_quote_reserves.checked_add(crate::reserved_bonding_curve_fees(curve)?)
            .ok_or_else(|| error!(crate::PumpError::Overflow))?
    };


    let minimum = Rent::get()?.minimum_balance(size);
    let available = curve.to_account_info().lamports().saturating_sub(reserved);
    if minimum > available {
        let lamports = minimum.saturating_sub(available);
        anchor_lang::system_program::transfer(
            CpiContext::new(
                system_program.to_account_info(),
                anchor_lang::system_program::Transfer {
                    from: payer.to_account_info(),
                    to: curve.to_account_info(),
                },
            ),
            lamports,
        )?;
    }
    Ok(())
}
