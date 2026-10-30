# Lane w3-buyv3 (wave 3): `trade::buy` (buy_v3) at 0x147ba0, IR-oracle-first

Base: origin/main 665499915 (1022 normalized / 276 raw). buy_v3 on base: 3680 B against the original's 3672 B, ratio 0.87739.
Tools are in `~/.cache/pumpfun-reconstruction/lanes/w3-buyv3/tools/`: `oracle2.py` (block moves, then llc, then a diff against the original), `greedy.py` (parallel greedy hill climb over single block moves), `trial.sh` (pass `WORK=` to give each parallel build its own work dir).

## IR oracle results (llc on the slimmed main IR reproduces the build exactly: 445 insns, r0.8774)

| IR edit (cumulative) | insns | diff slots | ratio |
|---|---:|---:|---:|
| base | 445 | 79 | 0.8774 |
| move bb8 (umin) after bb7, bb59 (memcmp) after bb3.i, bb6 (crossing) after bb59 | 444 | 45 | 0.9167 |
| + move bb79 (v3_buy_costs Err edge) after bb86 (greedy search finds no other single-block gain) | 443 | 21 | 0.9628 |
| + load order in the v3_pool_before args: assoc amount, then curve.real_quote, then global.migration_fee | 443 | 17 | 0.9673 |
| + one i64 load of the v3_buy_costs result at +16 in the call block (Ok and Err paths share it) | 442 | 16 | 0.9661 |

The ratio dips slightly at the last row, but slot count is the stricter measure and it drops.

The last 16 slots are jump offsets plus two branch-direction tells. BPF cannot reverse a branch, so each tell records which block came next at ISel:
1. After memcmp, the original has `jne r0,0,+1; ja join`. That means the join (r0==0 target) followed the memcmp block's split tmp block in ISel MBB order, and MBP later put the crossing block after it.
2. After the `add(..)?` call, the original has `jeq r1,2,+1; ja err`. That means bb82 (Ok) was not the next ISel block. Moving bb81 after bb80 in IR does produce that branch, but MBP then relocates the v3_execute_buy chain (75 to 89 slots).

Adding an empty or lifetime.end join block after memcmp leaves the result unchanged; CGP or branch folding probably removes it.

Structural point: rustc emits MIR blocks in RPO, with LLVM blocks appended in first-reference order. Since bb59 (memcmp) precedes bb11 and bb12 in the CFG, plain RPO cannot place it after bb3.i (the BuyZeroAmount to_string chain, which comes from LLVM inlining). The original's IR order therefore likely comes from a different CFG shape or from LLVM-level inlining, not from a respelling of the same CFG.

## Source trials (all 0 losses, none improved)
| trial | mechanism | buy |
|---|---|---|
| t01 | `let curve_base=a.associated_base_bonding_curve.amount;` before v3_pool_before | byte-identical |
| t02 | exempt computed before the `real` read | 3688 r0.847 |
| t03 | v3_buy_costs via `match {Ok(v)=>v,Err(e)=>return Err(e)}` | identical metrics |
| t04 | `let total=add(..)?;` before require_gte! | 3544 r0.741 |
| t05 | clip as `match partial_fill{true=>..,false=>..}` | identical metrics |
| t06 | clip as `if partial_fill==false{amount}else{min}` | identical metrics |
| t07 | exempt as an inline `||` expression with no helper | 3728 r0.666 |

Ledger: analysis 87769c2d (`0x147ba0-main-665499915-ir-oracle-acg-load-hoist-v1`), plus one row per trial under `0x147ba0-main-665499915-*`.
