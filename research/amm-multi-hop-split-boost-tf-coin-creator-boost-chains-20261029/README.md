# research: split x boost x tf chains meet coin-creator reassignment at the boost leg, at TRUE 3-hop

## Problem

Packet #70 pinned coin-creator reassignment (`set_coin_creator`,
`migrate_pool_coin_creator`, sweep/collect reroute, migrate gates) on the
split x boost x tf chain, including one boost chain with a set no-op in
the middle. What #70 did not measure is the interaction in the other
direction: the boost leg itself against reassignment — does a patched-window
boost burn move when the creator changes, does a sweep to the NEW vault move
the next burn the way a sweep to the old vault does, does migrate change the
boost, and does any of this reproduce on the hop pools (P2/P3), where
`set`/`migrate` use that pool's own base-mint metadata, bonding-curve and
sharing-config PDAs? This packet answers those questions on the same true
3-hop split x boost x tf route (three_amm only, final output U3).

The route is a TRUE 3-hop route: `three_amm` only, three hop groups, final
output token U3. No g4/g5 hop group is added.

## Setup

Three images are compared on every case: the original program, the
control rebuild (#424) and the candidate rebuild (#427). The chain is the
#64/#115 chain: a split fee-table route (hop 1 fee-tier selection, tail hop
exotic flat fees) with a boost leg and a transfer-fee quote mint. The
case's `bps` field is the transfer-fee basis of the quote mint
(100 = tf100 override unless noted). The main pool's seeded creator
bucket is 123,394 in every case, and so is each hop pool's.

Reassignment primitives, exactly as in #33/#70:

- `set_coin_creator` accounts: [pool, metadata PDA, bonding-curve PDA,
  EVENT, PROGRAM]. The metadata PDA is derived from the metaplex program
  (`metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s`) and the sharing-config
  PDA from the fees program (`pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`).
  With metadata creators present the first creator wins; with no
  creators the bonding-curve creator wins. On an already-set pool `set`
  is a silent no-op (0 events, only the 5,000 fee); it fires only on a
  zero-creator pool.
- `migrate_pool_coin_creator` accounts: [pool, sharing-config PDA, EVENT,
  PROGRAM]; it moves `coin_creator` (pool bytes 211..243) to the
  sharing-config PDA, and only after the creator bucket has been swept
  (else 6081 CreatorFeesNotSwept).
- Hop-pool variants `set2`/`mig2` (P2, base mint BASE2) and `set3`/`mig3`
  (P3, base mint BASE3) use that pool's own PDAs. P2 and P3 are canonical
  pools (creator = the pool-authority PDA of their base mint), so the
  canonical-pool gate in `set` passes for them exactly as for the main
  pool.

Boost anchors on this route (request 10^9, min-base 0, vq field patched
to 10^9 unless noted): main boost 5,338,379,201,831 fresh,
5,254,679,949,141 after a buy, 5,254,441,549,265 second burn; hop-pool
boost 999,997,999 fresh, 989,418,199 after a buy. The buy tail is
5,262,910,281,902 (buyback leg 4,515,471 + withheld 45,611).

## Cases (32 cases, 174 steps, 522 receipts)

Family A — main-pool patched-window boost meets the set no-op (bps 100):

- `A-boost-set-boost`: boost, set, boost.
- `A-set-boost`: set, boost.
- `A-buy-set-swc-boost`: buy, set, creator sweep, boost.
- `A-buy-set-swc-col-boost`: buy, set, creator sweep, collect, boost.
- `A-buy-boost-set-boost`: buy, boost, set, boost.

Family B — zero main pool: boost before/after set, rerouted sweep/collect
(bps 100):

- `B-zero-boost`: zero coin_creator, boost.
- `B-zero-set-boost`: zero, set, boost.
- `B-zero-mhbuy-set-boost`: zero, buy, set, boost.
- `B-zero-set-swc-col-boost`: zero, set, sweep to the NEW vault, collect
  to the new creator, boost.
- `B-zero-mhbuy-set-swc-col-boost`: zero, buy, set, sweep to the NEW
  vault, collect to the new creator, boost.

Family C — migrate on the main pool, then boost / sharing sweep / blocked
collect (bps 100, sharing admin = the pool creator):

- `C-mhbuy-mig-fail-boost`: buy, migrate (fails), boost.
- `C-mhbuy-swc-col-mig-boost`: buy, sweep, collect, migrate, boost.
- `C-mig-boost-swc-sh-col-blocked-boost`: buy, sweep, collect, migrate,
  boost, sharing sweep, sharing collect (blocked), boost.
- `C-mig-mhbuy-boost`: buy, sweep, collect, migrate, buy, boost.
- `C-mig-mhbuy-swc-sh-boost`: buy, sweep, collect, migrate, buy, sharing
  sweep, boost.

Family D — hop-pool reassignment (bps 100; sharing2 admin = the P2 creator):

- `D-zero-p2-set-boost`: zero P2 coin_creator, set2, P2 boost.
- `D-zero-p2-mhbuy-set2-p2boost`: zero P2, buy, set2, P2 boost.
- `D-zero-p2-set2-swc-col-p2boost`: zero P2, set2, sweep to the NEW
  vault, collect to the new creator, P2 boost.
- `D-zero-p2-set2-mhbuy-p2boost`: zero P2, set2, buy, P2 boost.
- `D-zero-p3-set-boost`: zero P3 coin_creator, set3, P3 boost.
- `D-zero-p3-set3-swc-col-p3boost`: zero P3, set3, sweep to the NEW
  vault, collect to the new creator, P3 boost.
- `D-p2-mig-fail-boost`: buy, migrate2 (fails), P2 boost.
- `D-p2-swc-col-mig-boost`: buy, P2 sweep, P2 collect, migrate2, P2 boost.
- `D-p2-mig-boost-swc-sh-col-blocked-boost`: buy, P2 sweep, P2 collect,
  migrate2, P2 boost, P2 sharing sweep, P2 sharing collect (blocked),
  P2 boost.
- `D-p2-mig-mhbuy-p2boost`: buy, P2 sweep, P2 collect, migrate2, buy,
  P2 boost.

Family E — tf variants:

- `E-zero-set-swc-col-boost-tf5000`: zero, set, rerouted sweep+collect,
  boost at tf5000.
- `E-mig-boost-tf0`: buy, sweep, collect, migrate, boost at tf0.
- `E-zero-p2-set2-boost-tf5000`: zero P2, set2, P2 boost at tf5000.

Family F — cashback claim after reassignment, and set inside longer walks:

- `F-set-claim`: set, cashback claim (tf0 quote mint, seeded UVA).
- `F-zero-set-claim`: zero, set, cashback claim (tf0 quote mint, seeded UVA).
- `F-buy-set-sell-boost`: buy, set, sell, boost.
- `F-boost-set-sell-boost`: boost, set, sell, boost.

## Result (0 divergent cases; control == candidate everywhere)

### The set no-op is boost-blind, and so is the coin_creator field itself

A set on the already-set main pool emits 0 events, leaves
`coin_creator` unchanged
(4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae), and
leaves every boost burn byte-identical: fresh boost 5,338,379,201,831
before and after the set, second burn 5,254,441,549,265, buy-then-boost
5,254,679,949,141, buy-boost-set-boost 5,172,699,871,084. A zero-creator
pool boosts at exactly the anchor burn too (5,338,379,201,831), so the
boost leg never reads `coin_creator` at all — it reads vaults and the
vq field, not the creator field.

### Zero-to-set fires, and the rerouted sweep moves the next main burn

On a zero pool, `set` fires: the metaplex event disc is
966bc77b7ccf66e4 (len 144) and `coin_creator` becomes 1111…
(CREATOR0). After zero-to-set, a sweep of the NEW vault drains the whole
seeded bucket 123,394 (net 122,160 / withheld 1,234 under tf100) and the
collect pays 120,938 (withheld 1,222) to the new creator's Token-2022
ATA. The next patched-window boost then burns 5,338,384,474,298 —
exactly the anchor burn + 5,272,467, the #109 creator-sweep slope
(123,394 x ~42.73/unit). The rerouted sweep moves the burn by precisely
the same amount as a sweep to the old vault: after buy + set + rerouted
sweep + collect, the boost is 5,254,685,098,328, identical to the
old-vault sweep+collect walk (post-buy burn + 5,149,187 — the
collect step itself never moves the burn, only the sweep does).
Mechanism, as pinned by #112: the sweep moves the pool's vq field up by
exactly the swept bucket (−125,882 → −2,488), and the main boost burn
reads the vq field.

### Migrate gates reproduce, and the boost after migrate is the swept value

- Migrate before sweeping fails custom 6081 (CreatorFeesNotSwept,
  migrate_pool_coin_creator.rs:59) with a full rollback, and the
  following boost is the untouched post-buy burn 5,254,679,949,141.
- After sweep (123,394) and collect, migrate succeeds: event disc
  aadd52c793a5f72e, len 176, old creator 4052… to new creator
  00227b4418b2609389185b46abad39b4e37f35940229a719bab852a8c0705960
  (the sharing-config PDA). The following boost is the swept post-buy
  burn 5,254,685,098,328 — migrate itself moves nothing.
- After migrate, a sharing sweep with a zero bucket is a 0-event no-op,
  and the sharing collect fails custom 6048
  (CreatorVaultMigratedToSharingConfig, collect_coin_creator_fee.rs:68)
  with a full rollback; the second boost is then 5,172,704,860,229.
- A buy after migrate has the second-buy tail 5,072,980,706,277 and its
  boost is 5,172,938,878,067. The post-migrate buy accrues nothing to
  the main creator bucket — the multi-hop creator fee is charged only
  at the terminal hop (#115) — so the sharing sweep after it is again a
  0-event no-op and the boost is unchanged.

### Hop-pool reassignment reproduces the main-pool gates exactly

- Zero P2 + set2 fires to CREATOR0 (144-byte metaplex event, P2
  `coin_creator` 1111…), and the P2 boost is the anchor hop burn
  999,997,999. After a buy, set2 then P2 boost is the post-buy hop burn
  989,418,199. Zero P3 + set3 behaves identically (P3 boost
  999,997,999).
- Zero P2 + set2 + sweep to the NEW vault pays the full 123,394 (plain
  SPL hop mint, no withholding) and the collect pays the full 123,394
  to the new creator; the P2 boost is still exactly 999,997,999. The
  same holds for P3 (sweep 123,394, collect 123,394, P3 boost
  999,997,999). Contrast with the main pool, where the identical sweep
  pair moves the burn by +5,272,467: at hop scale the 123,394-unit
  sweep pair (vq field up, real vault down) leaves the hop boost burn
  byte-identical, while the buy-scale vault moves (10^12) move it by
  ~10,579,800. The hop burn is insensitive to sweep-scale moves; the
  main burn is not.
- Migrate2 before sweeping fails 6081; after P2 sweep (123,394) and
  collect, migrate2 succeeds and P2 `coin_creator` becomes
  f67da02d8ff46763fd208909115b2380a6c78e58b824965e12633557d4e46762
  (the P2 sharing-config PDA). The P2 boost after migrate2 is the
  post-buy hop burn 989,418,199. A P2 sharing sweep with a zero bucket
  is a 0-event no-op, the P2 sharing collect fails 6048, and the
  second P2 boost is 989,416,230. A buy after migrate2 has the
  second-buy tail 5,072,980,706,277 and its P2 boost is 979,167,679.

### Tf variants and the claim gate

- At tf5000, the rerouted sweep nets 61,697 (half of 123,394 withheld)
  and the rerouted collect nets 30,848 (half of 61,697 withheld, 1-unit
  rounding: 30,848 + 30,849); the following main boost burns
  2,706,769,696,611. At tf0, the boost after migrate burns
  5,306,497,528,599. The P2 boost after zero-to-set2 is tf-blind:
  999,997,999 at tf5000, identical to tf100.
- Cashback claim after set still fails custom 2021 under the
  transfer-fee quote mint (tf0 included), with a full rollback — both
  for the already-set pool and after zero-to-set. Reassignment does
  not rescue the claim gate on this route (see also #114).
- Longer walks stay inert under set: buy, set, sell, boost ends at
  5,254,695,806,281 (sell payout 185,288); boost, set, sell, boost ends
  at 5,254,457,135,466 (sell payout 182,879).

## Limits

- The zero-creator pools are produced by zeroing the pool's
  `coin_creator` bytes (211..243) with a harness field reset, as in
  #33/#70; the `set`/`migrate` steps themselves are real instructions.
- The migrate cases patch the sharing-config admin and the
  sharing-config PDA bytes by construction; they pin the gate
  behaviour, not the sharing-config provisioning path.
- The transfer-fee quote mint's `withdraw_withheld_authority` is
  patched to the payer after the transfer-fee override, as in #69;
  without the patch the authority is zero and recovery fails
  custom 29. No withdraw-withheld cases are in this packet.
- The hop-burn sweep insensitivity is reported as measured (byte-identical
  burns); the packet does not prove the rounding mechanism behind it.
- Error sites are recorded per image in the report's `error_sites`
  (Token-2022 failures carry no "thrown in" / "caused by account"
  site line, so none is asserted for them).

## Files

- `README.md` — this file.
- `producer.py` — the packet builder (MEASURE mode emits per-step
  measurements; the normal run writes receipts and the report).
- `verify.py` — independent re-verification.
- `MANIFEST.json` — sha256 of every packet file except itself.
- `runtime/report.json.gz` — 32 cases, 522 receipts, 53 parts
  (52x10 + 2), per-image expected values, error sites, image hashes.
- `runtime/raw-transactions-part01..53.jsonl.gz` — the receipts,
  10 per part except part 53 (2).

## Verification

```
$ python3 verify.py
PASS: 32 cases, 522 receipts, 53 parts, per-image expectations hold (signatures, deltas, withheld, lamports, events, error codes, rollback, pool creator_fee_bps/config creator-fee fields/UVA/GVA/mint fields, account lengths, cpatch harness resets, set no-op boost-blindness, zero-pool set firing, rerouted sweep moves main burn +5272467 but not hop burns, migrate gates 6081/6048, hop-pool set2/set3/migrate2 reproduction, tf5000 reroute halving, claim gate 2021 after set); control == candidate everywhere; original agrees everywhere; (0 divergent cases): []
```

Made via @slopdotcash
