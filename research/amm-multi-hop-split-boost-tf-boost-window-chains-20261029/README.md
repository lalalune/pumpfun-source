# research: multi-hop split x boost fee-window chains under transfer fee

## Problem

The boost gate is described by the pool's total virtual quote reserves,
the "window": `window = virtual_quote_reserves + protocol_fees +
creator_fees` (pool.rs `total_virtual_quote_reserves`). A fresh pool has
window exactly 0 (vq -125,882 + protocol 2,488 + creator 123,394), and a
boost on it fails. But the gate and the burn are two different reads:
this packet asks, on the TRUE 3-hop split x boost x tf chain (three_amm
only, final output U3 -- the route 3rd #63/#64 pinned), which input the
burn actually follows when each window component is varied alone, when
the same window sum is rebuilt from different compositions, and when
every leg that moves the window (trade, sweep, collect, deposit,
withdraw) is followed by a boost.

## Cases

61 cases, 285 receipts, 29 parts (28x10 + 5), all on the split x boost
x tf chain at TRUE 3 hops, transfer-fee override on the quote mint
(bps 0/100/5000 per case). Every case is run on three images (original,
control #424, candidate #427) and all three agree on every surface
(0 divergent cases; error sites are pinned per image, never compared
across images).

- **A (window components, single boost):** vq field ladder
  (10^6/10^8/10^9/10^10/10^12, 0, -10^9, fixture), protocol-bucket
  seeds (0/10^6/10^9/10^11/10^12), creator-bucket seeds
  (0/10^9/10^11/10^12), all at vq 10^9 unless noted.
- **F (same window sum, different compositions):** window
  1,000,125,882 built as (vq 10^9 + fixture buckets), (vq 10^9+123,394
  + creator 0), (vq 10^9+2,488 + protocol 0), (vq 10^9+125,882 + both
  buckets 0); and window 3,000,125,882 built as (vq 10^9 + both
  buckets 10^9) versus (vq 3x10^9 + fixture buckets).
- **B (window motion through legs):** buy/sell then boost, buy then
  sweep then boost, buy then sweep+collect then boost, buy then two
  boosts, two and three boosts in a row, sell then two boosts,
  deposit then boost, deposit+withdraw then boost, buy+sell then
  boost.
- **C (authority / flags):** boost authority outsider, zero, restore
  to payer; boost-enabled toggle off, off-then-on; buy-disabled
  config then boost, then re-enable then boost.
- **D (transfer fee and requested amount):** boost at tf0 / tf5000,
  requested 10^6/10^8/10^10/2x10^9/10^12, buy then boost at tf0.
- **E (failure and recovery):** boost on a fresh pool, buy, boost
  again (window invariant); base-vault-zero, quote-vault-zero,
  boost-ATA-short, boost-ATA-zero boosts; 10^12 bucket boost then
  field restore then boost; tail-pool boost before and after a buy;
  v2 buy then boost; legacy buy then boost.
- **G (vault balances at fixed window):** base vault 10^12 / 10^15,
  quote vault 10^12, all at vq 10^9.

## Result

All figures are measured on the chain above, tf100 unless noted.
Anchor: a 10^9-quote boost at fixture vaults burns
5,338,379,201,831 (used 10^9, quote-after 123,936,690,720,
base-after 668,358,016,710,914, boost ATA remaining 999,000,000,000).

- **The burn does NOT read the fee buckets.** Protocol or creator
  seeds from 0 to 10^11 leave the anchor burn byte-identical
  (5,338,379,201,831), and a 10^9 + 10^9 bucket seed on a 10^9 vq pool
  burns exactly the anchor. The buckets enter only the gate: a
  bucket at 10^12 fails the boost with 6023 Overflow and 0 events
  (protocol and creator alike), exactly the trap 3rd #99 found for
  buy/sell/sweep -- now confirmed for boost as well.
- **The burn reads the pool vq field, with slope about -42.73 per
  unit at fixture vaults.** The same window sum rebuilt from
  different compositions burns differently: 5,338,379,201,831 (vq
  10^9 + fixture buckets) vs 5,338,373,929,374 (vq 10^9+123,394 +
  creator 0) vs 5,338,379,095,522 (vq 10^9+2,488 + protocol 0) vs
  5,338,373,823,065 (vq 10^9+125,882 + both buckets 0). The
  differences are exactly -42.73 x the vq-field shift
  (123,394 -> -5,271,457; 2,488 -> -106,309; 125,882 ->
  -5,378,766). The window sum is a gate input, not the burn input.
- **A sweep is burn-neutral.** After a buy the burn is
  5,255,205,915,165, and a full protocol sweep + creator sweep +
  collect leaves it byte-identical at 5,255,205,915,165: the sweep
  moves the vq field (+4,563,570) and the quote vault (-4,563,570)
  by opposite equal amounts, so their sum -- the quantity the burn
  curve actually follows -- is unchanged. The quote-after shifts
  by exactly the sweep amount (124,922,129,638 -> 124,917,566,068
  after the protocol sweep), while base-after is unchanged.
- **Trades move the burn through the vaults.** Buy then boost:
  5,255,205,915,165 (the 3rd #99 post-buy burn, reproduced exactly).
  Sell then boost: 5,338,394,947,565. Buy+sell then boost:
  5,255,221,870,808. A fresh-pool buy leaves the window at 0
  (vq -4,686,964 + protocol 4,563,570 + creator 123,394), so the
  next boost still fails 6065 -- the window invariant of 3rd #92,
  now pinned through the boost gate itself.
- **Boost decay is about 1.56% per 10^9-quote boost:**
  5,338,379,201,831 -> 5,254,441,549,265 -> 5,172,468,136,601.
  After a buy the second boost is 5,173,214,684,656, the same
  decay rate on the drained vault.
- **The vq ladder is non-monotone.** 10^6 -> 5,381,409,217,895;
  10^8 -> 5,377,114,041,125; 10^9 -> 5,338,379,201,831; 10^10 ->
  4,979,661,866,360; 10^12 -> 593,413,700,956. vq 0 burns
  5,381,452,638,525, and a negative vq (-10^9) still burns
  5,425,226,816,983 -- the negative-window burn of 3rd #91,
  extended to the boost leg (there is no zero/negative clamp on
  the burn; only the exact-zero window sum gates with 6065).
- **The burn is linear in the base vault at fixed curve position:**
  vb1 10^12 -> 7,924,013,300; vb1 10^15 -> 7,924,013,300,677
  (1000x the vault, 1000x the burn). A 10^12 quote vault at vq
  10^9 burns 665,634,817,992.
- **Transfer-fee ladder (gross requested 10^9):** tf0 ->
  5,391,870,655,895 (the 3rd #34 0-bps figure, reproduced exactly),
  tf100 -> 5,338,379,201,831 (net 990,000,000 credited), tf5000 ->
  2,706,767,012,738 (net 500,000,000 credited). The event's `used`
  field is the gross requested amount; the net credit is what
  moves quote-after.
- **Requested-amount ladder (tf100, vq 10^9):** 10^6 ->
  5,380,970,054; 10^8 -> 537,672,386,159; 2x10^9 ->
  10,592,820,756,404; 10^10 -> 49,830,102,507,836. Requested
  10^12 uses the full 10^12, burns 598,735,502,793,632, drains
  the boost ATA to 0 remaining, and then fails 6088 with both
  events emitted (the transaction rolls back).
- **Authority and flag gates, in check order:** boost authority
  outsider or zero -> 6005 InvalidAdmin, 0 events (before the
  window check); boost-enabled off -> 6066, 0 events (the toggle
  itself is a silent 0-event setter; off-then-on restores the
  anchor burn exactly); buy-disabled config -> 6020 on boost,
  and re-enabling restores the anchor burn. Restoring the payer
  authority after a 6005 failure also restores the anchor burn.
- **Vault gates:** empty base vault -> 6001, empty quote vault ->
  6023, zero boost ATA -> 6002, all 0 events (the 3rd #98 vault
  gates, now pinned for boost). A boost ATA holding only 10^6
  spends exactly 10^6 (burn 5,380,970,054, identical to the
  requested-10^6 burn), emits both events, then fails 6088 and
  rolls back -- so 6088 means "requested exceeds the boost ATA
  balance", with the partial spend visible in the event but not
  in state.
- **Tail pool:** a tail-pool boost fails 6065 before a buy and
  still fails 6065 after a buy (the tail window invariant holds
  too). V2 and legacy buys move the main-pool burn by the same
  -15,829 (5,338,379,186,002): both drain the base vault by 10^6
  and touch no pool field.
- **Deposit/withdraw:** deposit nudges the vq field by +238
  (10^6 LP) and the burn by +10,079 (5,338,379,211,910);
  deposit+withdraw restores the anchor burn exactly
  (5,338,379,201,831, vq field 999,999,999 vs 10^9 and
  quote/base-after off by 1, a 1-unit rounding residue).
- **Recovery from the 10^12 trap:** restoring the bucket field to
  the post-setup snapshot recovers the anchor burn exactly.
  On-chain this is not an escape -- the sweep that would drain
  the bucket also fails 6023 (3rd #99) -- the restore here is a
  harness-level field reset used to prove the failure left no
  other state behind.

## Limits

- The bucket-gate boundary between 10^11 (passes) and 10^12
  (6023) is not measured; only the two endpoints are pinned.
- No closed-form burn formula is claimed: the packet pins the
  empirical slopes (vq field -42.73/unit at fixture vaults,
  linear in vb1) and the sweep-neutral sum, not a derived curve
  equation.
- The tail-pool boost is pinned only at window 0 (before/after a
  buy); a tail pool with a nonzero window is not covered.
- No plain-mint (non-transfer-fee) boost case: all boosts run
  under the transfer-fee override (bps 0/100/5000). The tf0 case
  is the no-fee limit of that override, not the SPL path.
- The 6023 bucket recovery uses a harness field restore; it does
  not demonstrate an on-chain recovery instruction.

## Reproduction

`producer.py` rebuilds the receipts (same builder that produced
them); `verify.py` re-verifies them from the packet files alone
plus the three program images (original, control #424, candidate
#427). Part files are 10 receipts each, gzip-compressed JSONL.

Made via @slopdotcash
