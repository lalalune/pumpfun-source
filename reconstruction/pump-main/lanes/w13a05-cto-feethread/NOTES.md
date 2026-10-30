# w13a05-cto-feethread: fee-None per-arm threading in admin_cto::execute

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: the original sends each fee-None path straight into the sharing tree, per arm (orig 0x0e38, 0x10e8, 0x1508).
The fee-OK block then has a single predecessor, and error block 334 is laid out right after 338.
Bases: main 3912c47 (0.48772), then cb298d5 (0.49101), then 9eb6c00 (#2906, 0.49131).

## What the original does (orig offsets relative to 0x22a10)

- **Holder arm (0x0ab8).** Target = holder_key, then a fee-tag test.
  - None goes to 0x10e8, which tests `shared` and jumps to the holder&shared tree block (0x1128) or to the non-shared tree (0x18b0).
  - Some goes to ql (326), skips 330 and continues at the 334 test (0x1638). This part is already on main (#2831).
- **Non-holder arm.** After the 306/307/312 checks it computes cashback and then tests `shared` *before* the fee test (0x0dc0).
  - The shared sub-arm (0x0dc8) copies `st.creator` (the `[r10-0x38..]` pieces) into the target slot. This is the target override inside the arm.
  - The non-shared sub-arm (0x1490) copies `t` instead.
  - Each sub-arm has its own fee-tag test. None jumps straight to the shared/!holder tree block 0x1850 (`Some(new)`) or to 0x18f8 (the `creator != default` memcmp). `holder_reward` is known false there because 289 passed.
- **Fee-OK (0x1800)** re-tests `shared`, then holder.

## Source mechanism: found, but blocked by inlining

**f02b (validation inline in execute plus the override in the arm) reproduces this exactly.**
- Change: the `validate` fn is removed and its body is written inline at lines 283-338. The non-holder arm yields `if shared{st.creator}else{t}`, and the tree no longer assigns target.
- Result: rustc's MIR JumpThreading, now seeing the validation and the tree in one body, produces the original's three fee-tag tests. Their None edges go straight into the tree blocks, and errseq is `284 298 289 296 326 306 312 307 330 338 334 410`, so 334 sits right after 338.
- Blocker: execute drops to 11,192 B with 86 calls, because `wallet` and `sweep` are no longer inlined.

**Why they are no longer inlined (`tools/bficall.py`, pre-inliner BFI from the debug opt).**
- In main the wallet call site sits at 0.047 of entry and sweep at 0.035, just above the 2 % cold-callsite cut.
- With validation inline, the ~11 sequential 50/50 error branches drop them to 0.0025 and 0.0019.
- LLVM 18 `InlineCost::updateThreshold` disables *all* bonuses, including LastCallToStaticBonus, for a cold call site ("Do not apply bonuses for a cold callsite"). So wallet costs 3005 against a threshold of 45 and is not inlined. Remarks:
  `opt -O3 -pass-remarks-missed=inline` → `wallet not inlined into execute because too costly to inline (cost=3005, threshold=45)`.
- `#[inline(always)]` on wallet/sweep (f03) or on a tail fn (f08) does not help.
  - `always-inline` is a *module* pass that runs before the CGSCC inliner (`opt -O3 -print-pipeline-passes`), so the callee is inlined unoptimised.
  - Its own call sites are then judged cold in execute: 180 calls, 21 more `AccountInfo::clone` and 4 more `to_string` left as calls.
  - The raw-IR oracle with LLVM-only alwaysinline gives the same 19,000 B as the source trial, so the MIR inliner is not involved.
- Branch weights that make every validation error edge unlikely (`tools/errw.py`, raw-IR) restore 154 calls. But the frame shrinks to r4 spill `-0x860` (main `-0x8f8`, orig `-0x928`) and the ratio is 0.21. Inline validation therefore moves the frame *away* from the original.
- Conclusion: the original's call histogram (154+3) and larger frame argue for `validate` staying an LLVM-inlined fn. The per-arm fee-None threading then has to come from something other than MIR JumpThreading across validate and the tree, and I did not find that source shape.

## Rejected source shapes (main 3912c47, measured with the lane's capture build; scoring identical to measure.sh)

| trial | change | bytes | ratio |
| --- | --- | ---: | ---: |
| f01 | validate takes `shared`, non-holder arm `if shared{st.creator}else{t}` (same as w12a10 v9) | 27,440 | 0.24577 |
| f02a | validation inline in execute (override still in the tree) | 11,288 (86 calls) | 0.11424 |
| f02b | f02a + override in the arm: **exact per-arm fee-None threading** | 11,192 (86 calls) | 0.09744 |
| f03a/b | f02a/b + `#[inline(always)]` wallet and sweep | 19,136 / 19,000 (180 calls) | 0.160 / 0.162 |
| f04 | tree in validate through `&mut` out-params, override in the arm | 27,632 | 0.41342 |
| f05 | f04 with the override in the tree | 27,608 | 0.41361 |
| f06/f07 | validate returns `Result<(Pubkey,Option<Option<Pubkey>>,bool)>` (arm / tree override) | 27,944 / 27,920 (155 calls) | 0.30783 / 0.30559 |
| f08a/b | f02a/b with everything after the tree in an `#[inline(always)] fn post(&mut ctx, ..)` | 11,272 / 11,200 (86 calls) | 0.125 / 0.109 |

In f01, LLVM merges the shared and non-shared sub-arms (target phi) before a single fee-tag test, so nothing threads. In f04 to f07, SimplifyCFG folds the per-arm tree stores into or/select form and places `prepare_bonding_curve` right after the holder fee-None path, so 410 comes before 330.

## IR oracle: per-arm fee-None threading alone (post-opt IR + llc, `tools/thread_ir*.py`)

- `thread_ir.py` edits main's post-opt IR so each arm's fee-None edge enters its own copy of the tree test. `h` threads the holder arm, `n` the non-holder arm (`holder_reward` known false), `hn` both.
- `thread_ir2.py` reuses the existing tree blocks and adds phis instead of copying them.
- Every variant puts 334 right after 338, as in the original.

| base | h | n | hn | n (no dup) |
| --- | --- | --- | --- | --- |
| 3912c47 (0.48772) | 27,696 / 0.47401 | 27,816 / **0.48841** | 28,120 / 0.48182 | 27,512 / 0.48401 |
| cb298d5 (0.49101) | 27,688 / 0.45769 | 27,800 / 0.48736 | 28,104 / 0.45446 | |

So the threading is only about neutral as an isolated CFG feature, and it costs 300-700 B. The w13a01 recipe agrees: the remaining gap is mostly frame and registers.

## Fee spelling that does gain: `let Some(f)=fee else{return Ok(target)};`

In validate, the fee check `match fee{Some(f)=>{..}None=>{}}` becomes a let-else whose None branch returns `Ok(target)` early. This is the closest source form of "fee-None leaves on its own edge" that keeps validate a fn.
- On cb298d5 it measures 27,424 B / **0.51085** (main 0.49101). The frame grows 8 B (r4 spill `-0x900`; orig `-0x928`, main `-0x8f8`), and errseq is unchanged.
- On older bases this spelling measured negative (w10r1, w12a09). It pays now because of the newer frame.
- `match fee{None=>{}Some(f)=>..}` (None-first) is byte-identical to main on cb298d5.

Size work on 9eb6c00 (main 0.49131) is in the summary below.

Ledger keys: `0x22a10-w13-*-feethread-*`.
