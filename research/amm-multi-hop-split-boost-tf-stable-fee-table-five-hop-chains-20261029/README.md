# research: split x boost x tf stable fee-table chains at TRUE 5 hops

## Problem

Packet #81 pinned, at a TRUE 3-hop split chain, the stable tier
table itself: a real STABLE_QUOTE (USDC) hop prices from the
stable tier table, the stable count-0 misparse (the exotic triple
deserializes from the first stable tier slot), the count-1
misparse (the exotic triple deserializes from the second stable
tier slot and fails 6024), the stable branch's 6082 gate under
truncation, and the stable table's inertness without a stable
hop. This packet asks whether every one of those holds on the
TRUE 5-hop split x boost x tf chain, where the stable hop is the
terminal hop. Measurement says yes, with the ghost counts scaled
to depth 5: the stable buy pays exactly the standard anchor tail
(because the fixture stable tier-24 fees (20, 5, 5) match the
exotic fixture triple), stable tier edits move only the terminal
hop, the cap crossing reproduces between two stable buys, the
count-0 and count-1 misparse equivalences are exact, and the
stable branch fails 6082 with 4 ghost events on buys and 0 on
sells. Stable edits never move the main post-buy boost burn, and
the stable table is inert on the standard route.

Route confirmation (from the builder itself): the standard route
calls `three_amm` and appends the g4 and g5 hop groups, final
output U5: TRUE 5 hops. The stable route replaces the P4/P5
groups with P4S (base USDC, quote BASE3, canonical creator
C_USDC) and P5S (base BASE5, quote USDC, canonical creator C5),
so the buy runs main -> P2 -> P3 -> P4S -> P5S and the sell runs
the reverse, final output U5 in both directions. The terminal hop
P5S has quote mint USDC, so it prices from the stable tier table;
the P4S hop has quote mint BASE3, so it prices from the exotic
flat fees (fixture (20, 5, 5), unchanged in every stable case).
Successful swaps emit 5 hop events. This packet does not repeat
3rd #61's naming error (a "3-hop" packet whose builder actually
appended a P4 group).

## Cases

38 cases, 186 receipts (62 steps x 3 images), 19 parts of 10
receipts (18x10 + 6). All cases run the same steps on the
original, control (#424) and candidate (#427) images. All
families run under tf100 on the quote mint unless noted. The
fixture fee table: flat (25, 5, 0), tier count 25, stable count
25, stable[0] = (0, (2, 93, 30)), stable[1] = (59000000000,
(20, 5, 95)), stable[5] = (900000000000, (20, 5, 75)), stable[23]
= (19000000000000, (20, 5, 8)), stable[24] = (20000000000000,
(20, 5, 5)), exotic (20, 5, 5).

Family A — anchors at depth 5 (5 cases):

- `A-buy5`: 5-hop buy tail 5,207,955,235,891, 5 hop events,
  buyback leg 4,515,471.
- `A-sell5`: 5-hop sell payout 178,541, 5 hop events, leg 837.
- `A-buy-boost`: buy, vq patch, boost burns 5,254,679,949,141.
- `A-sell-boost`: sell, vq patch, boost burns 5,338,394,848,076.
- `A-buy-swp-col`: buy, protocol sweep net 4,517,934, creator
  sweep net 122,160, collect net 120,938.

Family S — the stable route at depth 5 (13 cases):

- `S-stbuy5` / `S-stsell5`: the stable route at fixture tables.
- `S-stbuy-boost`: stable buy, vq patch, main boost.
- `S-t0-buy` / `S-t0-sell`: stable thresholds 1..24 set to
  10^16, so the cap is below every threshold and tier 0 is
  selected.
- `S-t5-buy`: stable thresholds 6..24 set to 10^16, so the last
  met threshold is tier 5.
- `S-t24c99-buy` / `S-t24c99-sell`: stable[24] creator bps
  5 -> 99.
- `S-cross-buy`: two consecutive stable buys with stable[24]
  threshold set to 1,007,000,000,000,000 and creator bps 99, so
  the cap crosses the planted threshold between the buys.
- `S-count0-stbuy` / `S-count0-stsell`: stable route with
  stable count 0.
- `S-trunc-stbuy` / `S-trunc-stsell`: stable route with the
  fee-table account truncated to 3000 bytes.

Family M — stable-count misparses on the standard route (8 cases):

- `M-count0-buy` / `M-count0-sell`: standard route with stable
  count 0 (the #80/#134 observation reproduced at depth 5).
- `M-misparse-a-buy`: stable[0] = (0, (7, 11, 13)) with stable
  count 0, against `M-exo007-buy` (direct exotic (0, 0, 7)).
- `M-misparse-b-buy`: stable[0] threshold 2^64+3, lp 40, with
  stable count 0, against `M-exo3140-buy` (direct exotic
  (3, 1, 40)).
- `M-count1-buy`: standard route with stable count 1, against
  `M-exo59e-buy` (direct exotic (59000000000, 0, 20)).

Family E — stable table inert without a stable hop (2 cases):

- `E-stable-buy` / `E-stable-sell`: standard route with
  stable[24] creator bps 5 -> 99.

Family O — stable-edit ordering (4 cases):

- `O-stbuy-stedit-stbuy`: stable buy, stable[24] creator-99
  edit, second stable buy.
- `O-stedit-stbuy-steditback-stbuy`: stable[24] creator-99
  edit, stable buy, restore to creator 5, second stable buy.
- `O-stbuy-stedit-boost` / `O-stedit-stbuy-boost`: stable buy
  and stable edit in both orders around the main post-buy
  boost.

Family D — downstream legs after a stable buy (2 cases):

- `D-stbuy-tclaim`: stable buy, then token claim (seeded UVA).
- `D-stbuy-depwd`: stable buy, then main-pool deposit and
  withdraw.

Family F — tf variants (4 cases):

- `F-tf5000-stbuy` / `F-tf0-stbuy`: stable buy under tf5000
  and tf0.
- `F-tf5000-count0-buy` / `F-tf0-count0-buy`: standard route
  with stable count 0 under tf5000 and tf0.

## Result

All 38 cases pass on all three images with 0 divergent cases:
control and candidate agree with the original everywhere. Error
sites (source line numbers) differ per image and are recorded per
image in each report row's `error_sites`, never in the observed
surfaces.

The stable hop prices from the stable tier table at depth 5, and
only the terminal hop moves:

- Stable-route buy tail 5,207,955,235,891, buyback leg
  4,515,471, 5 hop events — exactly the standard anchor, because
  the fixture stable tier-24 fees (20, 5, 5) equal the exotic
  fixture triple (20, 5, 5). The P5S creator bucket after the
  buy is 2,617,733,408; the main pool state after the stable buy
  is byte-identical to the standard buy (vq -4,686,964,
  protocol 4,563,570, creator 123,394). Stable-route sell payout
  178,541, leg 837 — again the standard anchor.
- Tier 0 (thresholds 1..24 at 10^16): buy tail 5,204,340,208,094,
  sell payout 178,415. Tier 5 (thresholds 6..24 at 10^16): buy
  tail 5,172,029,394,614 (tier-5 fees (20, 5, 75)). Tier-24
  creator 99: buy tail 5,159,825,795,151 (P5S creator bucket
  51,347,341,460), sell payout 176,858 — the sell value is
  exactly #81's 3-hop stable-creator-99 sell value.
- Cap crossing: with stable[24] threshold planted at
  1,007,000,000,000,000, the first stable buy pays
  5,206,405,323,492 (tier 23, fees (20, 5, 8)) and the second
  pays 4,872,641,652,554 (tier 24 with creator 99). The tier
  change is a cap crossing between the buys, not a table edit
  between steps.

The stable branch gates at depth 5:

- Stable count 0 on the stable route fails 6082 (FeeTiersEmpty)
  with 4 ghost events on buys (main, P2, P3, P4S execute, the
  terminal P5S hop fails at fee selection) and 0 ghost events
  on sells (the stable hop is first for sells and fails before
  any hop event). The 3000-byte truncation fails identically
  (6082, 4 ghosts buy / 0 ghosts sell): the stable branch
  requires fee-table length >= 4073, else the stable tier list
  is empty.
- On the standard route, stable count 0 moves the buy tail to
  5,219,868,625,118 and the sell payout to 178,953 (the #134
  values, reproduced) — only the terminal hop moves, because
  only the terminal hop prices from exotic.

The count-0 and count-1 misparse equivalences are exact at
depth 5:

- Count-0 misparse-a (stable[0] = (0, (7, 11, 13)), count 0)
  gives tail 5,217,274,123,700, exactly equal to direct exotic
  (0, 0, 7). The count-0 exotic triple is (threshold low 8
  bytes, threshold high 8 bytes, stable tier-0 lp bps) =
  (0, 0, 7).
- Count-0 misparse-b (stable[0] threshold 2^64+3, lp 40,
  count 0) gives tail 5,198,669,578,781, exactly equal to direct
  exotic (3, 1, 40). The threshold's low/high halves land in
  the exotic triple's first two slots, and the tier-0 lp bps
  lands in the third.
- Count 1 and direct exotic (59000000000, 0, 20) both fail
  6024 (Truncation) with 1 ghost event and full rollback. With
  count 1 the exotic triple deserializes from the second stable
  tier slot — (59,000,000,000, 0, 20) — and that triple's lp
  value is far outside the valid bps range, so the misparse
  surfaces as a rejection rather than a moved tail. The
  equivalence is exact (same code, same event count, same
  rolled-back state), and the 1-ghost count is the same as at
  3 hops; the failure's hop position is not separately
  isolated in this packet.

Without a stable hop, the stable table is inert at depth 5:
stable[24] creator-99 edits leave the standard buy tail
(5,207,955,235,891) and sell payout (178,541) byte-identical.

Stable edits never move the main post-buy boost burn: stable
buy then tier-24-c99 edit then patched-window boost burns
5,254,679,949,141, and edit-then-buy-then-boost burns the same
5,254,679,949,141 — the standard post-buy burn. Ordering pins:
stable buy then edit then second stable buy pays
4,872,626,491,334 on moved pools; edit-then-buy pays
5,159,825,795,151, then restore-then-buy pays 4,918,564,277,184
on moved pools.

Downstream legs after a stable buy: token claim pays the full
3,334,551; main-pool deposit quote -29,846 and withdraw
+29,250.

Tf variants: tf5000 stable buy tail 2,668,075,748,732 (leg
1,151,788) and tf0 stable buy tail 5,259,040,470,738 (leg
4,607,153) — the standard tf anchors, so the stable hop is
tf-neutral in the same way. Count-0 misparse moves the tf tails
to 2,674,194,688,772 (tf5000) and 5,271,070,100,122 (tf0).

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The stable route is synthetic: the USDC mint, P4S/P5S pools
  and their vaults are fixture accounts (10^15 each), funded
  like #81's P2S/P3S; hop pools share the fixture fee-table and
  GlobalConfig, so the pins are about stable-table interaction,
  not about per-hop fee-table variation.
- Fee-table edits are harness patches (`feepatch` at case setup
  and `cpatch` "feetier" steps), recorded as such, never
  presented as on-chain instructions.
- The 6024 failure's hop position is not separately isolated:
  the packet reports the code, the 1-ghost event count, and the
  exact equivalence with the direct exotic triple, and does not
  claim which hop raises it.
- Only the tf100 quote-mint config is used for the stable
  route except where a case states tf5000/tf0; the stable hop's
  own quote mint (USDC) carries no transfer fee in any case.
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
