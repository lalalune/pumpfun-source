# research: signer and authority validation on the split x boost x tf chain

## Problem

The split x boost x tf chain (TRUE 3 hops, pinned by 3rd #63/#64)
has been measured for account-content validation: fee-table (#83),
GlobalConfig (#84), pools (#85), the UserVolumeAccumulator (#86),
the GlobalVolumeAccumulator (#87), and vaults and token accounts
(#88). What was not pinned is the other half of account
validation: the accounts that authorize the legs. When a setter,
a sweep, a boost, a trade, a claim, or a Token-2022 recovery leg
is called with the wrong signer, an unsigned signer, or a
readonly target account, which gate fires -- and does the
failure leak into the next leg?

This packet answers that on the same chain: three AMM hops
(main -> POOL2 -> P3, final output U3), the quote mint carrying
a 100 bps transfer-fee config, the split legs routing the
buyback through the TOKEN22 ATA. Every case is run against all
three program images (original, control, candidate) and every
case agrees on all three.

## Cases

82 cases, 318 receipts, 32 parts (31 x 10 + 8). Families:

- **A anchors (15).** Multi-hop buy/sell, v2 buy, deposit,
  protocol sweep, creator sweep + collect, boost at vq 10^9,
  token claim, cashback claim (plain mint), sync-fire, the four
  setter controls (buyback config, fee config, disable,
  update_admin), and set_coin_creator on the already-set pool
  (silent no-op). Anchor amounts reproduce #64 exactly:
  mhbuy3 in 10^9 -> U3 5,262,910,281,902, buyback 4,515,471,
  withheld vq1 10,000,000 / buyback 45,611; mhsell3 -> user
  quote +178,541; protocol sweep 2,488 -> net 2,463 (withheld
  25); creator sweep 123,394 -> net 122,160 (withheld 1,234);
  collect 122,160 -> net 120,938 (withheld 1,222); boost
  (vq 10^9) burns 5,338,379,201,831; token claim 3,334,551 ->
  net 3,301,205 (withheld 33,346); cashback claim 5,475 in full.
- **B admin signer (22).** Each setter (buyback config, fee
  config, disable, toggle_mayhem_mode, toggle_boost,
  update_admin) with an outsider signer, an unsigned signer,
  and a readonly GlobalConfig; plus stored-value variants
  patching GlobalConfig.admin to the outsider or to zero.
- **C boost authority (6).** Stored boost authority patched
  to the outsider or to zero, outsider-signed boost under a
  patched authority, unsigned authority, readonly authority,
  and outsider authority key under the stored payer authority.
- **D sweep/collect payer (8).** Outsider payer sweep,
  unsigned payer sweep, readonly pool / pool quote vault /
  recipient ATA on the protocol sweep, outsider recipient on
  the creator sweep, unsigned creator sweep, and outsider
  vault authority on collect (after a creator sweep filled
  the bucket).
- **E trade/liquidity user (11).** Outsider, unsigned, and
  readonly user on the multi-hop buy; unsigned user on the
  multi-hop sell, v2 buy, deposit, and withdraw; outsider
  user on the v2 buy and deposit; and a multi-hop buy with
  the main pool's creator patched to an outsider.
- **F claim/sync user (9).** Outsider user, unsigned payer,
  and readonly UVA on the token claim; outsider user and
  readonly UVA on the cashback claim; outsider user and
  readonly UVA on sync; close by another user and close
  unsigned.
- **G withdraw-withheld authority (6).** The #69 pattern on
  the split chain: outsider signer, unsigned signer, stored
  outsider authority, stored zero authority, harvest +
  withdraw-from-mint control, and harvest + withdraw-from-mint
  under a stored outsider authority.
- **H no-leak after authority failure (4).** Failed setter
  then anchor buy; failed boost then protocol sweep; failed
  token claim then anchor buy; failed withdraw-withheld then
  anchor sell.
- **I pool-authority PDA (1).** set_coin_creator with the main
  pool's creator patched to an outsider.

## Result

The gates are uniform within each family, and they split
cleanly by mechanism:

- **Setters: wrong signer 6005, unsigned 3010, readonly
  config 2000.** All five setter instructions (plus
  update_admin) behave identically: an outsider signer fails
  6005 InvalidAdmin (Anchor offset on PumpAmmError::
  InvalidAdmin = 5, via the `has_one = admin` constraint on
  the AdminGlobal struct), an unsigned signer fails 3010
  ConstraintSigner, and a readonly GlobalConfig fails 2000
  ConstraintMut with site "caused by account: global_config".
  The check is on the stored value, not the key: with
  GlobalConfig.admin patched to the outsider, the
  outsider-signed setter succeeds and the payer-signed
  setter fails 6005; with admin patched to zero, every
  signer fails 6005 -- the setters are bricked. This is the
  #75 rotation result seen from the stored-value side, and
  update_admin follows the same gate (a successful rotation
  hands the setters over completely, event emitted).
- **Boost authority: stored-value check, readonly authority
  succeeds.** With boost authority patched to the outsider,
  the payer-signed boost fails 6005 and the outsider-signed
  boost succeeds with a byte-identical burn
  (5,338,379,201,831 at vq 10^9, as in #64). With the
  authority patched to zero, the payer-signed boost fails
  6005 (the nonzero check fires before the window check).
  An unsigned authority fails 3010. But a readonly
  authority account SUCCEEDS with the identical burn: the
  authority is a signer that is never written, so its
  writable flag is not enforced. This is the only
  readonly-signer case in the packet that succeeds.
- **Sweeps and collect take no admin.** An outsider payer
  sweeps the protocol bucket for the anchor-identical
  2,488 -> 2,463 net, confirming #75's admin-independence
  on the split chain. An unsigned payer fails 3010. A
  readonly pool, pool quote vault, or recipient ATA each
  fail 2000 ConstraintMut (sites: pool, pool quote vault,
  recipient ATA). The creator sweep's recipient must be
  the creator-vault PDA (outsider recipient: 2006
  ConstraintSeeds), and collect's vault authority must be
  the creator-vault PDA (outsider authority: 2006 after
  the creator sweep filled the bucket).
- **Trade user: seeds check, not a signer check.** A
  multi-hop buy with an outsider user (signed, separate fee
  payer) fails 2006: the passed UVA is derived from the
  payer, not the outsider, so the PDA derivation fails
  before any amount moves. The same 2006 fires for a v2
  buy with an outsider user. An unsigned user fails 3010
  on every leg (multi-hop buy/sell, v2 buy, deposit,
  withdraw). A readonly user with the payer key fails
  with the runtime PrivilegeEscalation error (no Anchor
  site line): the multi-hop program passes the user
  account writable into a CPI, so the runtime -- not an
  Anchor constraint -- rejects the escalation. A deposit
  with an outsider user fails 2015 ConstraintTokenOwner:
  the user's base/quote/LP token accounts are payer-owned.
- **Claim user gates split by claim type.** A token claim
  with an outsider user fails 2015 (the user ATA is
  payer-owned, so the token-owner check fires first),
  while a cashback claim with an outsider user fails 2006
  (the UVA PDA is derived from the user key). An unsigned
  claim payer fails 3010. A readonly UVA fails 2000 on
  both claim types. A sync with an outsider user fails
  2006 and a sync with a readonly UVA fails 2000; close
  by another user fails 2006 and close unsigned fails
  3010 -- matching #68/#1 exactly.
- **Withdraw-withheld: #69 reproduced.** A wrong signer
  fails token custom 4 (OwnerMismatch), an unsigned signer
  fails MissingRequiredSignature, a stored authority of
  zero fails token custom 29, and a stored outsider
  authority fails custom 4 for both the direct withdraw
  and the harvest-then-withdraw-from-mint route (harvest
  itself needs no authority and succeeds; the mint
  withdrawal then fails custom 4).
- **Pool-authority PDA gate is real but narrow.** Patching
  the main pool's creator field (Pool.creator, bytes
  11..43) to an outsider makes multi-hop entry fail 6078
  OnlyPumpPools (multi_hop_swap.rs:499) and
  set_coin_creator fail 6028
  OnlyCanonicalPumpPoolsCanHaveCoinCreator
  (set_coin_creator.rs require_keys_eq, which runs before
  the already-set early return). Patching coin_creator
  (bytes 211..243) instead leaves both legs untouched:
  the trade succeeds anchor-identically and set returns
  its silent no-op -- the two fields must not be confused.
- **No leak after authority failure.** A failed setter
  then a full anchor buy, a failed boost then the
  protocol sweep, a failed token claim then a full anchor
  buy, and a failed withdraw-withheld then a full anchor
  sell all succeed with anchor-identical amounts.

All 82 cases agree on all three images (0 divergent cases
on the full expected surface, not just error codes).

## Limits

- The fee authority (admin_set_coin_creator_authority,
  GlobalConfig bytes 321..353) has no signer gate to
  measure: no instruction takes it as a signer, and the
  source only writes it (create_config, update_fee_config)
  without reading it back. It is out of scope here.
- The unsigned-signer cases use a separate outsider fee
  payer: when fee payer and user share a key, LiteSVM
  merges the signatures and the unsigned case succeeds
  (the #68 trap). Every unsigned case in this packet
  separates them.
- Error sites are recorded per image in the receipts and
  are never compared across images (line numbers differ
  between original and rebuilt code).
- The readonly-user multi-hop failure is a runtime
  PrivilegeEscalation, not an Anchor error: it carries no
  site line, so verify.py asserts the error code and the
  rollback only for that case.
- No source changes, no builds, no claim of whole-program
  equivalence: this packet pins the signer/authority gate
  surface on the split x boost x tf chain only.

Made via @slopdotcash
