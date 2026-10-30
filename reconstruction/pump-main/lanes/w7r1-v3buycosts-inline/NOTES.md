# Lane w7r1-v3buycosts-inline: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Angle: inlining boundaries and callee-multiset census. Base: origin/main a418dd3 (1027 normalized / 276 raw).

| Build | Bytes | ratio | '-' / '+' slots | calls | normalized / raw | losses |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| base a418dd3 | 2,136 | 0.920 | 19 / 21 | 17/17 | 1027 / 276 | - |
| quote_sums helper (this branch) | 2,112 | 0.982 | 5 / 4 | 17/17 | 1027 / 276 | none |

unstripped sha256 12fa4f605f4c0696f2728662bb023d6004dccba50536d15eae5eb7fa3c8cf44f

## Census

* The original and the candidate make the same 17 direct calls in the same order to the same callees (original
  targets mapped to windows through score.json; every target window is normalized-matched and is the same
  symbol): `__multi3`, `__udivti3` (x2), `expect_failed`, `add3` (x2), `pre_fee_amount`, `gross_up_quote_error`,
  `PumpError::name` / `Display::fmt` (x2), `unwrap_failed`, `From<AnchorError>` (x2), `unwrap_failed`. No helper is
  missing or extra.
* `protocol_fee_split` is LLVM-inlined in both. In this rustc its MIR cost is between 140 and 200, above the hint
  threshold 100, and `#[inline(always)]` does not bypass the cost, so it is never MIR-inlined (4 call sites).
  Forcing MIR inlining (diagnostic `-Zinline-mir-hint-threshold=200`) gives 0.736, which is much further from the
  original. Writing the split by hand at both sites gives 19 calls, because the per-site `#[track_caller]` Locations
  stop the panic merge. So the original shares one LLVM-inlined split body.
* The 371/375 `ok_or_else` closures are LLVM-inlined. A closure, a plain fn item, an `#[inline(always)]` fn item, or
  inline `error!` all give the same IR.

## Mechanism of the improvement

Both `add3` calls (the first sum and the optional post sum) move into one helper,
`quote_sums(..) -> Result<(u64,u64)>`, defined on the old second line so that no line changes. LLVM inlines the
helper. Its two `?` exits join in one phi (both add3 error payloads), and v3 then propagates that phi to the shared
error tail. This changes the late CFG enough that the sret pointer is spilled at entry and reloaded into r3 at each
tail, as in the original. The r6 split and the duplicated pre_fee Err block are gone. Plain and
`#[inline(always)]` builds are byte-identical.

Residual (-5/+4, 8 B short): the original tests the first add3 Result as `jeq r1,2,+1; ja <err>`. That is a
separate Err MBB, where we have one direct `jne`. Everything else, including the sret allocation, matches.

## Trials

Ledger keys `0x80df8-main-a418dd3-<mech>-v1`, lane w7r1-v3buycosts-inline. See SUMMARY.json for the full list.
