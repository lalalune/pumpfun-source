# research: split x boost x tf reserved-fee-boost chains at TRUE 5 hops

## Problem

Packet #117 showed, at a TRUE 3-hop route, that the boost leg is
reserved-list-blind, that the mayhem multi-hop gate fails 6080 at the
first mayhem hop in buy order and the last in sell order, that a
replacement setter invalidates the old reserved member immediately,
and that sweep position versus the setter does not change the boost
burn. This packet extends every one of those measurements to a TRUE
5-hop route (main -> POOL2 -> P3 -> P4 -> P5, final output U5): does
reserved-list blindness survive at depth 5 for the main boost and for
the P4/P5 hop boosts, does the 6080 gate still fire at the first
mayhem hop in execution order with a ghost-count ladder of 0-4, do
mayhem single-hop legs still pay the reserved member, does replacement
still invalidate immediately, and does sweep/collect position versus
the setter still not matter?

## Cases

39 cases, 408 receipts, 41 parts (40x10 + 8), across original, control
and candidate images. Successful 5-hop swaps emit exactly 5 hop
events; failed chains emit only the ghosts before the rejecting hop.

- A (4 anchors): patched-window main boost; 5-hop buy then boost;
  5-hop sell then boost; boost on a mayhem-flagged main pool.
- B (8): setr then boost; boost, setr, boost; boost, replacement
  setr, boost; outsider setr (6005) then boost; unsigned setr (3010)
  then boost; 7-recipient setr (6044) then boost; duplicate-list setr
  then boost; unrelated-whitelist setr then boost.
- C (11): mayhem legbuy with the fixture reserved member then boost;
  mayhem legbuy with PROTOCOL then boost (6013); mayhem legsell with
  the reserved member then boost; mayhem 5-hop buy with main mayhem
  (6080, 0 ghosts); mayhem 5-hop sell with main mayhem (6080, 4
  ghosts); mayhem 5-hop buy with P4 mayhem (6080, 3 ghosts); mayhem
  5-hop sell with P5 mayhem (6080, 0 ghosts); mayhem 5-hop buy with P5
  mayhem (6080, 4 ghosts); replacement setr then mayhem legbuy with
  the old member (6013); replacement setr on an unrelated whitelist
  then mayhem legbuy with PROTOCOL (succeeds); non-mayhem legbuy with
  the reserved member (6013).
- D (5): buy, protocol sweep, setr, boost; buy, setr, protocol sweep,
  boost; buy, sweep, collect, setr, boost; buy, sweep, collect,
  replacement setr, boost; sell, sweep, setr, boost.
- E (3): setr, buy, boost at tf5000; mayhem reserved legbuy, boost at
  tf0; setr, buy, boost at tf0.
- F (8): setr then P4 boost; replacement setr then P5 boost; P4 boost
  on a mayhem-flagged P4; 5-hop buy then P4 boost; 5-hop buy, setr,
  then P4 boost; 5-hop buy then P5 boost; setr then P5 boost; 5-hop
  buy, setr, then P5 boost.

## Result

0 divergent cases: original, control and candidate agree on every
case. All numbers below are measured on all three images.

- Anchors: patched-window main boost burn 5,338,379,201,831; 5-hop
  buy tail U5 5,207,955,235,891, buy-then-boost burn
  5,254,679,949,141; 5-hop sell payout 178,541, sell-then-boost burn
  5,338,394,848,076; boost on a mayhem-flagged main pool is the
  anchor burn 5,338,379,201,831.
- Reserved-list blindness at depth 5: boost after any setr (fixture
  list, duplicate list, unrelated whitelist, or a failed setter) is
  the anchor burn 5,338,379,201,831; boost, setr, boost and boost,
  replacement, boost both give the second-burn decay value
  5,254,441,549,265. The setter writes the whitelist PDA, the first
  recipient and the other seven, with a 272-byte event
  (disc 2bbcfa12dd4bbb5f). Outsider setter fails 6005 (outsider pays
  -5,000 lamports), unsigned 3010, 7-recipient 6044. Replacement
  installs PROTOCOL as the first recipient.
- Mayhem gate at depth 5: 6080 fires at the first mayhem hop in
  execution order, with a ghost ladder that counts the hops before
  it: buy with main mayhem 0 ghosts, P4 mayhem 3 ghosts, P5 mayhem 4
  ghosts; sell with P5 mayhem 0 ghosts, main mayhem 4 ghosts. The
  following boost is the anchor burn in every failed-chain case.
- Mayhem single-hop legs at depth 5: legbuy with the fixture reserved
  member costs 186,623, pays the protocol leg 1,681 net to the
  reserved member's TOKEN22 ATA (gross 1,698, withheld 17) and the
  creator 542; the following boost is 5,338,363,478,447 (anchor
  -15,723,384). Legsell with the reserved member pays 178,409 plus
  the protocol leg 1,681; the following boost is 5,338,394,922,055
  (anchor +15,720,224). Legbuy with PROTOCOL and no setter fails
  6013; a non-mayhem legbuy with a reserved recipient fails 6013.
- Replacement invalidation at depth 5: after a replacement setter
  installs PROTOCOL, a mayhem legbuy with the old reserved member
  fails 6013. A replacement on an unrelated whitelist that installs
  PROTOCOL lets the PROTOCOL leg succeed (1,681 net to PROTO22) and
  the following boost equals the reserved-member leg then boost
  (5,338,363,478,447).
- Sweep/collect position versus the setter at depth 5: the protocol
  sweep after a 5-hop buy discharges 4,563,570 (net 4,517,934,
  withheld 45,636). Sweep-then-setr-boost and setr-then-sweep-boost
  both burn 5,254,870,391,988; adding collect, and adding a
  replacement setter, leaves that burn unchanged. Sell, sweep (3,301
  net, withheld 34), setr, boost burns 5,338,394,990,577
  (16 below the #117 3-hop value 5,338,394,990,593: the 5-hop sell
  leaves the vault quote balance 16 lower at boost time).
- tf variants: tf5000 setr-buy-boost tail 2,668,075,748,732 and boost
  2,685,165,599,125; tf0 setr-buy-boost tail 5,259,040,470,738 and
  boost 5,306,492,329,463; tf0 mayhem reserved legbuy costs 184,779
  with a 1,698 gross protocol leg and no withholding, then boost
  5,391,854,775,591.
- Hop-pool boosts at depth 5 are reserved-list-blind: P4 and P5
  boosts after any setr, after a replacement, or on a mayhem-flagged
  hop pool burn the fresh hop value 999,997,999. After a 5-hop buy,
  the P4 hop boost burns 989,528,958 and the P5 hop boost burns
  989,596,358, with or without a mid-walk setter.

## Limits

- The route is a fixture route built by three_amm plus the g4/g5 hop
  groups with fixture pools; hop pools carry proper pool data (bump,
  pool-authority creator, their base mints, their vaults). Results
  are measured on the three images under this harness, not on
  mainnet, and say nothing about pools or fee configurations outside
  the fixture.
- No source change is proposed. No claim is made about the whole
  program beyond the measured cases.

Made via @slopdotcash
