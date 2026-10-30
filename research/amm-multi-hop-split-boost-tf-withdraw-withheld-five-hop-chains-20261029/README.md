# research: split x boost x tf chains meet withdraw-withheld recovery at TRUE 5 hops

3rd-run packet #126: the split x boost x tf chain at TRUE 5 hops
(`three_amm` + g4 + g5, final output U5) meets Token-2022
withdraw-withheld recovery. This is the 5-hop extension of #69,
not a re-measure: every #69 result is re-checked at depth 5, and
the new depth-5-only behaviour is the tf10000 5-hop buy/sell
failures and the exact recovery sums on the 5-hop route.

## Problem

After a split-chain sweep and collect under a transfer-fee quote
mint, withheld sits stranded in three places at once: the hop-1
vault quote ATA (the buy's own fee), the buyback leg ATA, and the
creator vault ATA plus the collect destination. #69 pinned, at
3 hops, that one WithdrawWithheldTokensFromAccounts call recovers
exactly the stranded withheld, that the authority gates hold, that
harvest then withdraw-from-mint is the two-step equivalent, that
recovery is idempotent and tolerant of duplicated, empty,
extensionless and wrong-mint sources, that the destination binding
is asymmetric, and that recovery moves neither the boost burn nor
the tail. This packet asks whether every one of those holds on
the real 5-hop route main -> POOL2 -> P3 -> P4 -> P5, where the
intermediate hop vaults are plain SPL accounts that cannot
withhold at all, and how the recovery composes with the boost,
which itself withholds on the hop-1 vault.

The route is a TRUE 5-hop route: `three_amm` plus the g4 and g5
hop groups, five hop groups, final output token U5. (The #61
miscount does not apply here: the builder appends g4 AND g5, and
successful 5-hop swaps emit exactly 5 hop events.) The quote mint
carries a per-case transfer-fee config (100/5000/10000/0 bps) with
the split legs routing the buyback through the TOKEN22 ATA; the
withdraw-withheld destination WDEST is a TOKEN22 account whose
mint's withdraw_withheld_authority is patched into mint data
[202:234] after the transfer-fee override (without the patch the
authority is zero and recovery fails custom 29, as in #28).
WithdrawWithheldTokensFromAccounts is instruction bytes
[26, 3, n], harvest_withheld [26, 4], withdraw_from_mint
[26, 2]; the recovery metas are [mint read-only, destination
writable, authority signer, sources writable]. All figures below
are measured on the original image; control and candidate agree
on every case (0 divergent cases). All figures are re-measured
on the 5-hop chain here, not copied from #69 -- where they match,
that is itself the result.

## Cases (36 cases, 402 receipts, 41 parts)

Family A -- anchors at depth 5 (bps 100): 5-hop buy alone, 5-hop
sell alone, buy-then-boost, sell-then-boost.

Family B -- full recovery chains at depth 5: seed sweep/collect/
recovery; seed recovery into the source vault ATA itself; buy
sweep/collect/recovery; buy + protocol sweep + creator
sweep/collect/recovery; sell sweep/collect/recovery; buy +
protocol sweep + protocol-only recovery; buy sweep/collect/
recovery twice; buy sweep/collect/recovery, then a second
sweep/collect/recovery round.

Family C -- authority gates at depth 5: outsider recovery, zero
authority recovery, unsigned authority recovery, failed recovery
then retry by the right payer, harvest then withdraw-from-mint
under a zero authority.

Family D -- harvest / withdraw-from-mint / binding asymmetry at
depth 5: seed harvest then withdraw-from-mint; buy harvest-all
then withdraw-from-mint; withdraw-from-mint on a zero-withheld
mint; duplicated source; zero sources; wrong-mint source;
wrong-mint destination; Token-owned destination; extensionless
source.

Family E -- recovery ordering against the boost at depth 5:
buy-boost-recovery; buy-boost-sweep/collect-recovery-boost;
buy-boost-sweep/collect-boost without recovery (the anchor);
buy-harvest-boost-recovery; buy-boost-harvest-withdraw-from-mint;
sell-boost-recovery.

Family F -- tf variants at depth 5: buy recovery at tf5000, buy
at tf10000 (buy fails), sell at tf10000 (sell fails), buy
recovery at tf0.

## Result (0 divergent cases; control == candidate everywhere)

### Anchors and where the withheld lands at depth 5

- 5-hop buy tail anchor 5,207,955,235,891, emitted as exactly 5
  hop events of 508 bytes each; 5-hop sell payout anchor
  178,541, emitted as exactly 5 hop events of 449 bytes each.
- The 5-hop buy withholds only on the hop-1 vault quote ATA
  (10,000,000) and the buyback leg ATA (45,611). The
  intermediate hop vaults (vq2..vq5) withhold nothing: they are
  plain SPL accounts of non-quote mints, so the transfer fee
  never touches them. The 5-hop sell withholds only on the user
  quote account (1,804) and the buyback leg (9).
- The boost itself withholds a further 10,000,000 on the hop-1
  vault quote ATA: buy-then-boost burns 5,254,679,949,141 and
  sell-then-boost burns 5,338,394,848,076, each with the fresh
  hop-1 withheld doubled on the vault.
- The 5-hop buy pays 1,849,400 (1,844,400 rent for the
  auto-created 137-byte UVA + 5,000 fee), as at depth 5 in #125;
  every other leg pays the 5,000 fee only.

### One recovery call recovers exactly the stranded withheld

- Seed chain (creator sweep net 122,160 / withheld 1,234,
  collect destination net 120,938 / withheld 1,222): recovery
  pays 2,456 = 1,234 + 1,222. With the destination equal to
  the source vault ATA itself, the recovery still pays the
  full 2,456 into it.
- Buy chain: recovery pays 10,048,067 = 10,000,000 (hop-1 vault)
  + 45,611 (buyback) + 1,234 + 1,222 -- exactly the #69 3-hop
  buy value, unchanged at depth 5.
- Buy + protocol sweep chain: recovery pays 10,093,703, adding
  the protocol sweep's withheld 45,636 (sweep discharges
  4,563,570, net 4,517,934). The protocol bucket alone
  recovers as 45,636.
- Sell chain: recovery pays 4,269 = 1,804 + 9 + 1,234 + 1,222
  -- exactly the #69 3-hop sell value, unchanged at depth 5.
- Recovery is idempotent: a second recovery pays 0. A second
  sweep/collect/recovery round after a full recovery pays
  only the fresh protocol withheld 45,636 (the second creator
  sweep and collect are 0-event no-ops: the creator bucket
  is already drained).

### Authority gates hold at depth 5

- Recovery by a wrong signer fails custom 4 (payer delta 0,
  outsider payer -5,000, full rollback). Recovery under a zero
  authority fails custom 29. Recovery with an unsigned
  authority fails MissingRequiredSignature. All three cost
  only the 5,000 fee with full rollback of everything else.
- A failed recovery strands nothing: the retry by the right
  payer after an outsider failure pays the full 2,456.
- Harvest under a zero authority still lands (mint withheld
  2,456), but the following withdraw-from-mint fails custom
  29 and the mint keeps the 2,456.

### Harvest / withdraw-from-mint and the binding asymmetry

- Harvest then withdraw-from-mint is the two-step equivalent:
  seed harvest moves 2,456 to the mint and withdraw-from-mint
  pays it out; buy harvest moves 10,045,611 to the mint and
  withdraw-from-mint pays it out; buy+boost harvest moves
  20,045,611 to the mint and withdraw-from-mint pays it out.
  Withdraw-from-mint alone on a zero-withheld mint succeeds
  and moves 0.
- Recovery over zero sources succeeds with withheld unchanged.
  Recovery over a duplicated source pays 1,234 + 1,222 exactly
  once. An extensionless source is silently skipped (the
  1,234 is recovered afterwards, and the destination's 1,222
  separately). A wrong-mint source holding 999 withheld is
  silently skipped and its 999 is untouched.
- The destination binding is asymmetric. A wrong-mint
  destination fails custom 3. A destination owned by the
  legacy Token program fails IncorrectProgramId. Sources, by
  contrast, are skipped silently (see above).

### Recovery ordering against the boost at depth 5

- Buy+boost recovery pays 20,045,611 = 20,000,000 (buy + boost
  hop-1 withheld) + 45,611 (buyback). Sell+boost recovery pays
  10,001,813 = 1,804 + 9 + 10,000,000.
- Recovery itself is burn-neutral: buy-boost-sweep/collect/
  recovery-boost burns 5,172,890,909,983 on the second boost,
  byte-identical to the same walk without the recovery. The
  sweeps move the burn (as in #102/#112); the recovery does
  not.
- Harvest before a boost leaves the anchor burn untouched:
  buy-harvest-boost burns 5,254,679,949,141, the later
  recovery pays only the boost's fresh 10,000,000, and the
  mint keeps the harvested 10,045,611 throughout.

### Tf variants at depth 5

- tf5000 buy recovery pays 501,244,335 = 500,000,000 (hop-1
  vault) + 1,151,789 (buyback) + 61,697 (creator sweep
  withheld) + 30,849 (collect destination withheld). The
  tf5000 creator sweep nets 61,697 and the collect nets
  30,848.
- tf10000 is a NEW depth-5 pin: the 5-hop buy itself fails
  6039 with 0 events and full rollback (the 100% fee leaves
  nothing for the curve), while the 5-hop sell fails 6004
  with 5 events. After the failed buy, the seed sweep still
  runs but nets 0 with the whole 123,394 withheld in the
  creator vault ATA, the collect is a silent no-op, and the
  recovery pays the full 123,394 -- the #69 tf10000 seed
  behaviour, reached here through a failed buy.
- tf0 buy tail is 5,259,040,470,738; the creator sweep nets
  the full 123,394 and the collect nets the full 123,394
  with no withholding anywhere, and the recovery pays 0.

## Limits

- The tf10000 buy failure (6039) and sell failure (6004) are
  reported as measured; this packet does not identify the
  internal branch that rejects them, and the sell's 5 logged
  events on a failed transaction are reported as observed.
- The hop-vault non-withholding is a fixture property (hop
  vaults are plain SPL accounts of non-quote mints); on a
  chain where a hop vault itself carried the transfer-fee
  mint, that hop could withhold too.
- Error sites are recorded per image in the report's
  `error_sites` (Token-2022 failures carry no "thrown in" /
  "caused by account" site line, so none is asserted for them).

## Files

- `README.md` -- this file.
- `producer.py` -- the packet builder.
- `verify.py` -- independent re-verification.
- `MANIFEST.json` -- sha256 of every packet file except itself.
- `runtime/report.json.gz` -- 36 cases, 402 receipts, 41 parts
  (40x10 + 2), per-image expected values, error sites, image hashes.
- `runtime/raw-transactions-part01..41.jsonl.gz` -- the receipts,
  10 per part except part 41 (2).

## Verification

```
$ python3 verify.py
PASS: 36 cases, 402 receipts, 41 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, 5-hop tail anchor with 5 hop events, hop-1-only buy withheld with buyback leg, full buy/sell/seed recovery sums, authority gates 4/29/unsigned, harvest/withdraw-from-mint equivalence, idempotence and silent-skip tolerance with asymmetric destination binding, boost-doubled withheld with burn-neutral recovery, tf5000/tf10000/tf0 variants); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []
```

Made via @slopdotcash
