# Lane w7r1-execute-sibling (wave 7, round 1)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Angle: sibling transplant (copy spellings from matched sibling handlers / AMM / Fees / Mayhem).

Base: origin/main e3f3be8 (1027 normalized / 293 raw), target 0.96854 at 15,584 B.
Worktree note: the assigned worktree path was in use by another session, so this lane worked in
`worktrees/w7r1-execute-sibling-e7c0` (detached at e3f3be8), outputs under
`~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-sibling/e7c0/`, branch
`swarm/w7r1-execute-sibling-cv2` (PR #2341), because `swarm/w7r1-execute-sibling` carries that
session's sweep::execute PR #2309.

## Result

| Build | Bytes | Ratio | slots_diff | Official | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- |
| main e3f3be8 | 15,584 | 0.96854 | | 1027 / 293 | |
| s1 = fee if/else expr + creator after tts (= #2293) | 15,576 | 0.98763 | 42 | 1027 / 293, 0 losses | 67c0a5a7 |
| **L1 = s1 + legacy-create head store order** | **15,576** | **0.98870** | **43** | **1027 / 293, 0 losses, 0 raw losses** | **e5aaaaad** |

L1 equals the independently found `o2` of lane w7r1-execute-frame (#2297); here it came from the
sibling: the matched legacy `create` (lib.rs:335) initializes the curve as
`virtual_quote_reserves, initial_virtual_quote_reserves, virtual_token_reserves, ...`. Moving
those three stores to the head of `init_curve` makes both vqr stores precede the vtr global load,
as in the original (the vtr load now uses r3 like every other temp). The full legacy order
(L2) is worse (0.96745): since #2229 the creator/quote_mint memcpys keep their IR position, so
the tail order (creator after tts, quote_mint after cashback) must stay.

## Residual (after L1): two independent mechanisms

1. **mov r2,0 / mov r7,0 order in both Sol returns** = phi-copy order at the
   validate_quote_mint join (bb112). IR oracle: moving the quote-mint word-0 phi
   (`_84.sroa.31`, ptr) directly above the source-tag phi (`_84.sroa.47`) fixes both sites
   (L1 0.98870 -> 0.98978). `-print-changed` trace: after SROA the phis sit in order
   31,51,47,18,0 (mem2reg inserts at the block front, so .31 was promoted *last*, not in
   offset order 0,18,31,47,51); JumpThreading then re-creates the join phis in reverse
   (0,18,47,51,31). The original needs .31 promoted in offset order. No pointer phi/select
   uses _84+16 before SROA, so the deferral is not speculation; spellings of the Sol return
   (Pubkey::new_from_array, system_program::ID, const, helper, let), of the final Ok
   (`*mint.key`, `mint.key()`: 0.53), single-exit if/else (0.44), tuple orders and result
   bindings are all identical or much worse (also tried by sibling lanes).
2. **Creator pointer r2 instead of r4, name-ptr reload late.** In the original the reload of
   `&name` (`ldxdw r2,[r10-0x718]`) is the first instruction of the init_curve store block
   (target of both bb2 branches; bb1 falls into it), so r2 is busy across the block and the
   creator pointer gets r4; in ours greedy reloads `&name` right before the `name.len` load
   (local split) while `&symbol` is region-split (reloads at the pred ends). Exhaustive IR
   oracle scans on L1+phi: every legal single-instruction move in every block (6,271
   candidates, <=11 steps), every block move within +-12 (3,924), branch weights on the
   memcmp/reserves branches, splitting the None critical edge, stripping alias metadata in the
   block, moving the creator GEP or the len loads: nothing beats 0.98978. The residual is not
   an IR-order effect; it needs a different IR value structure that no tried spelling gives.

## Rejected spellings (this lane; ledger keys `0x1e7c0-main-2b85821-*`, `0x1e7c0-main-e3f3be8-*`)

Sol returns via new_from_array / system_program::ID (identical); validated binding then
destructure (identical); explicit match on validate result (0.874); final Ok via `*mint.key` /
`mint.key()` (0.534); `let mint_key=*mint.key` (identical); inner `(reserves,source)` order
(0.986: flips the Whitelisted-path copy order the wrong way, confirming tuple construction order
drives those phi copies); legacy `create_metadata` spelling for initialize_metadata (&String +
clone inside: 0.777, 122 calls); full legacy store order (0.967); single-exit Sol if/else
(0.440); init_curve returning Result (identical); quote_mint by reference (0.500).

## Tools

`~/.cache/.../e7c0/scripts/`: `ir.py`, `capmir.py`, `slim.py`, `ren.py`, `irsearch.py` (copied
from w6r1-execute-ir with lane paths), `exh.py`/`exh2.py` (exhaustive single-move scan),
`exhblk.py` (exhaustive block-move scan).

## Merge outcome (PR #2341)

Superseded on main by #2386 (80393778f, w6r3-execute-ir), which reached
create_v2::execute 0.99892 / slots_diff 4 at 15,576 B. Re-measured on latest
main merged into this branch with the PR's create_v2.rs hunks: 0.98870 /
slots_diff 43 at 15,576 B (no score change, 1032/347 both). The source changes
were therefore dropped; this lane's create_v2 notes are kept as
NOTES-create_v2.md / SUMMARY-create_v2.json (the lane's NOTES.md/SUMMARY.json
on main belong to the same-named sweep::execute session, #2309).
