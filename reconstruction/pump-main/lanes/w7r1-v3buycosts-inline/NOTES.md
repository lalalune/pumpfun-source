# Lane w7r1-v3buycosts-inline: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Angle: inlining boundaries and callee-multiset census. Base: origin/main a418dd3 (1027 normalized / 276 raw).
**Outcome: the target reaches a normalized match through the same labeled-block source as PR #2272
(w7r1-v3buycosts-blockorder), found independently from this angle. This branch carries no source change, to avoid
a duplicate of #2272. It carries the census and the inlining analysis that explains why the labeled block works
and an inlined helper does not.**

| Build (a418dd3 base) | Bytes | ratio | '-' / '+' | calls | normalized / raw | losses |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| base | 2,136 | 0.920 | 19 / 21 | 17/17 | 1027 / 276 | - |
| `quote_sums` helper (plain or `#[inline(always)]`, nested or module-level), IIFE closure | 2,112 | 0.982 | 5 / 4 | 17/17 | 1027 / 276 | none |
| labeled block `'sums: {.. break 'sums Err(e) ..}; sums?` (= #2272) | **2,120** | **1.000** | **0 / 0** | 17/17 | **1028 / 276** | none |

Labeled-block official build: unstripped sha256 c19d507685e3cb5d86021bdf11b8cb11a5892b3c36a4147f617731ce2226d3ca
(gain 0x80df8, no normalized or raw losses vs a418dd3).

## Census

* The original and the candidate make the same 17 direct calls in the same order to the same callees. Original
  targets were mapped to windows through score.json; every target window is normalized-matched and is the same
  symbol: `__multi3`, `__udivti3` (x2), `expect_failed`, `add3` (x2), `pre_fee_amount`, `gross_up_quote_error`,
  `PumpError::name` / `Display::fmt` (x2), `unwrap_failed`, `From<AnchorError>` (x2), `unwrap_failed`. No helper is
  missing or extra, so the residual was never an outlining difference.
* `protocol_fee_split` is LLVM-inlined in both builds. Its MIR cost is between 140 and 200 (above the hint threshold
  of 100), and `#[inline(always)]` does not bypass cost in this rustc. Forcing MIR inlining with the diagnostic
  `-Zinline-mir-hint-threshold=200` gives 0.736. Writing the split by hand at both sites gives 19 calls, because the
  per-site `#[track_caller]` Locations stop the panic-call merge. So the original shares one LLVM-inlined split body.
* The 371/375 `ok_or_else` closures are LLVM-inlined. A closure, a plain fn item, an `#[inline(always)]` fn item, or
  inline `error!` all give the same IR. `add3`, `pre_fee_amount` and `gross_up_quote_error` are outlined calls in
  both builds.

## Why a helper gets 0.982 and the labeled block 1.000

1. Joining both `add3` error exits in one Result before a single `?` fixes the sret allocation. With that join the
   sret pointer is spilled at entry and reloaded into r3 at each tail; without it it stays in r6. Other waves read
   that r6 result as an MBFI tie.
2. With a helper (or an immediately-invoked closure), LLVM inlines the body and splices the callee's blocks directly
   after the call block. The add3#1 Result test then has its Ok block as the IR-order successor, so ISel emits
   `jne Err`. The original has `jeq Ok; ja Err`, which BPF cannot fold because analyzeBranch does not handle
   conditional branches.
3. IR oracle on the helper build: moving the line-371 error region (error block, to_string panic, closure exit) to
   just after the add3#1 call block gives 0 diff at 2,120 B. Base (no helper) already has that order, because rustc
   creates LLVM blocks in first-reference order.
4. A MIR-level join keeps rustc's block order. MIR-inlining the helper would do this, but the nested fn is never
   MIR-inlined and the module-level fn costs between 250 and 500. A labeled block gives the same join in ordinary
   Rust, which is the #2272 source. Err-first arms give a byte-identical result; `match post` instead of `if let`
   gives 0.974.

## Trials

Ledger keys `0x80df8-main-a418dd3-<mech>-v1`, lane w7r1-v3buycosts-inline (46 rows); see SUMMARY.json.
