# research: signer and authority validation on the split x boost x tf chain at TRUE 5 hops

## Problem

Packet #89 pinned the signer and authority surface on the TRUE
3-hop split chain: setters fail 6005 for a wrong signer, 3010
for an unsigned signer, 2000 for a readonly GlobalConfig; the
boost authority is a stored-value check with a readonly
authority succeeding; sweeps take no admin; trade user faults
fail 2006/3010; claim/sync user faults fail 2015/2006/3010;
withdraw-withheld authority faults fail token custom 4/29 and
MissingRequiredSignature; and no authority failure leaks into
the next leg. This packet asks whether every one of those
holds at depth 5, on the split x boost x tf chain
(three_amm + g4 + g5, final output U5), and adds three things
#89 did not cover: the user signer on the 5-hop sell, the
signer-check order on setters under combined faults, and tf
variants of the signer gates.

Route check (read from the builder, not the packet name):
build_route calls three_amm and appends the g4 and g5 hop groups,
so the fixture route is main -> POOL2 -> P3 -> P4 -> P5, final
output U5: TRUE 5 hops. #61 appended g4 only and was actually 4
hops; this packet appends g4 AND g5 and names itself 5-hop,
matching. Hop pools carry proper pool data (bump,
pool-authority creator, own base mints, own vaults) per the #119
lesson; a routed hop pool with raw main-pool bytes fails 6008.

## Cases

98 cases, 372 receipts, 38 parts (37 x 10 + 2), each run on three
images (original, control rebuild, candidate rebuild). All cases
use the bps-100 tf fixture unless a tf variant says otherwise.
Fee payer lamport cost is 5,000 per step (fee only on failure
with full rollback) and 1,849,400 per successful 5-hop swap
(5 hop events; the trade creates the UVA at 1,844,400 lamports).

- A (anchors, 15): 5-hop buy, 5-hop sell, v2 buy, deposit,
  protocol sweep, creator sweep + collect, boost at vq 10^9,
  token claim, cashback claim (plain mint), sync-fire, the four
  setter controls (buyback config, fee config, disable,
  update_admin), and set_coin_creator on the already-set pool
  (silent no-op).
- B (admin signer, 22): each setter (buyback config, fee
  config, disable, toggle_mayhem_mode, toggle_boost,
  update_admin) with an outsider signer, an unsigned signer,
  and a readonly GlobalConfig; plus stored-value variants
  patching GlobalConfig.admin to the outsider or to zero.
- C (boost authority, 6): stored boost authority patched to
  the outsider or to zero, outsider-signed boost under a
  patched authority, unsigned authority, readonly authority,
  and outsider authority key under the stored payer authority.
- D (sweep/collect payer, 8): outsider payer sweep, unsigned
  payer sweep, readonly pool / pool quote vault / recipient
  ATA on the protocol sweep, outsider recipient on the creator
  sweep, unsigned creator sweep, and outsider vault authority
  on collect (after a creator sweep filled the bucket).
- E (trade/liquidity user, 11): outsider, unsigned, and
  readonly user on the 5-hop buy; unsigned user on the 5-hop
  sell, v2 buy, deposit, and withdraw; outsider user on the v2
  buy and deposit; and a 5-hop buy with the main pool's
  creator patched to an outsider.
- F (claim/sync user, 9): outsider user, unsigned payer, and
  readonly UVA on the token claim; outsider user and readonly
  UVA on the cashback claim; outsider user and readonly UVA on
  sync; close by another user and close unsigned.
- G (withdraw-withheld authority, 6): outsider signer,
  unsigned signer, stored outsider authority, stored zero
  authority, harvest + withdraw-from-mint control, and harvest
  + withdraw-from-mint under a stored outsider authority.
- H (no-leak after authority failure, 4): failed setter then
  anchor buy; failed boost then protocol sweep; failed token
  claim then anchor buy; failed withdraw-withheld then anchor
  sell.
- I (pool-authority PDA, 1): set_coin_creator with the main
  pool's creator patched to an outsider.
- J (5-hop sell signer, 4, new): outsider user, payer-readonly
  user, and outsider-readonly user on the 5-hop sell; failed
  sell then anchor buy.
- K (signer-check order, 7, new): outsider signer + readonly
  config and unsigned signer + readonly config on buyback
  config, disable, and toggle_mayhem_mode; outsider + readonly
  setter failure then anchor buy.
- T (tf variants, 5, new): outsider user on the 5-hop buy at
  tf5000, unsigned user on the 5-hop buy at tf0, outsider
  setter at tf5000, boost-authority-outsider at tf0, unsigned
  sweep at tf5000.

## Result

0 divergent cases: original, control and candidate agree on
every case, including every error code, event count and balance
delta. Error sites are pinned per image in the report and are
never compared across images.

Anchors (bps-100 tf, 5 hop events each direction): 5-hop buy
tail 5,207,955,235,891 with buyback leg 4,515,471 (per-hop vault
deltas vb1 -5,332,264,170,203 / vq1 +985,438,918 through vb5
-5,207,955,235,891 / vq5 +5,248,308,076,854, buyback ATA
+4,515,471); 5-hop sell payout 178,541 with buyback leg 837;
boost at vq 10^9 burns 5,338,379,201,831 (requested = used =
1,000,000,000, quote_after 123,936,690,720); protocol sweep
2,488 -> net 2,463 (withheld 25); creator sweep 123,394 ->
net 122,160 (withheld 1,234); collect 122,160 -> net 120,938
(withheld 1,222); token claim 3,334,551 -> net 3,301,205
(withheld 33,346); cashback claim 5,475 in full.

Setters: wrong signer 6005, unsigned 3010, readonly config
2000, on all five setter instructions plus update_admin, at
depth 5 exactly as at 3 hops. The check is on the stored
value, not the key: with GlobalConfig.admin patched to the
outsider, the outsider-signed setter succeeds and the
payer-signed setter fails 6005; with admin patched to zero,
every signer fails 6005 -- the setters are bricked. A
successful rotation hands the setters over completely.

Boost authority: stored-value check, readonly authority
succeeds. With boost authority patched to the outsider, the
payer-signed boost fails 6005 and the outsider-signed boost
succeeds with a byte-identical burn (5,338,379,201,831 at
vq 10^9). With the authority patched to zero, the payer-signed
boost fails 6005 (the nonzero check fires before the window
check). An unsigned authority fails 3010. But a readonly
authority account SUCCEEDS with the identical burn: the
authority is a signer that is never written, so its writable
flag is not enforced. This is the only readonly-signer case
in the packet that succeeds.

Sweeps and collect take no admin: an outsider payer sweeps
the protocol bucket for the anchor-identical 2,488 -> 2,463
net. An unsigned payer fails 3010. A readonly pool, pool
quote vault, or recipient ATA each fail 2000 ConstraintMut.
The creator sweep's recipient must be the creator-vault PDA
(outsider recipient: 2006 ConstraintSeeds), and collect's
vault authority must be the creator-vault PDA (outsider
authority: 2006 after the creator sweep filled the bucket).

Trade and liquidity users at depth 5: an outsider user fails
2006 ConstraintSeeds on both the 5-hop buy and the 5-hop sell
(0 events, full rollback) -- the user accounts are
seed-checked, so a wrong user key fails the seeds gate, not
a signer gate. An unsigned user fails 3010 on the 5-hop buy,
the 5-hop sell, the v2 buy, deposit, and withdraw. A
payer-readonly user fails PrivilegeEscalation (a runtime
error, not a program error code) on both the 5-hop buy and
the 5-hop sell: a readonly fee payer cannot pay. A 5-hop buy
with the main pool's creator patched to an outsider fails
6078 OnlyPumpPools, and set_coin_creator with the same patch
fails 6028 -- the pool-authority PDA derivation check from
#89 reproduces at depth 5.

Claim and sync users: token claim with an outsider user fails
2015 ConstraintTokenOwner (the claim's user token account
owner check); cashback claim and sync with an outsider user
fail 2006; close by another user fails 2006; unsigned payer
on the token claim and unsigned close fail 3010; a readonly
UVA fails 2000 on the token claim, the cashback claim, and
sync.

Withdraw-withheld authority: outsider signer fails token
custom 4, unsigned signer fails MissingRequiredSignature,
stored outsider authority fails custom 4, stored zero
authority fails custom 29 -- the #69 pattern reproduced on
the 5-hop chain. Harvest + withdraw-from-mint succeeds under
the stored payer authority and fails custom 4 under the
stored outsider authority (the harvest itself succeeds; the
withdraw-from-mint step fails).

NEW -- signer-check order on setters (family K): an outsider
signer on a readonly config fails 2000, not 6005 -- the
writable check fires before the admin check. An unsigned
signer on a readonly config fails 3010, not 2000 -- the
signer check fires before the writable check. So the setter
gate order at depth 5 is 3010 > 2000 > 6005: signer first,
then writable, then admin. The same order holds on buyback
config, disable, and toggle_mayhem_mode alike, and the
failed setter leaves the next anchor buy untouched (tail
5,207,955,235,891, 5 events).

NEW -- 5-hop sell signer (family J): the sell side mirrors
the buy side exactly (outsider 2006, payer-readonly
PrivilegeEscalation, outsider-readonly 2006, 0 events), and
a failed sell does not leak into the next anchor buy.

NEW -- tf variants (family T): outsider user on the 5-hop
buy fails 2006 at tf5000, unsigned user fails 3010 at tf0,
outsider setter fails 6005 at tf5000, boost-authority-outsider
fails 6005 at tf0, unsigned sweep fails 3010 at tf5000.
Signer validation is tf-neutral: the transfer-fee rate does
not move, mask or reorder any gate.

After an authority failure the downstream legs all still work
with no leak: a failed setter then a full anchor buy, a
failed boost then the protocol sweep, a failed token claim
then a full anchor buy, and a failed withdraw-withheld then
a full anchor sell all succeed with anchor-identical amounts.

## Limits

- Signer mutations (outsider key, unsigned flag, readonly
  flag) and stored-authority patches (GlobalConfig.admin,
  boost authority, withdraw-withheld authority, pool
  creator) are harness fixture edits recorded with empty
  transactions where applicable, not on-chain instructions;
  they measure the program's authorization logic against a
  given signer/authority state, not an attacker's ability to
  reach that state on chain.
- Ghost counts are measured on this fixture route (main ->
  POOL2 -> P3 -> P4 -> P5); other routes were not re-measured
  here. Trade-leg signer faults carry 0 events in both
  directions at depth 5: the seeds/signer check fires before
  any hop executes.
- The payer-readonly PrivilegeEscalation is a runtime
  privilege error, not a program error code; it is reported
  as observed, not as a program gate.
- No source change is proposed. This packet records measured
  authorization behaviour only; it does not claim the full
  program is equivalent across images.

Made via @slopdotcash
