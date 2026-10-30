# research: fee-table validation at TRUE 5 hops on the split x boost x tf chain

## Problem

Packet #83 pinned the fee-table account's own validation on the TRUE
3-hop split chain: a wrong discriminator fails 3002, a wrong owner
fails 3007, lamports 0 fails 3012 while lamports 1 and 2,000,000
(below rent-exempt) succeed anchor-identically (no rent-exempt
check), the check order is 3012 > 3007 > 3002, every key swap fails
3007 (the owner check fires before any discriminator read), and
sweep/collect/boost/claim legs after a 3002 failure still pay
fixture values. This packet asks whether every one of those holds at
depth 5, on the split x boost x tf chain (three_amm + g4 + g5, final
output U5), and adds the ghost counts in both directions at depth 5
for each fault class, mid-chain corruption (a good buy, then a
corruption patch, then a second buy), and tf variants of the
discriminator/owner/swap faults.

Route check (read from the builder, not the packet name):
build_route calls three_amm and appends the g4 and g5 hop groups, so
the fixture route is main -> POOL2 -> P3 -> P4 -> P5, final output
U5: TRUE 5 hops. #61 appended g4 only and was actually 4 hops; this
packet appends g4 AND g5 and names itself 5-hop, matching.

Fee-table validation mutations are case-level harness account edits
(fee_valid) or mid-case cpatch "feevalid" resets, recorded as such,
never presented as on-chain instructions. cpatch steps carry an empty
transaction by design: a harness field reset, not an instruction.

## Cases

58 cases, 243 receipts, 25 parts (24 x 10 + 3), each run on three
images (original, control rebuild, candidate rebuild). All cases use
the bps-100 tf fixture unless a tf variant says otherwise. Fee
payer lamport cost is 5,000 per failed step (fee only, full rollback)
and 1,849,400 per successful 5-hop swap (5 hop events).

- A (anchors, 5): buy5, sell5, buy-then-patched-window boost,
  sell-then-patched-window boost, buy-sweep-collect.
- D (discriminator, 8): zeroed / pool / GlobalConfig / single flipped
  byte discriminator, buy and sell.
- W (whole data, 4): fee-table data replaced wholesale by
  GlobalConfig / pool / zeroed data, buy (plus zeroed data, sell).
- O (owner, 7): owner set to the pump program itself / SPL token /
  Token-2022 / system / default (zero) owner, buy (plus program and
  default owners, sell).
- L (lamports, 4): lamports 0 buy, lamports 0 sell, lamports 1 buy,
  lamports 2,000,000 buy.
- R (check order, 4): discriminator + owner together buy and sell,
  lamports 0 + discriminator buy, lamports 0 + owner buy.
- S (key swaps, 7): fee-table key replaced by the GlobalConfig key /
  pool / quote token account / an absent fresh key / the user quote
  account, buy (plus GlobalConfig key and fresh key, sell).
- P (leg parity, 7): disc-zero on v2 buy, v2 sell, legacy buy,
  legacy sell, stable buy; owner-program on v2 buy and stable buy.
- M (mid-chain corruption, 4): good buy, corruption patch, second
  buy (disc-zero -> 3002, owner-program -> 3007, lamports 0 ->
  3012); good buy, disc corruption, sweep/collect.
- F (downstream after failure, 4): disc-zero buy failure then
  sweep/collect; disc-zero buy failure then patched-window boost;
  disc-zero buy failure then token claim; disc-zero failure then
  plain-quote cashback claim (no_ww guard: no withdraw-withheld
  authority patch on the plain mint).
- T (tf variants, 4): disc-zero buy at tf5000 and tf0, owner-program
  buy at tf5000, GlobalConfig-key swap buy at tf0.

## Result

0 divergent cases: original, control and candidate agree on every
case, including every error code, event count and balance delta.

Anchors (unmutated fee table, bps 100 tf): 5-hop buy tail
5,207,955,235,891 with bb leg 4,515,471 and 5 hop events; 5-hop sell
payout 178,541 with bb leg 837 and 5 hop events. Buy-then-patched-
window burn 5,254,679,949,141; sell-then-patched-window burn
5,338,394,848,076. Buy-then-sweep-collect: protocol sweep net
4,517,934 (gross 4,563,570), creator sweep net 122,160 (gross
123,394), collect net 120,938.

Discriminator: every D and W case fails 3002
(AccountDiscriminatorMismatch, "caused by account: fee_config")
with 0 events and full rollback, in both directions. That covers
zeroed, pool, GlobalConfig and single-flipped-byte discriminators
and wholesale GlobalConfig / pool / zeroed data replacements.

Owner: every O case fails 3007 (AccountOwnedByWrongProgram,
"caused by account: fee_config") with 0 events and full rollback,
including the pump program itself as owner, in both directions.

Lamports: lamports 0 fails 3012 (AccountNotInitialized, "caused by
account: fee_config") with 0 events, both directions. Lamports 1
and lamports 2,000,000 (below rent-exempt) succeed with
anchor-identical deltas (buy tail 5,207,955,235,891): no
rent-exempt check fires on the fee-table account at depth 5.

Check order: discriminator + owner together fails 3007 (both
directions); lamports 0 + discriminator fails 3012; lamports 0 +
owner fails 3012. Order at depth 5 is 3012 > 3007 > 3002, exactly as
at 3 hops.

Key swaps: every S case fails 3007 with 0 events, both directions.
The owner check fires before any discriminator read, so even the
GlobalConfig key (a valid account with a valid discriminator of a
different type) and the pool key fail as wrong-owner, not as
wrong-discriminator.

Leg parity: disc-zero fails 3002 on v2 buy, v2 sell, legacy buy,
legacy sell and the stable buy; owner-program fails 3007 on v2 buy
and the stable buy. The fee-table gate is leg-independent.

Mid-chain corruption: a good buy, then a corruption patch, then a
second buy fails 3002 (disc), 3007 (owner) or 3012 (lamports)
respectively, with the first buy's effects intact. A good buy, then
disc corruption, then sweep/collect still pays the post-buy values
(protocol sweep net 4,517,934, creator sweep net 122,160, collect
net 120,938): the fee table is not read by the sweep/collect legs.

Downstream after failure: a disc-zero buy failure leaves the fee
buckets untouched, so the protocol sweep pays only the fixture
bucket (net 2,463, gross 2,488), while creator sweep net 122,160
and collect net 120,938 are unchanged. The patched-window burn
after a failed buy is 5,338,379,201,831 (the fresh-window value).
Token claim after a failed buy pays 3,334,551 gross with no
withheld in this fixture. Plain-quote cashback claim after a
failure pays 5,475.

tf variants: disc-zero fails 3002 at tf5000 and tf0, owner-program
fails 3007 at tf5000, GlobalConfig-key swap fails 3007 at tf0.
Fee-table validation is tf-neutral: the transfer-fee rate does not
move, mask or reorder any gate.

Depth-5 note: unlike the length gates in #136 (6082 failures carry
4 buy ghosts / 0 sell ghosts at depth 5), every fee-table
validation failure here carries 0 events in both directions. The
fee-table check fires up front, before any hop executes, so no hop
event is emitted even on the 5-hop route.

## Limits

- The fee-table mutations are harness account edits and cpatch
  field resets, not on-chain transactions; they measure the
  program's validation logic against a corrupted account state,
  not an attacker's ability to reach that state on chain.
- Ghost counts are measured on this fixture route (main -> POOL2
  -> P3 -> P4 -> P5); other routes were not re-measured here.
- The token claim's withheld figure is fixture-dependent: this
  fixture pays 3,334,551 gross with no withheld, unlike #83's
  fixture, which showed a withheld split. The gross figure is the
  comparable value.
- No source change is proposed. This packet records measured
  validation behaviour only; it does not claim the full program is
  equivalent across images.

Made via @slopdotcash
