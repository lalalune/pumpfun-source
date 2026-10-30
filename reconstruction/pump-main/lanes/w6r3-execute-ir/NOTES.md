# w6r3-execute-ir: 0x72810 `sweep::execute` (IR-oracle loop)

Assigned base: origin/main 6484b28 (target 0.88669, 7880 B). The work started from PR #2307's head
(w7r1-sweep-anchor: 0.99687, 7832 B, slots_diff 30). Lane scripts and outputs are in
`~/.cache/pumpfun-reconstruction/lanes/w6r3-execute-ir/` (`scripts/t.sh`, `oracle.py`, `irlib.py`).

## 1. IR oracle: the residual is IR block order only

When the SDK `llc` runs on the extracted `sweep::execute` from the PR #2307 IR, it reproduces the
build (fullmask 4, ratio 0.99687). Then one block move is made with `irlib.move`: the N-arm chain
`bb28 .. bb83` (protocol-native recipient clone plus the Option diamonds) goes between admit1's test
block and `admit_quote_pair.exit` (admit2). The llc output is then **identical to the original
window (0 diff lines)**.

Control moves, none of which match:

| Move | Fullmask |
| --- | ---: |
| `bb83` chain between the admits | 2 |
| `bb35` chain between the admits | 2 |
| `bb28` chain before `bb31` | 4 |
| `bb82` chain between the admits | 120 |

So the required order is: admit1 test, N chain, admit2, then bb83 directly after admit2.
Why: BPF ISel inverts a `br` only when its true successor is the next IR block. The LLVM inliner
puts an inlined helper's blocks straight after the call block, so the `admit_quote_pair` helper
(which merges both results, keeping the join clone warm) can never let bb28 sit between its two
admits. Writing the admits inline gives the right order, but the join clone is cold
(0.5R + 0.25T < 2%).

## 2. Re-verifying the sibling match (PR #2309) on current main

w7r1-execute-sibling resolves this. Its creator-vault compare goes through a plain `keys_eq`
helper (vault branch 0.5 instead of 0.375 before inlining, so the join is warm), and both admits
are written inline. It was scored on 2b85821. This lane rebuilt its `sweep_fees.rs` on
origin/main fb25fce02:

| Build | Normalized | Raw | Losses |
| --- | ---: | ---: | --- |
| Control: fb25fce02 | 1030 | 295 | none |
| fb25fce02 + PR #2309 sweep_fees.rs | **1031** | **296** | **0 normalized, 0 raw** |

The PR #2309 build gains 0x72810 (normalized) and 0x65eb0 (raw). Target: ratio 1.0, 7832 B,
slots_diff 0, llc oracle fullmask 0. Unstripped sha256 prefix: 8b2fcd0caddd215a.

## Ledger
- `0x72810-main-6484b28+pr2307-mv-bb28-before-admit2-oracle-v1` (analyzed)
- `0x72810-main-fb25fce-pr2309-reverify-v1` (normalized-match, PR #2309's source)
