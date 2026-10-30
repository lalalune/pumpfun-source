# research: boost is reserved-list-blind, but mayhem multi-hop is not — 6080 gate, reserved-leg pipes, swept-burn equality

3rd-run packet #117: the split x boost x tf chain at TRUE 3 hops
(`three_amm` only, final output U3) meets the reserved fee
recipients list. #74 pinned the setter's storage, the whitelist's
single-hop binding, the reserved list's mayhem gate on single-hop
legs, and the split chain's indifference to the list — and it
explicitly left mayhem-mode split-chain behaviour uncovered. This
packet covers what #74 did not: the boost leg itself against the
list (with the window patched open, so boosts actually burn), the
mayhem multi-hop gate, and the sweep/collect walks around a
mid-walk list rotation. It does not re-measure #74's setter
storage or chain-indifference families except as controls inside
the boost walks.

Route confirmation (from the builder itself): the fixture route
calls `three_amm` only and appends no g4/g5 hop group — 3 hop
groups, final output U3. This packet does not repeat 3rd #61's
naming error (a "3-hop" packet whose builder actually appended a
P4 group).

Scope note on the briefed name: the briefed directory
`research/amm-multi-hop-split-boost-tf-reserved-fee-chains-20261029`
is already #74's packet, so this packet pivoted to
`research/amm-multi-hop-split-boost-tf-reserved-fee-boost-chains-20261029`,
as #114 and #116 did for taken names. Nothing was overwritten.

## Problem

On the true 3-hop split x boost x tf chain, three questions are
open after #74. First, does the boost leg read the reserved list
at all — does installing, replacing, or failing to install a list
move the next boost burn? The boost instruction takes no protocol
fee recipient account, so the structural answer should be no, but
it had never been measured with an open window. Second, what does
a mayhem-flagged pool do to the multi-hop route itself — #74
measured only single-hop mayhem legs, and the multi-hop code path
is separate. Third, when a list rotation lands between a sweep and
a boost, does the swept burn change — do accrued buckets live in
the pool or in the list?

## Cases

32 cases, 342 receipts (114 steps x 3 images), 35 parts (34x10 +
2). All cases run the same steps on the original, control (#424)
and candidate (#427) images. All families run under tf100 on the
quote mint unless noted. Setter cases use recipient keys
`0x61..0x69` (R0..R8); the fixture reserved member used in family
C is the config byte range 385..417 as it stands before any
setter call (`GesfTA3X2arioaHp8bbKdjG9vJtskViWACZoYvxp4twS`); its
TOKEN22 ATA for the quote mint is
`2dmiSdVXhau9JVgrW7BFhYZCnPhDX8vKZ4Rj8vsowAb3`. The fixture
PROTOCOL account is a setter recipient where noted. Boosts use a
harness VQ patch (vq field = 10^9) to open the window; the patch
is a cpatch field reset, recorded with an empty transaction and
never presented as an on-chain instruction.

- A anchors (3): patched-window boost; buy-then-boost;
  boost on a mayhem-flagged main pool.
- B reserved rotation vs the main boost (8): setr then boost;
  boost, setr, boost; boost, replacement setr, boost; outsider
  setr then boost; unsigned setr then boost; 7-recipient setr
  then boost; duplicate-list setr then boost; unrelated-whitelist
  setr then boost.
- C mayhem legs and the mayhem multi-hop gate, then boost (8):
  mayhem legbuy with the reserved member as protocol recipient,
  then boost; mayhem legbuy with PROTOCOL as recipient, then
  boost; mayhem legsell with the reserved member, then boost;
  mayhem mhbuy3, then boost; mayhem mhsell3, then boost;
  replacement setr then mayhem legbuy with the old member, then
  boost; replacement setr (unrelated whitelist) then mayhem
  legbuy with PROTOCOL, then boost; non-mayhem legbuy with the
  reserved member, then boost.
- D sweep/collect, then rotation, then boost (5): buy, protocol
  sweep, setr, boost; buy, setr, protocol sweep, boost; buy,
  protocol sweep, collect, setr, boost; buy, protocol sweep,
  collect, replacement setr, boost; sell, protocol sweep, setr,
  boost.
- E tf variants (3): setr, buy, boost at tf5000; mayhem
  reserved legbuy, boost at tf0; setr, buy, boost at tf0.
- F hop-pool boosts vs the reserved list (5): setr then P2
  boost; replacement setr then P3 boost; P2 boost on a
  mayhem-flagged P2; buy then P2 boost; buy, setr, then P2
  boost.

## Result

All 32 cases agree on original, control and candidate (0
divergent cases). The boost leg never reads the reserved list;
the mayhem multi-hop gate is absolute.

### Anchors (family A)

- Fresh patched-window main boost burn 5,338,379,201,831
  (request 10^9, used 10^9).
- Buy-then-boost burn 5,254,679,949,141; anchor buy tail
  5,262,910,281,902 (buyback leg 4,515,471 + withheld 45,611).
- Boost on a mayhem-flagged main pool burns exactly the anchor
  5,338,379,201,831: the boost instruction does not consult the
  mayhem flag either.

### The boost burn is reserved-list-blind (family B)

- Setr writes exactly: whitelist PDA 353..385, first recipient
  385..417, remaining recipients 418..642; event 272 bytes, disc
  `2bbcfa12dd4bbb5f`, timestamp 1234567890. With whitelist =
  PAYER and recipients R0..R7, the following boost burns the
  anchor 5,338,379,201,831.
- Boost, setr, boost = 5,254,441,549,265 (the #100 second-burn
  decay value); boost, replacement setr ([PROTOCOL, R1..R7]),
  boost = the same 5,254,441,549,265. Rotation between two
  boosts changes nothing.
- Outsider setr fails 6005 (fee paid by the outsider, -5,000),
  unsigned setr fails 3010, 7-recipient setr fails 6044; each
  following boost burns the anchor 5,338,379,201,831.
- Duplicate list (all R0) succeeds with no uniqueness check and
  the following boost burns the anchor. Unrelated-whitelist
  setr (whitelist = R8) writes and the following boost burns
  the anchor: the whitelist field does not bind the boost leg.

### Mayhem legs pay the reserved member; mayhem multi-hop fails outright (family C)

- Mayhem legbuy with the fixture reserved member as protocol
  recipient succeeds: userquote -186,623, userbase +10^9,
  protocol leg +1,681 net into the reserved member's TOKEN22
  ATA (gross 1,698, withheld 17), creator +542, withheld vq1
  1,844. The following boost burns 5,338,363,478,447 (anchor -
  15,723,384): the leg moves the burn only through its own
  vq/bucket change, not through the list.
- Mayhem legbuy with PROTOCOL as recipient (no setter) fails
  6013 InvalidProtocolFeeRecipient, full rollback; the
  following boost burns the anchor.
- Mayhem legsell with the reserved member succeeds: userquote
  +178,409, protocol leg +1,681 net to the reserved member's
  ATA; the following boost burns 5,338,394,922,055 (anchor +
  15,720,224).
- Mayhem multi-hop buy fails 6080 MayhemPoolNotSupported
  (`multi_hop_swap.rs:504`, `require!(!h.pool.is_mayhem_mode)`)
  at hop 1 with 0 events; mayhem multi-hop sell fails 6080 at
  the terminal hop with 2 ghost hop events (the P3 and P2 legs
  emit before the main-pool leg rejects). The gate is 6080 on
  all three images — a pinned gate, not a divergence. The
  following boost in both cases burns the anchor.
  This is the mayhem split-chain behaviour #74 left uncovered:
  the route does not consult the reserved list, it refuses
  mayhem pools entirely, and the refusal point depends on
  direction (buy: first hop; sell: last hop).
- Replacement setr ([PROTOCOL, R1..R7]) then a mayhem legbuy
  with the old member fails 6013: replacement, not append —
  the old member is immediately invalidated, and the following
  boost burns the anchor.
- Replacement setr with an unrelated whitelist (the #74
  masking note: a PAYER whitelist plus the standard remaining
  layout fires the 6053 whitelist trap before the mayhem gate,
  so this case uses an unrelated whitelist) then a mayhem
  legbuy with PROTOCOL succeeds: protocol leg +1,681 net to
  PROTO22 (withheld 17), boost 5,338,363,478,447 — identical
  to the reserved-member leg then boost, as the economics are
  the same and only the recipient account differs.
- Non-mayhem legbuy with the reserved member fails 6013: off
  mayhem, the recipient must be in the protocol_fee_recipients
  list, and the reserved member is not. The following boost
  burns the anchor.

### Sweep/collect vs rotation (family D)

- Protocol sweep after a buy discharges the full main-pool
  protocol bucket 4,563,570 to PROTO22 (+4,517,934 net,
  withheld 45,636). Sweep-then-setr-then-boost and
  setr-then-sweep-then-boost both burn 5,254,870,391,988:
  accrued buckets live in the pool, not in the list, and the
  setter's position relative to the sweep is irrelevant.
- Collect after a protocol-only sweep is a 0-event no-op
  (collect discharges the creator vault ATA, which only a
  creator sweep fills), and boost after sweep, collect, setr
  or replacement setr is still 5,254,870,391,988.
- Sell, protocol sweep (bucket 3,335 -> PROTO22 +3,301 net,
  withheld 34), setr, boost = 5,338,394,990,593 (the post-sell
  swept burn).

### Tf variants (family E)

- tf5000 setr-buy-boost: tail 2,682,425,360,738, boost
  2,685,165,599,125 — the #106/#112 tf5000 anchors, unchanged
  by the preceding setter.
- tf0 mayhem reserved legbuy: userquote -184,779, protocol
  leg 1,698 gross to the reserved member's ATA with no
  withholding; boost 5,391,854,775,591.
- tf0 setr-buy-boost: tail 5,315,084,721,958, boost
  5,306,492,329,463 — the #115 tf0 anchors, unchanged by the
  preceding setter.

### Hop-pool boosts are reserved-list-blind (family F)

- P2 boost after setr = 999,997,999; P3 boost after
  replacement setr = 999,997,999; P2 boost on a
  mayhem-flagged P2 = 999,997,999.
- P2 boost after a buy = 989,418,199, with and without a
  mid-walk setter: the setter does not move even the post-buy
  hop burn.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The fixture split chain is the 3rd #64/#71 fixture (true 3
  hops, tf100); the reserved/boost results are pinned for
  that fixture state, not claimed for other pool states.
- The mayhem multi-hop gate (6080) is measured with the main
  pool flagged mayhem and with P2 flagged mayhem for the hop
  boost only; a mayhem-flagged P3 inside a multi-hop route
  was not measured (the route rejects at the first mayhem
  hop it reaches, so a P3-mayhem buy would fail at hop 3
  with 2 ghost events by the same mechanism — stated as
  mechanism, not measured).
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
