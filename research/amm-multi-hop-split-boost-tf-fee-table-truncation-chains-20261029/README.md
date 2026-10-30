# Fee-table account length / truncation on the split x boost x tf chain

## Problem

The v2 fee path prices every hop from a single `TradeFeeConfig`
account (`select_and_apply_v2`, `programs/pump-amm/src/curve/fees.rs`).
The account is 4097 bytes in the fixture, but the code reads it in
three different ways: a Borsh deserialization of the whole struct at
instruction entry, a hard `fee_config_len >= 2512` gate inside
`select_and_apply_v2`, and per-branch length checks (stable table
only if `fee_config_len >= 4073`, exotic fees only if
`fee_config_len >= 4097`). This packet pins, on the split x boost x
tf chain at true 3 hops, which of those gates is a hard failure and
which is a silent fallback, and the exact 1-byte boundary of each.

## Cases

68 cases, 219 receipts (73 steps x 3 images: original, control,
candidate), 22 parts. All cases run the same split x boost x tf
route (three_amm only, final output U3) with transfer fee on, except
where noted. The fee-config account is truncated to the stated
length before the case runs; nothing else changes.

- Family A, anchors (6): standard buy/sell (`a-buy3`, `a-sell3`),
  single-leg v2 buy/sell (`a-buy2`, `a-sell2`), stable-route
  buy/sell (`s-buy3`, `s-sell3`), all at full length.
- Family L, standard-route length ladder (20): lengths 3000, 4000,
  4072, 4073, 4074, 4096 buy and sell; 4097 buy and sell; 4098 buy;
  v2 buys at 3000, 4073, 4096 and 2511; v2 sell at 3000.
- Family S, stable-route length ladder (16): lengths 3000, 4000,
  4072, 4073, 4074, 4096 buy and sell; 4097 buy; 2511 buy; 2512 buy
  and sell.
- Family C, cut positions (22): buy at lengths 0, 41, 65, 69, 100,
  109, 469, 1069, 1073, 1500, 2073, 2080, 2096, 2097, 2511, 2512,
  2513; sell at 469, 1069, 2073, 2511, 2512.
- Family D, downstream of a truncated buy (4): truncated (3000)
  buy followed by Token-2022 protocol sweep, creator sweep and
  collect (`d-3000-swp-col`); truncated buy with a 10^9 virtual
  quote patch followed by boost (`d-3000-boost`); truncated buy
  followed by token claim (`d-3000-tclaim`); cashback claim alone
  under truncation (`d-3000-cclaim`, plain-quote mode).

## Result

All 68 cases agree across the original, control and candidate
images: 0 divergent cases. The length gates are sharp 1-byte
boundaries, not gradual degradation.

### The four gates, in length order

1. Length 0: `3001 AccountDiscriminatorNotFound` on fee_config
   (no discriminator bytes at all), 0 events.
2. Lengths 1..2096: `3003 AccountDidNotDeserialize` on
   fee_config, 0 events. The Borsh `TradeFeeConfig` struct is
   2097 bytes (41 header + 24 flat + 4 + 25x40 tier + 4 + 25x40
   stable + 24 exotic), so any shorter account fails
   deserialization before any fee logic runs.
3. Lengths 2097..2511: `6083 FeeConfigTooShort`
   (`fees.rs:184`, the `require!(fee_config_len >= 2512)` gate in
   `select_and_apply_v2`), 0 events. The struct deserializes
   but the trade is refused.
4. Length 2512 and above: trades succeed. The single-leg v2 buy
   shares the gate (2511 -> 6083, 3000/4073/4096 -> success).

### Branch thresholds above 2512

- Standard route (native-quote hop 1, exotic tail hop): every
  length 2512..4096 prices the tail hop from the flat fees
  (25, 5, 0) instead of the exotic triple. The buy tail output
  is 5,262,910,281,903 at 3000, 4000, 4072, 4073, 4074 and 4096
  alike, exactly +1 vs the exotic anchor 5,262,910,281,902
  (buyback 4,515,471 unchanged). At 4097 and 4098 the anchor is
  restored: the exotic branch requires `fee_config_len >= 4097`.
  Sells succeed at every length >= 2512 with the same user
  quote receipt (178,541).
- Stable route (USDC tail hop): lengths 2512..4072 fail `6082
  FeeTiersEmpty` (the stable tier slice is empty below 4073),
  with 2 ghost hop events on buys and 0 on sells. At 4073,
  4074, 4096 and 4097 the stable route succeeds at the anchor
  (buy 5,262,910,281,902, buyback 4,515,471). The stable
  threshold (4073) and the exotic threshold (4097) are distinct
  1-byte boundaries 24 bytes apart.
- Cut positions confirm the ladder: every buy cut at 41, 65, 69,
  100, 109, 469, 1069, 1073, 1500, 2073, 2080 and 2096 fails
  3003; 2097 and 2511 fail 6083; 2512 and 2513 succeed with
  the flat-fallback tail. Sell cuts at 469, 1069 and 2073 fail
  3003; 2511 fails 6083; 2512 succeeds.

### Truncation cannot shrink the tier table

Cutting the tier vector mid-way (469, 1069, 1073) does not
produce a shorter tier table with different tier selection:
every cut below 2097 fails at Borsh deserialization first.
There is no partial-tier pricing behaviour to pin; tier
selection is all-or-nothing through the struct boundary.

### Downstream legs are untouched by truncation

After a truncated (3000-byte) buy, every downstream leg works
at its untruncated value: Token-2022 protocol sweep 4,563,570
(net 4,517,934 to the protocol ATA), creator sweep 123,394
(net 122,160), collect 122,160 gross / 120,938 net, boost
burn 5,255,205,915,165 (vq 10^9 patch, requested = used =
1,000,000,000), token claim gross 3,334,551 / net 3,301,205,
cashback claim 5,475. Truncation gates the trade instruction
only; it does not leak into sweep, collect, boost or claim.

Note: a plain SPL-Token sweep of the main pool fails
`InvalidAccountData` in this harness at every length, including
full length, because the main quote vault is Token-2022-owned
while the sweep step passes the SPL Token program. The packet
therefore uses the Token-2022 sweep/collect legs for the
downstream case; that failure is a harness-fixture property,
not a truncation effect.

## Limits

- Only this fixture is measured: 25 tier entries, 25 stable
  entries, fixture flat fees (25, 5, 0), tf 100 bps on the quote
  mint, split x boost x tf route at true 3 hops.
- Error sites (source line numbers) differ between the original
  image and the rebuilt images (e.g. 6083 at fees.rs:184 vs
  fees.rs:83, 6082 at fees.rs:160 vs fees.rs:62); they are pinned
  per image in the report and never compared across images.
- Lengths between the probed points behave per the branch rules in
  `select_and_apply_v2`; only the probed lengths are receipted
  (the ladder covers every boundary at +-1: 2096/2097, 2511/2512,
  4072/4073, 4096/4097).

## Reproduction

`producer.py` rebuilds the packet from the three program images
in `~/workspace/slop-verify/` (original, control, candidate).
`verify.py` re-checks every receipt independently (signatures,
deltas, withheld, events, error codes, rollback, pool/UVA/config
state, 3-image agreement) from the packet files alone.

Made via @slopdotcash
