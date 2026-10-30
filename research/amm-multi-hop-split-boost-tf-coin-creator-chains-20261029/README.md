# research: split x boost x tf chains meet coin-creator reassignment at TRUE 3-hop

## Problem

Packets #64/#65/#66 pinned the split x boost x transfer-fee chain at true
3-hop, true 4-hop and true 5-hop. Packet #33 pinned coin-creator
reassignment (set_coin_creator, sweep/collect reroute, migrate gates) on
single-pool trades. This packet asks whether #33's reassignment mechanism
survives composition with the split x boost x tf chain: does `set` reroute
the creator bucket on the chain, do the zero-creator and migrate gates
reproduce, and does reassignment move the chain itself (boost burn, tail
output, fee-tier crossing)?

The route is a TRUE 3-hop route: `three_amm` only, three hop groups, final
output token U3. No g4/g5 hop group is added.

## Setup

Three images are compared on every case: the original program, the
control rebuild (#424) and the candidate rebuild (#427). The chain is the
#64 chain: a split fee-table route (hop 1 fee-tier selection, tail hop
exotic flat fees) with a boost leg and a transfer-fee quote mint. The
case's `bps` field is the transfer-fee basis of the quote mint
(0 = plain quote, 100 = tf100 override). The main pool's seeded creator
bucket is 123,394 in every case.

Reassignment primitives, exactly as in #33:

- `set_coin_creator` accounts: [pool, metadata PDA, bonding-curve PDA,
  EVENT, PROGRAM]. The metadata PDA is derived from the metaplex program
  (`metaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s`) and the sharing-config
  PDA from the fees program (`pfeeUxB6jkeY1Hxd7CsFCAjcbHA9rWtchMGdZ6VojVZ`).
  With metadata creators present the first creator wins; with no
  creators the bonding-curve creator wins.
- `migrate_pool_coin_creator` accounts: [pool, sharing-config PDA, EVENT,
  PROGRAM]; it moves `coin_creator` (pool bytes 211..243) to the
  sharing-config PDA.

## Cases (19 cases, 77 steps, 231 receipts)

Family A — set on an already-set pool (bps 100 unless noted):

- `a-mhbuy-setnoop-wrongvault-swc-col`: mhbuy3, set, sweep of a
  non-creator vault, sweep of the original vault, collect to the
  original creator's Token-2022 ATA.
- `a-mhbuy-setnoop-mhbuy-swc-col`: mhbuy3, set, mhbuy3, sweep, collect.
- `a-set-already-set-noop`: set first, then mhbuy3, sweep, collect.

Family B — zero-creator pool:

- `b-zero-mhbuy` (bps 0): mhbuy3 alone.
- `b-zero-mhbuy-set-swc-col-new` (bps 0): mhbuy3, set to CREATOR0, sweep
  of the old (zero) vault, sweep of the new vault, collect to the new
  creator.
- `b-zero-mhbuy-set-mhbuy-swc-col-new` (bps 0): mhbuy3, set, mhbuy3,
  sweep, collect.
- `b-zero-mhbuy-set-bonding-swc-col` (bps 0, no metadata): mhbuy3, set
  (bonding-curve creator wins), sweep, collect.
- `b-zero-buy2-skip` (bps 0): a single-pool v2 buy on the zero pool.
- `b-zero-legacy-rejected` (bps 0): legacy buy and legacy sell on the
  zero pool.
- `b-zero-mhbuy-tf100-set-swc-col-new` (bps 100): mhbuy3, set, sweep,
  collect under tf100.

Family C — migrate gates (bps 100):

- `c-mhbuy-mig-fail-swc-col-mig`: mhbuy3, migrate (fails), sweep,
  collect, migrate (succeeds).
- `c-mig-buy2-swc-sh-col-blocked`: mhbuy3, sweep, collect, migrate,
  single-pool v2 buy, protocol sweep, sharing-vault sweep, sharing
  collect (blocked).
- `c-zero-mhbuy-set-swc-col-mig`: zero pool, mhbuy3, set to CREATOR0,
  sweep, collect, migrate (sharing admin = new creator).
- `c-mhbuy-mig-bad-admin-swc-col`: migrate with a sharing admin that is
  not the pool creator, then sweep and collect.

Family D — chain neutrality and recovery (bps 100):

- `d-mhbuy-boost-set-mhbuy-boost`: mhbuy3, boost, set, mhbuy3, boost.
- `d-mhbuy-boost-mhbuy-boost-anchor`: the same chain without set.
- `d-tiercap-set-mhbuy`: tier-crossing mhbuy3, set, tier-crossing
  mhbuy3 (fee tiers patched in place).
- `d-tiercap-mhbuy-mhbuy-anchor`: the same chain without set.
- `d-zero-mhbuy-set-swc-col-ww`: zero pool, mhbuy3, set, sweep,
  collect, one WithdrawWithheldTokensFromAccounts call.

## Result (0 divergent cases; control == candidate everywhere)

### Set is a silent no-op on an already-set pool, and only fires on a zero pool

On the already-set pool, `set` emits 0 events, costs only the 5,000
fee, and leaves `coin_creator` unchanged
(4052257bce28a510753a2426213a620a1c1b2a6cc2586e616e76e874212e1bae).
The chains that include it are byte-identical to the uninterrupted
anchors (Family A and Family D, below). On a zero-creator pool, `set`
fires: the metaplex event disc is 966bc77b7ccf66e4 (len 144) and
`coin_creator` becomes 1111… (CREATOR0); with no metadata creators the
bonding-curve event disc is f2e7eb664163bdd3 (len 144) and
`coin_creator` becomes 3333… (the bonding-curve creator).

### Reroute reproduces exactly

After a zero-to-CREATOR0 set, a sweep of the OLD (zero) vault fails
custom 2006 with a full rollback, and a sweep of the NEW vault drains
the whole seeded bucket 123,394. The new collect pays 123,394 to the
new creator's Token-2022 ATA. Under tf100 the same reroute goes through
the transfer-fee pipe: sweep net 122,160 / withheld 1,234, collect
destination net 120,938 / withheld 1,222 — the #5/#69 pipe, unchanged.
On the already-set pool the non-creator vault sweep also fails 2006,
and the original vault sweep/collect pay 122,160 / 120,938 under tf100
to the original creator's Token-2022 ATA (a distinct account from the
plain-Token destination used in #33's collect).

### Zero-creator asymmetry: multi-hop is transparent, v2 skips, legacy refuses

- Zero-pool multi-hop buy: tail output 5,315,084,721,958 and buyback
  4,607,153, byte-identical to the plain 0-bps tail in #67. The main
  creator bucket stays at the seed 123,394. The zero main creator is
  transparent to the multi-hop trade.
- Zero-pool single-pool v2 buy: spends 1,842,321 (not the normal
  1,847,796), vault net 1,833,835, buyback 8,486, BuyEvent len 500 —
  the creator fee is skipped wholesale, exactly as in #33.
- Zero-pool legacy buy and legacy sell: both fail custom 6053
  (BuybackFeeRecipientNotAuthorized, global_config.rs:326) with a
  full rollback, exactly as in #33.

### Migrate gates reproduce exactly

- Migrate before sweeping fails custom 6081 (CreatorFeesNotSwept,
  migrate_pool_coin_creator.rs:59). After sweep (123,394) and collect,
  migrate succeeds: event disc aadd52c793a5f72e, len 176, old creator
  4052… / 1111… to new creator 00227b4418b2609389185b46abad39b4e37f35940229a719bab852a8c0705960
  (the sharing-config PDA).
- Migrate with a sharing admin that is not the pool creator fails
  custom 6046 (InvalidSharingConfigCoinCreator); sweep and collect
  afterwards still work.
- After a successful migrate, a single-pool v2 buy accrues 5,563 to
  the main creator bucket (buy spend 1,896,275, vault net 1,868,776,
  vq1 withheld 18,877, buyback withheld 87 under tf100); the protocol
  sweep drains 4,572,193 (net 4,526,471 / withheld 45,722); the sharing
  vault sweep drains the 5,563 (net 5,507 / withheld 56); and the
  sharing collect fails custom 6048 (CreatorVaultMigratedToSharingConfig,
  collect_coin_creator_fee.rs:68) with a full rollback.
- Zero-to-set-to-migrate also succeeds when the sharing admin is the
  new creator (CREATOR0).

### Reassignment does not move the chain

- Boost chains: first buy tail 5,221,217,806,636, first boost burn
  5,255,205,915,165, second buy tail 4,956,499,821,134, second boost
  burn 5,093,856,866,968 — identical with and without the set-noop in
  between. The boost step emits 2 events (a leading 512-byte BuyEvent
  plus the 208-byte BoostEvent).
- Tier-cap chains: first buy buyback net 5,379,839 (tier A), second
  buy buyback net 10,642,838 (tier B), second tail 4,972,170,179,853 —
  identical with and without the set-noop.
- Recovery: after zero-to-set, sweep and collect, one
  WithdrawWithheldTokensFromAccounts call recovers exactly 2,456
  (1,234 + 1,222) under tf100, the same stranded total as #69.

## Limits

- The transfer-fee quote mint's `withdraw_withheld_authority` is
  patched to the payer after the transfer-fee override, as in #69;
  without the patch the authority is zero and recovery fails
  custom 29.
- The migrate cases patch the sharing-config admin and the
  sharing-config PDA bytes by construction; they pin the gate
  behaviour, not the sharing-config provisioning path.
- The zero-creator pool is produced by zeroing the main pool's
  `coin_creator` bytes (211..243) after route construction, as in #33.
- Error sites are recorded per image in the report's `error_sites`
  (Token-2022 failures carry no "thrown in" / "caused by account"
  site line, so none is asserted for them).

## Files

- `README.md` — this file.
- `producer.py` — the packet builder (MEASURE mode emits per-step
  measurements; the normal run writes receipts and the report).
- `verify.py` — independent re-verification.
- `MANIFEST.json` — sha256 of every packet file except itself.
- `runtime/report.json.gz` — 19 cases, 231 receipts, 24 parts
  (23x10 + 1), per-image expected values, error sites, image hashes.
- `runtime/raw-transactions-part01..24.jsonl.gz` — the receipts,
  10 per part except part 24 (1).

## Verification

```
$ python3 verify.py
PASS: 19 cases, 231 receipts, 24 parts, per-image expectations hold (signatures, deltas, withheld, mint withheld, lamports, events, error codes, rollback, UVA fields, pool creator bytes, sweep/collect/set/migrate/boost events, GVOL invariance); control == candidate everywhere; original agrees everywhere (0 divergent cases): []
```

Made via @slopdotcash
