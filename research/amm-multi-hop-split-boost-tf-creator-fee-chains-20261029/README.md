# amm-multi-hop-split-boost-tf-creator-fee-chains-20261029

3rd-run packet #115: the split x boost x tf chain at TRUE 3 hops
(`three_amm` only, final output U3) meets creator fees.

## Problem

On a multi-hop route, which pool's `creator_fee_bps` actually charges
the creator fee, and does the fee move the next boost burn? The pool
field (pool bytes 261..269) overrides the fee-table creator bps
whenever `GlobalConfig.creator_fee_configurable` is set and the pool
value is nonzero (`curve/fees.rs`, `select_and_apply_v2`). But the
multi-hop fee gates charge the creator fee only at one hop per
direction (`instructions/swap/multi_hop_swap.rs`: buys charge creator
on the LAST hop, sells on the FIRST hop; protocol on the opposite
end, lp on the other end). This packet measures, on the real 3-hop
route main -> POOL2 -> P3, what each pool's creator fee does to the
chain tail, the fee buckets, and the following boost burn, plus the
real `update_creator_fee_config` setter, mid-walk creator-fee edits,
creator sweep/collect after a boost, and tf variants.

The real `admin_cto_pool` setter is NOT used here: it requires the
pool-authority PDA as a transaction signer, which no harness
transaction can supply, and it additionally requires
`pool.creator_fees == 0` first. Creator-fee values in this packet
are set with harness field resets (`cpatch` steps, recorded with an
empty transaction and never presented as on-chain instructions),
except for the `update_creator_fee_config` cases, which are real
instructions. The fixture pool has `creator_fee_bps` 0, so the
fee-table creator bps (5 bps on this tier) applies until patched.

## Cases

53 cases, 399 receipts (3 images x 133 steps), 40 parts of 10
receipts. All amounts are for a 10^9 quote buy / 10^9 base sell
unless noted; `tf100` unless noted.

- A anchors (5): buy, sell, boost, buy-then-boost, boost-then-buy.
- B main-pool creator-fee ladder (6): main `creator_fee_bps`
  5 / 100 / 300 / 1000 / 10000 buys, plus a P2-only 300 buy.
- C buys at a main creator fee, then a main boost (3).
- D sells at a main creator fee (3).
- E mid-walk main-pool creator-fee edits (3): buy, patch to 300,
  buy, boost; boost, patch to 300, buy, boost; 300-buy, patch to
  0 / 10000, buy, boost.
- F configurable gate and the real setter (6): main 300 with
  configurable off / on; `update_creator_fee_config` off (0, 300)
  and on (1, 10000) then a 300-buy; outsider and unsigned setter
  then a buy.
- G GlobalConfig `creator_fee` field alone (2): patched to 0 and
  to 10000, then buy-then-boost.
- H creator sweep/collect after a buy (3): 300-buy, creator sweep,
  collect, boost; 300-buy, protocol sweep, boost; 0-buy, creator
  sweep, collect, boost.
- I hop boosts after a creator-fee buy (3): P2 boost, P3 boost
  after a 300-buy; P2 boost after a 10000-buy.
- J tf variants under a creator fee (2): 300-buy at tf0 and at
  tf5000, then a main boost.
- K single-pool legs under a creator fee (2): legacy buy and v2
  buy on the main pool at 300.
- L walks under a creator fee (6): buy-sell-boost, sell-boost,
  deposit-boost, withdraw-boost, buy-buy-boost, boost-boost.
- M terminal-hop (P3) creator fee, the real lever (8): P3 300 /
  10000 buys; P3 300 / 10000 sells; P3 300 buy then P3 boost; P3
  300 buy then main boost; P3 300 with configurable off; mid-walk
  P3 patch to 300 between two buys, then a main boost.

## Result

All 53 cases agree on original, control and candidate (0 divergent
cases). The creator fee on this route is a terminal-hop fee only:

- Anchor: buy tail 5,262,910,281,902 (buyback leg 4,515,471 +
  withheld 45,611); sell payout 178,541 (leg 837); main boost burn
  5,338,379,201,831; buy-then-boost burn 5,254,679,949,141;
  boost-then-buy tail 5,139,964,404,268.
- The main pool's `creator_fee_bps` moves NOTHING on this route.
  At 5, 100, 300, 1000 and 10000, the buy tail stays
  5,262,910,281,902, the main creator bucket stays 123,394, the
  sell payout stays 178,541, and the buy-then-boost burn stays
  5,254,679,949,141. Mid-walk main-pool edits (0 -> 300 -> 10000)
  likewise leave the second-buy tail (5,072,980,706,277) and the
  second burn (5,172,933,848,347) unchanged. The P2-only patch is
  also inert (tail 5,262,910,281,902): the middle hop charges no
  creator fee in either direction.
- The terminal hop is the lever. P3 `creator_fee_bps` 300 cuts the
  buy tail to 5,113,237,807,854 (down 149,672,474,048) and fills
  the P3 creator bucket to 154,185,644,849 (from the anchor
  2,645,500,920 at the fee-table 5 bps). P3 10000 roughly halves
  the buy tail to 2,642,341,163,278 with a P3 creator bucket of
  2,649,341,750,777. On sells, P3 300 cuts the payout to 173,261
  (from 178,541) with a P3 creator bucket of 30,123,364, and P3
  10000 fails the whole sell with Overflow 6023 and full rollback
  (no deltas, no events): a 100% first-hop creator fee overflows
  the sell computation instead of paying zero.
- Configurable gate: P3 300 with `creator_fee_configurable` off
  falls back to the fee-table creator bps exactly (buy tail
  5,262,910,281,902, P3 creator bucket 2,645,500,920). The real
  `update_creator_fee_config` writes configurable/max (off:
  0/300, on: 1/10000); an outsider setter fails 6005 and an
  unsigned setter fails 3010, both with full rollback, and the
  following buy is the anchor buy.
- The GlobalConfig `creator_fee` field (313..321) alone moves
  nothing: patched to 0 or 10000, the buy tail and the
  buy-then-boost burn are anchor-identical.
- The boost burn itself does NOT read the creator fee rate: it
  reads the buckets. A P3 300 buy followed by a MAIN boost burns
  the anchor 5,254,679,949,141, because P3 fees never touch main
  buckets. But sweeping buckets after a buy DOES move the next
  main boost burn even though the VQ patch is identical (10^9 in
  all cases): creator sweep (123,394 bucket, net 122,160 after
  1,234 withheld) + collect (120,938, withheld 1,222) then boost
  burns 5,254,685,098,328 (anchor + 5,149,187);
  protocol sweep (4,517,934 of the 4,563,570 bucket, withheld
  45,636) then boost burns 5,254,870,391,988 (anchor +
  190,442,847). The cf0 sweep-collect burn equals the cf300 one,
  confirming the main-pool rate is inert here too.
- P3 boost after a P3 300 buy burns 989,635,771, which is the
  anchor P3 hop burn (989,486,889) + 148,882: the enlarged P3
  creator bucket nudges the P3 burn slightly. Hop boosts after a
  main-pool 300 buy are the anchor hop burns (P2 989,418,199,
  P3 989,486,889).
- tf variants under a main 300 fee: tf0 buy tail 5,315,084,721,958
  then boost 5,306,492,329,463; tf5000 buy tail 2,682,425,360,738
  then boost 2,685,165,599,125. The tf ordering from #106/#112
  holds; the creator fee does not change it.
- Single-pool legs DO charge the main pool creator fee, unlike
  the multi-hop route: a legacy buy at 300 pays 5,420 to the
  creator ATA (quote paid 191,550 for 10^9 base), while a v2 buy
  at 300 accrues 5,475 to the pool creator bucket (128,869 from
  123,394; quote paid 191,614). Same rate, different destination.
- Walks: sell-then-boost under main 300 burns 5,338,394,848,092
  (anchor + 15,647,261, from the sell's +847 protocol accrual);
  boost-then-boost burns 5,254,441,549,265 on the second burn.

## Limits

- Creator-fee values on multi-hop pools are harness field resets,
  not the `admin_cto_pool` setter (PDA-signer-gated, see Problem).
  The setter's own gates are therefore not measured here; only
  `update_creator_fee_config` is exercised as a real instruction.
- The "terminal hop" rule is measured on this exact route
  (main -> POOL2 -> P3, buys and sells). Other routes charge the
  creator fee at their own terminal hop by the same gate code.
- The P3 10000 sell Overflow (6023) is measured at a 10^9 base
  sell with the fixture reserves; the overflowing computation is
  not narrowed to a single arithmetic site by these receipts.
- No source change is proposed by this packet.

Made via @slopdotcash
