# research: split x boost x tf chains meet withdraw-withheld recovery (TRUE 3-hop)

## Problem

3rd #64/#65/#66 pinned the split x boost x transfer-fee chain at TRUE
depths 3, 5, and 4, 3rd #67 chained token/cashback claims onto it,
and 3rd #68 chained the UVA lifecycle onto it. 3rd #28 pinned
WithdrawWithheldTokensFromAccounts recovery on a single-pool
setup, but nobody had chained the recovery onto the split chain:
after a sweep and a collect on the split chain, the first hop's
withheld sits stranded in the vault ATA while the collect's own
withheld sits in the destination -- can one
WithdrawWithheldTokensFromAccounts call recover both, do the
authority gates (wrong signer, zero authority, unsigned authority)
hold on the split chain exactly as in #28, is the destination
mint binding asymmetric (wrong-mint destination fails, wrong-mint
sources are silently skipped), do sweep/collect/withdraw move
lamports the way the seed chain says, and does the recovery move
the boost burn, the tail output, or the hop-1 tier-cap crossing
at all?

Route (read from the builder, not the packet name): `three_amm`
only, no g4/g5 hop group appended, so the route is
main -> POOL2 -> P3, final output U3: TRUE 3 hops. The quote mint
carries a per-case transfer-fee config (100/5000/10000 bps) with
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
on the split chain here, not copied from #28/#5 -- where they
match, that is itself the result.

## Cases (25 cases, 264 receipts, 27 parts)

- `a-swc-col-ww`, `a-swc-col-ww-dest-is-source`: the seed chain
  (sweep, collect, withdraw) under tf100, the second with the
  destination equal to the creator vault ATA itself.
- `a-swc-col-ww-tf5000`, `a-swc-col-ww-tf10000`: the seed chain
  at higher bps.
- `a-buy-swc-col-ww-all`, `a-sell-swc-col-ww-all`: split buy and
  split sell chains, sweep, collect, then one withdraw over all
  withheld sources.
- `b-ww-wrong-authority` (outsider fee payer), `b-ww-zero-authority`
  (no authority patch), `b-zero-auth-harvest-wfm-fails`,
  `b-ww-payer-unsigned`: recovery authorization gates.
- `c-harvest-then-wfm`, `c-wfm-zero`, `c-ww-twice`,
  `c-ww-zero-sources`, `c-ww-dup-source`: harvest / mint
  withdrawal, idempotence, empty and duplicated source lists.
- `d-ww-extensionless-source`, `d-ww-wrongmint-source`,
  `d-ww-wrongmint-dest`, `d-ww-tokenowned-dest`: source/destination
  binding asymmetry.
- `e-buy-boost-swc-col-ww-buy-boost` (main vq patched to 10^9),
  `e-buy-boost-buy-boost-anchor`: recovery between two
  buy-boost legs, with the uninterrupted anchor.
- `e-tiercap-ww-buy` (main vq patched to 10^9, tiers
  A = (10, 111, 333) at cap 100, B = (20, 222, 444) at cap
  185,000,000,000), `e-tiercap-buy-buy-anchor`: recovery
  between the tier-cap crossing buys, with the uninterrupted
  anchor.
- `e-buy-swc-col-ww-swc-col-ww`: recovery, then a second
  sweep/collect/recovery round.
- `e-proto-swc-ww`: the protocol bucket's withheld recovered
  alone.

## Result

- One recovery call recovers exactly the stranded withheld.
  Under tf100 the seed chain is sweep net 122,160 / withheld
  1,234, collect destination net 120,938 / withheld 1,222, and
  the recovery pays 2,456 = 1,234 + 1,222 -- the first hop's
  withheld, stranded in the creator vault ATA, plus the
  collect's own withheld. With destination equal to the source
  vault ATA the recovery still pays the full 2,456 into it.
- The recovered amount scales with bps. At tf5000 the sweep
  withholds 61,697 and the collect destination withholds
  30,849, and the recovery pays 92,546. At tf10000 the sweep
  nets 0 with the whole 123,394 withheld in the vault ATA,
  the collect is a silent no-op, and the recovery pays the
  full 123,394.
- On the split buy chain under tf100 the first hop withholds
  10,000,000 in vq1 and the buyback withholds 45,611, and
  after sweep and collect one recovery pays 10,048,067 =
  10,000,000 + 45,611 + 1,234 + 1,222. On the split sell
  chain the user quote withholds 1,804 and the buyback
  withholds 9, and one recovery pays 4,269 =
  1,804 + 9 + 1,234 + 1,222.
- The authority gates reproduce #28 exactly. Recovery by a
  wrong signer fails custom 4 (payer delta 0, outsider payer
  -5,000, full rollback; a later recovery by the right payer
  succeeds). Recovery under a zero authority fails custom 29.
  Recovery with an unsigned authority fails
  MissingRequiredSignature. All three cost only the 5,000
  fee with full rollback of everything else.
- Harvest then withdraw-from-mint is the two-step equivalent:
  harvest moves the account withheld to the mint (account
  withheld 0, mint withheld 2,456) and withdraw-from-mint
  pays the 2,456 out; under a zero authority the mint
  withdrawal fails custom 29. Withdraw-from-mint alone on a
  zero-withheld mint succeeds and moves 0.
- The recovery is idempotent and tolerant. A second recovery
  pays 0. Recovery over zero sources succeeds with withheld
  unchanged. Recovery over a duplicated source pays
  1,234 + 1,222 exactly once. An extensionless source is
  silently skipped (the 1,234 is recovered afterwards, and
  the destination's 1,222 separately). A wrong-mint source
  holding 999 withheld is silently skipped and its 999 is
  untouched.
- The destination binding is asymmetric. A wrong-mint
  destination fails custom 3. A destination owned by the
  legacy Token program fails IncorrectProgramId. Sources, by
  contrast, are skipped silently (see above).
- Lamport movement follows the gross/net split: the sweep
  moves lamports with the gross amount (creator vault ATA
  +123,394, vq1 -123,394), while collect and
  withdraw-withheld move no lamports at all (fees aside).
- The recovery moves nothing on the chain. Buy, boost, sweep,
  collect, recovery, buy, boost recovers 20,048,067 =
  vq1 20,000,000 (buy 10M + boost 10M) + buyback 45,611 +
  1,234 + 1,222, and its second buy tail 4,956,499,821,134
  and second boost burn 5,093,856,866,968 are byte-identical
  to the uninterrupted anchor. The second boost's vq and
  quote-after differ from the anchor by exactly 123,394 --
  that is the sweep repricing the accrued creator bucket into
  vq 1:1 (the vq + accrued window is unchanged across the
  sweep), not the recovery.
- The tier-cap crossing survives the recovery. The first buy
  (buyback net 5,379,839, buyback withheld 54,342) is followed
  by a recovery of 10,054,342 = 10,000,000 + 54,342, and the
  second buy (buyback 10,642,838, tail 4,972,170,179,853) is
  byte-identical to the uninterrupted anchor's second buy.
- A second sweep/collect/recovery round is a no-op: the
  second sweep and collect are silent, and the second
  recovery pays 0. The protocol bucket alone recovers
  cleanly: sweep 2,488, protocol ATA net 2,463 / withheld 25,
  recovery 25.

## Limits

- Token-2022 failures leave no "thrown in" / "caused by
  account" site line in the logs, so this packet asserts the
  error code and full rollback for them, and records no site
  line (per-image sites are not compared across images
  anywhere else in the packet either).
- The wrong-authority and unsigned-authority cases use a fee
  payer different from the authority account: when fee payer
  and authority are the same key, LiteSVM merges the
  fee-payer signature onto the authority meta and the
  unsigned recovery succeeds instead of failing
  MissingRequiredSignature (measured during construction;
  the packet pins the separated-payer form, matching
  3rd #68's unsigned-user cases).
- Only the quote mint carries a transfer fee here; the
  withdraw-withheld destination mint is the quote mint
  itself, and the mint authority patch is applied after the
  transfer-fee override (the override rewrites the mint
  data, so patching first would be lost).
- All amounts are LiteSVM replays of signed receipts, not
  mainnet transactions.

## Reproduce

```
python3 verify.py
```

Expected output:

```
PASS: 25 cases, 264 receipts, 27 parts, per-image expectations hold (0 divergent cases)
```

Made via @slopdotcash
