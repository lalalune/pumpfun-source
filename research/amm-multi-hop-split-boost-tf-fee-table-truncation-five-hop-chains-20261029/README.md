# research: split x boost x tf fee-table truncation chains at TRUE 5 hops — length gates, the 8-byte 3001/3003 boundary, flat fallback and stable 6082 all hold at depth 5, truncated buys leave downstream legs untouched

## Problem

Packet #82 pinned, at a TRUE 3-hop split chain, that the v2 fee
path prices every hop from a single `TradeFeeConfig` account
(`select_and_apply_v2`, `programs/pump-amm/src/curve/fees.rs`).
The account is 4097 bytes in the fixture, but the code reads it
in three different ways: a Borsh deserialization of the whole
struct at instruction entry, a hard `fee_config_len >= 2512` gate
inside `select_and_apply_v2`, and per-branch length checks
(stable table only if `fee_config_len >= 4073`, exotic fees only
if `fee_config_len >= 4097`). At 3 hops the gates were: length 0
-> 3001, 1..2096 -> 3003, 2097..2511 -> 6083, >= 2512 -> trades
succeed, with the exotic branch falling back to flat fees below
4097 (tail +1) and the stable branch failing 6082 below 4073 (2
ghost events on buys, 0 on sells). This packet asks whether
every one of those holds on the TRUE 5-hop split x boost x tf
chain, and adds: the ghost counts in both directions at depth 5,
single-leg v2 buys/sells under truncation, cut positions across
the whole account including the previously untested lengths 1, 7
and 8, truncated-buy downstream legs, and tf variants.

Route confirmation (from the builder itself): the fixture route
calls `three_amm` and appends the g4 and g5 hop groups, so the
route is main -> POOL2 -> P3 -> P4 -> P5, final output U5: TRUE 5
hops. This packet does not repeat 3rd #61's naming error (a
"3-hop" packet whose builder actually appended a P4 group).

## Cases

77 cases, 270 receipts (90 steps x 3 images), 27 parts of 10
receipts. All cases run the same steps on the original, control
(#424) and candidate (#427) images. All families run under tf100
on the quote mint unless noted. The fee-table account is
truncated to the stated length before the case runs (case-level
`feepatch` with `fee_len`); nothing else changes.

Family A — anchors at depth 5 (5 cases):

- `A-buy5`: 5-hop buy tail 5,207,955,235,891, 5 hop events,
  buyback leg 4,515,471.
- `A-sell5`: 5-hop sell payout 178,541, 5 hop events, leg 837.
- `A-buy-boost`: buy, vq patch, boost burns 5,254,679,949,141.
- `A-sell-boost`: sell, vq patch, boost burns 5,338,394,848,076.
- `A-buy-swp-col`: buy, protocol sweep net 4,517,934, creator
  sweep net 122,160, collect net 120,938.

Family L — standard-route length ladder at depth 5 (15 cases):

- Lengths 3000, 4000, 4072, 4073, 4074, 4096 buy and sell;
  4097 buy and sell; 4098 buy.

Family V — single-leg v2 under truncation at depth 5 (6 cases):

- v2 buys (10^6 base out) at 3000, 4073, 4096, 2511, 2512;
  v2 sell (10^6 base in) at 3000.

Family S — stable-route length ladder at depth 5 (14 cases):

- Lengths 3000, 4072, 4073, 4074, 4096 buy and sell; 4097 buy;
  2511 buy; 2512 buy and sell. The stable route replaces the
  P4/P5 hop groups with the stable pair P4S/P5S (terminal hop
  P5S has quote mint USDC, so it prices from the stable table).

Family C — cut positions across the account (28 cases):

- Buy at lengths 0, 1, 7, 8, 41, 65, 69, 100, 109, 469, 1069,
  1073, 1500, 2073, 2080, 2096, 2097, 2511, 2512, 2513.
- Sell at lengths 1, 7, 8, 469, 1069, 2073, 2511, 2512.

Family D — downstream legs after a truncated (3000-byte) buy
(4 cases):

- `D-3000-buy-swp-col`: truncated buy, protocol sweep, creator
  sweep, collect.
- `D-3000-buy-boost`: truncated buy, vq patch, boost.
- `D-3000-buy-tclaim`: truncated buy, token claim.
- `D-3000-cclaim`: cashback claim alone under truncation, in
  plain-quote mode with the withdraw-withheld authority patch
  skipped (`no_ww`) and the cashback ATA seeded with 5,475.

Family F — tf variants under truncation (5 cases):

- tf5000 buy at 3000; tf0 buy at 3000; tf5000 stable buy at
  3000; tf0 stable buy at 4073; tf5000 buy at 4097.

## Result

All 77 cases pass on all three images with 0 divergent cases:
control and candidate agree with the original everywhere. Error
sites (source line numbers) differ per image and are recorded per
image in each report row's `error_sites`, never in the observed
surfaces.

The four length gates hold at depth 5, with one boundary
sharpened. Lengths 0..7 fail 3001 AccountDiscriminatorNotFound
(0 events) in both directions — the discriminator itself is 8
bytes, so an account shorter than 8 bytes has no discriminator
at all. Lengths 8..2096 fail 3003 AccountDidNotDeserialize (0
events): the Borsh `TradeFeeConfig` struct is 2097 bytes, so any
shorter account fails deserialization before any fee logic runs.
Lengths 2097..2511 fail 6083 FeeConfigTooShort (0 events, the
`fee_config_len >= 2512` gate in `select_and_apply_v2`). Length
2512 and above: trades succeed. The sharpening vs #82 is the
3001/3003 boundary: #82 tested cuts from 41 up and reported
1..2096 -> 3003, but lengths 1 and 7 fail 3001 here, and length
8 is the first to fail 3003 — so the boundary is exactly 8
bytes, in both directions. Cutting the tier vector mid-way
(469, 1069, 1073) does not produce a shorter tier table with
different tier selection: every cut below 2097 fails at
deserialization or discriminator first. Tier selection is
all-or-nothing through the struct boundary, as at 3 hops.

Branch thresholds above 2512, at depth 5:

- Standard route (native-quote hop 1, exotic tail hop): every
  length 2512..4096 prices the tail hop from the flat fees
  (25, 5, 0) instead of the exotic triple. The buy tail output
  is 5,207,955,235,892 at 3000, 4000, 4072, 4073, 4074, 4096,
  2512 and 2513 alike, exactly +1 vs the exotic anchor
  5,207,955,235,891 (buyback 4,515,471 unchanged). At 4097 and
  4098 the anchor is restored: the exotic branch requires
  `fee_config_len >= 4097`. Sells succeed at every length >=
  2512 with the same user quote receipt (178,541).
- Stable route (USDC tail hop): lengths 2512..4072 fail 6082
  FeeTiersEmpty (the stable tier slice is empty below 4073),
  with 4 ghost hop events on buys and 0 on sells at depth 5
  (vs 2 and 0 at 3 hops: the buy executes main, P2, P3 and P4S
  before the terminal P5S fails at fee selection; the sell
  fails at its first hop). At 4073, 4074, 4096 and 4097 the
  stable route succeeds at the anchor (buy 5,207,955,235,891,
  buyback 4,515,471, sell 178,541). The stable threshold (4073)
  and the exotic threshold (4097) are distinct 1-byte
  boundaries 24 bytes apart, as at 3 hops. Length 2511 fails
  6083 on the stable route too (0 events): the 2512 gate fires
  before the branch check.
- Single-leg v2 shares the gates: v2 buy at 2511 fails 6083
  (0 events); v2 buys at 2512, 3000, 4073 and 4096 all succeed
  with identical values (10^6 base out costs 189 quote: base
  vault -1,000,000, quote vault +186, event curve 183, uin
  187); v2 sell at 3000 pays 176 quote (event quote 181, uout
  178, 2 withheld under tf100).

Truncation gates the trade instruction only. After a truncated
(3000-byte) buy, every downstream leg works at its untruncated
value: Token-2022 protocol sweep 4,563,570 (net 4,517,934 to
the protocol ATA), creator sweep 123,394 (net 122,160),
collect 122,160 gross / 120,938 net, post-buy boost burn
5,254,679,949,141 (vq 10^9 patch, requested = used =
1,000,000,000), token claim gross 3,334,551, and cashback claim
5,475 under truncation in plain-quote mode (ATA -5,475,
userquote +5,475, 1 event). Truncation does not leak into sweep,
collect, boost or claim, as at 3 hops.

Tf variants under truncation: tf5000 truncated buy tail
2,668,075,748,732 (leg 1,151,788, the tf5000 anchor); tf0
truncated buy tail 5,259,040,470,738 (leg 4,607,153, the tf0
anchor); tf5000 truncated stable buy fails 6082 with 4 ghosts;
tf0 stable buy at 4073 pays the tf0 anchor; tf5000 buy at 4097
pays the tf5000 anchor. Truncation is tf-neutral: only the
length gates move the outcome, never the tf scale.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- Only this fixture is measured: 25 tier entries, 25 stable
  entries, fixture flat fees (25, 5, 0), tf 100 bps on the quote
  mint, split x boost x tf route at true 5 hops.
- Fee-table truncation is a harness patch to the fee-table
  account (case-level `feepatch` with `fee_len`), not an
  on-chain account-resizing instruction; the `cpatch` steps in
  downstream cases are harness field resets recorded with an
  empty transaction, never presented as on-chain instructions.
- The plain-quote cashback-claim case skips the
  withdraw-withheld authority patch (`no_ww`): that patch
  writes the payer into the quote-mint transfer-fee authority
  slot, which corrupts SPL mint parsing in plain mode.
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
