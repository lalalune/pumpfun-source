# w10r1-swaphop-slots: slot census of 0x5b3b0 multi_hop_curve::swap_hop

Base: origin/main e9e87de87 (fresh build 1032/347, zero losses, unstripped sha256 3ca6911a…).
swap_hop is 18,584 B (the original size), ratio 0.85352, slots_diff 1023, calls 107/1.
Analysis only: no source change beats main on the official ordering (size, then slots_diff, then ratio).

## 1. What slots_diff counts

`shift_census.py` aligns the two instruction streams (difflib) and asks, for each slot, whether
the original instruction sits at the original offset:

| candidate | bytes | ratio | slots_diff | equal, same offset | equal, shifted | differing |
|---|---:|---:|---:|---:|---:|---:|
| main e9e87de87 | 18,584 | 0.85352 | 1023 | 1292 | 696 | 335 |
| x1 fees-whole (6936bc3f8 file) | 18,584 | 0.92654 | 1047 | 1265 | 890 | 168 |
| x1m = x1 + `match complete_fill(..)? { None => .., Some(..) => .. }` | 18,584 | 0.93048 | 1048 | 1265 | 899 | 159 |
| w9 d1 (post_fill tuple + match + adapter bind) | 18,528 | 0.91176 | n/a | 637 | 1481 | 205 |

About two thirds of main's slots_diff are equal instructions sitting at a shifted offset. The x1
variants differ in half as many instructions as main (159 vs 335), but they score *worse* on
slots_diff because more equal code is shifted. At equal size, slots_diff is mostly a measure of a few
length-changing sites, not of how much code differs.

## 2. Cause groups (main)

`census.py` puts each diff hunk into one class:

| class | hunks | insns |
|---|---:|---:|
| stack-slot offset only | 44 | 48 (largest: the -0xaa8/-0xab0 swap, ~16 sites) |
| jump displacement only | 37 | 39 (all downstream of length changes) |
| register only | 5 | 7 |
| register+stack | 1 | 2 |
| constant | 1 | 3 |
| structural / insert / delete | 45 | 412 |

`abstract_diff.py` (layered): differing insns 511 raw, 492 with registers abstracted, 399 with
stack offsets abstracted too, and 258 with displacements and call targets abstracted as well. For x1m the same
layers give 204 → 184 → 146 → 77.

The structural groups on main, by cause:
- **Error-return tail merging (bb216, 13 predecessors).** The original stores most errors straight into
  sret at the error site. Ours jumps to a shared epilogue (`mov r9,rX; ja`). Sites 0x1898, 0x1db8/0x1dc0,
  0x2718 and 0x2c28..0x2e30. The w9/x1 post_fill tuple removes this (see the x1 rows).
- **complete_fill block placement (±584 B at 0x2830/0x2998).** The original lays out the `base <= reserves`
  arm (`mov r1,0; stxdw [..],r1` on the split edge) and the join before the whitelist memcmp + complete_fill.
  base / the base_amount phi live in stack slot -0xb28 in the original and in r9 in ours. Fixed by the w9 tuple/match variants.
- **Buy-arm register choice.** The original keeps trade_amount in r9 across get_fees, net_quote_for_budget and sub3. Ours spills it
  (-0xaf0) and keeps base in r9 instead.
- **Two branch-polarity / IR-order sites:** `if last` merge placement (0x2d10/0x2e38) and the final
  `if let Some(post)=post_fill` (0x3df8).

## 3. Which length fixes are worth slots (`shift_sites.py`)

The script simulates making one site, or a pair of sites, length-neutral and recounts the aligned slots:

| base | best pair | gain | next best |
|---|---|---:|---|
| main | 0x3978 (orig-only `stxdw [r10-0xab0], r3`) + 0x3df8 (cand-only `ja`) | **+142** | +48 (0x1350 + 0x17f8), +44 |
| x1m | 0x3978 + 0x3e00 (same pair) | **+143** | +48 |

Every single site on its own loses slots: each one only moves where the shift starts. The 0x3978/0x3df8 pair is
the only site worth more than about 50 slots, on both bases. On x1m it would bring slots_diff to about 905, below main's
1023, at ratio of about 0.935.

### 3a. 0x3df8: the `ja` at the final post_fill test (solved at IR level, not at source level)
- IR oracle (`edits/i_pol.py`, `edits/i_mv159.py`, using llc on the saved post-opt IR): flipping only that `br`
  (`icmp eq tag,0 → none, else some`) or moving `bb159` (the Some arm) right after the branch gives
  the original `jeq r1,0x0,-0xe2` and changes nothing else (-8 B).
- Cause: in IR order the CompleteEvent `route_event!` error chain (bb350 plus inlined drop glue) sits between the
  switch block and the Some arm, so SelectionDAG cannot use the Some arm as the fall-through. BPF has no
  reverseBranchCondition, so branch folding keeps `jne +1; ja`.
- Source spellings tried (all rejected): `match post_fill {Some=>..,None=>{}}` (and the x1 lane's None-first
  form) fixes the site but flips the post_complete_buy_event `?` at 0x4088 (a 129-insn block swap), giving 0.794.
  An `if let Err(e)=invoke_signed(..)` early return for the completion route moves its error chain to the end of the function (0.810).
  Explicit `drop(ix)`/bound result variants are -136 B or leave the site unchanged.

### 3b. 0x3978: the original's redundant re-spill of the curve pointer
The original reloads the curve Account pointer into r3, stores `complete=1`, copies mint and user, and then
writes r3 back to its own slot (-0xab0) before reading the key. The same happens at 0x5d920, in the
post_fill curve stores. Pre-greedy MIR shows a single vreg (%0 = h.val) in that block, reloaded once.
The original instead behaves as if a split interval were spilled after a local split. The instructions
from 0x3980 to 0x3df0 are otherwise identical, so the split decision comes from global interference, not from this
block. IR-oracle attempts to force a distinct SSA value (reload the Box from h; phi at the arm merge) did not reproduce it.

## 4. Tools (`reconstruction/pump-main/lanes/w10r1-swaphop-slots/`)
- `census.py <show.txt> [--verbose]`: classify win.py `show --full` hunks (stack-slot/jump/register/const/structure).
- `abstract_diff.py <show.txt>`: layered differing-instruction counts (raw, -regs, -stack, -displacements).
- `shift_census.py <show.txt>`: slots that are equal at the same offset, equal but shifted, or differing.
- `shift_sites.py <show.txt>`: what making each length-changing site (and each pair) neutral is worth in slots.
- `tools/orcshow.py <orc-name|unstripped.so>`: show-format diff for llc-oracle objects or builds. `tools/deltas.py`: list of
  length-changing hunks with the running byte offset. `tools/orc.py`, `capir.py` and `extract.py` are adapted from
  w10r1-swaphop-region1of4. `named.py` renames numbered IR values so blocks can be moved in IR edits.
- `edits/*.py`: the IR-oracle edits listed in the ledger.

## Ledger (lane w10r1-swaphop-slots)
d19cc128 (match post_fill, rejected), 21d39800 / d9c17591 (completion route if-let Err, main / x1m),
dcf89de3 (IR polarity oracle), dccdfce1 (reload curve Box), 6523f883 (split else edge), 5b87ee10 (merge after if-last),
1689b908 (x1/x1m re-measure), 7e684f92 / 270e0e08 / 1ff25e46 (completion route drop variants), 82b5b3c0 (phi oracle),
3f291057 (census).

## Next
1. Work on x1m (0.93048) rather than main. Its residual structure is 77 abstract instructions, and the 0x3978/0x3df8 pair is worth +143.
2. 0x3df8 needs a source form whose IR order puts the Some arm right after the post_fill switch without
   flipping the post_complete_buy_event `?`. The lever is where inlined drop glue of the CompleteEvent route lands:
   for example the order of the route's temporaries (`authority_info`, `ix_data`, `ix`), or the event built before
   `complete=true`.
3. 0x3978 is probably a downstream effect of global RA. Re-check it after each structural fix upstream on x1m.

## Landing addendum (merge of origin/main bf0b20087)

The figures above were measured against e9e87de87. Since then, w10r1-swaphop-stitch (#2574) changed
`programs/pump/src/multi_hop_curve_swap.rs`. A fresh build of bf0b20087 scores 1033 normalized / 1033 raw
with zero losses, and swap_hop is 18,584 B, ratio 0.97551, slots_diff 672. The merged branch builds
byte-identically to main (unstripped sha256 5de92be1…), because this lane adds only notes and tools.
Before reusing the per-site slot values (+142 for the 0x3978/0x3df8 pair, and the others), rerun
`shift_sites.py` against the current build.
