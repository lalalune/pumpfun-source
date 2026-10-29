# Lane w3-swaphop (wave 3): 0x5b3b0 `multi_hop_curve::swap_hop`

Base: origin/main 665499915 (1022 normalized / 276 raw). Approach: stack-slot / local-layout
reconstruction, then the LLVM-IR oracle.

## Step 0: port of round-2 pf1

PR #1248 merged only round 1 of the multihop-reconstruction lane. Its round-2 commits
(d2e730407 mac1 `macro_rules! route_event!`, 1e90f38b7 pf1 deferred `let post_fill;`) never
reached main. Applied unchanged on 665499915 (attempt 051b0bbc):

| build | bytes (orig 18,584) | win ratio | opregs | op | segdist opregs / exact | official |
|---|---:|---:|---:|---:|---:|---|
| main 665499915 | 18,376 | 0.0915 | 0.6574 | 0.7370 | 1132 / 1886 | 1022 / 276 |
| pf1m (pf1 on main) | 18,272 | 0.2148 | 0.7233 | 0.8071 | 903 / 1628 | 1022 / 276, no losses |

pf1m unstripped sha256 83fbc9e46b15bc0443afa9c136154f0edd29a2a97aa20ae9b2bc031acb8c29e4.

## Frame-object census (tools: `fimap.py`, `frame.py`, `oracle.py`, `nmove.py`, `nsweep.py` in the lane OUT `bin/`)

`llc -stop-after=prologepilog` on the extracted swap_hop IR lists every frame object with its
offset. Frame-index order is alloca order: reverse MIR-local order, and the route_event!
temporaries of the last event come first. Stack coloring merges disjoint 32-byte key temps into
earlier slots. `fimap.py` pairs each of our frame objects with the original object base through
opregs-aligned r10 accesses.

On pf1 the original has two extra unmerged 32-byte objects (0x158 mint, 0x178 user) between
authority_info53 and the 232-byte post_complete_buy_event result. They are fresh copies of the
user key and of `h.base_mint.key()`, made right before `post_complete_buy_event` (orig 0x4068).
We pass the CompleteEvent temps instead. Every frame object after them is shifted +24.

IR oracle (edits/pe3.py, edits/peA_user.py): giving the call fresh user/mint copies in a new
alloca pair placed before `_502` raises r10-offset agreement from 107/620 to 311/620 and
exactish from 0.12 to 0.43. On peA, the fresh user copy alone gives exactish 0.121 -> 0.437
and opregs 0.7320 -> 0.7354.

Why ours reuses the user copy: MIR GVN. The MIR shows
`_450 = CompleteEvent { user: _451, .. }` and later
`post_complete_buy_event(move _499, move _451, ..)`. Derefs of `&Pubkey` reached through
`a: &MultiHopCurve` count as stable values. Mint through `&mut h` is not, so
`h.base_mint.key()` gives a fresh mint (peA). The spelling (`*a.user.key`, `as_ref().key()`),
a helper fn or closure (MIR-inlined), and an indirect store in between (peJ) all keep the
reuse. What breaks it is dominance: in peL1 the CompleteEvent block no longer dominates the
post call, which sits in a second `if completed` on the same bool, and LLVM jump-threads it
back into the nested layout.

| build | bytes | win ratio | opregs | op | segdist opregs / exact | aligned calls |
|---|---:|---:|---:|---:|---:|---:|
| pf1m | 18,272 | 0.2148 | 0.7233 | 0.8071 | 903 / 1628 | 101 |
| peA: CompleteEvent + post mint = h.base_mint.key() | 18,320 | 0.1876 | 0.7320 | 0.8091 | 861 / 1631 | 101 |
| **peL1: peA + split `if completed` (in source)** | 18,328 | **0.3584** | 0.6821 | 0.7693 | 1049 / 1659 | 98 |

peL1 cost: per-segment distances equal or improve against peA, except the segment after
post_complete_buy_event (orig@0x4070). There the original places the buy HopOutput block
(base_mint key, vault clone, token-program drops) and peL1 places it at the end of the
function. All builds are 1022/276 with no losses.

Ledger ids: 31f15d57 (oracle), 72d8b363/5379420d/1d6998a9 (peA-C), 0187e3b7 (peD-F), 82c63b5f
(peH1-3), cd810fed (peJ), c5a80b37 (peK), cd7d5a67 (peL1/L2), plus L4/L6.

## Block order after peL1 (IR oracle, `nsweep.py`: 5852 single block moves in the tail)

peL1's only structural regression is block order. The post_complete_buy_event call block (bb337)
is followed directly by its Ok continuation (bb339, the PostComplete emission). Any IR order
that separates the two restores the original layout of the HopOutput/buy blocks. Placing the
`?` Err block bb338 right after bb337, or bb337 after bb339, gives opregs 0.682 -> 0.736,
exactish 0.326 -> 0.415, segdist 1049/1659 -> **844/1479** with 101 aligned calls. That is the
best structure and frame of any configuration so far (orc/best1, orc/best2). peA's nested form
had the join bb158 between them, but that form keeps the GVN fold.

Source spellings tried for that order, none effective: an explicit match on the post Result
(Err arm first, M1 = M2), an if-let-Err plus let-else (M3: drops a call), then-first integer
compares (N1-N3), post tested first (P1, P2 = L1 bytes).

## Rejected (all 1022/276, no losses)
peD-F (user spelling), peH1-3 (closure/helper), peJ/J2 (store placement), peK/K2 (unnested),
L2 (on pf1), L4 (tuple if-let = L1), L6 (post by value), M1-M3, N1-N3, O1-O3 (non-SSA temp),
P1-P2.
