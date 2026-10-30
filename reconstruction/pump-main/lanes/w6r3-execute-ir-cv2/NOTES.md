# Lane w6r3-execute-ir (create_v2::execute instance, `-cv2` worktree)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (15,576 B, 1,859 insns, 125 calls).
Approach: IR oracle (SDK `llc` on rustc's IR reproduces the fastbuild function exactly), then the Rust spelling.

A second agent was already using the `w6r3-execute-ir` worktree and OUT directory for `sweep::execute`,
so this instance works in `worktrees/w6r3-execute-ir-cv2`, branch `swarm/w6r3-execute-ir-cv2`,
OUT `~/.cache/pumpfun-reconstruction/lanes/w6r3-execute-ir-cv2`. Ledger lane: `w6r3-execute-ir-cv2`.

## Result

| Build | Bytes | Ratio | slots_diff | Official (vs main 255a0fd) | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- |
| origin/main 255a0fd | 15,576 | 0.98763 | 42 | 1031 / 337 | 94672169 |
| **this branch** | **15,576** | **0.99892** | **4** | 1031 / 337, 0 losses, 0 raw losses | c78c5ae9 |

(On the older base 6484b28 with the PR #2341 L1 source the same change went 0.98870 -> 0.99892, sha 4b6cf24c.)

## Mechanism

Residual before: the creator pointer was computed into r2 (original r4) and the name `String` pointer was
reloaded from `[r10-0x718]` right before `name.len()` instead of at the top of the store block.

- In the original, the `jeq`/`ja` of the reserves test both land on `ldxdw r2,[r10-0x718]`, the first
  instruction of the store block. That is a tail-merged reload: every predecessor of the store block reloaded
  the name pointer at its end, and BranchFolder merged the copies. Our IR had a critical edge
  (`bb2.i73 -> exit` for `None`, plus an empty `bb9.i` for `Some`, 3-pred exit phi), so greedy could not
  place the reload on that edge and spilled the name pointer to its use instead.
- IR oracle: replace that branch by `select(tag==0, ivqr, some)` in `bb2.i73` with a 2-pred exit phi.
  SBF lowers the select to a Select pseudo whose expansion has its own join block: llc then gives exactly the
  original store block (0.98870 -> 0.99892, 4 difflines left, ledger `65bd4777`).
- Why no select before: `unwrap_or` is MIR-inlined with the outer `let` as destination, so its `Some`/`None`
  arms jump straight to the outer join; no 2-entry join ever exists for SimplifyCFG to fold
  (`-print-changed` on init_curve). Spellings that keep the outer join tried and failed:
  `let r=..;r`, plain helper fn, `map_or`, `match` arm swap, `if let` (polarity only), assigning the `if`
  straight to a curve field. Computing `unwrap_or` before the `if` folds both levels into selects (much worse).
- Fix: do the two reserve stores inside each arm:
  `if quote_mint==sol {let r=global.initial_virtual_sol_reserves; bc.vqr=r; bc.ivqr=r;}
   else {let r=reserves.unwrap_or(ivqr); bc.vqr=r; bc.ivqr=r;}`.
  The `unwrap_or` arms now join in the block that does the stores, LLVM folds that 2-entry phi into the select,
  and the outer test stays a branch. Byte-identical to the IR oracle. Behaviour is unchanged (same values
  stored to the same fields). Line count and all `line!()` immediates are unchanged (3 lines replaced by 3).

## Remaining residual (4 slots)

The two `mov64 r7,0` / `mov64 r2,0` order swaps at the Sol returns of `validate_quote_mint` (window 0x490 and
0x2310). Known cause (w7r1 lanes): phi order at the validate join, from SROA promoting the ptr-typed quote word-0
slice of the inlined Result late because both Sol returns write the quote with a 32-byte memset.

## Ledger

`65bd4777` (IR oracle select), `a5276b7a` (L1 port), `1b57db61` `d4373406` `0bae9c2f` `d60d55a8` `4de2cf05`
`0a2d46fc` `ab0013e9` (rejected spellings), `818a9cac` (v12/v13 per-arm stores, 0.99892).

## Tools (lane OUT, not committed)

`scripts/ir.py` (llc oracle, from w7r1-execute-blockorder-b), `scripts/mir.py` (pre-greedy MIR oracle:
`llc -start-before=greedy` round-trips at 0.97741, faithful except outgoing stack-arg offsets),
`scripts/swapscan.py` / `movescan_mir.py` (vreg-number and MIR move scans), `scripts/trial.sh`, `scripts/rec.py`.
