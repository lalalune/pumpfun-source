# w12a10-cto-optoracle: LLVM pass-level oracle for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base: main 20a1ae9c0 (0.43919 / 3,352 slots),
re-checked on main b5975fa67 (#2749, 0.45147 / 3,308). Analysis lane: this notes PR changes no program
source.

## Retained diagnostic

`tools/bfi.py INPUT --opt /path/to/debug-opt` snapshots caller-supplied LLVM IR
or bitcode and reports the selected function's pre-inliner block frequencies.
It writes only to a temporary directory and fails if a selected call has no
frequency diagnostic. The executable must support this project's SBF pipeline.
The default function pattern selects `admin_cto::validate`; `--function` can select
another single definition. These frequencies describe the supplied candidate,
not the unknown original source.

During review, the retained diagnostic reproduced all eleven values in the table
below using the lane's cached `ir-main/noopt.bc`. The input and compiler hashes
are recorded with the review output. This did not rerun a source build or all
historical scans. The `results/` tables below are reported experiment records;
they bound those searches, not every possible compiler configuration.
Private capture, module-rewriting, sweep and knockout runners are omitted.

## Pass map (results/*.tsv)

1. **The tested codegen knobs did not fix the divergence.** I ran 66 llc variants on the exact post-opt IR,
   covering MBP (disable, ext-tsp, misfetch/jump cost, triangle, exit bias, static-likely-prob),
   branch folding and tail merging, tail duplication (placement thresholds, size, early taildup),
   machine sink (disable, split, bfi, avoid-spills), CodeGenPrepare (disable, branch opts,
   select2branch, freq-ratio-to-skip-merge), the pre-RA schedulers, misched and post-RA, greedy
   options and regalloc=basic, coalescing, and stack coloring and slot sharing. The best result is
   +0.00013 (`-disable-tail-duplicate`, which changes the size). Every other variant is equal or
   worse, and `-no-stack-coloring` drops to 0.172. With identical IR, the SDK llc defaults were the best match among those tested variants.
2. **Global opt knobs do not help.** I tried JumpThreading thresholds (dup 0/3/12, phi 1/20,
   implication 0), SimplifyCFG hoist and sink, phi and two-entry folding, GVN PRE and load PRE,
   ConstraintElimination, InstCombine code sinking, DSE store merging, and the inliner settings
   (threshold 300, cold-callsite threshold 0/100, cold-callsite-rel-freq 10). None of them improves
   on the base.
3. **The divergence is already present when execute's own passes start.** I knocked out each of the
   63 post-inline pass instances in turn. The best gain is +0.0003 (the second
   CorrelatedValuePropagation) and +0.0002 (the 9th SimplifyCFG). Removing the first JumpThreading
   (-0.019), GVN (-0.013), the first SROA (-0.014), EarlyCSE (-0.10) or MemCpyOpt (-0.21) makes the
   result worse. The second JumpThreading changes nothing. So none of execute's own JumpThreading,
   SimplifyCFG, GVN, SROA, InstCombine or LICM runs creates a divergence that the original lacks.
   These measurements direct further investigation toward three places: rustc's MIR-to-IR for execute, the bodies of `validate`,
   `wallet` and `sweep` as optimized before they are inlined, and the inlining decisions.
   Execute's post-inline passes (print-changed, 28 changing passes): the inliner gives 291 blocks and
   194 allocas, JumpThreading threads validate's Err exits to execute's Err return (291 to 284
   blocks), MemCpyOpt drops 53 calls, and the InstCombine after DSE deletes 47 dead allocas (193 to
   146).
4. **Callees before inlining** (print-changed): validate has its own JumpThreading (48 to 46 blocks),
   MemCpyOpt, and an InstCombine that takes it from 68 to 37 allocas. wallet has its own
   JumpThreading (62 to 60). **sweep has no JumpThreading change.** ArgumentPromotion changes sweep,
   and SimplifyCFG takes it from 96 to 93 blocks. The sweep's Ok/Err threading that earlier lanes saw
   therefore happens after inlining (see 3: not a pass-tuning fix).
5. **Inliner: an observed candidate/original call-pattern divergence (to_string at lines 307 and 312).**
   - Call-target histogram: the original has 7 `to_string` and 8 `<PumpError as Display>::fmt` calls,
     ours has 5 and 10. Ours inlines `to_string` at error sites 307 and 312. Those two inlined bodies
     are also the 2 extra lddw relocations (String `fmt::Write` vtable) behind the extra `.rel.dyn`
     entries.
   - Rule (inline remarks): to_string costs 130. It is inlined at threshold 325, but at a cold call
     site, where BFI is below 2% of validate's entry, the threshold is 45.
   - `bfi.py` on main gives:

| line | 284 | 289 | 296 | 298 | 306 | **307** | **312** | **326** | 330 | 334 | 338 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| freq in ours | .625 | .117 | .094 | .023 | .059 | **.0220** | **.0223** | **.0118** | .0035 | .0013 | .0011 |
| ours | in | in | in | in | in | in | in | call | call | call | call |
| original | in | in | in | in | in | **call** | **call** | **in** | call | call | call |

   - Under the hypothesis that the same inliner rule explains the original, a useful candidate
     target is frequencies below 0.02 for 307/312 and at least 0.02 for 326. The original IR and
     its branch-frequency metadata are unavailable; this is a search heuristic, not a recovered
     original execution probability. To inspect a restructuring: run `tools/bfi.py` on the candidate's `no-opt.bc` with an explicit `--opt` before scoring it. The
     original's skeleton fits this. It tests the fee tag once per target arm, at 0x0af0 in the
     holder arm and at 0x0e20 in the non-holder arm.
   - A noinline-only IR what-if (`noinl.py` at 307 and 312) gives 0.40918 at 26,960 B, 440 B short.
     The original has the same size as ours while outlining two more to_string calls, so its validate
     region carries about 440 B of structure that ours lacks. The inlining set will only come right
     together with that structure. A source-level gate that merely makes 307/312 cold, as tried by
     x1-cto-tostring-cold-307-312, loses ratio.

## Ledger

Approach `pass-oracle`, keys `0x22a10-w12-20a1ae9-optoracle-*`.
