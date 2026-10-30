# Multi-hop fee-table split x boost chains (3-hop)

3rd run packet #61: the split route (main -> POOL2 -> P3, hop 1 =
fee-tier cap selection, tail = exotic flat fees, from 3rd #37)
meets `boost_buy_and_burn` (from 3rd #34).

## Setup

The quote mint carries a 0-bps transfer-fee config, so the split
legs route the buyback through the TOKEN22 ATA (`BB22`) and the
main-pool sweeps/collects use the TOKEN22 pipes (`swc22`/`col22`).
The global config's boost authority is the payer and boost is
enabled; without that patch the boost fails 6005 InvalidAdmin at
`global_config.rs:297` before any window check. The main pool is
either left as-is (virtual_quote_reserves −125,882, protocol_fees
2,488, creator_fees 123,394, so the vq + accrued sum is exactly 0)
or patched to virtual_quote_reserves = 10^9 (sum 10^9 + 125,882).
All amounts below are measured on the original image; control and
candidate agree on every receipt.

## Problem

`can_boost` is the vq + accrued sum being nonzero
(`pool.rs`: `total_virtual_quote_reserves() != 0`). Split trades
and fee sweeps move that sum's components in lockstep, so it is
not obvious whether any trade/sweep chain can open the boost
window on a fresh pool — and, once the window is open, whether a
boost (which touches only the real vaults, never the pool fields)
reprices a following split trade, survives sweeps/collects, or
shifts the hop-1 fee-tier selection cap.

## Cases (32 cases, 219 receipts, 22 parts)

Fresh pool (sum 0) — every boost attempt fails 6065
PoolCannotBoost at `boost.rs:245` with full rollback (payer fee
5,000 only):

- `c-fresh-boost`: bare boost, 10^9 quote.
- `c-buy-boost`, `c-sell-boost`, `c-buy-buy-boost`,
  `c-buy-sell-boost`, `c-sell-buy-boost`: a split trade never
  opens the window — a buy moves main vq by exactly minus the
  accrued delta (buy: vq −4,607,154 while protocol +4,607,154),
  so the sum stays 0.
- `c-buy-swc22-boost`, `c-buy-swc22-col22-boost`: sweeping the
  creator bucket (123,394) into vq and collecting it relabels
  accrued into vq 1:1, so the sum still stays 0.
- `c-buy-boost3`, `c-buy-boost3-buy`: the tail pool's boost
  fails 6065 the same way, and the failed tail boost leaves the
  next split buy byte-identical to the uninterrupted second buy.

Boostable pool (main vq = 10^9):

- `c-vq1e9-boost`: 10^9 quote in burns exactly
  5,391,870,655,895 base, vaultquote +10^9, pool fields
  untouched, two events (BuyEvent 512 +
  BoostBuyAndBurnEvent 208: requested = used = 10^9,
  vq = 10^9, quote_after = 123,946,690,720,
  base_after = 668,304,525,256,850,
  remaining = 999,000,000,000).
- `c-vq1e9-boost-min-exact` / `c-vq1e9-boost-min-plus1`:
  min == burned succeeds; min == burned + 1 fails 6004
  ExceededSlippage at `boost.rs:274`.
- `c-vq1e9-boost-amt1` / `c-vq1e9-boost-amt2`: amount 1 fails
  6001 ZeroBaseAmount at `boost.rs:273`; amount 2 burns 5,435.
- `c-vq1e9-buy` / `c-vq1e9-boost-buy` and `c-vq1e9-sell` /
  `c-vq1e9-boost-sell`: the boost reprices the following split
  trade off the boosted real vaults — boost-then-buy moves
  vaultbase1 by −5,257,740,431,110 vs the anchor's
  −5,342,582,297,894, and the tail legs move with it, while the
  pool fields end at the same (995,392,846, 4,609,642, 123,394).
- `c-vq1e9-boost-buy-buy`: a second split buy after the boost
  prices off the boosted, post-trade vaults.
- `c-vq1e9-boost-swc22-col22`: sweep/collect after a boost
  moves the 123,394 creator bucket normally; the window
  survives the boost, so `c-vq1e9-boost-boost` burns a second,
  smaller amount (5,306,249,181,882).
- `c-vq1e9-buy-boost` and
  `c-vq1e9-buy-swc22-col22-boost-buy`: on the boostable pool
  the same trade/sweep chains that fail 6065 on the fresh pool
  succeed — the window survives trades, sweeps and collects —
  and the post-boost buy prices off the boosted vaults.
- `c-vq1e9-dep-boost` / `c-vq1e9-wd-boost` /
  `c-vq1e9-depwd-boost`: liquidity drifts the window
  proportionally — dep-1e9 moves vq 10^9 -> 1,000,238,445 and
  the next boost burns 5,391,880,941,907; wd-1e9 moves vq to
  999,761,554 and the next boost burns 5,391,860,365,016;
  dep -> wd leaves vq at 999,999,999 and the next boost burns
  the baseline 5,391,870,655,895 again. (On the fresh pool the
  same drift rounds to zero: vq stays −125,882, window shut.)
- `c-vq1e9-dep-boost-buy` / `c-vq1e9-wd-boost-sell`: the
  drifted, boosted pool reprices the following split trade.
- `c-vq1e9-cross` / `c-vq1e9-cross-boost-shift` /
  `c-vq1e9-boost-cross`: the hop-1 fee-tier selection cap is
  base-mint supply * effective quote / vault base, input
  transfer included (pre-buy1 cap 183,833,319,883 on the
  boostable pool, 186,811,616,360 after a boost). At threshold
  185e9 the no-boost buys cross tier A (10, 111, 333) -> B (20,
  222, 444) across two buys (buyback 5,489,071 then
  10,858,932) while the boosted first buy already selects B;
  at threshold 188e9 the boosted buys cross A -> B.

## Result

- The boost window is exactly the vq + accrued sum. Trades and
  sweeps are window-neutral (sum invariant), so no trade/sweep
  chain opens the window on a fresh pool; only a direct vq patch
  or proportional liquidity drift on an already-boostable pool
  moves it.
- A boost never touches pool fields, but it reprices every
  following split trade through the real vault balances, shifts
  the hop-1 tier-selection cap, and leaves the window open for
  further boosts.
- All 219 receipts agree across the original, control (#424)
  and candidate (#427) images. No divergence is pinned.

## Limits

- Only the 3-hop split route (main -> POOL2 -> P3) is covered;
  the 4-hop and 5-hop depths are not re-checked under boost.
- The tail-pool boost is only shown failing (6065); a
  successful tail boost would need the tail pool's vq patched,
  which this packet does not do.
- The quote mint's transfer-fee config is 0 bps throughout, so
  no withheld amounts appear; the nonzero-fee boost case is
  3rd #34 (`d-boost-tf100`), not repeated here.
- The boost authority is the payer and boost is enabled in the
  fixture config; the 6005 authority gate itself is not part
  of the receipt set (it was observed during probing only).
- No source change is proposed: this packet pins behaviour of
  the program as deployed.

## Files

- `producer.py` — the builder (this packet's producer).
- `verify.py` — independent re-verification (run from this
  directory: `python3 verify.py`).
- `runtime/report.json.gz` — case list, per-image expectations,
  error sites, part list.
- `runtime/raw-transactions-partNN.jsonl.gz` — 219 signed
  receipts in 22 parts of 10 (last part 9).
- `MANIFEST.json` — sha256 of every packet file.
