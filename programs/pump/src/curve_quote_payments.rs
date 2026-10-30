use anchor_lang::prelude::*;
use anchor_spl::token_interface::TokenInterface;
use crate::trade_types::BondingCurve;

#[inline(never)]
pub fn transfer_native<'info,T:AsRef<AccountInfo<'info>>>(
    source:&Account<'info,BondingCurve>,destination:T,amount:u64,
)->Result<()>{
    if amount==0{return Ok(())}
    source.sub_lamports(amount)?;
    destination.add_lamports(amount)?;
    Ok(())
}

/// Lamport move without the zero-amount early return (callers check the amount).
#[inline(never)]
pub fn move_native<'a,'info,T:AsRef<AccountInfo<'info>>>(
    source:&Account<'a,BondingCurve>,destination:T,amount:u64,
)->Result<()>{
    source.sub_lamports(amount)?;
    destination.add_lamports(amount)?;
    Ok(())
}

/// Lamport payout from the curve to a user-side account (zero amounts are a no-op).
#[inline(never)]
pub fn pay_out_native<'info,T:AsRef<AccountInfo<'info>>>(
    source:&Account<'info,BondingCurve>,destination:T,amount:u64,
)->Result<()>{
    if amount==0{return Ok(())}
    source.sub_lamports(amount)?;
    destination.add_lamports(amount)?;
    Ok(())
}

#[inline(never)]
pub fn transfer_to_user<'info>(
    native:bool,base_mint:&AccountInfo<'info>,curve:&Account<'info,BondingCurve>,
    destination:&AccountInfo<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,
    quote_decimals:u8,quote_mint:&AccountInfo<'info>,
    quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,
    bump:u8,
)->Result<()>{
    if native{return pay_out_native(curve,destination,amount)}
    let (from,to)=crate::curve_quote_accounts(quote_source,quote_destination);

    crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
        token_program,from,to,curve.to_account_info(),quote_decimals,quote_mint,amount,
        &[&[b"bonding-curve",base_mint.key().as_ref(),&[bump]]],
    )
}

#[inline(never)]
pub fn transfer_to_owned<'info>(
    native:bool,base_mint:&AccountInfo<'info>,curve:&Account<'info,BondingCurve>,
    destination:AccountInfo<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,
    quote_decimals:u8,quote_mint:&AccountInfo<'info>,
    quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,
    bump:u8,
)->Result<()>{
    if native{return pay_out_native(curve,destination,amount)}
    let (from,to)=crate::curve_quote_accounts(quote_source,quote_destination);

    crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
        token_program,from,to,curve.to_account_info(),quote_decimals,quote_mint,amount,
        &[&[b"bonding-curve",base_mint.key().as_ref(),&[bump]]],
    )
}

#[inline(never)]
pub fn transfer_to_recipient<'info>(
    native:bool,base_mint:&AccountInfo<'info>,curve:&Account<'info,BondingCurve>,
    destination:&&UncheckedAccount<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,
    quote_decimals:u8,quote_mint:&AccountInfo<'info>,
    quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,
    bump:u8,
)->Result<()>{
    if native{return transfer_native(curve,destination,amount)}
    let (from,to)=crate::curve_quote_accounts(quote_source,quote_destination);

    crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
        token_program,from,to,curve.to_account_info(),quote_decimals,quote_mint,amount,
        &[&[b"bonding-curve",base_mint.key().as_ref(),&[bump]]],
    )
}

#[inline(never)]
pub fn transfer_native_unchecked<'info,T:AsRef<AccountInfo<'info>>>(
    source:&Account<'info,BondingCurve>,destination:T,amount:u64,
)->Result<()>{
    source.sub_lamports(amount)?;
    destination.add_lamports(amount)?;
    Ok(())
}
