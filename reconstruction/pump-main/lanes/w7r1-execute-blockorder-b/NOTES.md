# Lane w7r1-execute-blockorder (instance b), wave 7 round 1

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Angle: basic-block order and branch sense.

A second agent was already running this lane in the shared `w7r1-execute-blockorder` worktree,
so this instance works in its own worktree/branch/OUT with a `-b` suffix
(`swarm/w7r1-execute-blockorder-b`, `~/.cache/pumpfun-reconstruction/lanes/w7r1-execute-blockorder-b`).
Ledger rows use lane `w7r1-execute-blockorder-b`, keys `0x1e7c0-main-2b85821-*`.

Base: origin/main 2b85821 (1027/1035 normalized, 276 raw); rebased on 7e26cbf (raw 293, link order) with 0 losses, target 0.96854 at 15,584 B (+8 B).

## Results

| Build | Bytes | Ratio | slots_diff | Official | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- |
| main 2b85821 | 15,584 | 0.96854 | | 1027 / 276 | ec660de7 |
| **e1** | **15,576 (= orig)** | **0.98332** | 43 | 1027 / 276, 0 losses, 0 raw losses | 651e83a1 |
| e1 rebased on 7e26cbf | 15,576 | 0.98332 | 43 | 1027 / 293, 0 losses, 0 raw losses | ac434e5a |

## Mechanism (e1): fee as an `if .. else` expression

The only +8 B residual was the `validate_metadata(..)?` test in execute: the original has
`jne r9,2,<err>` falling through into the Ok path, ours had `jeq r9,2,+1; ja <err>`.
SBF's `analyzeBranch` cannot handle conditional branches, so branch sense is fixed at ISel:
SelectionDAG inverts `br (icmp eq tag,2), ok, err` to `jne err` only when `ok` is the IR-next
block. In our IR the inlined `validate_metadata.exit` block was followed by the creator-fee check
blocks (bb47..bb54): with `let mut fee=0; if cond {..; fee=x;}` the `&&` switch references the
join block first (MIR `[0: join, otherwise: ..]`), so rustc creates the join LLVM block (which
later absorbs depth, init_curve and the validate_metadata call) before the fee-check blocks.
IR oracle: flipping only that branch to `icmp ne`/err-first gives 0.98332 at 1,859 insns.

Spelling: `let fee=if matches!(..) && creator_fee_bps.0>0 { require!..; require!..; creator_fee_bps.0 } else {0};`
The join is now first referenced from the then/else ends, so it is created after the fee-check
blocks; the validate call block sits after them and its Ok successor is IR-next at ISel. Result is
byte-identical to the IR-oracle edit (0.98332, exact original size 15,576 B). Line count and every
`line!()` immediate are unchanged (lines 772/779/780 edited in place). Behaviour is identical.

(The same spelling was rejected on the much older base 630a074 (`g8`, 0.82359 < mut form), before
the later RA-affecting changes; on current main it is the winner.)

## Remaining residuals (43 slots)

1. `mov64 r7,0` / `mov64 r2,0` order swapped at two sites (0x1ec50, 0x20ad0): scheduling.
2. init_curve store block: original stores creator through r4 (`mov r4,r7; add r4,8` after the
   quote_mint memcmp) after `[r7+0x68]`; ours computes it in r2, stores creator first, and loads
   `[r10-0x718]` (r2) late.

## Ledger

`98bd0661` (IR oracle ne), `4ee6327f` (e1), `c25ff263` (e2: explicit match on validate_metadata,
byte-identical).

## Later findings (after e1)

Concurrent lanes combined e1 with "creator store after token_total_supply" (PR #2293, 0.98763). Analysis on that combo:

- **mov r7,0 / mov r2,0 swaps = phi order in bb112** (validate_quote_mint Ok join). With the IR oracle, putting
  `_84.sroa.31` (quote_mint word 0, ptr) before the source-tag phis gives 0.98763 -> 0.98870.
- **Root cause (opt-21 SROA on the captured pre-SROA module reproduces it):** mem2reg inserts phis at the block
  front in alloca-processing order, and JumpThreading clones them in reverse. The `Pubkey::default()` memset over
  `_84[16,48)` in BOTH Sol early returns delays promotion of the ptr-typed `[16,24)` slice to after
  sroa.47/51. If both memsets become `store ptr null` plus a 24-byte memset, or a memcpy from a zeroed local, the
  order comes out as wanted. With only one replaced, nothing changes.
- I found no source spelling yet: `system_program::ID` gives identical output (still memset); `pubkey!` is much worse;
  a shared `let sol` local used only in the returns is propagated (identical); used in the `==` compare too, it stays
  a stack local and moves the whole frame by 0x20 (0.553).
- The creator ptr r2 vs r4 plus the early `[r10-0x718]` reload is not a block-order residual: an exhaustive
  single-block move scan (28,730 llc runs) and an 1,800-step IR hill climb on combo+phi fix found nothing better.

## Tools (lane OUT, not committed)

`scripts/trial.sh` (copy crate, edit, IR capture build, score, metric), `ir.py` (llc oracle), `blockscan.py`
(exhaustive block-move scan), `irsearch.py` (hill climb, from w6r1-execute-ir), `pm/hyp.py` (opt-21 SROA hypothesis tests).
