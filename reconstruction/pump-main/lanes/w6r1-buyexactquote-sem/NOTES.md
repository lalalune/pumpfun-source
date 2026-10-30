# Lane w6r1-buyexactquote-sem (wave 6, round 1)

Target `0x1489f8` `trade::buy_exact_quote` (v3), original 7856 B. Base origin/main 099b0dd30 (1027 normalized / 276 raw):
7768 B, ratio 0.66033 (llc-oracle masked 0.8928), 66/66 calls.

**Best (head of PR #2170): ratio 0.85100, 7872 B, masked 0.9675, 66/66 calls; official 1027 / 276, no gains or losses
(also re-checked merged onto origin/main 6edd839ea: 1027 / 276, no losses vs that main, target 0.851).**

Approach: assembly-first semantic reconstruction. Lane-local tools (`~/.cache/pumpfun-reconstruction/lanes/w6r1-buyexactquote-sem/scripts`):
`calls.py` (listing with callees named; original callees named through the score windows), `cfg.py` (block summary with
callees, Source lines and successors), `blocks.py` (block matching orig vs candidate; `DIFF=1` prints per-block masked diffs),
`ltscan.py` (llc oracle: drop the lifetime.end of every block made only of lifetime.end + br, one at a time),
`phiscan.py` (swap every adjacent phi pair), `batch.py`/`trial.py` (2 parallel trial builds through the slot locks), and
`rec.py` (records a trial in the ledger). The w4 lane's trial/ir/hc scripts are reused (the capture hook now wraps
`fastbuild.run_compiler`).

## What the original says

Callee multisets already agree. The original lays out the whitelist split as
`memcmp -> [non-whitelist: net_quote_for_budget, tokens_for_quote(net), try_from] -> [891 err -> EXIT] -> [whitelist: tokens_for_quote(available)] -> merge -> tokens>real`.
The base placed the 891 error right after net_quote_for_budget and the whitelist arm before the non-whitelist
tokens_for_quote. The original's merge block moves the fee values as one group, which suggests that the
non-whitelist fees come back as one `TradeFees` value and not as four scalars.

## Mechanisms that landed

1. **b04**: carry the fees as a `TradeFees` value through the whitelist split, with the struct first in the tuple:
   `let (net_fees,tokens,net)=if wl{..(fees,tokens,available)}else{let (net,net_fees)=net_quote_for_budget(..)?;..(net_fees,tokens,net)}`.
   The noncross arm reads `net_fees.protocol_fee`/`creator_fee` and returns `net_fees`. Result: 0.66033 -> 0.84304 (7864 B), masked 0.8928 -> 0.9617.
   The order of the tuple fields matters. Orders with net_fees before net give 0.843; `(tokens,net,net_fees)`,
   `(net,tokens,net_fees)` and `(net,net_fees,tokens)` give 0.688/0.688/0.729.
2. **nw02**: `#[inline]` instead of `#[inline(always)]` on `buy_exact_quote_body`: 0.84409. A plain fn body gives the same result as `#[inline]`.
3. **r02**: with (1) in place, the x04 workaround (`let (is_sol,quote_fee);(is_sol,quote_fee)=check_quote(a)?;` plus
   `require_neq!(available,0)`) no longer helps. The plain spelling `let (is_sol,quote_fee)=check_quote(a)?;` +
   `require_gt!(available,0,..)` gives **0.85100**, masked 0.9675. Keeping only one half of x04 is worse: 0.7694 or 0.8447.

None of these changes runtime behaviour: the same values flow through a struct, and `require_gt!(x,0)` and
`require_neq!(x,0)` behave the same for u64 (same error code, same logged values).

## Residuals (r02)

* The main remaining factor is a global r6/r9 rotation (orig: ctx r6, partial_fill r9, error payload r6; ours: the reverse).
  Swapping r6<->r9 in our listing alone gives 0.9056.
* llc oracle (`ltscan.py`): deleting the lifetime.end in the `?` error-only block of `net_quote_for_budget` (bb136 on r02, bb137 on b04)
  gives **0.9276 / masked 0.978** and fixes the rotation. Doing the same for `v3_trade_fees(a,available)` gives 0.915. Deleting it in the other
  lifetime-only error blocks makes things worse. In the original, the error edges of these two calls go straight to EXIT with the payload
  loaded before the branch (`jeq r1,0,+1; ja EXIT`). The sibling IR lane found the same effect for quote_fee's error-join lifetime.end (0.9071).
  These are probably the same register-allocation flip.
* Why the source cannot easily drop that marker: rustc 1.79 MIR-inlines `Try::branch`, and JumpThreading duplicates the
  join's `StorageDead(result)` into both arms. Every `?` therefore gets an error block made only of lifetime.end. The marker disappears only when the
  result local loses its markers altogether (CopyProp head, s01/s02/s06), and the inliner then adds markers that span the whole body,
  which costs more (about 0.70).
* Smaller residuals: the prologue sret lea for prepare_bonding_curve (late in ours), the 881 unwrap_failed ZST pointer (-0x68 vs -0x90),
  the check_quote result copy order, the v3_pool_before error edge, and `fees` in the formatter stack-colouring group instead of the 0x160 group
  (frameoracle; orig fees overlaps the cross-arm `post`).

## Trials (ledger keys `0x1489f8-main-099b0dd-*-v1`)

| trial | mechanism | bytes | ratio | masked | result |
| --- | --- | ---: | ---: | ---: | --- |
| base | main 099b0dd | 7768 | 0.6603 | 0.8928 | |
| b01 | TradeFees carried, tuple `(tokens,net,net_fees)` | 7888 | 0.6876 | 0.8344 | top layout orig-like |
| b02 | b01 + destructure in noncross | | = b01 | | |
| **b04** | TradeFees carried, tuple `(net_fees,tokens,net)` | 7864 | 0.8430 | 0.9617 | kept |
| b05, w_201 | other tuple orders | | 0.688 / 0.729 | | |
| w_102, w_021 | other tuple orders | | = b04 | | |
| o_* (12 perms) | outer `(amount,quote,fees,post,costs)` orders | 7856-7864 | 0.59-0.843 | | none better |
| v05 | `mut` on split bindings | | = b04 | | |
| v06, v07 | noncross costs/tokens via if-expression | 7872 | 0.6453 | 0.9213 | |
| t02/t03/t04/t06/t09 | cross tuple order, match arm order, `&` operand order, costs destructure, inline tokens | | = b04 | | |
| t10 | net_quote via match/return | 7760 | 0.7569 | 0.8932 | |
| s01/s02/s06/s07 | named result local (`quoted?`, `fees?`) to drop the error-only marker | 7864 | 0.70 | 0.93 | markers lost entirely |
| s03/s05 | named result + match | | 0.63 / 0.75 | | |
| u01 | noncross arm as tail `match ..?{..}` | | = b04 | | |
| m01/m02 | `.map_err(core::convert::identity)?` | | = b04 | | |
| d01/d02 | deferred-init destructure of the call results | | = nw02 | | |
| h01 | whitelist split as nested `#[inline(always)] fn split` | 7864 | 0.8420 | 0.9491 | rotation fixed, spills worse |
| h02/h03 | same helper `#[inline]`/plain | 7312 | | | not inlined, 61 calls, loses closures |
| nw01 | no wrapper | 7864 | 0.7349 | 0.9428 | |
| **nw02** | `#[inline]` body | 7864 | 0.8441 | 0.9627 | kept |
| z01/z02 | line swap / named `whitelisted` bool | | = / 0.6415 | | |
| r01/r04/r05 | half-reverts of x04, inline(always) | 7872-7888 | 0.769 / 0.845 / 0.850 | | |
| **r02** | plain check_quote + require_gt 891 | 7872 | **0.8510** | **0.9675** | kept |
| r06 | plain fn body | | = r02 | | |
| p01/p02 | outer tuple orders on r02 | 7864 | 0.820 / 0.599 | | |
