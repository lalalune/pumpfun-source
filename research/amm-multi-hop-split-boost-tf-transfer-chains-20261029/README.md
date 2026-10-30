# research: multi-hop split x boost transfer chains under transfer fee

#67–#104 pinned every other leg on the split x boost x tf chain, but
the pump program's own transfer instructions —
`transfer_creator_fees_to_pump` (v1, native-only) and
`transfer_creator_fees_to_pump_v2` (Token-2022-aware) — were only
ever measured standalone (2nd-run #22/#23). This packet puts them
on the chain: after a multi-hop buy/sell, after a boost, after a
sweep, and before the next leg. The question is twofold: which
branch of the transfer handler actually runs for each hop mint,
and does a transfer move anything the next leg can see?

All numbers below are measured receipts from this packet (3 images:
original, control, candidate; 0 divergent cases). The split chain is
the same genuine 3-hop route as #63–#104 (`three_amm` only, final
output U3). Transfer steps emit 0 events in every case below.

## Setup

- Route: three_amm (main -> pool2 -> pool3), split legs, tf
  override bps 100 unless a case says otherwise. Plain cases use
  no tf override and the `no_ww` guard (plain mint, no
  withdraw-withheld authority patch).
- Anchors on this chain: tf100 buy (10^9 quote) tails
  5,262,910,281,902, second buy tails 5,072,980,706,277; tf100
  buy-then-sell pays 185,288; plain buy tails 5,315,084,721,958,
  plain second buy tails 5,121,405,353,567, plain buy-then-sell
  pays 187,229; first-trade payer cost -1,849,400 (fee 5,000 +
  UVA rent 1,844,400), later trades -5,000.
- Fixture creator buckets: main 123,394, tail (P3) 123,394,
  middle (POOL2) 123,394. A buy adds 2,645,377,526 to the tail
  creator bucket and nothing to the middle (#99); a sell adds
  500,000 to the tail creator bucket.
- 49 cases, 420 receipts, 42 parts (42x10), 0 divergent cases
  across original / control / candidate.

## Cases

### T — tail transfers (non-native BASE2 mint, v2) (22 cases)

`T-buy-swc-xfer`: buy, sweep tail creator, transfer. `T-buy-swc-
xfer-xfer`: second transfer. `T-buy-swc-xfer-col`: collect after
transfer. `T-buy-swc-xfer-buy`: buy after transfer. `T-buy-buy`:
plain second-buy reference. `T-buy-swc-xfer-boost`: boost after
transfer (vq patched to 10^9). `T-sell-swc-xfer`: sell, sweep,
transfer. `T-xfer-before-buy`: transfer with an empty vault and
no destination. `T-buy-swc-xfer-out`: outsider pays the transfer.
`T-buy-swc-xfer-prefund`: destination pre-funded with 5,000.
`T-buy-swc-freeze-xfer`: frozen vault transfer. `T-buy-swc-xfer-
wrongmint`: quote mint passed for a BASE2 vault. `T-buy-swp-xfer-
protoata`: protocol ATA passed as the vault. `T-buy-swc-xfer-
t22prog`: Token-2022 program passed for an SPL vault.
`T-buy-failbuy-swc-xfer`: failed buy (6004) then sweep and
transfer. `T-buy-swc-xfer-sell`: sell after transfer. `T-buy-sell`:
tf buy-sell reference. `T-buy-swc-xfer-dep`: deposit after
transfer. `T-buy-swc-xfer-tclaim`: token claim after transfer
(seeded UVA). `T-buy-swc-p2-xfer`: middle-hop sweep and transfer.
`T-boost-buy-swc-xfer`: boost, buy, sweep, transfer.
`T-buy-swc-xfer-tf5000`: tf5000 chain. `T-buy-swc-xfer-xfer-col`:
second transfer then collect.

### M — main transfers (native wSOL mint, v1 and v2) (14 cases)

`M-swc22-xfer2-tf100/tf5000/tf0`: TOKEN22 creator sweep, then
v2 transfer. `M-swc22-xfer1`: same sweep, then v1 transfer.
`M-swc22-xfer2-splprog`: SPL program for a TOKEN22 vault.
`M-xfer2-amt0-t22`: v2 with an empty TOKEN22 vault.
`M-xfer2-amt0-spl` / `M-xfer1-amt0-spl`: v2/v1 with an empty SPL
vault. `M-buy-swc22-xfer2-fail-buy/col22/boost`: buy, sweep,
failed transfer, then buy / collect / boost. `M-swp22-xfer-proto`:
protocol sweep, then transfer of the protocol ATA.
`M-seed-spl-xfer2` / `M-seed-spl-xfer1`: seeded SPL vault
(123,394, lamports 2,162,674) under the tf override, then v2/v1.

### P — plain-quote transfers (no tf override, native branch succeeds) (13 cases)

`P-swc-xfer1` / `P-swc-xfer2`: sweep, then v1 / v2 transfer.
`P-swc-xfer1-xfer1`: second transfer. `P-swc-xfer1-out`:
outsider pays. `P-buy-swc-xfer1-buy` / `P-buy-buy`: buy after
transfer vs plain second buy. `P-swc-freeze-xfer1`: frozen vault
transfer. `P-swc-xfer1-wrongmint`: BASE2 mint passed to v1.
`P-swc-xfer2-t22prog`: Token-2022 program for an SPL vault.
`P-swc-xfer1-col`: collect after transfer. `P-buy-swc-xfer1-sell`
/ `P-buy-sell`: sell after transfer vs plain buy-sell.

## Result

### 1. The tail transfer drains the creator vault in full

- Buy, sweep tail creator, transfer: sweep pays 2,645,500,920
  (fixture 123,394 + buy accrual 2,645,377,526). The transfer
  moves exactly that amount: vault 2,645,500,920 -> 0, pump-vault
  ATA (pump creator-vault PDA, SPL Token, BASE2) None ->
  2,645,500,920, 0 events, payer -2,044,280 (fee 5,000 + new ATA
  rent 2,039,280).
- The destination is created even for a zero transfer:
  transfer-before-buy (vault 0, destination missing) still costs
  the payer -2,044,280 and leaves a 0-amount destination ATA.
  A pre-funded destination (5,000) costs only the -5,000 fee.
  An outsider-paid transfer costs the outsider -2,044,280 and
  leaves the payer untouched.
- Second transfer: success, 0 events, -5,000 fee, no amount
  moves. Collect after a transfer: success, 0 events, 0 payout
  (the vault is empty, and an empty collect is silent).
- Sell side: sell, sweep tail creator (623,394 = fixture 123,394
  + sell accrual 500,000), transfer drains the full 623,394.
- Middle hop: sweep pays the fixture 123,394 only (the buy adds
  nothing to the middle, #99), and the transfer drains exactly
  that to the base-mint pump-vault ATA.
- Boost-then-buy: boost anchor 5,338,379,201,831, buy tails
  5,139,964,404,268 (#102), tail sweep 2,583,383,461, transfer
  drains it in full. tf5000: buy tails 2,682,425,360,738, tail
  sweep 1,344,943,454, transfer drains it in full. The tail mint
  carries no transfer fee, so no withheld ever appears on a tail
  transfer (destination withheld stays unset).

### 2. A transfer leaves the chain untouched

- Buy after transfer tails 5,072,980,706,277 — the plain second
  buy, byte-identical. Sell after transfer pays 185,288 — the
  plain tf buy-sell, byte-identical. Deposit after transfer
  costs -29,846 quote. Token claim after transfer pays the full
  3,334,551 (seeded UVA: claimed 222 -> 3,334,773).
- Failed legs leave no residue either way: a failed buy (6004,
  3 ghost hop events, full rollback) then sweep and transfer
  moves the full 2,645,500,920; a failed main transfer (below)
  then buy tails the plain second buy 5,072,980,706,277.
- The one visible exception is not the transfer but the sweep
  before it: boost after a buy + tail sweep + transfer burns
  5,254,679,949,141, while boost after a buy + main creator
  sweep + failed transfer burns 5,254,685,098,328. The main
  sweep moved 123,394 out of the real quote vault, and the burn
  reads vq + real quote balance (#103's spot-check) — so a sweep
  moves the next burn even though the transfer itself does not.

### 3. The main mint takes the native branch — for v1 AND v2

The chain's quote mint is the native wSOL mint, so
`transfer_creator_fees_to_pump_v2` never reaches its non-native
branch here: it runs the same close-and-recreate path as v1.

- With a balance, both fail Token custom 11 ("Non-native account
  can only be closed if its balance is zero") at every tf level:
  tf100 (sweep net 122,160, withheld 1,234), tf5000 (net 61,697,
  withheld 61,697), tf0 (full 123,394) — the transfer failure is
  tf-blind, and the swept amount stays stranded in the creator
  vault ATA until a collect moves it (collect after the failed
  transfer pays net 120,938, withheld 1,222, event fee field
  gross 122,160).
- With an empty TOKEN22 vault, v2 silently no-ops: -5,000 fee,
  vault and destination both unchanged, destination stays
  missing. The no-op is a rent floor, not a zero check: available
  2,157,600 < minimum 2,039,280 + pump-vault deficit 890,880
  = 2,930,160, so the handler returns Ok before closing.
- With an SPL vault under the tf override, both v1 and v2 fail
  `IncorrectProgramId` with full rollback: the close succeeds,
  but recreating the vault ATA fails because the mint is
  TOKEN22-owned while the passed program is SPL Token. This
  holds for the empty vault (lamports 2,039,280) and for a seeded
  vault (123,394, lamports 2,162,674) alike.
- The stranded main creator fees are still recoverable by
  collect: after the failed transfer, `collect_coin_creator_fee`
  (TOKEN22) pays the net amount above. Transfer is not the only
  exit; it is the one that does not work on a native mint.

### 4. The plain native branch succeeds — and recreates the vault

- Plain sweep then v1: vault 123,394 -> 0, pump-vault PDA
  lamports +123,394 (1,000,000,000 -> 1,000,123,394), payer
  -5,000 only. No pump-vault ATA is created: the native branch
  closes the vault ATA, recreates the same vault ATA
  (rent-only, 2,039,280 lamports, amount 0), and transfers the
  leftover lamports to the pump-vault PDA account.
- v2 on the plain mint does exactly the same (same branch, same
  amounts, same pump-vault gain). Second v1: success, 0 movement,
  -5,000 fee (close + recreate of an empty vault). Outsider-paid
  v1: outsider -5,000, payer untouched, pump vault still
  +123,394.
- Plain buy after transfer tails the plain second buy
  5,121,405,353,567; plain sell after transfer pays 187,229 —
  the plain buy-sell, byte-identical. Plain collect after
  transfer is silent (0 events, 0 payout).

### 5. Gates: frozen blocks the token leg, not the close leg

- Frozen tail vault (state byte 108 set to 2, verified in the
  receipt snapshots): v2 transfer fails Token custom 17, full
  rollback.
- Frozen plain main vault (state 1 -> 2, verified): v1 transfer
  SUCCEEDS — vault 123,394 -> 0, pump vault +123,394, and the
  recreated vault ATA comes back initialized (state 2 -> 1).
  The native close path does not enforce the frozen state that
  the non-native `transfer_checked` path does.
- Wrong mint (v2, quote mint for a BASE2 vault): 2009.
  Protocol ATA passed as the vault (tail and main alike): 2015
  — transfer moves creator fees only; protocol fees cannot be
  routed through it. Wrong token program (SPL vault + TOKEN22
  program, or TOKEN22 vault + SPL program): 2023 in all three
  positions (tail, main, plain). v1 with a non-native mint:
  6007 UnsupportedQuoteMint.

## Limits

- The transfer-fee epoch schedule (older -> newer switch) is not
  re-measured on the chain; it is covered standalone in 2nd-run
  #22 (switch exactly at the newer epoch). The chain clock here
  stays at epoch 0.
- A non-native main mint is not reachable on this chain: the
  fixture quote mint is the native wSOL mint by construction, so
  the main-mint non-native branch (2nd-run #22's synthetic mint)
  has no chain case here.
- `IncorrectProgramId` is a Fieldless error with no site line, so
  the ATA-recreation mechanism for the SPL-vault failure is
  inferred from the close-then-recreate code path plus the
  rollback, not from a recorded site.
- Freeze / seed steps are harness field resets recorded with an
  empty transaction, never presented as on-chain instructions.
- Transfer steps emit no events on any path (success or
  failure); all transfer amounts above are snapshot deltas.
- No source change, no build, and no whole-program identity claim
  is made. All three images agree on every receipt.

Made via @slopdotcash
