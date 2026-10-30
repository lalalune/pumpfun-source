# Lane w7r1-execute-frame (wave 7, round 1)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Angle: stack-frame / slot oracle, then MIR block/local order.
Base: origin/main 2b85821 (1027/1035 normalized, 276 raw), target 0.96854 at 15,584 B.

## Frame audit

On main 2b85821 every `r10` offset in the candidate already equals the original: all stack-slot
tokens sit in equal diff runs. The frame is solved; the residuals are scheduling and block layout:

1. `jeq r9,2,+1; ja LBB92` after the inlined `validate_metadata` (+8 B) where the original has a single
   `jne r9,2,LBB92`.
2. the `init_curve` creator memcpy is scheduled first (through r2) where the original stores it after
   `token_total_supply` (through r4).
3. `mov r7,0` / `mov r2,0` swapped at the end of two `[-0x4c0..]` zeroing blocks.

## Results

| Build | Bytes | Ratio | slots_diff | Official | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- |
| main 2b85821 | 15,584 | 0.96854 | | 1027 / 276 | ec660de7 |
| c1 = `let fee=if .. {..} else {0}` | 15,576 | 0.98332 | 43 | 1027 / 276, 0 losses, 0 raw losses | 651e83a1 |
| s1 = c1 + creator stored after `token_total_supply` | 15,576 | 0.98763 | | 1027 / 276, 0 losses | (ir build) |
| **c2 = s1 + `virtual_quote_reserves`, `initial_virtual_quote_reserves`, `virtual_token_reserves` store order** | **15,576** | **0.98870** | 43 | 1027 / 276, 0 losses, 0 raw losses | 030d0d70 |

## Mechanism c1: the fee then-blocks must be created before the fee join

BPF's `analyzeBranch` cannot analyze conditional branches, so a conditional branch keeps the
polarity SelectionDAG gave it from the IR block order. In main the IR order was
`bb58 (fee join, init_curve) .. validate_metadata.exit, bb47 bb48 bb52 bb54 (fee require! blocks), bb116`,
so ISel emitted `jeq tag,2 -> bb116` + `ja err`, and block placement could not invert it. IR oracle:
moving `bb47..bb54` before `bb58` (or to the end) gives 0.98332 at 1,859 insns.

rustc creates LLVM blocks on first reference. With `let mut fee=0; if cond {..; fee=x}` the switch's
`0` target is the join, so the join is created before the then-block. With
`let fee=if cond {..; creator_fee_bps.0} else {0};` the `0` target is the `else` arm, the then-block is
codegened first (RPO), and the join is created after the fee checks, exactly the oracle order.
Behaviour is unchanged; no `line!()` site moves (the `else {0};` replaces the closing brace line).

## Mechanism s1/c2: init_curve store order

With the `&mut BondingCurve` SSA pointer (main #2229) the SelectionDAG keeps the creator memcpy where the
IR puts it, so the memcpy position now matters (IR-oracle scan over every position of the exit block:
best right after the `token_total_supply` store, 0.98763; older ledger rows saying "byte-identical" were
on bases without the separate pointer). Writing `bonding_curve.creator=creator;` after
`token_total_supply` reproduces it. The original also stores both quote-reserve fields before loading
`initial_virtual_token_reserves`; storing `virtual_quote_reserves` first, then
`initial_virtual_quote_reserves`, then `virtual_token_reserves` reproduces that (0.98870).
All are plain field stores of the same values; no `line!()` site in `init_curve`.

## Remaining residuals (c2)

Everything else in the window is identical; the IR oracle on c2 plus the phi fix below leaves only the RA residual.

1. `mov r7,0`/`mov r2,0` swapped in the two Sol `Ok((Pubkey::default(),None,Sol))` blocks of
   `validate_quote_mint`. IR oracle: the `bb112` join phi for the quote_mint first qword (SROA slice
   `_84.sroa.31`, ptr-typed because it overlaps the `Error` payload) must come before the `QuoteSource`
   i8 phis (c2 0.98870 -> 0.98978). `-print-after=sroa` shows why: mem2reg created the slices'
   phis in the order `0,18,47,51` and then `31` in a later batch (phis are inserted at the block front,
   and a later pass re-creates them reversed). In LLVM 18 `AllocaSliceRewriter::visitMemSetInst`
   refuses to rewrite a memset whose full length (32, the zero `Pubkey`) does not convert to the
   partition type (`ptr`, 8 bytes), so the slice is re-queued and promoted one SROA iteration later.
   The original therefore promoted it with the others (e.g. an integer-typed access at offset 16,
   or no 32-byte memset over it). Spellings tried, all byte-identical or worse: tuple order,
   destructuring, `system_program::ID`/`new_from_array`/shared `sol` for the zero key,
   `*mint.key`, a bound tuple, Sol check moved to the caller.
2. creator pointer allocated to r2 instead of r4 (~34 instructions renamed r2/r3/r4). In the original
   the `name` pointer is live in r2 at the init_curve exit-block entry: both `bb2.i73` edges jump to the
   `ldxdw r2,[r10-0x718]` reload (tail-merged predecessor reloads), so greedy must have region-split
   `name` before assigning the creator pointer. Ours reloads `name` right before `name.len()` because the
   creator pointer already holds r2. Moving the `name.len()` load before the creator memcpy reproduces
   `mov r4,r7` (but schedules the load early). No local IR move (bb59, exit block, bb112..bb6.i,
   post-validate blocks, 674 block moves), branch weight, greedy knob or copy probe reproduces it with
   the load late: the cause is a global greedy ordering effect.

## Debug llc (reusable)

`~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin/llc` is an assertions-enabled build of
anza-xyz/llvm-project `08aedd64` (the llvm-project submodule of the platform-tools v1.44 rust commit),
targets BPF+SBF. It produces byte-identical code for `create_v2::execute` and supports
`-debug-only=regalloc`. Trace on c2: `name` (%135) is deferred to RS_Split and region-split for
candidate r0 after the creator pointer took r2; in the exit block it is "stack-in, reload before use".
In the `name.len()`-early variant its interval starts before the creator pointer ends and evicts it
through its r2 hint (the `String::clone` argument), giving the original pattern. The exit-entry
bundle choice is a spill-placement tie (pred-edge frequency sum = exit frequency 0.033351).

## Ledger

Lane `w7r1-execute-frame`, dedupe keys `0x1e7c0-main-2b85821-*`.
