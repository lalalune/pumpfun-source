# amm-multi-hop-split-boost-tf-account-length-chains-20261029

## Problem

3rd #82 pinned fee-table truncation, #83-#88 pinned account
validation (discriminator, owner, lamports, key substitution),
and #92 pinned state transitions on the split x boost x tf
chain at TRUE 3 hops (three_amm only, final output U3). What
none of them pinned is length as its own axis: every core
account has a byte length, and the program reads each one
through a different loader with a different minimum. Which
lengths succeed, which gate, what a truncated account prices
at when it still succeeds, what a successful trade writes
back into a truncated account, and what a byte-level restore
does to the next trade -- all on the same chain, with the
same anchors (#93: buy 10^9 quote pays tail U3
5,262,910,281,902 with buyback 4,515,471; sell 10^9 base pays
178,541 with buyback 837; plain second buy 5,072,980,706,277).

This packet truncates and extends each core account mid-case
-- between real trades, with no transaction of its own, so a
patch leaves no receipt -- and pins the length gate, the
price at each surviving length, the post-trade rewrite, and
the inspection order when two accounts are broken at once.
"Restore" in this packet means rewriting one account's bytes
to its pre-case snapshot: it is byte-level, not ledger-level,
and the packet pins exactly where that distinction bites.

## Cases

91 cases, 588 receipts, 59 parts (58x10 + 8), three program
images (original, control, candidate) per step. Fixture
lengths: pool 300, GlobalConfig 949, fee-table 4097, UVA 137,
GVA 600, SPL token account 165, Token-2022 input/vault
accounts 178, buyback ATA 182, quote mint 278.

Family A -- main pool length, buy direction: anchor, 299,
279, 245, 211, 210, 100, 8, 0, 301, 400, 1000 (each followed
by a byte-restored buy, except the anchor).

Family B -- hop-position pool length: middle pool 299, 100,
400; tail pool 299, 0; sell direction with main pool 299, 0
(each followed by a byte-restored trade).

Family C -- GlobalConfig length: 948, 907, 906, 900, 500,
100, 0, 950, 2000 (each followed by a byte-restored buy);
sweep after a failed buy with config restored; boost with
config truncated then restored (vq patch 10^9).

Family D -- fee-table length: standard route 4096, 3000,
2512, 2511, 2097, 2096, 1, 0, 5000 (each followed by a
byte-restored buy); stable route 4073, 4072 (each followed
by a byte-restored stable buy); downstream legs under a
3000-byte table (buy, protocol sweep, creator sweep,
collect, restored buy).

Family E -- UVA length, seeded accumulator (needs 1,
unclaimed 111, claimed 222, volume 333444, last 20, has 1,
earned 555, cashback-claimed 666): claim at 136, 90, 200,
1000; claim at 89 then extend then claim; claim at 1 and 0
then extend then claim; trade with UVA at 89 and 0 then
restored trade; close with UVA at 89 then init.

Family F -- GVA length, seeded accumulator: sync then claim
at 543, 544, 600, 1000, 100, 0; sync at 543 then sync
restored then claim restored.

Family G -- token-account length: user input (Token-2022,
178) at 164, 100, 0, 166, 167, 200; tail output (SPL, 165)
at 164, 166, 167, 200; main quote vault (Token-2022, 178)
at 164, 165, 167, 180; buyback ATA (182) at 181, 170, 165,
183, 200; quote mint (278) at 100, 200, 277, 300 (each
followed by a byte-restored buy, except as noted).

Family H -- inspection order (two broken accounts at once,
then one restored, then both restored): pool 100 + UVA 89;
config 500 + UVA 89; fee 2511 + UVA 89; pool 100 + fee 2511;
pool 100 + config 500; config 500 + fee 2511; downstream
sweep under a truncated pool; pool walk and fee walk
(buy, patched buy, restored buy, buy).

## Result

All 91 cases agree on all three images: **0 divergences**.
Error sites are pinned per image, never compared across
images.

- Pool: 211 bytes is the exact floor. At 211..260 the buy
  succeeds and prices with vq read as zero: tail
  5,262,904,992,332, exactly 5,289,570 below anchor -- a
  direct vq = 0 control buy reproduces that tail to the
  unit, so the missing vq field zero-fills rather than
  gating. At 261 and above the buy is anchor-identical, and
  at 210 and below it fails InvalidAccountData (caused by
  account: pool). The loader needs the header through
  lp_supply (203..211) and tolerates every trailing field
  missing. A successful buy rewrites a truncated pool
  account to the full 287-byte struct (a 245-byte pool is
  287 bytes after the buy), so truncation does not persist
  past a successful trade; a failed buy rolls back and the
  truncation persists. Ghost ladder: main-pool failure 0
  events, middle-hop failure 1 ghost, tail-hop failure 2
  ghosts on buys, main-pool failure 2 ghosts on sells.
- The buy rewrites pool virtual reserves, and only some
  pools. Main-pool vq moves by exactly the protocol
  accrual (-125,882 -> -4,686,964 on the anchor buy, a
  delta of -4,561,082 against a protocol bucket delta of
  +4,561,082); tail-pool vq moves by exactly the creator
  accrual (-125,882 -> -2,645,503,408); the window sum
  vq + protocol + creator stays exactly 0 for both. The
  middle pool is never touched by a buy (all four fields
  byte-identical before and after). That asymmetry is why
  restoring the middle pool is inert while restoring the
  main or tail pool is not (see below).
- GlobalConfig: 907 bytes is the exact floor for a buy.
  At 907..949 and at 950/2000 the buy is anchor-identical:
  the buy never reads bytes 907..949 (boost authority,
  boost enabled, creator-fee-configurable, max creator
  fee). At 906 and below it fails InvalidAccountData
  (caused by account: global_config) with 0 events -- one
  byte into buyback_basis_points (899..907) breaks the
  whole read. The buy path's config floor is buyback_bps,
  not the account size. Boost does read config: boost
  under a 500-byte config fails InvalidAccountData, and
  with config restored it burns 5,338,379,201,831 (the
  fresh vq 10^9 anchor). Sweep after a failed buy with
  config restored pays the fresh protocol bucket in full
  (2,488 -> net 2,463).
- Fee-table: the #82 gates re-confirm on the chain.
  4096/3000/2512 price at the flat fallback (+1 tail,
  5,262,910,281,903, on a fresh curve only -- later
  fallback buys equal the exotic buy to the unit, as #95
  pinned); 2511 and 2097 fail 6083 FeeConfigTooShort
  (fees.rs:184); 2096 fails 3003; 1 and 0 fail 3001; 5000
  is anchor-identical (trailing bytes ignored). Stable
  route: 4073 succeeds at the anchor, 4072 fails 6082
  FeeTiersEmpty with 2 ghost events. Downstream legs do
  not read the table: under a 3000-byte table the buy
  still falls back, the protocol sweep pays 4,563,570 ->
  net 4,517,934, the creator sweep 123,394 -> net 122,160,
  collect 122,160 -> net 120,938, and the restored buy
  pays 5,072,967,425,209.
- UVA: 90 bytes is the floor. Claim at 136, 90, 200, and
  1000 all pay the full 3,334,551 (claimed 222 ->
  3,334,773, volume -> 0, last -> 21); there is no upper
  bound in the tested range. At 89 the claim fails 3003,
  and extend restores the account to 137 with every field
  preserved (needs 1, unclaimed 111, claimed 222, volume
  333444, last 20, has 1, earned 555, cashback-claimed
  666) plus 1 event, after which the claim pays in full.
  At 1 and 0 the claim fails 3001, extend fails 6027
  (extend_account.rs:91, a different site from #86's
  disc-zero 6027 at :114), and the claim still fails
  3001 -- a sub-discriminator UVA cannot be extended
  back. A trade deserializes the UVA: trade with UVA at
  89 fails 3003 and at 0 fails 3001, both with 0 events,
  and the restored trade is anchor-identical. Close with
  UVA at 89 fails 3003, and init on the still-truncated
  account also fails 3003: init does not overwrite a
  malformed existing account.
- GVA: 544 bytes is the floor. Sync then claim at 544,
  600, and 1000: sync is a 0-event no-op (last 20 equals
  start 20, so the pre-start gate does not fire) and the
  claim pays the full 3,334,551. At 543 and 100 both sync
  and claim fail 3003; at 0 both fail 3001. Restoring the
  GVA bytes restores both legs (sync no-op, claim full).
- Token accounts: each slot has its own length rule.
  Input (Token-2022, 178): 165 succeeds, 166 fails
  InvalidAccountData (caused by account:
  user_in_token_account), 167 and above succeed
  anchor-identical including withheld -- the single
  trailing byte is the only failing extension stub.
  Output (SPL, 165): only exactly 165 succeeds; 164,
  166, 167, and 200 all fail InvalidAccountData (caused
  by account: user_out_token_account). Main quote vault
  (Token-2022, 178): 164 fails InvalidAccountData
  (caused by account: pool_quote_token_account), 165 and
  167 fail Token custom 13 with 0 events and no site
  line, 180 and 200 succeed anchor-identical. Buyback
  ATA (182): 181, 170, and 165 fail Token custom 13 with
  0 events, 183 and 200 succeed -- the buyback leg needs
  the full 182-byte extension and tolerates trailing
  bytes. Quote mint (278): 277 and 200 fail 6007
  UnsupportedQuoteMint (transfer_fee.rs:32), 166/165/100
  fail InvalidAccountData (caused by account:
  quote_mint), 300 succeeds anchor-identical -- cutting
  even one byte off the mint's extension breaks the
  transfer-fee read, while trailing zeros are ignored.
- Inspection order for a buy, from six two-error
  contests: **GlobalConfig > UVA > pool > fee-table**.
  Pool 100 + UVA 89 fails 3003 (UVA beats pool);
  config 500 + UVA 89 fails InvalidAccountData
  (global_config beats UVA); fee 2511 + UVA 89 fails
  3003 (UVA beats fee); pool 100 + fee 2511 fails
  InvalidAccountData (pool beats fee); pool 100 +
  config 500 fails InvalidAccountData (global_config
  beats pool, told apart by the site line); config 500
  + fee 2511 fails InvalidAccountData (global_config
  beats fee). Each contest's single-error fallback
  (second step) reproduces that account's own error,
  and the fully restored third step is anchor-identical.
- Restore is byte-level, not ledger-level. Restoring
  one account's bytes to its pre-case snapshot while
  vaults and token balances keep the trade's movements
  prices the next buy off a hybrid state whenever the
  restored account feeds the price, and is inert
  otherwise. Hybrid next buys: main pool restored after
  an anchor buy 5,072,797,372,654; main pool restored
  after a vq-zero buy 5,072,797,521,447; tail pool
  restored after an anchor buy 5,072,967,425,209 (the
  same value as the second buy after a flat-fallback
  buy, because the fallback buy leaves the tail pool
  exactly at fixture: flat creator 0 accrues nothing,
  so tail vq never moves); main vault restored after
  an anchor buy 5,112,903,787,841. Inert restores, all
  giving the plain second buy 5,072,980,706,277:
  middle pool (never touched), fee-table, config,
  user balances, buyback ATA. The ledger-level bite:
  sweeping the post-buy protocol bucket (4,563,570),
  restoring the pool bytes (which resurrects the
  2,488 bucket field), and sweeping again pays 2,488
  -> net 2,463 a second time; the following buy then
  prices at 5,072,980,906,297, not the plain second
  buy. Walks show the same split: the pool walk runs
  5,262,910,281,902 -> 5,072,980,706,277 ->
  4,892,799,527,955 -> 4,722,389,388,493 while the fee
  walk runs 5,262,910,281,902 -> 5,072,980,706,277 ->
  4,893,138,106,561 -> 4,722,704,279,356 -- identical
  through the second buy, diverging at the third
  exactly where the pool restore turns hybrid and the
  fee restore stays inert.

## Relation to earlier packets

- #82 established the fee-table length gates (3001/3003/
  6083/6082, boundaries 2097/2512/4073/4097); this packet
  re-confirms every one on the chain and adds the
  downstream-leg and stable-route pins.
- #83-#88 established per-account validation (disc,
  owner, lamports, key substitution, check order
  3012 > 3007 > disc code); this packet adds the length
  axis and the cross-account inspection order for buys.
- #86 established UVA length (90 floor, extend paths)
  and that trades deserialize the UVA; this packet adds
  the 1000-byte upper range, the 1/0-byte extend failure
  at extend_account.rs:91, and the close/init behaviour
  on a truncated UVA.
- #87 established GVA length (544 floor) and the start
  reset gate; this packet adds the sync/claim pair at
  each length and the restore leg.
- #92 established the window invariant (vq + protocol +
  creator constant) and that sweep/collect are price
  neutral; this packet quantifies the buy's rewrite
  (main vq absorbs protocol accrual exactly, tail vq
  absorbs creator accrual exactly, middle pool untouched)
  and shows where a byte-level restore breaks the
  neutrality story.
- #95 established that the fee table is read live and
  that the flat fallback +1 is fresh-curve only; this
  packet's fee-length buys and walks rely on both.

## Limits

- Patches are applied directly to account data between
  steps; they are not transactions and leave no receipt.
  The receipt stream pins the before/after state of every
  real step, and producer.py records every patch in the
  case definitions, so the sequence is reproducible from
  the packet files -- but a patch itself has no signature
  to verify.
- The "restore" steps rewrite one account only. The
  hybrid-state values they produce are harness
  artifacts of that method, not program behaviour on a
  real chain (no instruction restores a single account
  while leaving vaults moved); they are reported here
  because they identify exactly which accounts feed the
  next trade's price.
- The 166-byte single-stub failure on Token-2022
  accounts and the exact-165 rule on the SPL output
  account are recorded as measured patterns; the packet
  does not pin them to a source line.
- Token custom 13 (vault and buyback ATA failures) is
  reported as a code only: Token-2022 failures leave no
  "thrown in"/"caused by account" site line, so no site
  is claimed for them.
- The config floor of 907 bytes is for the buy path
  only. Boost and setter paths read further into the
  config (boost under a 500-byte config fails), and the
  boost floor between 500 and 949 is not measured here.
- Only the TRUE 3-hop route (three_amm, final output U3)
  is used; 4-hop and 5-hop routes are covered by #61/#62
  and #65/#66 and are not re-run here.

## Reproduce

`python3 producer.py` rebuilds the receipts under
`runtime/` (10 per part, 59 parts); `python3 verify.py`
re-checks signatures, deltas, withheld, pool/UVA/GVA/
GlobalConfig states, decoded events, error codes, rollback,
and three-image agreement from the packet files alone.

Made via @slopdotcash
