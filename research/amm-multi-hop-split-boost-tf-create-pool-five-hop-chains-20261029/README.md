# research: created pools cannot join 5-hop routes either — unpatched 6078, creator-patched PrivilegeEscalation, at middle and terminal hops

## Problem

The brief for this packet was to extend the #72 create_pool findings
(multi-hop entry requires creator == pool-authority PDA else 6078,
direct create cannot store a nonzero creator field, create gates)
from the true 3-hop split chain to the true 5-hop split x boost x
tf chain, and to answer the question #72 left open: does patching
a created pool's stored creator field to the pool-authority PDA
rescue the route? Measurement shows it does not — the patch passes
the 6078 gate but breaks the next leg's vault authority, because
the multi-hop program derives each leg's vault signer from the
stored creator field (`pool_seed_parts`, multi_hop_swap.rs:137-145,
applied at :440). A directly created pool is therefore unroutable
at depth 5 in every position and in both directions: unpatched it
fails the canonical-creator gate at its own hop, patched it fails
vault-authority derivation at the next vault pull. The two
requirements are jointly unsatisfiable for a direct create.

Route confirmation (from the builder itself): the fixture route
and every custom route in this packet call `three_amm` and append
the g4 and g5 hop groups — 5 hop groups, final output U5. The
custom middle routes replace only the P3 group with
`[BASE3, BASE2, CTAIL, CTVB, CTVQ]` (buy_c / sell_c) and the
custom terminal routes replace only the P5 group with
`[BASE5, BASE4, CTAIL5, CT5VB, CT5VQ]` (buy_t / sell_t), in both
cases by pool-key search over the fixture metas, so the hop count
stays 5 in every custom route. This packet does not repeat 3rd
#61's naming error (a "3-hop" packet whose builder actually
appended a P4 group).

## Cases

35 cases, 72 steps, 216 receipts (72 steps x 3 images), 22 parts
of 10 receipts (21x10 + 6). All cases run the same steps on the
original, control (#424) and candidate (#427) images. Families C
and V run in plain mode (`no_ww`, `fund_create`); families R and
F run under transfer fee on the quote mint.

Family C — create gates at depth 5, plain mode (12 cases):

- `C-create-std`: create the standard base/quote pair, index 0,
  10^12 / 10^12.
- `C-create-tail`: create the tail BASE3/BASE2 pair, index 0,
  10^12 / 10^12.
- `C-create-tail1`: create the tail pair with index 1 (a
  different PDA).
- `C-create-99`: create 99 / 99 — below minimum liquidity.
- `C-create-100`: create 100 / 100 — exactly minimum liquidity.
- `C-create-fee300`: create with creator_fee_bps 300.
- `C-create-canedit`: create with can_edit true and fee 0.
- `C-create-cashback`: create with cashback true.
- `C-create-mayhem`: create with mayhem true (fixture global
  mayhem flag enabled).
- `C-create-twice`: create the same pool twice.
- `C-create-disable`: create with the disable-create bit set.
- `C-create-tf`: create under a tf100 quote mint.

Family R — created pool in the true 5-hop route, tf100 (12 cases):

- `R-anchor-mhbuy5`: fixture mhbuy5, no create (anchor).
- `R-buy5c-unpatched`: create the tail pool, then buy through
  the custom route whose middle (P3) hop is the created pool.
- `R-sell5c-unpatched`: create the tail pool, then sell through
  the custom route whose middle hop is the created pool.
- `R-buy5c-coinfee`: create the tail pool, set its coin_creator
  to the payer and its creator_fee_bps to 300, then buy through
  the middle-hop custom route.
- `R-buy5c-vq`: create the tail pool, set its virtual_quote_
  reserves to 10^9, then buy through the middle-hop custom route.
- `R-buy5c-patched`: create the tail pool, patch its stored
  creator to the pool-authority PDA for BASE3, then buy through
  the middle-hop custom route.
- `R-sell5c-patched`: same patch, sell direction.
- `R-buy5t-unpatched`: create the terminal BASE5/BASE4 pool,
  then buy through the custom route whose terminal (P5) hop is
  the created pool.
- `R-sell5t-unpatched`: same, sell direction.
- `R-buy5t-patched`: create the terminal pool, patch its stored
  creator to the pool-authority PDA for BASE5, then buy through
  the terminal-hop custom route.
- `R-sell5t-patched`: same patch, sell direction.
- `R-anchor-after-create`: create the tail pool, then run the
  fixture mhbuy5 unchanged.

Family V — created-pool single-hop life, plain mode (8 cases):

- `V-buy2c`: create, then buy_v2 10^6 base out.
- `V-sell2c`: create, buy_v2 10^6 base out, sell_v2 10^6 base in.
- `V-sweep`: create, buy_v2, sell_v2, protocol sweep.
- `V-boost-fresh`: create, then boost 10^9.
- `V-boost-after-trade`: create, buy_v2 10^9 base out, then
  boost 10^9.
- `V-boost-vq-tf`: create, patch virtual_quote_reserves to
  10^9, bolt a tf100 transfer-fee extension onto the quote mint,
  convert the created quote vault to Token-2022 form, then
  boost 10^9.
- `V-dep-wd`: create, deposit 10^9 / 10^9, withdraw 10^9 LP.
- `V-dep-boost`: create, deposit 10^9 / 10^9, then boost 10^9.

Family F — tf variants (3 cases):

- `F-create-tf5000`: create under a tf5000 quote mint.
- `F-buy5c-tf5000`: create the tail pool, then buy through the
  middle-hop custom route under tf5000.
- `F-sell5c-tf5000`: same, sell direction.

## Result

All 35 cases pass on all three images with 0 divergent cases:
control and candidate agree with the original everywhere. Error
sites (source line numbers) differ per image and are recorded per
image in each report row's `error_sites`, never in the observed
surfaces.

Create math (freshly measured on this harness, matching #72):

- 10^12 / 10^12 create (standard, tail, and index-1 tail alike):
  initial liquidity = floor(sqrt(10^12 x 10^12)) = 10^12,
  lp_supply 10^12, user LP 999,999,999,900 (10^12 - 100 minimum
  liquidity), vaults 10^12 each, virtual_quote_reserves 0,
  creator_fee_bps 0, can_edit 0, holder 0, protocol_fees 0,
  creator_fees 0. Stored pool creator is the payer; stored
  coin_creator is all zeros even though the `coin_creator`
  argument was the payer. Create event: 344 bytes, discriminator
  `b1310cd2a076a774`, base_amount_in 10^12, quote_amount_in
  10^12, pool_base_amount 10^12, pool_quote_amount 10^12,
  minimum_liquidity 100, initial_liquidity 10^12,
  lp_token_amount_out 999,999,999,900. Payer lamport delta
  -10,507,640 (rents + 5,000 fee).
- (100, 100) succeeds: initial liquidity 100, user LP 0 (the
  whole 100 is the minimum liquidity), vaults 100 each.

Create authorization gates (all with full rollback, payer -5,000,
0 events):

- (99, 99) fails 6003 TooLittlePoolTokenLiquidity.
- creator_fee_bps 300 -> 6028
  OnlyCanonicalPumpPoolsCanHaveCoinCreator.
- can_edit true with fee 0 -> 6028, same gate.
- cashback true -> 6050 OnlyPumpPoolsCashback.
- mayhem true -> 6042 OnlyPumpPoolsMayhemMode.
- Duplicate create of the same PDA fails with system custom
  error 0 at pool-account allocation (no PumpAmm error code, no
  AnchorError site line); the first pool is intact.
- Disable-create bit set -> 6017.
- Create under a transfer-fee quote mint fails
  IncorrectProgramId, at bps 100 and at bps 5000 alike.

The 5-hop anchor and the created pool's shadow over it:

- Fixture mhbuy5: userquote -1,000,000,000, tail output U5
  +5,207,955,235,891, TOKEN22 buyback leg +4,515,471, hop-1
  credit +985,438,918, 5 hop events of 508 bytes each, payer
  -1,849,400.
- The fixture buy after a tail-pool create succeeds
  anchor-exactly (same tail, same buyback leg, same payer
  delta). Creation alone does not disturb the chain.

Created-pool entry into the 5-hop route, unpatched (the gate):

- Middle hop (P3), buy and sell alike: fails 6078
  OnlyPumpPools with 2 ghost hop events (the two hops before
  the created pool complete, the created hop fails), full
  rollback, payer -5,000.
- Terminal hop (P5), buy: fails 6078 with 4 ghost hop events.
- Terminal hop (P5), sell: fails 6078 with 0 ghost events (the
  created terminal pool is the first hop in sell direction).
- Under tf5000 the middle-hop gate is identical: 6078 with 2
  ghosts, both directions.

Created-pool settings do not rescue entry:

- Setting the created pool's coin_creator to the payer and its
  creator_fee_bps to 300, then buying through the middle-hop
  route: still 6078 with 2 ghosts. The gate reads the creator
  field, not the coin_creator field.
- Setting the created pool's virtual_quote_reserves to 10^9,
  then buying through the middle-hop route: still 6078 with 2
  ghosts. The gate precedes pricing.

Created-pool entry with the creator patched to the
pool-authority PDA (the gate passes, the seeds break):

- Middle hop, buy and sell alike: the patched pool's own hop
  emits its event (3 ghosts total), then the following leg
  fails PrivilegeEscalation naming the created pool account,
  full rollback, payer -5,000.
- Terminal hop, buy: 4 ghosts and no terminal event — the
  terminal hop's own payout transfer from its vault to the user
  fails PrivilegeEscalation before its event is emitted.
- Terminal hop, sell: 1 ghost — the patched terminal pool's
  own hop emits its event, then the next leg's input pull
  fails PrivilegeEscalation.
- Mechanism (read from the program source, not inferred from
  the error alone): after each AMM hop, the next leg's input
  transfer is signed by the previous hop's pool with seeds
  `[b"pool", index, stored creator, base mint, quote mint,
  bump]`; the last hop's payout transfer is signed the same
  way. Patching the stored creator makes those seeds derive a
  different PDA than the real created pool, so the runtime
  rejects the signer privilege. Unpatched, the seeds are
  consistent but the canonical-creator gate fails; patched,
  the gate passes but the seeds are inconsistent. A directly
  created pool therefore cannot route at depth 5 in any
  position, in either direction.

Created-pool single-hop life (plain mode):

- Buy_v2 10^6 base out: userquote -1,003,004, userbase
  +1,000,000, buyback recipient +250 (the builder's `buyback`
  and `bbspl` roles alias the same ATA, so the +250 appears
  under both names for one transfer), base vault -1,000,000,
  quote vault +1,002,754, pool [-251, 251, 0, 10^12]. Buy_v2
  event 500 bytes: curve 1,000,002, lp_bps 25, lp_fee 2,501,
  proto_bps 5, proto_fee 501, qwlp 1,002,503, uin 1,003,004.
- Sell_v2 10^6 base in (min quote 1): userquote +996,999,
  userbase -1,000,000, buyback +250, pool [-502, 502, 0,
  10^12]. Sell_v2 event 449 bytes: curve 1,000,001, lp_fee
  2,501, proto_fee 501, quote 997,500, uout 996,999.
- Protocol sweep discharges the full bucket (502) to the
  protocol ATA for the quote mint; after the sweep the pool
  is exactly back at its creation state [0, 0, 0, 10^12].
- Boost-window invariant (answer to brief item (d)): boost
  fails 6065 PoolCannotBoost on a fresh created pool, after a
  10^9-base buy (virtual drift exactly cancels protocol
  accrual, window still 0), and after a 10^9 / 10^9 deposit
  (deposit is virtual-reserve-neutral on a created pool:
  supply 10^12 -> 1,001,000,000,000, all fee/virtual fields
  unchanged).
- Boost after opening the window: patching
  virtual_quote_reserves to 10^9, bolting a tf100 extension
  onto the quote mint, and converting the created quote vault
  to Token-2022 form makes boost succeed — 2 events, burned
  988,033,811, base vault -988,033,811, quote vault
  +990,000,000 (10^9 in, 1% tf withheld), boost ATA -10^9.
  Boost event 208 bytes: requested 10^9, used 10^9, burned
  988,033,811, vq 10^9, quote_after 1,000,990,000,000,
  base_after 999,011,966,189, remaining 999,000,000,000. The
  pool's stored virtual_quote_reserves field stays 10^9.
- Deposit + withdraw returns the pool exactly to its
  creation state (deposit event 264 bytes base 10^9 quote
  10^9; withdraw event 264 bytes base 10^9 quote 10^9).

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The fixture split chain is the 3rd #128 fixture (true 5 hops,
  tf100 in families R and F); the created middle pool replaces
  only the P3 hop group and the created terminal pool only the
  P5 hop group.
- Plain-mode create cases skip the withdraw-withheld authority
  patch (`no_ww`): that patch writes the payer into the
  quote-mint transfer-fee authority slot, which is harmless in
  tf mode but breaks SPL mint parsing in plain mode and makes
  create fail InvalidAccountData.
- `cpatch` steps are harness field resets recorded with an
  empty transaction, never presented as on-chain instructions;
  the creator patches in family R exist only to test the gate
  interaction and are not a proposed on-chain operation.
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
