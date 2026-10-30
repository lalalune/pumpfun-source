# research: split-chain mode toggles — global flags are separate gates, toggle-back is exact, boost follows boost-enabled, claim ignores the cashback flag

## Problem

The brief for this packet was to compose the 2nd-run #28 admin mode
toggles bridge onto the split×boost×tf chain (true 3 hops,
`three_amm` only, final output U3): as the mayhem, cashback, and
boost global flags are toggled on and off around the chain, which
legs move, which gates fire first, and does toggling back leave
any residue? Measurement splits the answer five ways. Global
toggles never move an unflagged chain: buy, sell, sweep, collect,
boost, and claim are all byte-identical with any combination of
global flags off. Global flags are separate gates from per-pool
flags: toggling the global flag neither rescues a flagged pool
nor breaks an unflagged one. Toggling back is exact: after a full
off→on roundtrip of all three flags, the chain and the boost burn
are byte-identical to the anchor. Boost follows the
boost-enabled flag alone: off → 6066, on → the identical burn.
Cashback claim ignores the global cashback flag entirely: it pays
the earned amount with the flag on, off, and back on. The one
place the images disagree is gate order on flagged hops: on a
both-flagged hop the original checks mayhem first (6080) while
the rebuild checks cashback first (6079).

Route confirmation (from the builder itself): the fixture route
calls `three_amm` only and appends no g4/g5 hop group — 3 hop
groups, final output U3. This packet does not repeat 3rd #61's
naming error (a "3-hop" packet whose builder actually appended a
P4 group).

One scope note, measured first: the fixture starts with all three
global flags on (mayhem byte 417 = 1, cashback byte 642 = 1,
boost byte 939 = 1) and all fixture pools unflagged (pool bytes
243/244 = 0). Pool flags are applied per case by patching the
pool account (byte 243 = mayhem, byte 244 = cashback); global
toggles write only the GlobalConfig flag bytes. The cashback
claim cases run in plain-quote mode with the withdraw-withheld
authority patch skipped (`no_ww`): that patch writes the payer
into the quote-mint transfer-fee authority slot, which corrupts
SPL mint parsing in plain mode (measured: claim fails
`InvalidAccountData` with the patch, pays 5475 without it).

## Cases

35 cases, 80 steps, 240 receipts (80 steps × 3 images), 24 parts
of 10 receipts. All cases run the same steps on the original,
control (#424) and candidate (#427) images. All families run
under tf100 on the quote mint unless noted (family C runs in
plain-quote mode, see above).

Family T — toggle storage alone (8 cases):

- `t-mayhem-off`: mayhem True → False, then False again
  (same-state).
- `t-mayhem-roundtrip`: mayhem False, then True again.
- `t-cashback-off`: cashback True → False, then False again.
- `t-cashback-roundtrip`: cashback False, then True again.
- `t-boost-same`: boost True → True (already enabled).
- `t-boost-off-on`: boost False, then True.
- `t-boost-off-off`: boost False, then False again.
- `t-tog-outsider`: mayhem toggle signed by a non-admin, then
  with the admin account not signing.

Family M — global toggles vs the split chain (6 cases):

- `m-anchor`: mhbuy3 of 10^9, no toggle.
- `m-mayhem-off-buy`: mayhem off, then mhbuy3.
- `m-mayhem-off-sell`: mayhem off, then mhsell3 of 10^9.
- `m-cb-off-buy`: cashback off, then mhbuy3.
- `m-cb-off-sell`: cashback off, then mhsell3.
- `m-boost-off-buy`: boost off, then mhbuy3.

Family F — pool flags vs global toggles (6 cases):

- `f-cbflag-buy`: main pool cashback-flagged, mhbuy3.
- `f-cbflag-cboff-buy`: main pool cashback-flagged, global
  cashback off, mhbuy3.
- `f-cbflag-cbon-buy`: main pool cashback-flagged, global
  cashback off then on, mhbuy3.
- `f-mayhemflag-buy`: main pool mayhem-flagged, mhbuy3.
- `f-mayhemflag-moff-buy`: main pool mayhem-flagged, global
  mayhem off, mhbuy3.
- `f-bothflag-buy`: main pool both-flagged, mhbuy3.

Family P — priority across hops (4 cases):

- `p-mh1-cb2-buy`: main mayhem-flagged, pool2 cashback-flagged,
  mhbuy3.
- `p-cb1-mh2-buy`: main cashback-flagged, pool2 mayhem-flagged,
  mhbuy3.
- `p-cb1-mh2-moff`: same flags, global mayhem off, mhbuy3.
- `p-cb1-mh2-cboff`: same flags, global cashback off, mhbuy3.

Family B — boost under toggles (5 cases, main pool
virtual_quote_reserves patched to 10^9):

- `b-anchor-boost`: boost of 10^9, no toggle.
- `b-boost-off-boost`: boost off, boost, boost on, boost.
- `b-boost-off-on-boost`: boost off, boost on, boost.
- `b-mayhem-off-boost`: mayhem off, boost.
- `b-cb-off-boost`: cashback off, boost.

Family S — sweep/collect under toggles, and full roundtrip
residual (3 cases):

- `s-toggles-sweep`: mayhem off, cashback off, mhbuy3,
  protocol sweep (TOKEN22), creator sweep (TOKEN22), collect
  (TOKEN22).
- `s-roundtrip-chain`: mayhem off→on, cashback off→on, boost
  off→on, mhbuy3.
- `s-roundtrip-boost`: same roundtrip, main pool vq patched to
  10^9, boost of 10^9.

Family C — cashback claim under the global cashback toggle
(3 cases, plain-quote mode, seeded UVA earned 5475):

- `c-claim-anchor`: claim alone.
- `c-claim-cboff`: cashback off, claim.
- `c-claim-cbon`: cashback off, cashback on, claim.

## Result

All 35 cases pass on all three images with 7 divergent cases,
all the cashback-flagged non-terminal hop pattern (family F/P
below). Control and candidate agree everywhere.

### Toggle storage: same-state errors, silent boost, admin gates

- mayhem True → False rewrites GlobalConfig byte 417 (1 → 0);
  a second False → 6043 (same-state), full rollback.
- cashback True → False rewrites byte 642 (1 → 0); a second
  False → 6051 (same-state), full rollback.
- boost True → True succeeds silently with no config change,
  and boost False → False likewise: unlike mayhem/cashback,
  `toggle_boost` has no same-state check.
- Non-admin toggle → 6005; unsigned admin account → 3010;
  both with no config change. Toggles emit no event.

### Global toggles never move an unflagged chain

Anchor mhbuy3 (tf100, 10^9): userquote −10^9, tail output U3
+5,262,910,281,902, TOKEN22 buyback +4,515,471, withheld vq1
10,000,000 / buyback 45,611. Anchor mhsell3: user receipt
178,541 (gross 180,345, withheld userquote 1,804 / buyback 9),
buyback +837. Every global-toggle variant reproduces these
numbers exactly: mayhem off buy, mayhem off sell, cashback off
buy, cashback off sell, boost off buy — deltas, withheld, pool
states, and event discs/lengths are identical to the anchor in
every case. The global flags are not consulted by the split
route at all.

### Pool flags are separate gates; global toggles change nothing

- Cashback-flagged main pool, buy: original succeeds
  (anchor-identical), rebuild fails 6079 — with the global
  cashback flag on, off, and off-then-on alike. The global
  flag neither rescues the rebuild nor breaks the original.
- Mayhem-flagged main pool, buy: fails 6080 on all three
  images — with the global mayhem flag on and off alike.
  The mayhem gate is per-hop on every image and does not
  consult the global flag.
- Both-flagged main pool, buy: **divergent in gate order** —
  original fails 6080 (mayhem checked first), rebuild fails
  6079 (cashback checked first), 0 events on both. This is a
  rebuild difference in gate-check order within one hop, not a
  difference in toggle behaviour.

### Priority across hops follows hop order, not flag kind

- Mayhem hop 1 + cashback hop 2: fails 6080 on all three
  images, 0 events — the first hop's gate wins everywhere,
  and the cashback hop is never reached.
- Cashback hop 1 + mayhem hop 2: **divergent** — original
  fails 6080 with 1 ghost hop event (hop 1 succeeds on the
  original's terminal-only cashback gate, hop 2's mayhem gate
  fires), rebuild fails 6079 with 0 events (hop 1's per-hop
  cashback gate fires first). The same split holds with the
  global mayhem flag off and with the global cashback flag
  off: priority is hop order crossed with per-image gate
  placement, and global flags play no part.

### Boost follows the boost-enabled flag alone

Anchor boost (vq patched to 10^9, 10^9 requested): burn
5,338,379,201,831, vq 1,000,000,000, quote_after
123,936,690,720, base_after 668,358,016,710,914, remaining
999,000,000,000 — identical to the 3rd #75 boost anchor.

- Boost off, then boost: fails **6066** (boost disabled),
  full rollback, 0 events. Boost on again, then boost:
  succeeds with the anchor burn to the unit.
- Boost off then on, then boost: anchor burn exactly.
- Mayhem off then boost, cashback off then boost: anchor
  burn exactly. Neither flag touches the boost window or
  the burn math.

### Sweep, collect, and the full roundtrip leave no residue

Under mayhem off + cashback off, mhbuy3 then TOKEN22
protocol sweep discharges the full main-pool protocol bucket
4,563,570 (proto22 net +4,517,934, withheld 45,636), creator
sweep discharges 123,394 (creat22 +122,160), collect pays
122,160 (dest22 +120,938, withheld 1,222), and the main pool
ends at [0, 0, 0, 4194352106721] — the same discharge as the
no-toggle path in 3rd #74/#75.

After the full roundtrip (mayhem off→on, cashback off→on,
boost off→on), mhbuy3 is anchor-identical (deltas, withheld,
pool states) and the vq-patched boost burn is anchor-identical
(5,338,379,201,831). Toggling leaves no residue on the chain,
the pools, or the boost window.

### Cashback claim ignores the global cashback flag

Seeded UVA (earned 5475, uvata 5475, plain-quote mode): claim
pays exactly 5475 (userquote +5475, uvata −5475, 72-byte event
disc `e2d6f62107f293e5`, total_claimed 5475, total_earned
5475) with the global cashback flag on, off, and off-then-on
alike. The claim handler reads the UVA's earned field, not the
global flag.

### Divergence

7 divergent cases, all the cashback-flagged non-terminal hop
pattern already seen in 3rd #25/#43/#67/#71: original succeeds,
rebuild fails 6079 (`f-cbflag-buy`, `f-cbflag-cboff-buy`,
`f-cbflag-cbon-buy`); on a both-flagged hop the original fails
6080 while the rebuild fails 6079 (`f-bothflag-buy`); on a
cashback-hop-1 + mayhem-hop-2 route the original fails 6080
with 1 ghost event while the rebuild fails 6079 with 0 events
(`p-cb1-mh2-buy`, `p-cb1-mh2-moff`, `p-cb1-mh2-cboff`).
Control and candidate agree everywhere else. This is a rebuild
difference in gate placement (terminal-only vs every hop) and
in same-hop gate order, not a difference in toggle behaviour:
the toggles themselves behave identically on all three images
in every case.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The fixture split chain is the 3rd #64/#71 fixture (true 3
  hops, tf100 in families T/M/F/P/B/S); the cashback claim
  cases are plain-quote mode (see the scope note above).
- Only the true 3-hop split route is covered; 4- and 5-hop
  routes were not re-measured here, and mayhem-mode split-chain
  behaviour is not covered (mayhem source is absent from the
  sparse checkout).
- The both-flagged same-hop order observation (original 6080
  vs rebuild 6079) is a single-hop-layout observation, not a
  general precedence theorem across all hop layouts.
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
