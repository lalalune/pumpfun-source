# research: fee-config on the true 5-hop split x boost x tf chain — the rewrite moves no trade leg, gates and validation order hold, protocol sweep fails 6013 while creator sweep/collect succeed

## Problem

The brief for this packet was to extend the #79 fee-config findings
(`update_fee_config`: lp/protocol/creator bps, recipient ordering
gates, validation order, atomicity) from the true 3-hop split chain
to the true 5-hop split x boost x tf chain, and to answer whether
a fee-config rewrite binds a live 5-hop chain at all. Measurement
says it does not move any trade leg: after the rewrite (lp 30 /
protocol 40 / creator 100, 8 sorted 0xd2..0xd9 recipients, 0x63
authority), the 5-hop buy tail, the 5-hop sell payout and both
post-buy boost burns are anchor-identical, because all trade paths
price from the fee-table account, not from GlobalConfig. What the
rewrite does move is the protocol sweep: after the rewrite the
protocol sweep fails 6013 — with or without a preceding buy or
sell — while the creator sweep and collect still succeed at their
anchor values. The setter gates and their validation order are
unchanged at depth 5: bps over 1000 fails 6000 with lp checked
before protocol before recipients before creator (lp1001 plus a
misaligned list still fails 6000, creator1001 plus a misaligned
list fails 6012), misaligned/duplicate/adjacent-swap lists fail
6012, a zero-key-first list fails 6011, outsider fails 6005,
unsigned fails 3010, and every failure is followed by the anchor
buy. Rewrite ordering is neutral: buy-then-rewrite-then-boost,
rewrite-then-buy-then-rewrite-back-then-boost, double rewrite,
and rewrite-back sequences all leave the chain on its anchor
values.

Route confirmation (from the builder itself): the fixture route
calls `three_amm` and appends the g4 and g5 hop groups, so the
route is main → POOL2 → P3 → P4 → P5, final output U5: TRUE 5
hops. This packet does not repeat 3rd #61's naming error (a
"3-hop" packet whose builder actually appended a P4 group).

## Cases

39 cases, 102 steps, 306 receipts (102 steps × 3 images), 31 parts
of 10 receipts (30×10 + 6). All cases run the same steps on the
original, control (#424) and candidate (#427) images. All families
run under tf100 on the quote mint unless noted. The fixture
fee-config is lp 20 / protocol 5 / creator 5 with 8 sorted fixture
recipients and the fixture fee authority; the rewrite under test
writes lp 30 / protocol 40 / creator 100, 8 sorted 0xd2..0xd9
recipients, and a 0x63 authority, emitting the 360-byte
update_fee_config event (disc `5a1741233ef4bcd0`).

Family A — anchors at depth 5 (5 cases):

- `A-buy5`: 5-hop buy tail 5,207,955,235,891, 5 hop events,
  buyback leg 4,515,471.
- `A-sell5`: 5-hop sell payout 178,541, 5 hop events, leg 837.
- `A-buy-boost`: buy, vq patch, boost burns 5,254,679,949,141.
- `A-sell-boost`: sell, vq patch, boost burns 5,338,394,848,076.
- `A-buy-swp-col`: buy, protocol sweep net 4,517,934, creator
  sweep net 122,160, collect net 120,938.

Family F — fee-config rewrite binds the 5-hop chain (6 cases):

- `F-fc-buy` / `F-fc-sell`: rewrite, then buy / sell.
- `F-fc-buy-boost` / `F-fc-sell-boost`: rewrite, then buy / sell,
  vq patch, boost.
- `F-fc-buy2`: rewrite, then two buys.
- `F-fc-same-buy`: rewrite to the fixture values, then buy.

Family G — setter gates at depth 5 (12 cases, failed setter then
the anchor buy):

- `G-lp1001-buy` / `G-proto1001-buy` / `G-creator1001-buy`:
  each bps over 1000 alone.
- `G-lp1001-misalign-buy` / `G-proto1001-misalign-buy`:
  over-cap bps plus a misaligned list.
- `G-misalign-buy`: misaligned list alone.
- `G-zero-buy`: zero-key-first list.
- `G-dup-buy`: duplicate-recipient list.
- `G-swap-buy`: adjacent-swap list (first two sorted recipients
  exchanged).
- `G-creator1001-misalign-buy`: creator over-cap plus a
  misaligned list.
- `G-outsider-buy` / `G-unsigned-buy`: non-admin / unsigned
  setter.

Family O — rewrite ordering vs the 5-hop buy and the post-buy
burn (6 cases):

- `O-buy-fc-boost`: buy, rewrite, vq patch, boost.
- `O-fc-buy-fc-boost`: rewrite, buy, rewrite back to fixture
  values, vq patch, boost.
- `O-fc-fc-buy`: rewrite, second rewrite (lp 10 / protocol 20 /
  creator 50, same recipients and authority), buy.
- `O-fc-buy-fc-buy`: rewrite, buy, rewrite back, second buy.
- `O-sell-fc-buy`: sell, rewrite, buy.
- `O-buy-fc-sell`: buy, rewrite, sell.

Family S — rewrite then sweep/collect at depth 5 (5 cases):

- `S-fc-buy-swp`: rewrite, buy, protocol sweep.
- `S-fc-buy-swc-col`: rewrite, buy, creator sweep, collect.
- `S-fc-swp-nobuy`: rewrite, protocol sweep, no trade at all.
- `S-fc-sell-swp`: rewrite, sell, protocol sweep.
- `S-fc-buy-col`: rewrite, buy, collect with no preceding sweep.

Family F — tf variants of rewrite-then-buy (5 cases):

- `F-tf5000-fc-buy` / `F-tf5000-fc-sell` /
  `F-tf5000-fc-buy-boost`: rewrite, then buy / sell / buy-boost
  under tf5000.
- `F-tf0-fc-buy` / `F-tf0-fc-sell`: rewrite, then buy / sell
  under tf0.

## Result

All 39 cases pass on all three images with 0 divergent cases:
control and candidate agree with the original everywhere. Error
sites (source line numbers) differ per image and are recorded per
image in each report row's `error_sites`, never in the observed
surfaces.

The rewrite moves no trade leg at depth 5:

- Rewrite then buy: tail 5,207,955,235,891, leg 4,515,471 —
  anchor-identical. Rewrite then sell: payout 178,541, leg 837 —
  anchor-identical. Rewrite then buy then patched-window boost:
  burn 5,254,679,949,141; rewrite then sell then patched-window
  boost: 5,338,394,848,076 — both anchor-identical. Rewrite to
  the fixture values then buy is likewise anchor-identical, and
  a second buy after the rewrite pays the anchor second-buy tail
  4,918,089,082,874.
- The rewrite itself writes exactly the five fields and nothing
  else: lp 30, protocol 40, creator 100, the 8 sorted recipients,
  the 0x63 authority; the second rewrite writes lp 10 / protocol
  20 / creator 50 with the same recipients and authority, and
  the following buy is still anchor-identical.

Setter gates and validation order at depth 5 (each failure rolls
back the config to lp 20 / protocol 5 / creator 5 and is followed
by the anchor buy):

- lp 1001, protocol 1001, creator 1001 each fail 6000 alone.
- lp 1001 plus a misaligned list still fails 6000 (bps checked
  before recipients); protocol 1001 plus a misaligned list still
  fails 6000.
- Creator 1001 plus a misaligned list fails 6012 (recipients
  checked before creator) — the order pin: lp > protocol >
  recipients > creator.
- Misaligned, duplicate, and adjacent-swap lists each fail 6012.
- Zero-key-first list fails 6011.
- Outsider-signed rewrite fails 6005 (payer lamports unchanged);
  unsigned rewrite fails 3010.

Rewrite ordering is neutral at depth 5:

- Buy then rewrite then patched-window boost burns
  5,254,679,949,141 — the anchor burn, so a rewrite after the buy
  does not move the burn either.
- Rewrite then buy then rewrite-back then patched-window boost
  also burns 5,254,679,949,141.
- Double rewrite then buy is anchor-identical; rewrite then buy
  then rewrite-back then a second buy pays the anchor second-buy
  tail 4,918,089,082,874.
- Sell then rewrite then buy pays 5,208,011,418,184 and buy then
  rewrite then sell pays 189,218 (leg 888) — both are the
  moved-pool values from the first leg, not config effects
  (compare #132's no-op setter case, which shows the same
  moved-pool values).

The rewrite gates the protocol sweep at depth 5, not the creator
path:

- Rewrite then buy then protocol sweep fails 6013; rewrite then
  sell then protocol sweep fails 6013; rewrite then protocol
  sweep with no trade at all also fails 6013 — the failure is
  about the rewritten recipient list, not about anything the
  trade accrued.
- Rewrite then buy then creator sweep still discharges net
  122,160 and collect still pays net 120,938 — the creator path
  is untouched by the rewrite.
- Rewrite then buy then collect with no preceding sweep is a
  0-event no-op (fee only), as in the anchor chain.

Tf variants after the rewrite:

- tf5000 rewrite-then-buy tail 2,668,075,748,732, leg 1,151,788;
  tf5000 sell payout 90,172, leg 423; tf5000 rewrite-then-buy
  then patched-window boost burns 2,685,165,599,125.
- tf0 rewrite-then-buy tail 5,259,040,470,738, leg 4,607,153;
  tf0 sell payout 180,345, leg 846.
- All tf values match the no-rewrite tf anchors from earlier
  packets, so the rewrite is tf-neutral as well.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The fixture split chain is the 3rd #132 fixture (true 5 hops,
  tf100 in families A/F/G/O/S unless noted); hop pools share the
  fixture fee-table and GlobalConfig, so the pins are about
  fee-config interaction, not about per-hop fee-table variation.
- `cpatch` steps are harness field resets recorded with an
  empty transaction, never presented as on-chain instructions.
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
