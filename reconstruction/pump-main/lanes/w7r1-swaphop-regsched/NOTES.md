# w7r1-swaphop-regsched: 0x5b3b0 multi_hop_curve::swap_hop (regalloc / scheduling oracles)

Base: origin/main 7e26cbf (1027 normalized / 293 raw); swap_hop ratio 0.7332, 18,544 B (orig 18,584), calls 107/107.
Analysis-only so far: no source change committed.

## Oracles (tools/)
- `capir.py` scratch build with `--emit=llvm-ir` (+ optional extra rustc flags, scratch only).
- `extract.py` + `orc.py`: swap_hop body kept, other defines turned into declares, llc. Reproduces the
  fastbuild swap_hop bytes exactly (ref_equal), ~0.2 s per trial.
- `popt.py`: pre-opt IR (`-Cno-prepopulate-passes`) -> SDK `opt -passes=default<O3>` -> extract -> llc.
  Reproduces swap_hop exactly (18,544 B, 0.7332), ~8 s per trial. This tests hypotheses at the level of
  rustc's codegen output, much closer to the source than post-opt IR.
- `odiff.py` (diff vs original with callee names), `symb.py` (abstract interpreter: symbolic value of each
  register / frame slot, e.g. `L(a,24)`), `callmap.py` (original call targets -> names).

## Results
| trial | change | bytes | ratio | opregs | diff insns |
|---|---|---:|---:|---:|---:|
| base | main 7e26cbf | 18,544 | 0.7332 | 0.7796 | 791 |
| sweep hs1 | 712 single within-block hoist/sink | - | <= 0.7332 | | |
| sweep b1 | 66 icmp swap / br invert / add commute | - | best 0.7338 | | |
| fresh_global | fresh `a.global` load in bb60 (post-opt IR) | 18,552 | 0.7309 | | 798 |
| block moves | memcmp/complete_fill after transfer_input | 18,528-18,536 | 0.702-0.703 | | 958 |
| **p-a_noalias** | pre-opt: drop `noalias` on swap_hop param `a` | **18,600** | **0.8304** | **0.9244** | **556** |
| p-h_noalias | drop noalias on `h` | 18,688 | 0.6379 | | |
| p-ah_noalias | both | 18,784 | 0.6310 | | |

## Key finding
The original reloads `a`'s fields after calls: `symb.py` counts loads from `a` at offsets
0/8/24/48/56/64/72 as 7/4/2/2/1/2/2 in the original against 3/1/1/2/1/1/1 in ours. For example, the
original reloads `[a+8]` (fee_config) at get_fees and `[a+0]` (global) in the over-reserves block, which
also makes CodeGenPrepare fold the user load to `[a+0x18]` there. LLVM does that only if it cannot treat
`a`'s memory as invariant. The pre-opt oracle confirms it: taking `noalias` off `a` alone lifts swap_hop
from 0.7332 to 0.8304 (opregs 0.924). Most of the remaining "regalloc residual" follows from this one
IR property. Within-block instruction order and operand commutation are not levers.

## Open question / next
Find the ordinary-Rust signature or access path that gives `a` no `noalias` while `h` keeps it. For
reference, this toolchain gives `&T` (T: !Freeze) and `&mut T` (T: !Unpin) only `noundef nonnull align`,
with no dereferenceable. Check those attribute sets in the pre-opt oracle first, then the variants of how
execute passes `ctx.accounts`. A whole-crate `-Zmutable-noalias=no` is not it (0.5537, and it is a build flag).

Ledger: fc33de3c, 5b56a638, 256434be, dfaf484b, 06ac582f, 7b49c46a, 8d6b43fc, e63f48a2.
