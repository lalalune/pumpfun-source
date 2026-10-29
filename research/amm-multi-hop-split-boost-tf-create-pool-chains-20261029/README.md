# research: created pools cannot join multi-hop routes (6078) — create math, single-hop life, and the zero boost-window invariant

## Problem

The brief for this packet was to link a freshly `create_pool` pool as a hop of the
split×boost×tf chain (true 3 hops, `three_amm` only, final output U3) and compare
its tail output and buyback accrual with the fixture tail pool. Measurement
showed the link is impossible by program design: every hop pool's creator must
equal the pool-authority PDA for its base mint, and a payer-created pool fails
that check. This packet therefore pins the gate itself, plus the created pool's
working single-hop life, instead of inventing a working multi-hop link.

The canonical check is `programs/pump-amm/src/instructions/swap/multi_hop_swap.rs:499`
(pool creator must equal the PDA `[b"pool-authority", base_mint]` under PUMP,
else `OnlyPumpPools`). The deployed binaries' logs attribute the throw
differently per image (see Result), but the error number is 6078 on all three.

Route confirmation (from the builder itself): the fixture route and every custom
route in this packet call `three_amm` only and append no g4/g5 hop group — 3 hop
groups, final output U3, 31 metas. The custom tail route replaces only the P3
group with `[BASE3, BASE2, CTAIL, CTVB, CTVQ]` (buy indices 26–30, sell indices
16–20). This packet does not repeat 3rd #61's naming error (a "3-hop" packet
whose builder actually appended a P4 group).

## Cases

21 cases, 40 steps, 120 receipts (40 steps × 3 images), 12 parts of 10 receipts.
All cases run the same steps on the original, control (#424) and candidate
(#427) images. Family C and V run in plain mode (`no_ww`, `fund_create`);
family M runs under transfer fee 100 bps on the quote mint.

Family C — plain `create_pool` math and authorization gates (10 cases):

- `c-std`: create the standard base/quote pair, index 0, 10^12 / 10^12.
- `c-tail`: create the tail BASE3/BASE2 pair, index 0, 10^12 / 10^12.
- `c-99`: create 99 / 99 — below minimum liquidity.
- `c-100`: create 100 / 100 — exactly minimum liquidity.
- `c-fee300`: create with creator_fee_bps 300.
- `c-canedit`: create with can_edit true and fee 0.
- `c-cashback`: create with cashback true.
- `c-mayhem`: create with mayhem true (fixture global mayhem flag enabled).
- `c-dup`: create the same pool twice.
- `c-idx1`: create the tail pair with index 1 (a different PDA).

Family M — created tail against the tf100 split chain (4 cases):

- `m-anchor`: fixture mhbuy3, no create (anchor).
- `m-buy-created`: create the tail pool, then buy through the custom route
  whose tail hop is the created pool.
- `m-sell-created`: create the tail pool, then sell through the custom route
  whose first hop (sell direction) is the created pool.
- `m-anchor-after-create`: create the tail pool, then run the fixture mhbuy3
  unchanged.

Family V — created-pool single-hop life, plain mode (7 cases):

- `v-buy`: create, then buy 10^6 base out.
- `v-sell`: create, buy 10^6 base out, sell 10^6 base in.
- `v-sweep-collect`: create, buy, sell, protocol sweep, creator sweep, collect.
- `v-boost-fresh`: create, then boost 1.
- `v-boost-after-trade`: create, buy 10^9 base out, then boost 1.
- `v-dep-boost`: create, deposit 10^9 LP, then boost 1.
- `v-dep-wd`: create, deposit 10^9 LP, withdraw 10^9 LP.

## Result

All 21 cases pass on all three images with 0 divergent cases: control and
candidate agree with the original everywhere. Error sites (source line numbers)
differ per image and are recorded per image in each report row's `error_sites`,
never in the observed surfaces.

Create math (freshly measured on this harness, not copied from 2nd #45):

- 10^12 / 10^12 create (standard pair and tail pair alike): initial liquidity
  = floor(sqrt(10^12 × 10^12)) = 10^12, lp_supply 10^12, user LP 999,999,999,900
  (10^12 − 100 minimum liquidity), vaults 10^12 each, virtual_quote_reserves 0,
  creator_fee_bps 0, can_edit 0, holder 0, protocol_fees 0, creator_fees 0.
  Stored pool creator is the payer; stored coin_creator is all zeros even though
  the `coin_creator` argument was the payer. Create event: 344 bytes,
  discriminator `b1310cd2a076a774`, base_amount_in 10^12, quote_amount_in 10^12,
  pool_base_amount 10^12, pool_quote_amount 10^12, minimum_liquidity 100,
  initial_liquidity 10^12, lp_token_amount_out 999,999,999,900. Payer lamport
  delta −10,507,640 (rents + 5,000 fee).
- (99, 99) fails 6003 TooLittlePoolTokenLiquidity (`create_pool.rs:290` on the
  original, `:144` on control/candidate), 0 events, full rollback, payer −5,000.
- (100, 100) succeeds: initial liquidity 100, user LP 0 (the whole 100 is the
  minimum liquidity), vaults 100 each.
- Index-1 tail create succeeds on a different PDA with identical math.

Create authorization gates (all with full rollback, payer −5,000, 0 events):

- creator_fee_bps 300 → 6028 OnlyCanonicalPumpPoolsCanHaveCoinCreator
  (`create_pool.rs:279` original, `:133` control/candidate).
- can_edit true with fee 0 → 6028, same sites.
- cashback true → 6050 OnlyPumpPoolsCashback (`create_pool.rs:189` original,
  `:79` control/candidate).
- mayhem true → 6042 OnlyPumpPoolsMayhemMode (`create_pool.rs:177` original,
  `:74` control/candidate).
- Duplicate create of the same PDA fails with system custom error 0 at
  pool-account allocation (no PumpAmm error code, no AnchorError site line);
  the first pool is intact.
- General rule pinned: a direct create cannot store any nonzero creator field;
  canonical creator status is reachable only via the pump program's migration
  CPI, because a PDA cannot sign a direct transaction.

The multi-hop gate (the packet's central finding):

- Created-tail buy on the tf100 split chain fails 6078 OnlyPumpPools
  (original log: `trade_v2.rs:119`; control/candidate log:
  `multi_hop_swap.rs:499`), with 2 ghost hop events (hops 1 and 2 complete,
  hop 3 fails), full rollback except the payer's 5,000 fee.
- Created-tail sell on the tf100 split chain fails 6078 with 0 ghost events
  (the created tail is the first hop in sell direction), full rollback.
- The fixture tail chain after a create succeeds anchor-exactly: userquote
  −1,000,000,000, tail output U3 +5,262,910,281,902, TOKEN22 buyback
  +4,515,471, 3 hop events of 508 bytes each, payer −1,849,400 — identical to
  `m-anchor`. Creation alone does not disturb the chain.

Created-pool single-hop life (plain mode):

- Buy 10^6 base out: userquote −1,003,004, userbase +1,000,000, pool
  virtual_quote_reserves −251, protocol_fees +251, creator_fees 0, buyback
  account +250 (half of gross protocol 501 at buyback bps 5000; the pool
  protocol bucket keeps 251). Buy event 500 bytes, discriminator
  `67f4521f2cf57777`: curve 1,000,002, lp_bps 25, lp_fee 2,501, proto_bps 5,
  proto_fee 501, qwlp 1,002,503, uin 1,003,004.
- Sell 10^6 base in (min quote 1): userquote +996,999, userbase −1,000,000,
  pool virtual_quote_reserves −502, protocol_fees +502, creator_fees still 0.
  Sell event 449 bytes: curve 1,000,001, lp_fee 2,501, proto_fee 501,
  quote 997,500, uout 996,999.
- Protocol sweep discharges the full bucket (502) to the protocol ATA for the
  quote mint (per protocol+mint, not per pool); after the sweep the pool's
  virtual_quote_reserves returns to 0. Creator sweep succeeds as a silent
  no-op (bucket 0, 0 events). Collect with creator = zero pubkey succeeds as
  a silent no-op (0 → 0, 0 events). After sweep + creator sweep + collect the
  pool is exactly back at its creation state `[0, 0, 0, 10^12]`.

Boost-window invariant (answer to brief item (d)):

- Boost window = virtual_quote_reserves + protocol_fees + creator_fees.
- Fresh created pool: window 0 → boost fails 6065 PoolCannotBoost
  (`boost.rs:245` original, `boost_burn.rs:35` control/candidate).
- After a 10^9-base buy: virtual_quote_reserves −250,251 and protocol_fees
  +250,251, creator_fees 0, so the window is still exactly 0 → boost still
  fails 6065.
- After deposit: deposit is virtual-reserve-neutral on a created pool
  (10^9 base + 10^9 quote, supply 10^12 → 1,001,000,000,000, all fee/virtual
  fields unchanged) → window still 0 → boost still fails 6065.
- After sweep: sweep restores virtual_quote_reserves to 0 as the protocol
  bucket is discharged → window still 0.
- Conclusion: on a directly created pool the boost window is identically 0 and
  invariant under create, deposit, withdraw, trade, sweep and collect, because
  trade virtual drift exactly cancels protocol accrual, deposit/withdraw do not
  move virtual reserves, and creator fees can never accrue (creator_fee_bps is
  0 and cannot be set by direct create).
- Deposit + withdraw returns the pool exactly to its creation state
  (deposit event 264 bytes base 10^9 quote 10^9; withdraw event 264 bytes base
  10^9 quote 10^9).

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The fixture split chain is the 3rd #64/#71 fixture (true 3 hops, tf100 in
  family M); the created tail replaces only the P3 hop group.
- Plain-mode create cases skip the withdraw-withheld authority patch
  (`no_ww`): that patch writes the payer into the quote-mint transfer-fee
  authority slot, which is harmless in tf mode but breaks SPL mint parsing in
  plain mode.
- The packet pins behaviour; it makes no claim about source changes, builds,
  or whole-program identity. Error sites are recorded per image and are not
  compared across images.
- The brief's items (b) and (e) are answered negatively by design: there is no
  created-tail output or buyback to compare (the route fails 6078 before the
  tail hop), and there is no create → chain → sweep → collect discharge
  through the multi-hop route — the discharge shown is the created pool's
  single-hop sweep → collect.
