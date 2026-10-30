# research: multi-hop split x boost created-pool lifecycle under transfer fee

A directly created pool (#72) cannot join a multi-hop route (6078), but
can it boost on its own? This packet pins the created pool's boost
lifecycle through create, deposit, withdraw, trade, sweep and collect,
and shows why a patched window still does not burn: the boost quote
leg is a Token-2022 `transfer_checked` under the quote token program,
so the quote mint AND the quote vault must both be Token-2022. A
directly created pool is born with SPL Token mint and vaults, and a
transfer-fee quote mint is rejected at create, so no natural created
pool can boost. Converting the vault and adding a transfer-fee
extension to the mint (both harness rewrites, see Limits) makes it
burn — and makes it boost-only: later trade and sweep fail
`InvalidAccountData`.

All numbers below are measured receipts from this packet (3 images:
original, control, candidate; 0 divergent cases). The split chain is
the same genuine 3-hop route as #63–#102 (`three_amm` only, final
output U3); created-pool steps run standalone beside it.

## Method note: cpatch steps

Several cases use `cpatch` steps. A `cpatch` is NOT an instruction: it
is a harness field reset between instructions (pool virtual-quote /
bucket fields, GlobalConfig boost authority / enabled flag, boost-ATA
amount, quote-vault conversion, quote-mint transfer-fee extension).
Its receipt carries an empty transaction (`transaction_base64: ""`)
and zero events, and `verify.py` asserts exactly that instead of
verifying a signature. Every other receipt is a real signed
transaction. The five `cpatch` kinds:

- `cpool`: rewrite pool fields (vq / protocol_fees / creator_fees).
- `config`: rewrite GlobalConfig boost authority (907..939) and/or
  boost enabled (939).
- `cba`: rewrite the boost ATA amount (offset 64).
- `mint_tf`: rewrite the created quote mint to carry a transfer-fee
  extension (`transferfee(quote, bps, 2**64-1)(h, [])`).
- `conv_cvq`: convert the created quote vault CVQ to a Token-2022
  account (owner changed, 178-byte extension layout).

## Cases (59 cases, 648 receipts, 65 parts)

### L — natural lifecycle: the window is pinned at exactly 0 (10 cases)

`cpool` is reported as `[vq, protocol_fees, creator_fees, lp_supply]`
after each step; the window is `vq + protocol_fees + creator_fees`.

- `L-fresh`: create 10^12/10^12, cpool `[0, 0, 0, 10^12]`, boost 6065.
- `L-buy`: v2 buy 10^9 -> cpool `[-250251, 250251, 0, 10^12]`
  (vq drift -250,251 exactly cancels the protocol accrual 250,251),
  boost 6065. Buy deltas: userbase +10^9, userquote -1,004,004,006,
  buyback +250,250, cvb -10^9, cvq +1,003,753,756.
- `L-buy-sweep`: protocol sweep 250,251 out -> cpool `[0, 0, 0, 10^12]`
  (vq rises by the bucket), boost 6065.
- `L-buy-sweep-collect`: creator sweep and collect are both silent
  (creator bucket 0), boost 6065.
- `L-sell`: sell 10^6 -> cpool `[-250, 250, 0, 10^12]`, boost 6065.
- `L-dep`: deposit 10^9 -> cpool `[0, 0, 0, 1,001,000,000,000]`
  (liquidity is vq-neutral), boost 6065.
- `L-dep-wd`: deposit + withdraw -> cpool `[0, 0, 0, 10^12]`, boost 6065.
- `L-roundtrip`: buy + sell -> cpool `[-250502, 250502, 0, 10^12]`,
  boost 6065.
- `L-failed-boosts`: failed boost, then a second buy ->
  cpool `[-501004, 501004, 0, 10^12]`, boost still 6065 (no residue).
- `L-small`: 100/100 small pool, boost 6065.

### P — patched window: the gate passes, the leg fails (17 cases)

Every case below passes the window gate (window != 0) and then fails
`IncorrectProgramId` with 0 events. The window is a gate input only
(#100's fixture conclusion, reproduced on created pools).

- `P-vq1e9`, `P-vq1e6`, `P-vq1e10`, `P-vq1e12`: vq patches of
  10^6 / 10^9 / 10^10 / 10^12 -> `IncorrectProgramId`.
- `P-vqneg`: vq -10^9 (negative window) -> `IncorrectProgramId`.
- `P-proto1e9`: vq 0, protocol bucket 10^9 -> `IncorrectProgramId`
  (a bucket-only window also passes the gate).
- `P-creator1e9`: vq 0, creator bucket 10^9 -> `IncorrectProgramId`.
- `P-vq-trade`: vq patch, then buy -> cpool
  `[999749499, 250501, 0, 10^12]`, boost `IncorrectProgramId`.
- `P-trade-vq`: buy, then vq patch -> cpool `[10^9, 250251, 0, 10^12]`,
  boost `IncorrectProgramId`.
- `P-vq-sweep`: vq patch, then sweep (silent, bucket 0) ->
  `IncorrectProgramId`.
- `P-req1e6`, `P-req1e10`: request size does not matter ->
  `IncorrectProgramId` (the leg fails before any amount check).
- `P-shortata`: boost ATA 10^6, request 10^9 -> `IncorrectProgramId`,
  NOT 6088 (#100's 6088 is only reached after the leg succeeds).
- `P-zeroata`: boost ATA 0 -> 6002 (the ATA-0 gate precedes the leg
  check; consistent with #101's order 6065 > 6002).

### F — converted + transfer-fee: the burn succeeds (13 cases)

All burns use the created pool's own 10^12/10^12 vaults, so they
differ from the fixture anchor 5,338,379,201,831 (#100) in scale, not
in kind. Event fields are the 208-byte boost event
(disc `3f451c16305cc2b9`).

- `F-conv-boost`: vq 10^9 + `conv_cvq` + `mint_tf` 100 + boostc
  (10^9, 0) -> burn **988,033,811**, used 10^9, vq 10^9,
  quote_after 1,000,990,000,000, base_after 999,011,966,189,
  remaining 999,000,000,000. Deltas: cvb -988,033,811,
  cvq +990,000,000 (net of tf100), cba -10^9, withheld cvq +10,000,000.
- `F-conv-only`: vq 10^9 + `conv_cvq` WITHOUT `mint_tf` ->
  `IncorrectProgramId` (vault-only conversion is not enough).
- `F-conv-boost-twice`: 988,033,811 -> **986,083,317**
  (decay -1,950,494, about -0.20%/round, smaller than the fixture's
  about 1.56%/round because the vaults are 10^12-scale).
- `F-conv-boost-tf5000`: burn **499,251,122** (net 500,000,000 in).
- `F-conv-boost-vqneg`: vq -10^9 -> burn **990,009,899** (larger than
  the positive-vq burn, matching `q = vq + real quote balance`).
- `F-conv-boost-proto`: vq 0, protocol bucket 10^9 -> burn
  **989,020,868**. The bucket passes the gate but the burn reads the
  vq field (0), not the window sum (#100's correction, reproduced
  on a created pool).
- `F-conv-boost-req1e6`: burn **989,009**.
  `F-conv-boost-req1e10`: burn **9,793,253,535**.
- `F-trade-conv-boost`: buy, then convert + `mint_tf`, NO vq patch ->
  window still 0 -> 6065. Conversion itself creates no window.
- `F-trade-vq-conv-boost`: buy, then vq 10^9 patch + convert + tf100
  -> burn **986,057,984** (cpool at boost time
  `[10^9, 250251, 0, 10^12]`, quote_after 1,001,993,753,756,
  base_after 998,013,942,016).
- `F-conv-boost-trade`: after a successful burn, `buy2c` ->
  `InvalidAccountData` (the converted state breaks trade
  deserialization).
- `F-trade-conv-sweep`: buy, then convert + tf100, then `swpc`
  (bucket 250,251 exists) -> `InvalidAccountData` (the pre-conversion
  bucket is stranded by the conversion).
- `F-buy-claim`: created-pool v2 buy, then token claim -> silent
  no-op, 0 events, 0 payout, log "No tokens to claim". A created-pool
  buy does not move UVA volume (volume stays 0), unlike #73's seeded
  claim of 3,334,551.

### G — gate order on a created pool (10 cases)

- `G-off`: boost-off -> 6066, re-enable -> 6065.
  `G-disbuy`: buy-disable -> 6020, release -> 6065.
  `G-auth`: boost authority patched to outsider -> 6005,
  payer restored -> 6065.
- `G-off-dis`: off + buy-disable -> **6066** (off beats disable).
  `G-auth-off`: authority + off -> **6005**.
  `G-auth-dis`: authority + disable -> **6005**.
- `G-vq-off`: vq 10^9 + off -> 6066.
  `G-vq-dis`: vq 10^9 + disable -> 6020.
  `G-vq-auth`: vq 10^9 + outsider authority -> 6005.
- Head of #101's total order holds on created pools:
  6005 > 6066 > 6020 > 6065, and 6002 sits after the window gate
  (`P-zeroata`).

### T — transfer fee alone does not open the leg (4 cases)

- `T-fresh100`, `T-fresh5000`: `mint_tf` only, window 0 -> 6065
  (the gate is tf-blind).
- `T-vq100`, `T-vq5000`: vq patch + `mint_tf` (vault NOT converted)
  -> `IncorrectProgramId`. The mint side alone is not enough.

### C — create rejects a transfer-fee quote mint (3 cases)

- `C-tf100`, `C-tf0`, `C-tf5000`: `std` create under a tf quote mint
  (tf-only isolation, no withdraw-withheld authority) ->
  `IncorrectProgramId`, 0 events, full rollback (fee 5,000 only).
  Even a 0-bps extension is rejected: a created pool cannot be born
  under transfer fee.

### H — the created tail pool cannot be a hop (2 cases)

- `H-buy`: created tail pool as the route tail, multi-hop buy ->
  **6078 OnlyPumpPools**, 2 ghost hop events.
- `H-sell`: same, sell direction -> **6078**, 0 ghost events.
  (#72 re-confirmed on the split route.)

### A — anchors after a create (3 cases)

- `A-chain-after-create`: create, then the fixture 3-hop buy ->
  tail **5,262,910,281,902** (#102's no-patch anchor, byte-identical).
- `A-fixture-boost`: fixture pool, vq 10^9 patch, tf100 boost ->
  burn **5,338,379,201,831** (#100's anchor, reproduced).
- `A-fixture-boost-plain`: fixture pool, vq 10^9 patch, NO tf ->
  `IncorrectProgramId`. The Token-2022 requirement is not
  created-pool-specific: a plain fixture pool fails the leg too.

## Result

The 2x2 matrix (quote mint x quote vault), all receipt-backed:

| mint \ vault | SPL Token | Token-2022 |
| --- | --- | --- |
| SPL Token | `IncorrectProgramId` (P-vq1e9) | `IncorrectProgramId` (F-conv-only) |
| Token-2022 | `IncorrectProgramId` (T-vq100) | burn (F-conv-boost) |

So a created pool's boost lifecycle is: window pinned at exactly 0
through its whole natural life (create, deposit, withdraw, trade,
sweep, collect, failed boosts) -> boost always 6065; patching a
window passes the gate but the quote leg then fails unless BOTH
sides are Token-2022; converting both sides burns (tf100:
988,033,811 on 10^12/10^12 vaults, second burn 986,083,317) but the
converted pool is boost-only (trade and sweep become
`InvalidAccountData`); and the same pool still cannot be a
multi-hop hop (6078). The gate head order 6005 > 6066 > 6020 > 6065
(+ 6002 after the window gate) holds on created pools exactly as on
fixture pools (#101). Relation to earlier packets: #72 (created-pool
6078 + window-0 observation), #98 (vault gates 6001/6023/6088),
#100 (window is a gate input, burn reads the vq field, tf ladder),
#101 (gate total order), #102 (boost-trade interaction, no-patch
anchor 5,262,910,281,902).

## Limits

- `cpatch`, `conv_cvq` and `mint_tf` are harness field rewrites, not
  instructions and not on-chain reachable states in this packet:
  a directly created pool's vaults are SPL Token accounts and its
  quote mint is whatever it was created with (a tf quote mint is
  rejected at create, case C). The converted-burn numbers describe
  the burn formula on 10^12/10^12 vaults, not a state an on-chain
  created pool is shown to reach here (a migration path that
  converts vault and mint is not demonstrated).
- `IncorrectProgramId` is a Fieldless error with no site line, so
  the Token-2022 `transfer_checked` mechanism is inferred from the
  2x2 matrix plus the boost program's quote-leg structure, not from
  a recorded site.
- The burn formula was spot-checked against
  `base_for_quote(net, old_base, vq + old_quote)` on the F cases;
  it is not a full re-derivation of the curve.
- 6088 was NOT re-triggered on a created pool: the short-ATA case
  (`P-shortata`) fails earlier at the quote leg. The 6088 pin still
  rests on #100.
- The vault-only fixture cell (plain mint + converted fixture vault)
  is not receipt-backed here; only the created-pool 2x2 and the two
  fixture diagonal cells are.
- No source change, no build, and no whole-program identity claim is
  made. All three images agree on every receipt.

Made via @slopdotcash
