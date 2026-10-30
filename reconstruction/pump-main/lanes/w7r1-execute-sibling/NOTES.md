# w7r1-execute-sibling: 0x72810 `sweep::execute` (sibling-transplant lane)

Base: PR #2298 head d11716091 (w7r1-execute-regsched: `pay_owned` wrapper taking the accounts
struct, sweep 0.8867 -> 0.9495), itself on origin/main 2b85821 (1027 normalized / 276 raw).

| metric | main 2b85821 | #2298 head | r5 | m5 | **y3 (head)** |
|---|---|---|---|---|---|
| ratio (target_metric) | 0.88669 | 0.94951 | 0.99479 | 0.99687 | **1.0 (normalized match)** |
| bytes (orig 7832) | 7880 | 7856 | 7832 | 7832 | 7832 |
| slots_diff | - | - | 35 | 30 | **0** |
| calls (orig 37+2) | 37+2 | 37+2 | 37+2 | 37+2 | 37+2 |
| full-mask diff lines (regs+stack masked) | 64 | 50 | 8 | 4 | 0 |
| official normalized / raw | 1027 / 276 | 1027 / 276 | 1027 / 276 | 1027 / 276 | **1028** / 276 |
| gains / losses | - | none | none (raw 0xa868 kept) | none | gain 0x72810, no losses |
| unstripped sha256 | ec660de7.. | | 279944c5.. | d442f56c.. | 143055ebf8675d2cf390bff9b4b9df14f3812c72f84773e95dcd52e34610106d |

## Mechanism (two sibling transplants)

1. **Why the plain rent helper was never inlined.** LLVM 18 `InlineCostCallAnalyzer::updateThreshold`
   calls `DisallowAllBonuses()` on a cold call site, which also drops the LastCallToStaticBonus.
   So a sole-call local helper is inlined only if its call site is at least 2% of entry
   (w6r1-sweep-ir measured 0.01602). Replaying `opt -passes='cgscc(inline)'` on the
   `-print-before=inline -print-module-scope` dump reproduces the remark exactly
   (`scripts/wprobe.py` adds branch weights to one branch and reports the decisions). Making only
   the creator-path native test 50/50 inlines the rent helper (cost -14790) while Event::data,
   the event clone, from_iter and exchange_malloc stay out of line, as in the original.
2. **Native test as a sibling helper** `quote_is_native(curve:&BondingCurve)->bool` (verbatim from
   trade_v3.rs). Before the inliner runs, the creator-path native branch is a branch on a call
   result. The zero heuristic (memcmp==0 gets 0.375) does not apply, so the branch is 0.5. The
   inliner updates the caller's BFI incrementally, so the earlier inline of this helper does not
   bring the 0.375 back. The rent site goes to 0.02136 (warm), and the plain helper with the
   legacy_native_payments body (`Rent::get()?.minimum_balance(0)`) is CGSCC-inlined after its
   own simplification. That is the original rent region, payload slice and frame (frameoracle:
   every alloca at its original offset).
3. **Rent helper takes the accounts struct** `ensure_rent_exempt(a:&SweepFees,destination:&AccountInfo)`.
   With `system_program:&Program`, ArgumentPromotion turns the argument into the loaded info
   pointer. The load then happens at the call site, before Rent::get, and that swaps
   r6/r9 for the whole function (ratio 0.814). `&a.payer` escapes into transfer, so `a`
   cannot be promoted, and the system_program/payer loads stay at the transfer site
   (`ldxdw r2,[r9+0x30]; mov r3,r9`) as in the original. Taking only `a`, with the recipient
   read inside, is worse (0.8795).

4. **Dispatch cast width** (m5): `match creator as i32{1=>..,_=>..}` instead of `as u8`. With `as u8`,
   MIR GVN reuses the switch's `creator as u8` for the msg argument and for the event bucket (MatchBranchSimplification
   turns `if creator{1}else{0}` into the same cast). A `zext i8` therefore survives at entry, and the event block stores
   the shared value, which list-ilp schedules before amount/timestamp. IR oracle: a local `zext i1 %creator to i8`
   in the event block gives the original store order (`ldxdw r1,[r10-0x318]; stxb [r10-0x1b0],r1` after the
   timestamp store). With an i32 (or usize) dispatch cast, the u8 casts are separate values and the event zext
   is local. Shared bucket variables, `creator.into()`, `u8::from` and if/else consts in the msg were all neutral or worse.

5. **Normalized match (y3).** IR oracle on m5: moving the protocol-native clone chain (bb28..) in front of the
   inlined helper's admit2 block makes llc's output identical to the original. So the last residual was only IR block
   order. Writing both admits inline in the token arm (the buy_v2/sell_v2 sibling form) gives that order, but then the
   join's recipient clone is cold. Before inlining, its frequency is 0.5*R + 0.25*T = 0.01869, which is below 2%, and
   that gives 38 calls. The `opt cgscc(inline)` branch-weight probe found two branches that fix it: the creator-vault
   compare, and the shared native re-test. A 50/50 vault branch is enough. The source writes the `require_keys_eq!`
   expansion out on the same line 145, with the compare done by a plain `keys_eq(&Pubkey,&Pubkey)->bool`:
   `if !keys_eq(&a.recipient.key(),&expected){return Err(error!(ConstraintSeeds).with_pubkeys((a.recipient.key(),expected)));}`.
   This is the same quote_is_native mechanism applied to the vault branch. It is the same runtime code, with the
   same error, line and pubkeys. The join is then 0.02136 and its clone is inlined (39 calls). The event block is
   0.0145, so Event::data, the event clone, from_iter and exchange_malloc stay out of line. 0x72810 is
   normalized-equal, slots_diff 0. The official score is 1028/276 with no normalized or raw losses.

## Residuals at m5 (full-mask diff 4 lines)
- Only the admit branch polarity below (fixed in y3).

## Residuals at r5 (full-mask diff 8 lines)
- Admit branch polarity (+0xeb0, +0xf98): original `jeq r1,2,+1; ja err` then `jne r1,2,err`.
  The ledger has this as IR block order (w4-sweep s6a oracle).
- Event bucket byte (+0x1910): the original reloads the spilled `creator` (`ldxdw r1,[r10-0x318]; stxb [r10-0x1b0],r1`).
  Ours keeps a 0/1 value in r0 and stores it earlier.

## Ledger ids
8f8425ae (plain rent cost analysis), 9aa75942 (t2), 9b602cd5 (t3), b47ae727 (pay_owned verbatim),
9a56e1e6 (r2), 426cb6e7 (r3/r4), 6206fdb5 (r6), 86cfdc23 (r5).

Further ledger ids: 99701dc5 (block-order oracle), 8a82fd8a (y3 normalized match), 32791cdc (event bucket spellings), 336911f4 (admits inline: join 0.01869 cold), deba5927 (if/else and arm orders), cc7b9aba (admit helper plain), c2185914 (m5).

Scripts (lane cache ~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-sibling/scripts): trial.sh,
bt.sh (pre-inline BFI listing), bpath.py (block freq + terminators), wprobe.py (branch-weight inline probe),
fmso.py (full-mask / stack-mask / no-mask diff vs original).
