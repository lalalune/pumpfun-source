# research: split x boost x transfer-fee chains meet the boost gates

## Problem

Earlier packets pinned each boost gate alone: the authority check
(#75, #89), the boost-enabled toggle (#76), the buy-disable bit
(#77), the vault gates (#98), the window and the burn (#100). What
was never pinned on one chain is how those gates compose: when two
or three gates fail at once, which error surfaces, and whether the
authority, admin, and fee-authority fields are really three
separate checks or one. This packet measures all of that on the
same true-3-hop split x boost x tf chain (three_amm only, final
output U3 -- the route 3rd #63/#64 pinned), at vq 10^9 unless a
case says otherwise, transfer fee 100 bps unless a case says
otherwise.

## Cases

83 cases, 546 receipts, 55 parts (54x10 + 6), three images
(original / control / candidate) per step. The anchor boost is a
10^9-quote boost burning **5,338,379,201,831**.

### G. Boost authority basics (15 cases)

- `g-anchor`: the anchor burn itself.
- `g-auth-outsider`, `g-auth-zero`: stored authority outsider or
  zero, payer-signed boost -> **6005 InvalidAdmin**, 0 events.
- `g-auth-outsider-boost-o`: stored authority outsider,
  outsider-signed boost -> anchor burn exactly. The burn is
  signer-blind given an authority match.
- `g-auth-payer-boost-o`: stored authority payer,
  outsider-signed boost -> 6005.
- `g-auth-readonly`: authority meta passed non-signer, key =
  payer, stored = payer -> anchor burn. The fee-payer signature
  satisfies the check (see Result).
- `g-auth-readonly-outsider`, `g-auth-zero-key`: authority meta
  non-signer, key = outsider or zero -> **3010
  AccountNotSigner** (`caused by account: authority`), 0 events.
  A readonly meta is not itself a pass; the payer case passes
  only because the payer signed as fee payer.
- `g-auth-restore`: outsider stored -> 6005, restored to payer
  -> anchor.
- `g-auth-rot-outsider`, `g-auth-rot-payer-boost`,
  `g-auth-rot-zero`: `set_boost_authority` (112-byte event,
  disc `5980f08d5bca4769`) by the admin moves the stored
  authority; the boost follows the stored value in every step
  (outsider-signed anchor after rotation to outsider, 6005 for
  payer-signed after rotation to outsider or zero, anchor again
  after rotation back to payer).
- `g-auth-rot-unsigned`: `set_boost_authority` with a non-signer
  admin meta -> 3010, stored authority unchanged, next boost
  anchor.
- `g-auth-rot-outsider-signer`: `set_boost_authority` signed by
  the outsider -> 6005, stored authority unchanged.
- `g-auth-rot-then-off`: rotation to outsider, boost toggle off,
  outsider-signed boost -> 6066, toggle on, outsider-signed
  boost -> anchor.

### A. Admin / fee-authority separation (7 cases)

- `a-admin-rot-boost`: `update_admin` (80-byte event, disc
  `e198ab57f63f42ea`) to outsider, payer-signed boost -> anchor;
  rotation back by the outsider, boost -> anchor. The boost
  never reads the admin field.
- `a-admin-rot-dis`: after rotation, disable by payer -> 6005,
  disable by outsider -> success (buy bit set), clear by
  outsider -> success, boost -> anchor, rotation back by
  outsider -> success, boost -> anchor.
- `a-admin-rot-tog`: after rotation, boost toggle by payer ->
  6005, by outsider -> success (boost off), boost -> 6066,
  toggle on by outsider -> success, boost -> anchor, rotation
  back -> success, boost -> anchor.
- `a-admin-rot-ufc`: after rotation, `update_fee_config` by
  payer -> 6005, by outsider -> success (lp 30, proto 40,
  authority 0x63x32), restore by outsider -> fixture (lp 20,
  proto 5), rotation back -> success, boost -> anchor.
  `update_fee_config` follows the admin, not the fee authority.
- `a-feeauth-patch-ufc`, `a-feeauth-zero-ufc`,
  `a-feeauth-patch-dis`: fee authority patched to outsider,
  zero, or 0x63x32 before the call changes nothing --
  `update_fee_config` and disable by payer still succeed, and
  `update_fee_config` overwrites the fee authority with its own
  authority argument. The boost is fee-authority-blind too.

### S. Disable / toggle / pool-flag matrix (12 cases)

- `s-dis-sell`, `s-dis-create`, `s-dis-dep`, `s-dis-wd`:
  sell/create/deposit/withdraw disable bits set, boost ->
  anchor; cleared, boost -> second-boost burn
  5,254,441,549,265 (the #100 decay).
- `s-dis-buy`, `s-dis-buy-sell`: buy bit (alone or with sell)
  -> **6020**, cleared -> anchor-then-decay as above.
- `s-tog-boost-off`: boost toggle off -> **6066** (the toggle
  itself is a silent 0-event setter), on -> anchor.
- `s-tog-mayhem`, `s-tog-cashback`: global mayhem/cashback
  toggles off and back on -> anchor both times.
- `s-flag-cb`, `s-flag-mayhem`, `s-flag-both`: pool cashback /
  mayhem / both flags on the main pool -> anchor.

### D. Gate-order duels and triples (29 cases)

Each case stacks two (or three) failing gates on one boost and
records which error surfaces. The full duel table is in Result;
the pattern is a single total order, and every triple agrees
with it:

- Authority duels: auth-outsider beats window-0, boost-off,
  buy-disable, bucket-10^12, empty base vault, and zero boost
  ATA -- always 6005.
- Boost-off duels: off beats window-0, buy-disable, bucket,
  base vault, and ATA -- always 6066.
- Buy-disable duels: buy-disable beats window-0, base vault,
  quote vault, bucket, ATA, and short ATA -- always 6020
  (the short-ATA 6088 check never runs, because the gate fires
  before the burn is computed).
- Window duels: window-0 beats empty base vault and zero ATA
  -- always 6065.
- ATA duels: zero ATA beats empty base vault, empty quote
  vault, and bucket-10^12 -- always 6002.
- Vault duels: empty quote vault beats empty base vault
  (6023, not 6001); bucket-10^12 beats empty base vault
  (6023); empty quote vault beats short ATA (6023 -- the
  compute failure precedes the post-compute 6088 check).
- Triples: auth+off+buydis -> 6005; off+buydis+window0 ->
  6066; buydis+vb0+vq0 -> 6020; auth+off+window0 -> 6005.

### R. Failure recovery / leak checks (11 cases)

- `r-base-mhbuy-vq1e9` vs `r-auth-fail-mhbuy`: a multi-hop buy
  after a failed (6005) boost has byte-identical deltas and
  pool states to the same buy with no failed boost before it.
  The failed boost leaves nothing behind.
- `r-base-swp` vs `r-off-fail-swp`: a protocol sweep after a
  failed (6066) boost pays the same 2,488.
- `r-base-tclaim` vs `r-buydis-fail-tclaim`: a token claim
  after a failed (6020) boost still pays the full 3,334,551.
- `r-bucket-fail-restore`, `r-ata-fail-restore`,
  `r-vb0-fail-restore`: bucket-10^12 (6023), zero ATA (6002),
  and empty base vault (6001) failures, followed by a
  field restore, all recover the anchor burn exactly. The
  restores are harness field resets, not on-chain instructions.
- `r-window0-fail-vq`: window-0 boost fails 6065, then a
  vq patch to 10^9 in the same case boosts at the anchor.
- `r-multi-fail-seq`: four boosts in one case -- 6005 (auth),
  6005 (auth still outsider, now also off), 6066 (auth
  restored, still off), anchor (enabled restored). Gate
  state composes step to step with no residue.

### T. Transfer-fee variation of the gates (6 cases)

- `t-auth-tf0`, `t-auth-tf5000`: authority mismatch -> 6005
  at tf0 and tf5000.
- `t-off-tf5000`: boost-off -> 6066 at tf5000.
- `t-buydis-tf0`: buy-disable -> 6020 at tf0.
- `t-boost-o-tf5000`: outsider-signed boost with stored
  outsider authority at tf5000 -> 2,706,767,012,738, the #100
  tf5000 anchor exactly.
- `t-window0-tf5000`: window-0 -> 6065 at tf5000. The gates
  are transfer-fee-blind; only the burn amount moves with tf.

### M. Multi-user boost (3 cases)

- `m-boost-p-after-buy` vs `m-boost-o-after-buy`: after the
  same multi-hop buy, payer-signed and outsider-signed
  (stored outsider) boosts both burn 5,255,205,915,165, the
  #99 post-buy burn.
- `m-boost-o-twice`: two outsider-signed boosts in a row burn
  5,338,379,201,831 then 5,254,441,549,265 -- the same decay
  as payer-signed boosts. The buyer of the previous trade is
  irrelevant to the burn.

## Result

0 divergent cases across all 83: original, control, and candidate
agree on every error, event, delta, and pool state (error sites
are pinned per image, never compared across images).

The boost gates form one total order -- first failure wins:

**6005 InvalidAdmin (authority) > 6066 (boost enabled) > 6020
(buy-disable) > 6065 (window zero) > 6002 (boost ATA zero) >
6023 (quote-side: empty quote vault or hop-1 bucket at 10^12) >
6001 (base vault empty).**

Every one of the 29 duel/triple cases agrees with this order;
no pair inverts it. Two readings fall out of the order. First,
the authority check is a signature check, not a key-equality
check with a signature loophole: a readonly authority meta
passes only when the authority is the fee payer (whose
signature covers every account in the transaction), and fails
3010 AccountNotSigner for any other key. Second, the 6088
"requested exceeds ATA balance" check runs after the burn is
computed: a short ATA loses to every earlier gate (6020, 6023)
and only surfaces when all earlier gates pass (#100).

Authority, admin, and fee authority are three separate fields
with three separate readers: the boost reads only the boost
authority, the admin-gated setters (disable, toggles,
update_fee_config, update_admin itself, set_boost_authority)
read only the admin, and nothing in this packet's legs reads
the fee authority at all -- patching it to outsider, zero, or
0x63x32 changes no outcome, and update_fee_config overwrites
it with its own authority argument rather than checking it.

Only the buy disable bit gates a boost. The other four disable
bits, both global mode toggles, and both pool flags leave the
anchor burn byte-identical, and every failed boost is fully
rolled back: the next multi-hop buy, sweep, claim, or boost
lands exactly on its own baseline.

## Relation to earlier packets

- #75 (admin rotation): the update_admin / set_boost_authority
  instructions and their events (80 / 112 bytes) are reused
  here; the new finding is that rotation composes with the
  boost gates (admin-blind boost, admin-gated setters).
- #76 (mode toggles): the silent toggles are reused; the new
  finding is their position in the gate order (boost-off is
  second, after authority only) and their irrelevance to the
  burn when off is not the failing gate.
- #77 (disable): the bit matrix is completed for the boost
  leg -- buy only -- and positioned third in the order.
- #89 (signer / authority): the readonly-authority success is
  explained, not just observed -- it is the fee-payer
  signature, and readonly outsider / zero fail 3010.
- #98 (vault balances): the vault gates are positioned at the
  tail of the order (ATA 6002, quote-side 6023, base 6001),
  with the quote-before-base asymmetry pinned by the
  vb0+vq0 duel.
- #100 (boost window): the anchor burns, the decay, and the
  tf ladder are reproduced exactly, including by
  outsider-signed boosts; the 6088 post-compute check is
  confirmed indirectly (short ATA loses to 6020 and 6023).

## Limits

- The gate order is pinned for the main-pool boost leg only.
  The tail-pool boost is window-0-only (#100); its gate order
  under authority / toggle / disable faults is not covered.
- Within the 6023 group, the empty-quote-vault failure and the
  bucket-overflow failure share one code and are not separated
  further; the overflowing computation itself is not
  identified from these receipts alone.
- The fee authority's true consumer, if any, is not identified
  -- only that boost, disable, and update_fee_config do not
  read it as a gate on this chain.
- Bucket / vault / ATA / vq restores in the recovery cases are
  harness field resets used to prove the failure left no other
  state behind; they do not demonstrate on-chain recovery
  instructions.
- No 6088 case is re-triggered here: every short-ATA duel
  fails at an earlier gate (6020 or 6023). The 6088 pin itself
  stands on #100.

## Reproduction

`producer.py` rebuilds the receipts (same builder that produced
them); `verify.py` re-verifies them from the packet files alone
plus the three program images (original, control #424, candidate
#427). Part files are 10 receipts each, gzip-compressed JSONL.

Made via @slopdotcash
