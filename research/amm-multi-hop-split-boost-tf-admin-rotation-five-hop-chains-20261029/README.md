# research: split x boost x tf admin rotation chains at TRUE 5 hops

## Problem

Packet #75 showed, at a TRUE 3-hop split chain, that admin
authority rotation hands over atomically: the old admin's setters
fail, the new admin's succeed, the split chain itself is
admin-blind, sweep/collect follow the fee-payer rather than the
admin, boost answers only to the boost authority, the fee
authority is a third field that survives rotation, the new admin
is unvalidated (even the program id is accepted), and a zero
admin bricks further administration while trades keep working.
Packet #128 then showed the four admin setters binding a live
split chain at TRUE 5 hops. This packet joins the two: does
every #75 rotation behaviour still hold when the chain is a
TRUE 5-hop split x boost x tf route (main -> POOL2 -> P3 -> P4
-> P5, final output U5), and does rotation interact with the
5-hop boost window at all?

Route verification: the builder's `build_route` calls `three_amm`
and then appends the g4 and g5 hop groups, so the buy runs
main -> P2 -> P3 -> P4 -> P5 and the sell runs the reverse;
successful swaps emit 5 hop events. The name, this README, and
the PR title all say 5 hops because the route really is 5 hops
(contrast the earlier 3-hop-named packet whose route was actually
4 hops). Each hop pool carries proper pool data (its own bump,
pool-authority creator, base mint, and vaults), not raw main-pool
bytes, and each hop boost uses an SPL-derived ATA for its hop quote
mint (BA4S for BASE3, BA5S for BASE4). The quote mint carries a
per-case transfer-fee config (100 bps unless stated) and the split
legs route the buyback through the TOKEN22 ATA. The GlobalConfig
buyback baseline is 5000 bps in every case unless a setter changes
it.

## Cases

44 cases, 342 receipts, 35 parts (34x10 + 2), across original,
control and candidate images. The 5-hop buy tail anchor is
5,207,955,235,891 with buyback leg 4,515,471, the sell payout
anchor is 178,541, and the buy-then-patched-window boost anchor
burn is 5,254,679,949,141.

- A (5): anchors at depth 5: buy; sell; buy then patched-window
  boost; buy then sweep creator then collect; buy then sweep
  protocol.
- R (11): rotation basics at depth 5: rotate to outsider; rotate
  to self; rotate signed by outsider; rotate unsigned; rotate to
  the program id; rotate to zero; rotate to an unfunded key;
  rotate then buy; rotate then sell; rotate then buy then
  patched-window boost; rotate to zero then buy.
- S (9): setter handover at depth 5: old admin buyback setter;
  new admin buyback 7500 then buy; new admin buyback 7500 then
  buy then boost (no vq patch); old admin fee-config setter;
  new admin fee-config rewrite then buy; old admin disable
  setter; new admin disable buy bit then buy then clear then
  buy; new admin boost toggle off then boost then on then
  boost; new admin mayhem toggle off.
- W (3): sweep/collect admin-agnostic at depth 5: rotate then
  buy then sweep creator then collect; rotate then buy then
  sweep protocol; rotate then buy then patched-window boost
  then sweep creator.
- B (7): boost-authority separation at depth 5: rotate the boost
  authority while admin is unchanged; rotate it signed by an
  outsider; old admin rotates it after admin rotation; new
  admin rotates it after admin rotation; new-authority boost
  after both rotations with the old authority; new-authority
  boost with the new authority; rotate admin then patched-window
  boost with the unchanged boost authority.
- D (5): double rotation at depth 5: rotate out and back then
  buyback setter then buy; rotate out and back then boost;
  rotate to the same admin twice; rotate out then to an
  unfunded admin then both old and new buyback setters then
  buy; rotate to zero then patched-window boost.
- F (4): tf variants after rotation: rotate then buy at
  tf5000; rotate then new-admin buyback 7500 then buy at
  tf5000; rotate then buy at tf0; rotate then buy then
  patched-window boost at tf0.

## Result

Control and candidate agree on every case. Original agrees on
every case too: there are no divergent cases in this packet.

- Rotation gates are unchanged at depth 5: rotate to outsider
  succeeds with the 80-byte update_admin event (disc
  e198ab57f63f42ea, ts 1234567890, admin and new_admin fields);
  rotate to self succeeds; rotate signed by an outsider fails
  6005; rotate unsigned fails 3010; rotate to the program id
  succeeds (the new admin is not validated); rotate to zero
  succeeds; rotate to an unfunded key succeeds.
- The chain is admin-blind at depth 5: rotate then buy pays
  exactly the anchor tail 5,207,955,235,891 with leg 4,515,471;
  rotate then sell pays exactly 178,541; rotate then buy then
  patched-window boost burns exactly 5,254,679,949,141; rotate
  to zero then buy still pays the anchor tail. Rotation writes
  no other field: fee authority, boost authority, buyback bps,
  disable bits and mode flags are all unchanged by a
  rotation-only step.
- Setter handover is atomic at depth 5: after rotation the old
  admin's buyback, fee-config and disable setters all fail
  6005, while the new admin's succeed and bind the next 5-hop
  buy: new-admin buyback 7500 moves the leg to 6,773,206 with
  the tail unmoved; the new-admin fee-config rewrite leaves
  the buy byte-identical (tail 5,207,955,235,891, leg
  4,515,471); the new-admin disable buy bit blocks the buy with
  6020 and clearing it restores the anchor buy exactly; the
  new-admin boost toggle off blocks boost with 6066 and
  toggling it back on burns 5,338,379,201,831; the new-admin
  mayhem toggle clears the global mayhem flag.
- Sweep/collect are admin-agnostic at depth 5: after rotation
  the buy then sweep creator pays exactly 123,394 (collect
  122,160 on to 120,938) and sweep protocol pays exactly
  4,563,570, identical to the anchors, and the same holds
  after a patched-window boost.
- The boost authority is a separate field at depth 5: rotating
  it while the admin is unchanged succeeds; rotating it signed
  by an outsider fails 6005; after admin rotation the old
  admin cannot rotate it (6005) and the new admin can; after
  both rotations the old-authority boost fails 6005 while the
  new-authority boost burns 5,338,379,201,831; and admin
  rotation alone leaves the fresh-window boost burn unchanged
  at 5,338,379,201,831.
- The buy is window-neutral, and this is the packet's sharpest
  new pin: after a 5-hop buy the main pool reads vq
  -4,686,964, protocol 4,563,570, creator 123,394, whose sum is
  exactly 0, so the window the buy leaves behind is exactly
  closed. The protocol accrual offsets the vq movement to the
  unit. That is why setter-then-buy-then-boost without a vq
  patch fails 6065 in this packet, while the same sequence
  with a vq patch burns: a buy can never open a closed boost
  window at depth 5, and the #128 setter-before-buy burn
  movement is a patched-window effect, not a buy effect.
- Double rotation round-trips at depth 5: rotate out and back
  restores the old admin's setters (buyback 7500 leg
  6,773,206) and the fresh-window burn 5,338,379,201,831;
  rotating to the same admin twice succeeds; rotating out
  then to an unfunded admin bricks both old and new buyback
  setters (6005 each) while the 5-hop buy still pays the
  anchor tail and the patched-window boost after a zero
  rotation still burns 5,338,379,201,831.
- Tf variants after rotation: tf5000 rotate-then-buy tail
  2,668,075,748,732 with leg 1,151,788 (new-admin buyback 7500
  leg 1,727,682); tf0 rotate-then-buy tail 5,259,040,470,738
  with leg 4,607,153 and tf0 buy-then-patched-window burn
  5,306,492,329,463.

## Limits

These are LiteSVM receipts against three program images
(original, control, candidate) at the fixture state, not
mainnet transactions; the rotation steps use the fixture admin
key as the current admin and the outsider key as the new admin
unless stated. The window-neutrality pin is measured on the
fixture buy (10^9 quote in); other input sizes move vq and
protocol by the same offsetting amounts only insofar as the
hop-1 fee split holds, which this packet does not vary. The
created-pool route and the zero-admin brick's effect on a
later rotation back are out of scope here (the brick cases
measure trades and boosts only, and no case rotates away from
a zero or unfunded admin).

Made via @slopdotcash
