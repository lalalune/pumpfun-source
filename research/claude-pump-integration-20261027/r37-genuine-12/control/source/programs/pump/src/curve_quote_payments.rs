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

#[inline(never)]
pub fn transfer_to_user<'info>(
    native:bool,base_mint:&AccountInfo<'info>,curve:&Account<'info,BondingCurve>,
    destination:&AccountInfo<'info>,amount:u64,token_program:&Interface<'info,TokenInterface>,
    quote_decimals:u8,quote_mint:&AccountInfo<'info>,
    quote_source:Option<&AccountInfo<'info>>,quote_destination:Option<&AccountInfo<'info>>,
    bump:u8,
)->Result<()>{
    if native{return transfer_native(curve,destination,amount)}
    let from=quote_source.unwrap();
    let to=quote_destination.unwrap();
    let authority=curve.to_account_info();
    let mint_key=*base_mint.key;
    let bump=[bump];
    let seeds:&[&[u8]]=&[b"bonding-curve",mint_key.as_ref(),&bump];
    crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
        token_program,from,to,authority,quote_decimals,quote_mint,amount,&[seeds],
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
    if native{return transfer_native(curve,destination,amount)}
    let from=quote_source.unwrap();
    let to=quote_destination.unwrap();
    let authority=curve.to_account_info();
    let mint_key=*base_mint.key;
    let bump=[bump];
    let seeds:&[&[u8]]=&[b"bonding-curve",mint_key.as_ref(),&bump];
    crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
        token_program,from,to,authority,quote_decimals,quote_mint,amount,&[seeds],
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
    let from=quote_source.unwrap();
    let to=quote_destination.unwrap();
    let authority=curve.to_account_info();
    let mint_key=*base_mint.key;
    let bump=[bump];
    let seeds:&[&[u8]]=&[b"bonding-curve",mint_key.as_ref(),&bump];
    crate::sell_v2::quote_token_transfers::transfer_quote_tokens(
        token_program,from,to,authority,quote_decimals,quote_mint,amount,&[seeds],
    )
}

