# research: Pool validation at TRUE 5 hops on the split x boost x tf chain

## Problem

Packet #85 pinned the Pool account's own validation on the TRUE
3-hop split chain: a wrong discriminator fails InvalidAccountData
(the Anchor deserialization gate, same as GlobalConfig, NOT the
fee-table account's 3002), a wrong owner fails 6027 on multi-hop
(the `is_curve_hop` gate in `multi_hop_swap.rs`) but 3007 on
single-leg v2/legacy/set legs (Anchor's owner check), lamports 0
fails 6027 on multi-hop (a 0-lamport account vanishes from the VM,
so the program reads a default account whose owner is neither the
pump program nor PUMP) but 3012 on single-leg v2, lamports 1 and
2,000,000 succeed anchor-identically (no rent-exempt check), check
order on multi-hop collapses to a single 6027, key swaps split by
the swapped account (fee-table key 6027, GlobalConfig key
InvalidAccountData, fresh key 6027, user-quote account 6027,
another pool's key 6008 with ghost events), and a hop-pool failure
does not leak into main-pool legs. This packet asks whether every
one of those holds at depth 5, on the split x boost x tf chain
(three_amm + g4 + g5, final output U5), and adds the ghost counts
in both directions at depth 5 for each fault class and each hop
position, Pool length gates at depth 5 (the #96 lower bound of 211
bytes, tested from both sides, for the main pool and for the
terminal hop pool), mid-chain corruption, and tf variants of the
discriminator/owner/swap faults.

Route check (read from the builder, not the packet name):
build_route calls three_amm and appends the g4 and g5 hop groups, so
the fixture route is main -> POOL2 -> P3 -> P4 -> P5, final output
U5: TRUE 5 hops. #61 appended g4 only and was actually 4 hops; this
packet appends g4 AND g5 and names itself 5-hop, matching.

Pool validation mutations are case-level harness account edits
(pool_valid / pool_len / pool_len_hop) or mid-case cpatch
"poolvalid" resets, recorded as such, never presented as on-chain
instructions. cpatch steps carry an empty transaction by design: a
harness field reset, not an instruction.

## Cases

88 cases, 348 receipts, 35 parts (34 x 10 + 8), each run on three
images (original, control rebuild, candidate rebuild). All cases use
the bps-100 tf fixture unless a tf variant says otherwise. Fee
payer lamport cost is 5,000 per failed step (fee only, full rollback)
and 1,849,400 per successful 5-hop swap (5 hop events).

- A (anchors, 5): buy5, sell5, buy-then-patched-window boost,
  sell-then-patched-window boost, buy-sweep-collect.
- D (main-pool discriminator, 8): zeroed / flipped byte /
  GlobalConfig / fee-table discriminator, buy and sell.
- D2 (hop-pool discriminator, 6): P2 / P4 / P5 zeroed
  discriminator, buy and sell.
- W (whole data on the main pool, 4): GlobalConfig / fee-table /
  zeroed data, buy (plus zeroed data, sell).
- O (main-pool owner, 8): SPL token / Token-2022 / system /
  default / Fees program owner, buy (plus token owner, sell);
  token owner on single-leg v2 buy and v2 sell.
- L (main-pool lamports, 5): lamports 0 buy and sell, lamports 1
  buy, lamports 2,000,000 buy, lamports 0 on single-leg v2 buy.
- L2 (terminal hop-pool lamports, 2): P5 lamports 0, buy and sell.
- N (main-pool length, 6): lengths 100, 210, 211, 212 buy; 210 and
  211 sell.
- N2 (terminal hop-pool length, 2): P5 lengths 210 and 211 buy.
- R (check order, 6): discriminator + owner buy and sell,
  lamports 0 + discriminator buy, lamports 0 + owner buy, all
  three buy, flipped discriminator + system owner sell.
- S (key swaps, 9): main pool key replaced by the fee-table key
  (buy, sell), the GlobalConfig key (buy), a truly-absent key
  (buy), the user quote account (buy); P2 key replaced by the
  main pool key (buy, sell); P5 key replaced by the P4 key (buy,
  sell).
- P (leg parity, 8): disc-zero on v2 buy, v2 sell, legacy buy,
  legacy sell, stable buy, deposit, protocol sweep,
  patched-window boost.
- M (mid-chain corruption, 4): good buy, corruption patch, second
  buy (disc-zero -> InvalidAccountData, owner-token -> 6027,
  lamports 0 -> 6027); good buy, disc corruption, sweep/collect.
- F (downstream after failure, 4): disc-zero buy failure then
  sweep/collect; disc-zero buy failure then patched-window boost;
  disc-zero buy failure then token claim; disc-zero failure then
  plain-quote cashback claim (no_ww guard: no withdraw-withheld
  authority patch on the plain mint).
- S2 (setters under a corrupted main pool, 3): control
  buyback-config setter, disc-zero buyback-config setter,
  disc-zero disable setter.
- T (tf variants, 4): disc-zero buy at tf5000 and tf0,
  owner-token buy at tf5000, fee-table-key swap buy at tf0.
- H (terminal hop-pool failure isolation, 4): P5 disc-zero buy
  failure then main single-leg buy; then patched-window main
  boost; then token claim; then plain-quote cashback claim.

## Result

0 divergent cases: original, control and candidate agree on every
case, including every error code, event count and balance delta.

Anchors (unmutated pool, bps 100 tf): 5-hop buy tail
5,207,955,235,891 with bb leg 4,515,471 and 5 hop events; 5-hop sell
payout 178,541 with bb leg 837 and 5 hop events. Buy-then-patched-
window burn 5,254,679,949,141; sell-then-patched-window burn
5,338,394,848,076. Buy-then-sweep-collect: protocol sweep net
4,517,934 (gross 4,563,570), creator sweep net 122,160 (gross
123,394), collect net 120,938.

Discriminator: every D, D2 and W case fails InvalidAccountData
with full rollback, in both directions. That covers zeroed,
flipped-byte, GlobalConfig and fee-table discriminators and
wholesale GlobalConfig / fee-table / zeroed data replacements.
The ghost count is exactly the number of hops executed before the
failing hop: main-pool faults carry 0 buy ghosts and 4 sell ghosts
(the sell executes P5, P4, P3, P2 before the main hop fails);
P2 faults carry 1 buy / 3 sell ghosts; P4 faults 3 buy / 1 sell;
P5 faults 4 buy / 0 sell. At 3 hops the same ladder was 0/2 for
the main pool; depth 5 stretches it to 0/4, with the intermediate
rungs filled by P2 and P4.

Owner: every multi-hop owner fault fails 6027
(AccountTypeNotSupported, the `is_curve_hop` gate), with the same
position ghost ladder (token-owner sell: 4 ghosts). The same fault
on single-leg v2 buy and v2 sell fails 3007 (Anchor's owner
check, 0 events). So the pool owner gate is 6027 on multi-hop but
3007 everywhere else, exactly as at 3 hops.

Lamports: main-pool lamports 0 fails 6027 on multi-hop (0 buy
ghosts, 4 sell ghosts) -- the vanished-account mechanism, not a
lamports gate: a 0-lamport account is absent from the VM, so the
program reads a default account whose owner is neither the pump
program nor PUMP -- but 3012 on single-leg v2 buy (Anchor's
initialized check, as at 3 hops). Terminal hop-pool lamports 0 fails 6027 too,
with 4 buy ghosts and 0 sell ghosts. Lamports 1 and lamports
2,000,000 (below rent-exempt) succeed with anchor-identical
deltas (buy tail 5,207,955,235,891): existence only, no
rent-exempt check, at depth 5.

Length: the main-pool gate is exactly 211 bytes, both directions --
but a 211-byte pool does NOT trade anchor-identically. 100 and 210
bytes fail InvalidAccountData (210 sell: 4 ghosts); 211 and 212
succeed for the buy, but with tail 5,207,950,056,210 instead of the
anchor 5,207,955,235,891, and a post-trade main pool of [vq
-4,561,082, protocol 4,561,082, creator 0] instead of [vq
-4,686,964, protocol 4,563,570, creator 123,394]. The differences
are exactly the fixture trailing values (vq -125,882, protocol
2,488, creator 123,394): deserialization only requires 211 bytes,
so every field past 211 (coin_creator 211..243, vq 245..261,
creator_fee_bps, fee buckets) reads as zero, the trade prices off
that zeroed trailing state, and the write-back rebuilds the
account to 287 bytes with creator 0. The 211-byte sell still pays
the anchor 178,541 (all token deltas identical), but its post-trade
main pool is [vq -847, protocol 847, creator 0] instead of [vq
-126,729, protocol 3,335, creator 123,394] -- the payout is
insensitive to the main pool's zeroed trailing state while the
stored state is not. The terminal hop-pool gate is exactly 211
bytes too: P5 at 210 bytes fails InvalidAccountData with 4 buy
ghosts, at 211 succeeds with tail 5,210,540,474,247 (vs the anchor
5,207,955,235,891) and a fully zeroed terminal pool state [0, 0,
0]. The #96 lower bound of 211 bytes is a per-pool
deserialization floor, not a route-level one -- and clearing it
does not restore the fixture state.

Check order: on multi-hop there is no distinguishable order at
depth 5 either -- disc+owner, lamports+disc, lamports+owner, and
all three combined all fail 6027, in both directions. The 6027
owner/existence gate fires before any discriminator read, so a
combined fault never reaches the InvalidAccountData that a lone
disc fault reports. This collapses #83's 3012 > 3007 > 3002 and
#84's 3012 > 3007 > InvalidAccountData into a single 6027, as at
3 hops.

Key swaps: fee-table key fails 6027 (0 buy ghosts, 4 sell
ghosts); GlobalConfig key fails InvalidAccountData (0 events --
the config account is program-owned, so the is_curve_hop gate
passes and deserialization fails); truly-absent key fails 6027;
user quote account fails 6027. Another pool's key fails 6008
with the position ghost ladder: P2 replaced by the main pool key
fails with 1 buy ghost and 3 sell ghosts; P5 replaced by the P4
key fails with 4 buy ghosts and 0 sell ghosts. The 6008 is the
seed/authority mismatch of running one pool's data against
another hop's mints and vaults, and it fires only after the
earlier hops have already emitted their events.

Leg parity: disc-zero fails InvalidAccountData on v2 buy, v2 sell,
legacy buy, legacy sell, the stable buy, deposit, the protocol
sweep and the patched-window boost. The pool discriminator gate
is leg-independent (unlike the owner gate, which splits 6027 vs
3007 by leg).

Mid-chain corruption: a good buy, then a corruption patch, then a
second buy fails InvalidAccountData (disc), 6027 (owner) or 6027
(lamports) respectively, with the first buy's effects intact. A
good buy, then disc corruption, then sweep/collect: both sweeps
fail InvalidAccountData and collect stays a silent 0-event no-op
(collect only moves what a sweep already moved).

Downstream after failure: a disc-zero buy failure leaves the fee
buckets untouched, so both sweeps fail InvalidAccountData and
collect is a silent no-op, and the patched-window boost fails
InvalidAccountData -- but the token claim still pays the full
seeded 3,334,551 gross and the plain-quote cashback claim still
pays 5,475. Pool-reading legs fail alike; pool-blind legs keep
working.

Setters are pool-blind (new at depth 5, and a contrast with #85's
pool-reading set leg): under a disc-zero main pool, the
buyback-config setter still succeeds (no error) and the disable
setter still succeeds and visibly writes, flipping the
GlobalConfig disable byte from 0 to 8 (the buy bit). Both setters
read GlobalConfig only and never touch the pool account, so a
corrupted pool cannot block them.

tf variants: disc-zero fails InvalidAccountData at tf5000 and
tf0, owner-token fails 6027 at tf5000, fee-table-key swap fails
6027 at tf0. Pool validation is tf-neutral: the transfer-fee rate
does not move, mask or reorder any gate.

Hop-pool failure isolation: after a P5 disc-zero buy failure
(4 ghosts), the main single-leg buy still pays 1,000,000 base for
189 quote, the patched-window main boost still burns the
fresh-window 5,338,379,201,831, and token/cashback claims still
pay in full. A terminal hop-pool failure does not leak into any
main-pool leg.

## Limits

- The pool mutations are harness account edits and cpatch field
  resets, not on-chain transactions; they measure the program's
  validation logic against a corrupted account state, not an
  attacker's ability to reach that state on chain.
- Ghost counts are measured on this fixture route (main -> POOL2
  -> P3 -> P4 -> P5); other routes were not re-measured here.
- The buyback-config setter case sets bps 5000, the fixture value,
  so its success is evidenced by the absence of an error, not by
  a changed field; the disable setter case is the one that proves
  a real write under a corrupted pool (disable byte 0 -> 8).
- No source change is proposed. This packet records measured
  validation behaviour only; it does not claim the full program is
  equivalent across images.

Made via @slopdotcash
