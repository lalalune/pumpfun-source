# research: split-chain mode toggles at true 5 hops — global flags are separate gates, toggle-back is exact, boost follows boost-enabled, claim ignores the cashback flag, sell-side gate order agrees

## Problem

The brief for this packet was to extend the #76 mode toggle findings
(global mayhem/cashback/boost toggles, toggle gates, toggle-then-trade
binding) to a true 5-hop split x boost x tf chain. As the mayhem,
cashback, and boost global flags are toggled on and off around the
chain, which legs move, which gates fire first, and does toggling
back leave any residue — at depth 5? Measurement splits the answer
six ways. Global toggles never move an unflagged chain: buy, sell,
and boost are all byte-identical with any global flag off, and
toggle-before-buy and buy-then-toggle burn identically. Global
flags are separate gates from per-pool flags: toggling the global
flag neither rescues a flagged pool nor breaks an unflagged one, at
any hop position. Toggling back is exact: after a full off→on
roundtrip of all three flags, the config bytes are exactly the
anchor values. Boost follows the boost-enabled flag alone: off →
6066, on → the identical burn. Cashback claim ignores the global
cashback flag entirely: it pays the earned amount with the flag
on, off, and back on, including after a plain-quote 5-hop buy.
The image disagreements are confined to the buy direction on
cashback-flagged hops: on a cashback-flagged P4 buy the original
passes while the rebuilds fail 6079, and on a both-flagged P4 buy
the original checks mayhem first (6080) while the rebuilds check
cashback first (6079). New at depth 5: in the sell direction the
gates agree — a cashback-flagged P5 sell and a both-flagged P5
sell both fail 6079 with 0 ghost events in all three images, so
the buy/sell gate-order asymmetry is itself a measured pin.

Route confirmation (from the builder itself): the fixture route
calls `three_amm` and appends the g4 and g5 hop groups, so the
route is main → POOL2 → P3 → P4 → P5, final output U5: TRUE 5
hops. This packet does not repeat 3rd #61's naming error (a
"3-hop" packet whose builder actually appended a P4 group).

One scope note, measured first: the fixture starts with all three
global flags on (mayhem byte 417 = 1, cashback byte 642 = 1,
boost byte 939 = 1) and all fixture pools unflagged (pool bytes
243/244 = 0). Pool flags are applied per case by patching the
pool account (byte 243 = mayhem, byte 244 = cashback); global
toggles write only the GlobalConfig flag bytes. The cashback
claim cases run in plain-quote mode with the withdraw-withheld
authority patch skipped (`no_ww`): that patch writes the payer
into the quote-mint transfer-fee authority slot, which corrupts
SPL mint parsing in plain mode (measured in #76: claim fails
`InvalidAccountData` with the patch, pays 5475 without it).
Toggle steps emit 0 events and cost exactly the 5,000 fee; the
toggle instructions carry no event account for boost and the
event/program accounts for mayhem/cashback, and no toggle writes
any pool field.

## Cases

47 cases, 107 steps, 321 receipts (107 steps × 3 images), 33 parts
of 10 receipts (32×10 + 1). All cases run the same steps on the
original, control (#424) and candidate (#427) images. All families
run under tf100 on the quote mint unless noted (family C runs in
plain-quote mode, see above).

Family A — anchors at depth 5 (4 cases):

- `A-buy5`: 5-hop buy tail 5,207,955,235,891, 5 hop events,
  buyback leg 4,515,471.
- `A-sell5`: 5-hop sell payout 178,541, 5 hop events.
- `A-buy-boost`: buy, vq patch, boost burns 5,254,679,949,141.
- `A-sell-boost`: sell, vq patch, boost burns 5,338,394,848,076.

Family T — toggle storage alone at depth 5 (10 cases):

- `T-mayhem-off`: mayhem True → False succeeds (flag byte 417
  1 → 0), then False again fails 6043 with full rollback.
- `T-mayhem-roundtrip`: False then True restores byte 417 = 1.
- `T-cb-off`: cashback True → False succeeds (byte 642
  1 → 0), then False again fails 6051 with full rollback.
- `T-cb-roundtrip`: False then True restores byte 642 = 1.
- `T-boost-same`: boost True → True succeeds — no same-state
  check on the boost toggle.
- `T-boost-off-on`: False then True, byte 939 1 → 0 → 1.
- `T-boost-off-off`: False then False again also succeeds —
  boost toggle has no same-state check in either direction.
- `T-outsider`: outsider-signed mayhem toggle fails 6005,
  payer lamports unchanged (outsider pays nothing on failure).
- `T-unsigned`: unsigned mayhem toggle fails 3010.
- `T-all-roundtrip`: mayhem off, cashback off, boost off, then
  all three back on — final config bytes exactly the anchor
  (mayhem 1, cashback 1, boost_enabled 1), all six toggles 0
  events.

Family B — toggles around the 5-hop chain (12 cases):

- `B-mayhem-off-buy` / `B-mayhem-off-sell`: global mayhem off
  leaves the buy tail (5,207,955,235,891) and sell payout
  (178,541) byte-identical.
- `B-mayhem-off-boost`: mayhem off, patched-window boost burns
  5,338,379,201,831 — the fresh-window anchor, unchanged.
- `B-cb-off-buy` / `B-cb-off-sell`: global cashback off leaves
  buy tail and sell payout byte-identical.
- `B-boost-off-buy` / `B-boost-off-sell`: boost off leaves buy
  tail and sell payout byte-identical — the boost flag gates
  only boost itself.
- `B-boost-off-boost`: boost off → boost fails 6066, 0 events,
  full rollback.
- `B-boost-off-on-boost`: off → 6066, on → boost burns
  5,338,379,201,831, the identical fresh-window anchor.
- `B-tog-before-buy-boost`: mayhem off, buy, vq patch, boost
  burns 5,254,679,949,141.
- `B-buy-tog-boost`: buy, mayhem off, vq patch, boost burns
  5,254,679,949,141 — toggle order against the buy does not
  change the burn.
- `B-cb-off-buy-boost`: cashback off, buy, vq patch, boost
  burns 5,254,679,949,141.

Family G — global toggle vs pool flag at depth 5 (12 cases):

- `G-mayhemflag-p4-buy`: mayhem-flagged P4 buy fails 6080
  (MayhemPoolNotSupported, trade_v2.rs:124) with 3 ghost events
  in all images — main, P2, P3 executed before the P4 leg.
- `G-mayhem-off-mayhemflag-p4-buy`: global mayhem off does NOT
  rescue the flagged P4 buy — still 6080, 3 ghosts, all images.
- `G-mayhem-off-on-mayhemflag-p4-buy`: off then on, still 6080,
  3 ghosts, all images.
- `G-cbflag-p4-buy` (DIVERGENT): cashback-flagged P4 buy passes
  in the original with the anchor tail 5,207,955,235,891, but
  fails 6079 with 3 ghosts in control and candidate.
- `G-cb-off-cbflag-p4-buy` (DIVERGENT): global cashback off
  changes nothing — original still passes with the anchor tail,
  rebuilds still fail 6079.
- `G-cb-off-on-cbflag-p4-buy` (DIVERGENT): off then on, same
  split — original passes, rebuilds fail 6079.
- `G-bothflag-p4-buy` (DIVERGENT): both-flagged P4 buy — original
  fails 6080 (mayhem checked first), rebuilds fail 6079
  (cashback checked first), both with 3 ghost events.
- `G-mayhem-off-bothflag-p4-buy` (DIVERGENT): global mayhem off
  does not change the split — original 6080, rebuilds 6079.
- `G-cb-off-bothflag-p4-buy` (DIVERGENT): global cashback off
  does not change the split — original 6080, rebuilds 6079.
- `G-mayhemflag-main-sell`: mayhem-flagged main sell fails 6080
  with 4 ghost events in all images — main is the last executed
  hop in the sell direction (P5 → P4 → P3 → P2 → main).
- `G-cbflag-p5-sell`: cashback-flagged P5 sell fails 6079
  (CashbackCoinNotSupported, trade_v2.rs:120) with 0 ghost events
  in ALL images — no divergence in the sell direction.
- `G-bothflag-p5-sell`: both-flagged P5 sell fails 6079 with 0
  ghost events in ALL images — the sell-side gate order agrees
  (cashback first), unlike the buy side where the original
  checks mayhem first. The direction asymmetry is measured, not
  assumed: buy-side both-flagged P4 is 6080-vs-6079, sell-side
  both-flagged P5 is 6079 everywhere.

Family C — cashback claim vs the global cashback flag (4 cases,
plain quote, `no_ww`):

- `C-cclaim-flag-on`: claim pays 5,475 (ATA −5,475, userquote
  +5,475, 1 event, cb_claimed 0 → 5,475).
- `C-cb-off-cclaim`: cashback flag off, claim still pays exactly
  5,475.
- `C-cb-off-on-cclaim`: off then on, claim still pays exactly
  5,475.
- `C-cb-off-buy-cclaim`: cashback flag off, plain-quote 5-hop
  buy tail 5,259,040,470,738, then claim still pays exactly
  5,475 — the claim reads the ATA balance, not the flag.

Family F — tf variants (5 cases):

- `F-tf5000-mayhem-off-buy`: mayhem off, tf5000 buy tail
  2,668,075,748,732, buyback leg 1,151,788.
- `F-tf5000-cb-off-buy`: cashback off, tf5000 buy tail
  2,668,075,748,732, leg 1,151,788 — identical to the mayhem-off
  case.
- `F-tf5000-boost-off-boost`: boost off under tf5000 → boost
  fails 6066.
- `F-tf0-mayhem-off-buy`: mayhem off, tf0 buy tail
  5,259,040,470,738, leg 4,607,153.
- `F-tf0-boost-off-on-boost`: off → 6066, on → boost burns
  5,391,870,655,895, the tf0 fresh-window value.

## Result

At depth 5, every #76 toggle pin holds: global toggles never move
an unflagged chain, global and pool flags are independent gates,
toggle-back is exact, boost follows boost-enabled alone, and
cashback claim ignores the global cashback flag. The gate codes
are unchanged (outsider 6005, unsigned 3010, mayhem same-state
6043, cashback same-state 6051, boost toggle with no same-state
check, boost-off 6066). The divergence set is exactly 6 cases,
all buy-direction cashback/both-flagged P4 buys: the original
passes a cashback-flagged non-terminal hop and checks mayhem
first on a both-flagged hop, while both rebuilds fail 6079 and
check cashback first. The sell direction shows no divergence at
all — including on both-flagged P5, where all images agree on
6079 — which pins the gate-order difference to the buy path
rather than to a global flag check. No other case diverges:
control and candidate agree everywhere, and the original agrees
with them in the other 41 cases.

## Limits

- Fixture pools are synthetic (proper pool data per hop, per the
  #119 build lesson: bump, pool-authority creator, own base
  mints, own vaults); hop pools share the fixture fee-table and
  GlobalConfig, so the pins are about toggle/flag interaction,
  not about per-hop fee-table variation.
- Pool flags are harness patches to pool bytes 243/244, not
  on-chain flag-setting instructions (no such instruction exists
  for these pool fields in the checked-out program); global
  toggles are real instructions.
- The mayhem program source is not in this sparse checkout, so
  the mayhem gate is pinned only through the pump-amm trade_v2
  error path (6080 at trade_v2.rs:124), not through mayhem-side
  code.
- Only the 5-hop split x boost x tf route was measured; single-hop
  and 3-hop toggle behaviour is #76's (and #128's) territory and
  is not re-asserted here beyond the anchor values.
- The rebuild images are control (#424) and candidate (#427);
  "original" is the deployed program image. Divergence means
  original-vs-rebuild, never a claim about upstream intent.

Made via @slopdotcash
