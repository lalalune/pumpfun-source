# admin_cto validation-order hypothesis

The remaining window is `0x22a10 admin_cto::execute` (27,400 bytes). The original
Source-line immediates appear in this layout order:

```
289 298 306 296 326 312 307 330 338 334 410 719 648 660 284 556
```

The 20a1ae9 candidate and the later k4 candidate place the validation errors as:

```
298 289 330 296 326 306 312 307 338 410 334 719 648 660 284 556
```

These order observations agree with the retained structural and call-sequence
packets. The candidate also inlines `to_string` at 307/312, where the original
has calls. A useful source experiment is to change how the `holder` and `new`
Option tags reach the validation branches, then inspect pre-inliner block
frequencies before building. The retained
[frequency diagnostic](../w12a10-cto-optoracle/NOTES.md) provides that measurement.

The lane reported that changing tag tests in raw IR moved the first error blocks,
and that a source `holder.unwrap_or(false)` trial reproduced its IR oracle at
27,128 bytes / 0.44986. That trial changes the window size and is not admissible
against the exact-size main. The historical raw IR and full compiler receipts
are not retained here, so this review does not certify those experimental results.

Branch-probability heuristics and Option range metadata are hypotheses for the
observed order, not recovered probabilities of the original program. A future
candidate must preserve all existing raw/normalized matches under the official
scorer. No source or completion gain is claimed by this packet.

Private cache-dependent oracle runners and duplicate display helpers are omitted.

## Follow-up (lane-local builds, identity recipe; numbers are this lane's `target_metric.py` readings)

**Per-arm fee threading.** In the original, the holder arm reaches the fee_configurable test (334/338) without
passing the 330 cashback test; only the non-holder path tests 330. A raw-IR edit that gives validate's holder arm its own copy
of the fee switch and the quote_locked test raised k4 (b5975fa, 0.45147) to 0.48374 at 27,376 B.

The source form k06 reproduces this. validate's target `if` yields `(target, cashback)`: `(*holder_key, false)` in the holder
arm and `(t, st.cashback)` otherwise. The 330 check becomes `if cashback`. rustc's MIR JumpThreading then threads the
constant `false` past the fee and quote_locked switches. The result was 27,368 B / 0.48381 (unstripped sha prefix
57ac0e6d35b92979), the same size and ratio as w12b13's 298 hoist. With the validate fee check as `match fee`, it was
27,384 B / 0.48517.

Spelling the per-arm value as `let mut cashback=false` before the `if` and assigning it in the non-holder arm does not
thread, because the constant is outside MIR JT's backtrack window. That gave 27,328 B / 0.44338, identical to a raw-IR
oracle where LLVM alone sees the phi. The same mechanism landed independently in #2831 (w12a14-cto-hillclimb-2,
`let cashback=if holder{false}else{st.cashback}`).

**On main 7cafddc (#2831 + #2808, 0.48742 / 3,273 at 27,400 B).** Each remaining error-order lever measured below main:

| change | level | bytes | ratio |
| --- | --- | ---: | ---: |
| holder test as `trunc` (`unwrap_or(false)`, orig `and64 r8,1`) | raw IR | 27,192 | 0.45113 |
| `new` tag loads without `!range` (orig `and64 r1,1`) | raw IR | 27,432 | 0.47994 |
| sharing tree tests `holder` before `shared` | raw IR / source h22 | 27,336 | 0.48350 / 0.4841 |
| separate return block for the fee-OK path (334 before the OK path, as in the original) | raw IR | 27,440 | 0.43886 |
| 289 as `st.holder_reward&!holder` | raw IR | 27,040 | 0.45024 |
| `to_string` outlined at 307/312 (`noinline` call sites, as in the original) | raw IR | 26,960 | 0.43304 |
| validate returns `(target, cashback)` and execute uses it (h18) | source | 27,096 | 0.21754 |

The raw-IR oracle used here: `opt -O3` (SDK v1.44 rustlib) on the `-C save-temps` no-opt module, slimmed to the
`llvm-extract --recursive` closure of execute (w12a10's `mkslim4.py`), then llc. It reproduced main 7cafddc exactly
(27,400 B / 0.48742) and predicted source trials k01 and k19 exactly.
