# w4-buyhandler (wave 4)

Target: `0x13b9b8` `buy_v2::buy_handler`. Base: origin/main 630a074126 (1023 normalized /
277 raw), buy_handler 0.97682 / 15,512 B (original 15,480 B), llc-oracle masked diff 50.
Method: llc IR block-order oracle (w3-buyhandler's `llcor.py`/`sodist.py`, reproduced in this
lane's cache at `~/.cache/pumpfun-reconstruction/lanes/w4-buyhandler/scripts`).

## Headline finding: the inline-complete family is RAW-UNSAFE (new, rules out w3's top next idea)

w3's leading "next idea" was to inline the CompleteEvent emission + `prepare_bonding_curve`
into `buy_handler` (the `if let Err` / caller-tail-call forms) to fix the two structural
residuals: the Complete-`if` branch sense (orig `jeq r1,0; ja`) and the terminal `jne r8,2`.

Inlining the complete block does fix both and is measurably closer under score-like masking:

| variant | plain masked | STACK+REGS masked | bytes | raw |
| --- | --- | --- | --- | --- |
| base (complete_and_prepare helper) | 50 | 39 | 15,512 | 277 |
| i1 (complete inlined, no drop) | 56 | 37 | 15,488 | **276 (loss 0xa868)** |
| di1 (complete inlined + `drop(ev)` after emit_cpi) | 54 | 35 | **15,480** | **276 (loss 0xa868)** |

`di1` even reaches the exact original size (15,480) and the whole tail region matches. But
**both i1 and di1 lose raw window `0xa868`** (a 3-instruction thunk `ldxdw r1,[r1+0x0]; call;
exit`): raw 277 -> 276. Inlining the complete emission changes which drop/thunk LLVM emits at
the crate level, breaking that window's raw identity. Verified with `score.py` against the
base `score.json`. Therefore every member of the inline-complete family (i1, di1, the explicit
block-scope variants s1/s2, and by extension w3's `if let Err`/caller-tail-call forms, which
all inline complete) is unacceptable on this base. The `complete_and_prepare` inline(always)
helper that base already uses is what keeps `0xa868` matched.

The oracle confirms that, had inlining been raw-safe, scoping the CompleteEvent CPI temporaries
(`_461`/`inner_data`/`authority_info`) with lifetime markers would take di1 to masked diff 41
(`di1-lt.ll`), the best structure seen. Those markers come only from a real inlined-function
boundary around the Complete emission, which is exactly what reintroduces the raw-unsafe
thunk change.

## Add-chain overflow placement (raw-safe, but no source form)

Oracle: moving the `trade_fees` `?` Err block (`bb214`) after the second checked-add block
(`bb218`) takes base from 50 to **25** (`bb214>bb218`), and placing any block between add2 and
the cmp has the same effect (BranchFolder then glues the overflow blocks to the end). This is
the single biggest raw-safe lever left (~25 instructions). No source spelling reaches it:
- `add()`-helper bound total (g1): 0.865, loses the `uadd.with.overflow` closures.
- operand swap `checked_add(cf).checked_add(pf)` (g2): byte-identical to base.
- fee tuple with `?` inside the else arm / unwrapped tuple (a1, f2, f3, f4): 80 or identical.
- (w3) IIFE/nested-fn/inline helper add chains: closure-window loss or Result tag retests.
rustc emits the `trade_fees` Break block before add1 for any `?`/`match`/`if let` on the
Result, and an LLVM-inlined add-chain helper adds tag retests. Unsolved at source level.

## Other residuals (raw-safe, unchanged from w3)

- quote_mint / snapshot struct copy (insn ~1060): field-copy order differs in one 32-byte
  group; byte-identical to all respellings (w3).
- Two spill-slot swaps (-0x750/-0x790 -> -0x7d0/-0x7d8, insns 1375/1486): LLVM stack-coloring /
  extractvalue order; not source-controllable here.

## Rejected this lane (ledger `log_attempt.py search --target 0x13b9b8`)
fee-tuple-destructure-assign, fee-tuple-match-bool, require-gte-iife-closure, inline-complete
(i1/di1/s1/s2/c1/c2), drop-ev-early, tailcall-helper-prepare-forms (match/and/map/is_err add a
`drop_in_place<Result>` call, dist 339), add()-bound-total, operand-swap.

## Conclusion
No raw-safe source change beats base (= w3's merged optimum) on this base. The actionable new
result is that the inline-complete direction is a dead end (raw loss 0xa868), so the two
structural residuals (Complete-if sense, terminal jne) cannot be fixed by inlining. Analysis
only; PR not for merge.
