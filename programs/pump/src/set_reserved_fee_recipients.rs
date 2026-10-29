use anchor_lang::prelude::*;
use crate::{AdminGlobal, AdminReadonly, PumpError, ReservedFeeRecipientsEvent};
use anchor_lang::error::ErrorCode;

































pub fn set_reserved_fee_recipients(ctx: Context<AdminReadonly>, whitelist_pda: Pubkey) -> Result<()> {
    let remaining_accounts = ctx.remaining_accounts;
    let global = &mut ctx.accounts.global;
    require_gte!(remaining_accounts.len(), 8usize, PumpError::NotEnoughRemainingAccounts);












    let recipients: [Pubkey; 8] = remaining_accounts[..8].iter().map(|account| account.key()).collect::<Vec<Pubkey>>().try_into().map_err(|_| ErrorCode::AccountNotEnoughKeys).unwrap();
    let reserved_fee_recipients: [Pubkey; 7] = recipients[1..].try_into().unwrap();
    let reserved_fee_recipient = recipients[0];
    let rent = Rent::get()?;
    {
        let mut accounts = remaining_accounts.iter().take(8).enumerate();
        while let Some((index, account)) = accounts.next() {
            require_keys_neq!(account.key(), Pubkey::default(), PumpError::AllFeeRecipientsShouldBeNonZero);
            if account.executable {
                return Err(Error::from(ErrorCode::ConstraintExecutable).with_account_name(format!("reserved_fee_recipients[{}]", index)));
            }
            if !rent.is_exempt(account.lamports(), account.try_data_len()?) {
                return Err(rent_exempt_error(Error::from(ErrorCode::ConstraintRentExempt), format!("reserved_fee_recipients[{}]", index)));
            }
        }
    }
    global.whitelist_pda = whitelist_pda;
    global.reserved_fee_recipient = reserved_fee_recipient;
    global.reserved_fee_recipients.copy_from_slice(&reserved_fee_recipients);
    let event = ReservedFeeRecipientsEvent {
        timestamp: Clock::get()?.unix_timestamp,
        reserved_fee_recipient: global.reserved_fee_recipient,
        reserved_fee_recipients: global.reserved_fee_recipients,
    };
    emit!(event);
    emit_cpi!(event);
    Ok(())
}




























pub fn update_buyback_config(ctx: Context<AdminGlobal>, buyback_basis_points: Option<u64>) -> Result<()> {
    let global = &mut ctx.accounts.global;
    if let Some(value) = buyback_basis_points {
        global.set_buyback_basis_points(value)?;
    }
    let ra = ctx.remaining_accounts;
    match ra.len() {
        0 => {}
        8 => {
            let recipients = [ra[0].key(), ra[1].key(), ra[2].key(), ra[3].key(), ra[4].key(), ra[5].key(), ra[6].key(), ra[7].key()];
            global.set_buyback_fee_recipients(recipients)?;
        }
        _ => return err!(PumpError::WrongBuybackFeeRecipientsCount),
    }
    Ok(())
}

#[cold] fn rent_exempt_error(error: Error, name: String) -> Error {
    crate::account_name::with_owned_name(error, &name)
}
