# w7r1-buyexactquoteinh-sibling

Target `0x13f630` `buy_v2::buy_exact_quote_in_handler` (original 20,184 B). Angle: sibling transplant.

## Result (current head)

| metric | origin/main 6edd839 | this branch |
| --- | --- | --- |
| eq body bytes (orig 20184) | 20216 | 20184 |
| target_metric ratio | 0.99635 | 0.99959 |
| diff hunks (win.py) | 5 | 1 (`mov r7,2` schedule at orig 0x1430d0) |
| calls (orig 130/1) | 130/1 | 130/1 |
| official normalized / raw | 1027 / 276 | 1027 / 276 |
| gains / losses / raw losses | - | none / none / none |

The body is now emitted as `pump_recovered::pump_recovered::buy_exact_quote_in_v2` (program-fn position).

## Mechanism (transplanted from sibling buy_handler, PR #2225)

1. `#[inline(never)]` on the `buy_exact_quote_in_v2` `#[program]` fn and `#[inline(always)]` on
   `buy_exact_quote_in_handler`: the handler body is LLVM-inlined into the program fn, so its
   marker-less MIR locals (the CompleteEvent `emit_cpi!` temporaries, whose StorageLive/Dead GVN
   strips) get LLVM-inliner lifetime markers, and the handler's Result is returned without a retest.
2. Tail written inline (w6r1 e2 form): `emit!(ev);emit_cpi!(ev);drop(ev);` then the Complete-if and
   `prepare_bonding_curve(..)?;Ok(())` directly in the handler (no `complete_and_prepare` helper).

Each half alone does not help (e2 alone: 20184 B / 0.99432, CPI temp slots wrong; program form
alone: body identical to main).

## Trials (ledger lane w7r1-buyexactquoteinh-sibling)

| trial | mechanism | eq bytes / ratio | verdict |
| --- | --- | --- | --- |
| e2 | drop(ev) + inline Complete-if + prepare? | 20184 / 0.99432 | partial (CPI slots) |
| h1 | e2 + by-ref inline(always) emit_complete_cpi helper, `?` | 20216 / 0.98865 | slots fixed, Err retest |
| h2 | h1 with if-let-Err-return | 20424 / 0.795 | rejected |
| h3 | ProgramResult helper, caller map_err? | 20080 / 0.959 | rejected (drop order) |
| t1/t2 | tail complete_and_prepare / finish_buy(&mut ctx) | 20184 / 0.99188 | rejected |
| c1/c2 | Complete CPI in closures | outlined | rejected |
| s1/s7 | tail emit_and_complete(ctx,&ev,ts) incl. Trade CPI | 20200 / 0.9931 | partial |
| s2/s6 | s1 with TradeEvent by value | 20224 / 20200 frame shift | rejected |
| p1 | program-fn form + e2 | 20184 / 0.99959 | **best** |
| p3 | program-fn form + h1 | 20216 / 0.98865 | rejected |
| m1-m4 | shareholders `unwrap_or_else(Vec::new)` / match / `unwrap_or(vec![])` / if-let (on p1) | = p1 | byte-identical |
| v3,v4,v6,v7 | shareholders type annotation / block / `.map(Option::unwrap_or_default)?` / split `?` | = p1, or 0.61-0.79 | rejected |
| f1,f2 | TradeEvent `shareholders` field before `buyback_fee` / first | 20200 / 0.99513 | fixes mov r7,2 (no drop flag) but flips mayhem select + prepare sense |
| f3,f4 | `shareholders` field last / after quote_mint | = p1 | byte-identical |
| u1-u3 | buy_handler snapshot spelling (`let uva=..`, `let c=..` rebind) | = p1 | byte-identical |
| w1 | sell_v2 `is_native_quote(quote_mint)` helper | 20232 / 0.778 | rejected |
| w2 | ix_name `.to_string()` | = p1 | byte-identical |
| w3 | `is_sol` before shareholders | 20208 / 0.982 | rejected |

## Analysis of the last residual (mov r7,2 at orig 0x1430d0)

llc oracle on the p1 IR (`ir/p1/o0710`): the residual is purely the order of the three
`shareholders` Vec phis (`sroa.7` ptr=2, `sroa.0` cap=0, `sroa.10` len=0) in the merge after
`sharing_config_shareholders(..)?.unwrap_or_default()`. Any order with `sroa.0` first gives llc
distance 0 (full match). The phis come from mem2reg in the post-inline SROA run of the program fn
(reverse of promotion order). Sibling evidence: buy_handler has [0,7,10], sell_v2 (matched) [10,7,0],
eq [7,0,10], with the same pre-SROA access pattern, so the order is set by the other allocas SROA
processes around `shareholders.i` (LIFO worklist), not by the shareholders spelling. Spellings of
the Option/Vec default are canonicalized away by MIR. Lane w7r1-buyexactquoteinh-regsched found a
lever on top of this branch (PR #2269: handler takes `partial:&bool`, adding one removable alloca)
that gives the normalized match.
