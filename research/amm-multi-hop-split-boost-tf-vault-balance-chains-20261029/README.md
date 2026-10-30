# amm-multi-hop-split-boost-tf-vault-balance-chains-20261029

## Problem

3rd #92 pinned the window invariant (vq + protocol + creator
constant) and that sweep/collect are price-neutral, #93 pinned
that chain prices move when a single-hop leg moves the real
vaults, and #97 pinned the user's own wallets. What none of
them pinned is the pool vaults themselves as priced inputs:
every hop reads two real token balances (a base vault and a
quote vault), and the LP supply sits in the pool account next
to them. Does a hop price off the real vault balance, the
virtual reserve, or both? Which vault empties first, what code
fires when it does, and does a restore bring the anchor back?
This packet patches vault amounts, lamports, frozen state,
absence, and LP supply mid-case -- between real trades, with
no transaction of its own, so a patch leaves no receipt --
and pins the price at each balance, the gate at each empty
vault, and the restore behaviour, on the split x boost x tf
chain at true 3 hops (three_amm only, final output U3).

## Cases

77 cases, 354 receipts, 36 parts (35x10 + 4), three program
images (original, control, candidate) per step. Fixture
vaults: main base vb1 673,696,395,912,745 (SPL 165 bytes),
main quote vq1 122,946,690,720 (Token-2022 178 bytes), middle
vb2/vq2 and tail vb3/vq3 10^15 each; main LP supply
4,194,352,106,721. Anchors: buy 10^9 quote pays tail U3
5,262,910,281,902 (hop1 base out 5,332,264,170,203, hop2 out
5,303,981,938,022, buyback 4,515,471); sell 10^9 base pays
178,541.

Family A -- main quote vault vq1: anchor buy/sell; buy with
vq1 0, 1, 10^15; sell with vq1 0, 100,000, 178,541, 10^9;
frozen buy/sell; absent buy/sell; lamports 0 buy; pre-seeded
withheld 999,999 then buy then sweep.

Family B -- main base vault vb1: buy with vb1 0, 10^9, 10^12,
5 x 10^12, 10^15; sell with vb1 0, 10^15; frozen buy/sell;
absent buy/sell; lamports 0 buy.

Family C -- middle vaults: buy with vb2 0, 10^12; sell with
vb2 0; buy with vq2 0; sell with vq2 0; frozen vb2 buy,
frozen vq2 sell; absent vb2 buy.

Family D -- tail vaults: buy with vb3 0, 10^12; sell with
vb3 0; buy with vq3 0; sell with vq3 0; frozen vb3 buy,
frozen vq3 buy; absent vb3 buy.

Family E -- LP supply: buy/sell with lp 0; deposit/withdraw
with lp 0; deposit with lp 1 and lp 10^6; buy with lp 10^12,
2^63, middle lp 0, tail lp 0; buy with lp 0 then lp restored
then buy; deposit then withdraw then buy.

Family F -- drain chains: vb1 6 x 10^12 then three buys then
vb1 restored then buy; vq1 300,000 then three sells then
vq1 restored then sell; buy/sell/buy/sell cycle; vb3
6 x 10^12 then three buys.

Family G -- downstream legs: buy then protocol sweep then
creator sweep then collect then buy; buy then sweep with
vq1 zeroed then sweep restored; boost with vb1 0, with
vq1 0, anchor boost (vq patch 10^9), boost with boost-ATA
10^6; failed buy (vb1 0) then token claim; deposit then
withdraw with vb1 0 then withdraw restored.

Family H -- restore / hybrid: buy then vb1 restored then
buy; sell then vq1 restored then sell; buy then vb3
restored then buy; buy then sweep then vq1 restored then
buy; buy then vb1 10^15 buy then vb1 restored buy then buy.

Family I -- v2 contrast: v2 buy with vb1 0, with vq1 0, with
vb1 frozen; v2 sell with vq1 0; v2 anchor buy.

## Result

All 77 cases agree on all three images: **0 divergences**.
Error sites are pinned per image, never compared across
images.

- Hops price off real vault balances, both sides. The
  anchor buy moves vb1 -5,332,264,170,203, vq1 +985,438,918
  (10^9 in, 10,000,000 withheld at the vault, 4,561,082
  protocol accrual absorbed into main vq), vb2
  -5,303,981,938,022, vq2 +5,332,264,170,203, vb3
  -5,262,910,281,902, vq3 +5,303,981,938,022, tail
  +5,262,910,281,902. Patching vb1 rescales the whole
  chain: vb1 10^9 pays tail 7,964,081, 10^12 pays
  7,963,960,047, 5 x 10^12 pays 39,817,260,255, fixture
  6.7 x 10^14 pays 5,262,910,281,902, 10^15 pays
  7,772,317,088,657. Patching vq1 rescales it the other
  way: vq1 10^15 pays tail 664,962,160 (hop1 base out
  666,625,458). The virtual reserve (-125,882) is a
  rounding-scale adjustment next to real balances of
  10^11-10^15, not the price driver -- #93's "real base
  vault" leg is confirmed and extended to both vaults of
  every hop.
- Sells price off the same real balances, mirrored. The
  anchor sell moves vb1 +997,498,005, vq1 -181,191,
  userquote +178,541. Patching vq1 to 10^9 collapses the
  payout to 1,451 (vq1 -1,473); patching vb1 to 10^15
  drops it to 120,282. A sell after a buy pays more than
  the anchor sell (185,288 after one buy, 192,159 after
  buy/sell/buy), and a buy after a sell pays more than
  the plain second buy (5,073,016,321,292 vs
  5,072,980,706,277) -- the cycle ratchets because each
  leg moves the real vaults the next leg prices off.
- Empty base vault: 6025 DivisionByZero (pool.rs:87/:386),
  every hop, both directions. Empty quote vault: 6023
  Overflow (pool.rs:417/:64), every hop, both directions.
  Ghost ladder for zero vaults: buy main 0 / middle 1 /
  tail 2 events, sell reversed (main 2 / middle 1 / tail
  0). Frozen vaults fail Token custom 17 with no site
  line, one event later than zero on base vaults (buy
  vb1 1 ghost vs 0, vb2 2 vs 1; sell vq2 2 vs 1) and at
  the same count elsewhere (buy vq1 0, vb3/vq3 2; sell
  vb1/vq1 2). Absent or lamports-0 vaults fail 3012
  (pool_base_token_account / pool_quote_token_account)
  with the zero-vault ghost ladder.
- Sell quote-vault ladder, finer than buy: vq1 0 and
  100,000 fail 6023 (2 ghosts), vq1 178,541 and 300,000
  fail 6002 ZeroQuoteAmount (multi_hop_swap.rs:712/:635,
  2 ghosts) -- the computed payout rounds to zero after
  fees -- vq1 10^9 pays 1,451, fixture pays 178,541.
  Buy quote-vault ladder has no 6002 step: vq1 0 and 1
  fail 6023 with 0 events, vq1 10^15 succeeds at the
  collapsed price above.
- LP supply is invisible to multi-hop but gates
  liquidity. Buy/sell with lp 0, 10^12, 2^63, middle lp
  0, tail lp 0 are all anchor-identical. Deposit with
  lp 0 fails 6025 (fees.rs:21/:19, the LP math divides
  by supply); lp 1 fails 6024 Truncation
  (deposit.rs:77/:14); lp 10^6 succeeds and the amounts
  prove proportional minting: base leg exactly the full
  vb1 balance 673,696,395,912,745, quote leg exactly
  the available quote 122,946,564,838 (= vq1 fixture
  minus the 125,882 virtual magnitude), LP minted
  1,000,000, supply 10^6 -> 2 x 10^6. Withdraw with
  lp 0 fails 6067 SeedLockViolation (withdraw.rs:6/:62:
  lp_supply must never drop below the circulating LP
  mint supply). The anchor deposit/withdraw pair
  (160,619,896 base + 29,610 quote in, 160,619,895 base
  + 29,018 quote out) leaves the next buy 42 below the
  anchor (5,262,910,281,860), the #91/#95 flooring dust.
- Withdraw with an empty base vault silently pays 0
  base. Withdraw 10^6 LP with vb1 0 burns the LP and
  pays the full quote leg (userquote +29,018, event
  base 0 / quote 29,312) with no failure; restoring vb1
  makes the next withdraw pay the full 160,619,895
  base. Proportional math gives 0, not an error -- the
  only silent-zero leg in the packet.
- Drain chains never partially fill. vb1 6 x 10^12 buys
  pay 47,799,950,369 -> 47,014,112,875 -> 46,665,417,748
  (tails shrink as vb1 drains); vb3 6 x 10^12 buys pay
  31,577,461,691 -> 30,437,884,237 -> 29,358,903,130
  (the tail vault caps the tail through the hop-3
  ratio, not through exhaustion). vq1 300,000 sells
  fail 6002 three times in a row; restoring vq1 pays
  the anchor 178,541 and the next sell pays 178,540,
  the plain second-sell value -- failed sells move
  nothing, as #97 pinned for wallets.
- Sweep needs vault funds, not just a bucket. After a
  buy the protocol sweep pays 4,563,570 (fixture 2,488
  + buy accrual 4,561,082, net 4,517,934 to the
  protocol ATA), the creator sweep pays 123,394 (net
  122,160), collect pays 122,160 (net 120,938), and the
  next buy is the plain second buy 5,072,980,706,277 --
  sweep/collect price-neutral, as #92 pinned. But
  sweeping with vq1 zeroed fails 6023 (pool.rs:417/:64):
  the bucket is a bookkeeping field, the transfer
  still draws the real vault. Restoring vq1 makes the
  sweep pay the full 4,563,570. A pre-seeded vault
  withheld 999,999 leaves the buy anchor-identical and
  the sweep unchanged (vault withheld 10,999,999 after
  the buy: seed + buy 10,000,000).
- Boost reads both vaults. Anchor boost (vq patch
  10^9) burns 5,338,379,201,831 base from vb1 against
  990,000,000 quote into vq1 (10^9 requested, 10,000,000
  withheld). vb1 0 fails 6001 ZeroBaseAmount
  (boost_burn.rs:50 / boost.rs:273); vq1 0 fails 6023
  (pool.rs:417 / boost_burn.rs:47). Boost with a
  10^6 boost-ATA against a 10^9 request fails 6088
  QuoteMintNotWritable (boost_burn.rs:97 / boost.rs:403)
  -- recorded as measured; the packet does not pin why
  a short ATA surfaces as a mint-writability error.
- Vaults are irrelevant to claims. A buy failed by
  vb1 0 (6025) is followed by a full token claim
  3,334,551 (claimed 222 -> 3,334,773, volume -> 0,
  last -> 21).
- Single-account restore is hybrid, as #96 pinned for
  pool bytes. Buy then vb1-restored buy pays
  5,113,034,555,206 (above the plain second buy
  5,072,980,706,277); buy then vb3-restored buy pays
  5,099,820,604,572; buy then sweep then vq1-restored
  buy pays 5,112,717,455,757. Only the sell-side vq1
  restore is inert: sell then vq1-restored sell pays
  178,540, the plain second-sell value (the sell
  moves vq1 by only 181,191 against a 10^11 balance).
  The vault walk shows the same split at scale: anchor
  buy -> vb1 10^15 buy 7,551,674,273,448 -> vb1
  restored buy 4,920,404,216,661 -> buy
  4,748,011,490,203 (the 10^15 buy drained the middle
  and tail vaults, and restoring vb1 alone cannot
  un-drain them).
- v2 mirrors multi-hop's vault gates with its own
  codes: v2 buy with vb1 0 fails 6016
  BuyMoreBaseAmountThanPoolReserves
  (constant_product.rs:21/:8) instead of multi-hop's
  6025; v2 buy/sell with vq1 0 fail 6023 as multi-hop
  does; v2 buy with vb1 frozen fails custom 17 with 0
  events (no ghost ladder on the single-hop leg). The
  v2 anchor buy spends 189 quote (vault quote +186,
  buyback 1) for 10^6 base.

## Relation to earlier packets

- #3 established liquidity/trade interaction through
  available quote; this packet shows the trade leg
  itself prices off real vault balances on both sides
  of every hop.
- #34 established the boost burn anchor
  (5,338,379,201,831 at vq 10^9); this packet adds the
  boost vault gates (vb1 0 -> 6001, vq1 0 -> 6023,
  short boost-ATA -> 6088).
- #88 established vault/token-account validation
  slots; this packet extends the same slots to vault
  balances (zero -> 6025/6023, frozen -> custom 17,
  absent/lamports-0 -> 3012) with hop-position ghost
  ladders.
- #91 established amount thresholds and ceiling
  rounding; this packet shows the vault-side thresholds
  are CPMM ratios, not fixed amounts (tails rescale
  smoothly with vb1/vq1, then gate at zero).
- #92 established the window invariant and sweep/
  collect price neutrality; this packet quantifies the
  buy's vault rewrite per hop, shows sweep still needs
  real vault funds, and re-confirms neutrality after
  sweep/collect.
- #96 established byte-level restore hybridity for
  pool accounts; this packet shows the same hybridity
  for single-vault restores (and the one inert case:
  sell-side vq1 restore).
- #97 established wallet-side thresholds (rent floor
  2,129,760, UVA auto-init 1,849,400); this packet is
  the pool-side counterpart -- vault balances, not user
  balances, gate and price the chain.

## Limits

- Patches are applied directly to account data between
  steps; they are not transactions and leave no receipt.
  The receipt stream pins the before/after state of every
  real step, and producer.py records every patch in the
  case definitions, so the sequence is reproducible from
  the packet files -- but a patch itself has no signature
  to verify.
- The "restore" steps rewrite one account only (vault
  restores rewrite the vault token account; the LP
  restore step rewrites the full main-pool snapshot,
  including vq and fee buckets). The hybrid-state values
  they produce are harness artifacts of that method, not
  program behaviour on a real chain; they are reported
  here because they identify exactly which accounts feed
  the next trade's price.
- The boost short-ATA 6088 is recorded as a measured
  code and site only; the packet does not pin the
  mechanism linking a short boost-ATA balance to a
  mint-writability error.
- The CPMM ratio reading of the vault patches (output
  scaling with vb1/vq1) is inferred from the measured
  ladder, not from a source line: the checked-out
  source does not expose the hop pricing formula in a
  single pinned line.
- Only the TRUE 3-hop route (three_amm, final output U3)
  is used; 4-hop and 5-hop routes are covered by #61/#62
  and #65/#66 and are not re-run here.

## Reproduce

`python3 producer.py` rebuilds the receipts under
`runtime/` (10 per part, 36 parts); `python3 verify.py`
re-checks signatures, deltas, withheld, pool/UVA/GVA/
GlobalConfig states, decoded events, error codes, rollback,
and three-image agreement from the packet files alone.

Made via @slopdotcash
