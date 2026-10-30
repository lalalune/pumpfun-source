# research: split-chain trades ignore the reserved-fee list — setter storage, whitelist single-hop binding, mayhem reserved gate, chain neutrality

## Problem

The brief for this packet was to compose the 2nd-run #50 reserved fee
recipients bridge onto the split×boost×tf chain (true 3 hops,
`three_amm` only, final output U3): how do split-chain trades accrue
into a reserved bucket, does a reserved collect move the chain, what
happens when the list is replaced, and do 0/1/8 recipients behave
differently? Measurement first corrected the premise: there is no
reserved bucket. `set_reserved_fee_recipients` writes two things into
GlobalConfig — a whitelist PDA (353..385) and 8 reserved recipients
(385..417, 418..642) — and those two fields bind two different paths:
the whitelist zeroes fees on single-hop `trade::fees` paths, and the
reserved list gates the protocol fee recipient on mayhem pools. The
multi-hop route consults neither. So this packet pins the setter's
storage, the whitelist's single-hop binding adjacent to the chain,
the reserved list's mayhem gate, and the split chain's complete
indifference to all of it.

Route confirmation (from the builder itself): the fixture route calls
`three_amm` only and appends no g4/g5 hop group — 3 hop groups, final
output U3. This packet does not repeat 3rd #61's naming error (a "3-hop"
packet whose builder actually appended a P4 group).

One scope note, measured first: the setter requires exactly 8
remaining accounts — 7 fail, a 9th is ignored, duplicates are
accepted — so "0 recipients" and "1 recipient" are not settable
states; the count dimension is pinned through the 7/8/9/dup cases
instead. The fixture reserved member used in family M is the config
byte range 385..417 as it stands before any setter call
(`GesfTA3X2arioaHp8bbKdjG9vJtskViWACZoYvxp4twS`); its TOKEN22 ATA
for the quote mint is `2dmiSdVXhau9JVgrW7BFhYZCnPhDX8vKZ4Rj8vsowAb3`.

## Cases

32 cases, 57 steps, 171 receipts (57 steps × 3 images), 18 parts
(17×10 + 1). All cases run the same steps on the original, control
(#424) and candidate (#427) images. All families run under tf100 on
the quote mint unless noted. Setter cases use recipient keys
`0x61..0x69` (R0..R8), unfunded key `0x72`, and the fixture
PROTOCOL account as a recipient where noted.

Family S — setter storage alone (9 cases):

- `s-set-8`: whitelist = PAYER, recipients R0..R7.
- `s-set-9`: whitelist = PAYER, recipients R0..R8 (9 remaining).
- `s-set-7`: whitelist = PAYER, recipients R0..R6 (7 remaining).
- `s-set-zero`: first recipient = default pubkey.
- `s-set-dup`: all 8 recipients = R0.
- `s-set-outsider`: setter signed by a non-admin.
- `s-set-unsigned`: setter with the admin account not signing.
- `s-set-exec`: first recipient = the TOKEN program account.
- `s-set-unfunded`: first recipient = the unfunded key.

Family R — reserved/whitelist vs the split chain (7 cases):

- `r-anchor`: mhbuy3 of 10^9, no setter (anchor).
- `r-wl-buy`: setter (whitelist PAYER, R0..R7), then mhbuy3.
- `r-wl-sell`: setter (whitelist PAYER, R0..R7), then mhsell3.
- `r-wl-other`: setter (whitelist = unrelated key, R0..R7), then mhbuy3.
- `r-res-proto`: setter (whitelist PAYER, recipients
  [PROTOCOL, R1..R7]), then mhbuy3.
- `r-buy-buy`: two mhbuy3 legs of 10^9, no setter (control).
- `r-buy-setr-buy`: mhbuy3, setter (whitelist PAYER, R0..R7),
  mhbuy3 again.

Family W — whitelist vs single-hop legs adjacent to the chain (4 cases):

- `w-leg-std`: setter (whitelist PAYER, R0..R7), then legacy buy
  10^9 with the standard 3-account remaining layout.
- `w-leg-trim`: setter (whitelist PAYER, R0..R7), then legacy buy
  10^9 with the trimmed 2-account remaining layout.
- `w-leg-other`: setter (whitelist = unrelated key, R0..R7), then
  legacy buy 10^9 with the standard remaining layout.
- `w-v2`: setter (whitelist PAYER, R0..R7), then v2 buy 10^6.

Family M — reserved list vs mayhem pools (4 cases, main pool
flagged mayhem):

- `m-noset`: legacy buy 10^9, protocol recipient = fixture
  PROTOCOL, no setter call.
- `m-res0`: legacy buy 10^9, protocol recipient = fixture
  reserved member, no setter call.
- `m-replaced`: setter (whitelist = unrelated key, recipients
  [PROTOCOL, R1..R7]), then legacy buy with the old reserved
  member as protocol recipient.
- `m-proto-set`: setter (whitelist = unrelated key, recipients
  [PROTOCOL, R1..R7]), then legacy buy with PROTOCOL as protocol
  recipient.

Family D — sweep/collect/boost vs the setter (5 cases):

- `d-swp-col`: mhbuy3, protocol sweep (TOKEN22), creator collect.
- `d-setr-swp-col`: setter, mhbuy3, protocol sweep, creator collect.
- `d-replace-swp-col`: mhbuy3, setter ([PROTOCOL, R1..R7]),
  protocol sweep, creator collect.
- `d-boost`: boost 10^9 on the main pool (window 0).
- `d-boost-setr`: setter, then boost 10^9 on the main pool.

Family E — recipient-count variants vs the chain (3 cases):

- `e-dup-buy`: setter (all recipients R0), then mhbuy3.
- `e-dup-sell`: setter (all recipients R0), then mhsell3.
- `e-fail-buy`: setter with 7 recipients (fails), then mhbuy3.

## Result

All 32 cases pass on all three images with 0 divergent cases:
control and candidate agree with the original everywhere.

### Setter storage (family S)

- Success writes exactly: whitelist PDA 353..385, first recipient
  385..417, remaining recipients 418..642. The mayhem_mode_enabled
  byte at 417 between the two recipient fields is untouched.
  Event: exactly 1, 272 bytes, disc `2bbcfa12dd4bbb5f`
  (= sha256("event:ReservedFeeRecipientsEvent")[:8]), timestamp
  1234567890, first recipient, then the other seven. Fee 5,000.
- 9 remaining accounts succeed; the 9th is ignored (config and
  event identical to the 8-recipient case).
- 7 remaining → 6044 NotEnoughRemainingAccounts, full rollback,
  fee 5,000.
- First recipient = default pubkey → 6011
  AllProtocolFeeRecipientsShouldBeNonZero, rollback.
- All 8 recipients identical → SUCCESS, all three write ranges
  filled with R0. No sorted/unique check — the exact opposite of
  `update_fee_config`'s 6012 gate (2nd #43).
- First recipient = an executable program account → 2007
  ConstraintExecutable, rollback.
- First recipient unfunded (0 lamports) → 2005
  ConstraintRentExempt, rollback.
- Outsider signer → 6005; unsigned admin account → 3010; both
  with no config change (the outsider case is paid by the
  outsider, fee 5,000, payer delta 0).

### The split chain ignores the list completely (families R, E)

Anchor mhbuy3 (tf100, 10^9): userquote −10^9, tail output U3
+5,262,910,281,902, TOKEN22 buyback +4,515,471, withheld vq1
10,000,000 / buyback 45,611. Anchor mhsell3: user receipt
178,541 (gross 180,345, withheld userquote 1,804 / buyback 9),
buyback +837. Every setter variant reproduces these numbers
exactly:

- Whitelist PAYER, whitelist unrelated, PROTOCOL in the list,
  all-duplicate list: mhbuy3 and mhsell3 deltas, withheld,
  pool states, and event discs/lengths are identical to the
  anchor in every case. The reserved member's ATA is untouched
  by split trades (no `res0ata` delta in any R case): nothing
  accrues to any reserved account from the chain.
- Second-leg control: the second mhbuy3 after a setter call
  (tail +5,072,980,706,277, main pool [−9,248,046, 9,124,652,
  123,394], P3 [−5,222,071,679, 2,488, 5,222,069,191]) is
  byte-identical to the second mhbuy3 with no setter call at
  all. The setter does not move even a later leg.
- A failed setter (7 recipients, 6044) leaves the following
  mhbuy3 anchor-identical: a rejected write is a pure no-op
  for the chain.

### Whitelist binds single-hop legs, not the chain (family W)

- Legacy buy with the standard remaining layout under
  whitelist = PAYER fails 6053 BuybackFeeRecipientNotAuthorized:
  fees are zeroed after selection, so `creator_fee == 0` leaves
  the buyback window unadvanced and the validator reads the
  pool-v2 PDA as the buyback recipient (the 2nd #50 trap,
  re-measured adjacent to the split chain).
- Legacy buy with the trimmed remaining layout under the same
  whitelist succeeds curve-only: userquote −184,340, userbase
  +10^9, vault quote +182,496, all fee legs 0, withheld vq1
  1,844 (transfer fee only). The curve moves; no fee moves.
- Legacy buy under an unrelated whitelist pays full fees:
  userquote −186,623, buyback +840, protocol +840, creator
  +542, withheld vq1 1,844 / buyback 9 / protocol 9 /
  creator 6 — identical to the non-whitelist legacy buy in
  3rd #73. The gate is the `whitelist_pda` FIELD, not the
  signer.
- v2 buy under whitelist = PAYER settles at curve 183 with
  every fee bps and fee 0 (event: curve 183, lp/proto/creator
  bps and fees all 0, qwlp 183, uin 183; userquote −185,
  withheld vq1 2). v2 zeroes out cleanly; it has no
  remaining-account trap.
- Observed masking note: a mayhem-pool legacy buy with
  whitelist = PAYER and the standard remaining layout failed
  6053 (the whitelist trap), not the mayhem gate — the
  whitelist path fires in that layout before the reserved
  gate is reached. Family M therefore uses an unrelated
  whitelist for its setter cases.

### Reserved list gates mayhem pools, and only mayhem pools (family M)

- Mayhem buy, protocol recipient = fixture PROTOCOL, no setter
  → 6013 InvalidProtocolFeeRecipient, full rollback.
- Mayhem buy, protocol recipient = fixture reserved member, no
  setter → SUCCESS: userquote −186,623, userbase +10^9, vault
  quote +182,533, protocol leg +1,681 net into the reserved
  member's TOKEN22 ATA (gross 1,698, withheld 17), creator
  +542, buyback 0 (mayhem forces buyback_bps 0). The gate
  reads the list as it stands.
- Setter replaces the list with [PROTOCOL, R1..R7], then the
  old reserved member buys → 6013. Replacement, not append:
  old members are immediately invalidated.
- Setter installs PROTOCOL, then mayhem buy → SUCCESS with
  the same numbers as the reserved-member case, protocol leg
  +1,681 net into PROTOCOL's TOKEN22 ATA (gross 1,698,
  withheld 17), buyback 0.
- Non-mayhem trades are untouched by the list: every family R
  case with PROTOCOL or the fixture member in the list trades
  at full fees, and the split chain never consults the list at
  all.

### Sweep, collect, and boost are list-neutral (family D)

- Protocol sweep after mhbuy3 discharges the full main-pool
  protocol bucket 4,563,570 to the protocol TOKEN22 ATA
  (+4,517,934 net, withheld 45,636); the main pool state moves
  from [−4,686,964, 4,563,570, 123,394] to [−123,394, 0,
  123,394]. The same discharge, to the unit, follows a setter
  call and follows a list replacement: accrued buckets live in
  the pool, not in the list, and replacement moves nothing
  already accrued.
- Creator collect after a protocol-only sweep is a silent
  no-op (0 events): collect discharges the creator vault ATA,
  which only a creator sweep fills; the protocol sweep does
  not touch it. Identical with and without the setter.
- Boost on the main pool fails 6065 PoolCannotBoost with and
  without a preceding setter call: the boost window
  (vq + protocol + creator) is 0 on this fixture either way,
  and the setter does not move it.

## Limits

- LiteSVM harness only; no mainnet or devnet execution.
- The fixture split chain is the 3rd #64/#71 fixture (true 3
  hops, tf100); the reserved/whitelist results are pinned for
  that fixture state, not claimed for other pool states.
- The whitelist masking observation (6053 before 6013 in the
  standard-remaining mayhem layout) is a single-layout
  observation, not a general precedence theorem.
- Mayhem-mode split-chain behaviour is not covered: the
  mayhem cases here are single-hop legacy buys on the flagged
  main pool, and mayhem source is absent from the sparse
  checkout.
- The packet pins behaviour; it makes no claim about source
  changes, builds, or whole-program identity. Error sites are
  recorded per image and are not compared across images.

Made via @slopdotcash
