# coordbodyA-03 (base L06, identity recipe): 903 normalized / 165 raw (+4: 0x3dd78, 0x6eed8, 0x6f3e8, 0x160d0)

Cumulative: includes coordbodyA-01 (fee_recipient.rs) and coordbodyA-02 (sell.rs helpers).

## Change (this delivery)
`src/buy_v2.rs`: new `pub fn check_token_account(account:&AccountInfo, authority:&AccountInfo, mint:&Pubkey,
token_program:&Pubkey) -> Result<()>` placed in the existing pad block after admit_associated_token_account
(lines 106-123; pad lines rebalanced, file length unchanged):

    require_keys_eq!(*account.owner,*token_program,PumpError::AccountTypeNotSupported);      // buy_v2.rs:109
    let data=account.try_borrow_data()?;
    let mut buf:&[u8]=&data;let token=TokenAccount::try_deserialize(&mut buf)?;
    require_keys_eq!(token.mint,*mint,PumpError::MintDoesNotMatchBondingCurve);              // buy_v2.rs:116
    require_keys_eq!(token.owner,authority.key(),PumpError::AccountTypeNotSupported);        // buy_v2.rs:121
    Ok(())

Call sites (buy_v2 buy handler line 363, buy_exact_quote_in line 777, sell_v2 line 253): the two-line
"owner-program require + check_token(mint) + re-borrow/deserialize owner require" sequence for
`associated_quote_user` is replaced in place by one call `check_token_account(&a.associated_quote_user, a.user, quote_mint,
quote_token_program)?` (second line left empty; no line shifts).

## Binary evidence
- Original 0x160d0 (2792 B): fn(ret, account r2, authority r3 (&AccountInfo: key loaded via [r3+0]), mint r4,
  token_program r5): memcmp(account.owner, token_program) else 6010 at line 0x6d=109; try_borrow_data; TokenAccount
  try_deserialize; memcmp(token.mint, mint) else 6004 at 0x74=116; memcmp(token.owner, authority.key copy) else 6010 at
  0x79=121; the data Ref is released only at the end (all checks run under the borrow). Callers: v2 buy 0x13b9b8,
  buy_exact_quote_in 0x13f630, sell_v2 0x144508 (args from the associated_quote_user / user / quote_mint /
  quote_token_program fields) and the v3 preparation 0x7f010.
- The explicit `let mut buf:&[u8]=&data;` slice local is what puts the slice at -0x1e8 and gives the original's frame
  (+0x10); the inline `&mut &data[..]` temporary (ct1) is identical except for those stack offsets.
- Behaviour: same three checks with the same errors in the same order as the base's sequence (the base deserialized the
  account twice; the original once). Coords of the removed call-site requires were not on original lines (handler
  windows unmatched). No losses.
