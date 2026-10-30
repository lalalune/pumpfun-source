# w7r1-buyhandler-coords

Target: `0x13b9b8` `buy_v2::buy_handler` (original 15,480 B). Angle: coordinate archaeology.
Base: origin/main a7135a6 (1027 normalized / 276 raw; buy_handler 15,512 B, ratio 0.97998,
llc masked dist 80 in this lane's oracle).

No source change is proposed. This is an analysis-only result.

## 1. Every coordinate already matches

| Kind | Original | Ours (a7135a6) |
| --- | --- | --- |
| `Source{buy_v2.rs,line}` sites, all windows | 34 distinct lines across 19 windows | identical multiset and per-function grouping |
| buy_handler sites (byte slot: line) | 1000:345, 1248:354, 4408:356, 5136:369, 6584:494 | identical, except the 494 site sits at 6536 |
| buy_handler closure sites | 465, 469 (near 0x16bb8); 498, 500 (0xac2b8/0xac4c0) | identical lines; same near/far split |
| panic `Location` constants referenced from the window | one: len-84 path, line 2559, col 14 | identical |
| lddw rodata contents (39 refs) | — | identical apart from relocated pointers |
| error-code immediates and string literals | — | identical (coordinate-archaeology IMMEDIATES.json) |

The only coordinate-adjacent difference is the slot of the 494 site: 48 B early. That is the
checked-add block placement (below), not a line or column. Line numbers can't fix this window.

What the lines constrain (useful for every lane rewriting this region):
- `494 require_gte!(` / `498 .ok_or_else` / `500 .ok_or_else` is the rustfmt layout of the add
  chain *inside* the macro arguments (chain_width 60 forces the vertical chain). So the chain
  cannot be hoisted into a `let total` before the macro.
- `464-465 let quote = ..map_err` / `466 let gross` / `467-469 let quote_transfer_fee = gross
  .checked_sub(quote).ok_or_else(..)?` (rustfmt chain), so the fee region is exactly 470-493
  (24 lines). It contains no Source site and no closure with `error!`: no `require!`,
  `ok_or(error!)`, `unwrap`/`expect`/indexing panics there (any of those would leave a
  coordinate the original lacks).
- sell_v2's matched fee region is 342-363 (22 lines), between its quote statement (340-341)
  and `let output = quote` (364, closures 366/368). Buy has 2 more lines (e.g. the
  `let whitelisted` binding).

## 2. The residual is IR block order: the trade_fees `?` Err block

llc oracle on our own IR (`tools/ora.py`, `tools/edit_*.py`):

| IR edit on base | dist |
| --- | ---: |
| none | 80 |
| move tf Err block (bb215) after add2 (bb219) or after ovf1 (bb218) | **28** |
| move bb215 after cmp (bb223) | 155 |
| branch_weights on tf switch 1:1 / 2000:1 / 1:2000 / 12:20 | 142 / 245 / 80 / 80 |
| invert br sense: tf switch / add1 / add2 | 142 / 251 / 196 |
| drop lifetime.end in bb215 | 80 |
| hoist the payload load so bb215 is empty | 164 |

So it's neither branch probability nor lifetime markers, only block order. The 28 left are zero-movs
(fixed by the cf-first tuple, regsched B1), is_sol selects (regsched A1) and the shared tail.

Why spelling can't do it inside rustc: rustc codegens MIR blocks in reverse postorder and
creates each LLVM block lazily at first reference. The tf `?` switch creates its Ok target
(the add1 block) and then its Err target. add2 and ovf1 are created only when add1 is
codegenned, which RPO puts after the switch. So whenever the tf `?` switch dominates add1,
the Err block is created before add2. The original's order (Err after add2, before or after
ovf1) needs something else:
- the Err content lives in a block that LLVM creates or keeps later, such as a JumpThreading
  `.thread` block, which is inserted before the threaded block, or a forwarder that gets removed
  in favour of a later block;
- or the Err path reaches the shared return through a block created later (for example a
  drop-flag or shared-error block).
I could not find an ordinary spelling that does this (see trials). We have no `opt` binary,
so the oracle can't test LLVM-pass hypotheses directly.

## Trials (all 0 losses; ledger lane w7r1-buyhandler-coords)

| Trial | buy_handler | Note |
| --- | --- | --- |
| t01 cf-first tuple (sell_v2 form) | 15504 / 0.95968 | duplicate of regsched B1 |
| x1 `let Ok(..)=fees else{return fees.map(\|_\|())}` + map swap | 15648 / 0.81353 | +2 calls |
| x2 `.. else{return Err(fees.unwrap_err())}` | 15656 / 0.81279 | +2 calls |
| x3 x1 without swap | 15632 / 0.81239 | +2 calls |
| h1 plain helper `creator_first_trade_fees` + `?` in else | 15424 / 0.77886 | not inlined (280 B local fn) |
| h2 same helper, outer `?` | 15432 / 0.7887 | not inlined |
| k5 B1 + `.map_err(Error::from)?` | 15504 / 0.95652 | worse |
| k6 B1 with named `let fees=..; fees?` | 15504 / 0.81739 | own 40 B slot, frame +0x28 |

## Next ideas
- Get an `opt` matching platform-tools LLVM, or run single passes through rustc
  `-C llvm-args=-print-after=...` on a capture build. That would show which pass (JumpThreading,
  SimplifyCFG sink) could produce "Err after add2" from some MIR shape. Then search spellings
  for that MIR shape.
- Spellings where the tf error reaches the return through a shared block that is first
  referenced after the add chain. One example: an error that is stored and returned at a single
  exit, as a labeled block `let fees = 'f: { .. }`.
