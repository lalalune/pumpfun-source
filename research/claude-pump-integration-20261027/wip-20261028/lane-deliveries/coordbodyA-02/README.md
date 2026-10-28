# coordbodyA-02 (base L06, identity recipe): 902 normalized / 165 raw (+3: 0x3dd78, 0x6eed8, 0x6f3e8)

Cumulative: includes coordbodyA-01 (fee_recipient.rs validate_fee_recipient, +0x3dd78).

## Changes (this delivery)
1. `src/sell.rs` (legacy_sell module, original file programs/pump/src/sell.rs) gains the two shared helpers the original
   keeps in sell.rs, appended after the existing items with pad lines so the sites sit on the original lines:
   - `pub fn check_bonding_curve_v2(remaining_accounts:&[AccountInfo], mint:&Pubkey) -> Result<()>`:
     `require!(!remaining_accounts.is_empty(), InvalidBondingCurveV2)` at sell.rs:126, PDA
     `find_program_address([b"bonding-curve-v2", mint], crate::ID)` then `require!(remaining_accounts[0].key()==expected,
     InvalidBondingCurveV2)` at sell.rs:133.  -> matches original 0x6eed8 (1296 B).
   - `pub fn buyback_fee_recipient(remaining_accounts, global:&Global, index) -> Result<&AccountInfo>`:
     `require!(index < len, BuybackFeeRecipientMissing)` at sell.rs:145, then
     `global.validate_buyback_fee_recipient(account.key()).map(|_| account)`.  -> matches original 0x6f3e8 (752 B).
2. Call sites (same lines, statement replaced in place; no line shifts):
   lib.rs:367 (buy) / buy.rs:17 (legacy buy execute): `buyback_fee_recipient(rem,&a.global,1)?`;
   lib.rs:1045 (sell): `buyback_fee_recipient(rem,&a.global,index+1)?`;
   lib.rs:692 / buy.rs:37: `check_bonding_curve_v2(rem,&a.mint.key())?`;
   lib.rs:1040 (sell): `check_bonding_curve_v2(&rem[index..],&a.mint.key())?` (index is 0, or 1 after the cashback
   accumulator `rem.first()` check, so the subslice always exists; same accounts as the base's `rem.get(index)`).

## Binary evidence
- 0x6eed8: fn(ret, rem.ptr r2, rem.len r3, &mint r4): `jne len,0` else InvalidBondingCurveV2 (6074) at line 0x7e=126;
  seeds [b"bonding-curve-v2"(16 B @0x1b6690), mint(32)] program 0x1b79df; memcmp(rem[0].key copy, pda) else 6074 at
  line 0x85=133 (coords.py shows 133,133 because both blocks reuse the same stack slot; actual lines 133 and 126).
  Callers: 0x14c038 (lib.rs buy), 0x14f4e0 (buy.rs), 0x152888 (lib.rs sell), each passing a stack copy of the mint key.
- 0x6f3e8: fn(ret, rem.ptr, rem.len, &Global (Account+8), index): `jlt index,len` else BuybackFeeRecipientMissing (6062)
  at line 0x91=145; key copy -> call Global::validate_buyback_fee_recipient (0x98438); Ok -> (2, &rem[index]).
  The Ok/Err branch shape (`jeq tag,2,+1; ja`) comes from `.map(|_| account)`; `?`+Ok, if-let, match forms keep `jne`.
  Callers pass index 1 (buy, buy.rs) and 1/2 (sell, cashback-dependent) = the base's `get(1)` / `get(index+1)`.
- Behaviour: identical checks, errors and order as the base's inline code; only the error Source moves to sell.rs as in
  the original binary. All lib.rs/buy.rs edits replace a statement inside its existing line (line-neutral); sell.rs has
  no matched sites (new items appended at the end). No losses.
