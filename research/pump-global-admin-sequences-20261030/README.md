# Pump Main Global admin-command sequences on persistent state

## Problem

The existing Pump Main admin harnesses (`scripts/pump_validate_admin.py`,
`scripts/pump_validate_config_admin.py`, `scripts/pump_validate_authority.py`)
send one admin instruction against a fixed Global snapshot. Nothing measures
what happens when admin commands are chained on the same Global account:
authority rotation followed by commands from the old and new authority,
toggles that are re-sent with the stored value, the single-slot quote-mint
whitelist filled, swapped and emptied, buyback configuration with valid and
invalid recipient lists, and multi-instruction transactions that fail on
their last instruction. This packet runs those sequences on the original
image and on the rebuild and compares them step by step.

## Setup

- Images: original `evidence/original/pump/deployed.so`
  (sha256 `7a19affa…f7b02d`) and rebuild `candidate.so`
  (sha256 `1cbf63ae…ab81c6`). Only the Pump program is loaded into LiteSVM;
  no other program is needed by these instructions.
- Global: built from the IDL layout (1,088 bytes), authority A, the USDC mint
  in the single `whitelisted_quote_mints` slot, create_v2 enabled, mayhem and
  cashback disabled, buyback 5,000 bps with 8 distinct recipients.
- Keypairs A, B, C and the fee payer use fixed seeds. Each step expires the
  blockhash and sets a fixed clock, so receipts are byte-reproducible.
- Each case is a sequence of transactions on one VM; a step may hold several
  instructions in one transaction.

## Cases

29 cases, 102 steps, 204 receipts (2 images x 102 steps), 48 failing steps.

- Authority rotation (11 cases): A->B then old/new signer, chain A->B->C,
  rotate to self, rotation signed by a non-authority, A->B->A, rotate to the
  default key, to the Global PDA and to the program id, two rotations in one
  transaction, rotation plus a command from the old or the new authority in
  the same transaction.
- Toggles (4 cases): `toggle_create_v2`, `toggle_mayhem_mode`,
  `toggle_cashback_enabled` sent with the stored value and the new value in
  turn, and a true/false pair inside one transaction.
- Quote-mint whitelist (4 cases): add while full, add duplicate, remove,
  add another, remove absent, the default key and WSOL on an empty slot,
  remove+add swap in one transaction, non-authority before and after rotation.
- Buyback config (4 cases): bps 10,000 / 10,001 / none / 0 / u64 max / 9,999;
  recipient lists of 8 (rotate and restore), 7, 9 and 1 accounts; duplicate
  recipient, default-key recipient, valid list with 10,001 bps.
- Other setters (3 cases): `update_creator_fee_config`, `set_max_curve_depth`,
  `set_virtual_quote_reserves`, `update_holder_reward_config`, including an
  invalid bool byte (2) and a truncated u64.
- Account metadata (2 cases): read-only authority, authority key not signed.
- Atomicity (1 case): rotation, a toggle, a buyback update and a remove all
  succeed in one transaction and a final remove fails.

## Result

**Behavior: original and rebuild match in all 29 cases.** In every one of the
102 steps the transaction bytes, error, Global bytes before and after,
`Program data` events and inner instructions are identical.

Measured sequence behavior (identical on both images):

- After A->B rotation, A gets 6000 NotAuthorized and B succeeds. Rotation to
  the default key, the Global PDA or the program id succeeds and every later
  admin command from A fails with 6000. Rotation to self leaves Global
  unchanged and still emits 1 event.
- Two rotations in one transaction (A->B signed by A, B->C signed by B)
  succeed. A rotation followed by a command signed by the old authority in
  the same transaction fails with 6000 and the rotation is rolled back. The
  same pair signed by the new authority succeeds.
- Re-sending a toggle with the stored value fails with 6000 NotAuthorized
  (handler body `require_neq`), not with an account-constraint error.
  A true/false pair in one transaction succeeds and leaves Global unchanged.
- With one whitelist slot: adding any mint while the slot is used gives 6066
  QuoteMintWhitelistFull, adding the stored mint gives 6067
  QuoteMintAlreadyWhitelisted, removing an absent mint gives 6068, and the
  default key or WSOL gives 6069 for add and for remove-of-default. Removing
  WSOL from an empty slot gives 6068, not 6069.
- `update_buyback_config` with 7, 9 or 1 remaining accounts gives 6061; a
  duplicate recipient gives 6059; a default-key recipient gives 6058; 10,001
  bps gives 6060 even with a valid list, and the stored bps stays unchanged in
  every failing step. `None` with no accounts succeeds and changes nothing.
- Invalid bool byte 2 and a truncated u64 fail with Anchor 102
  InstructionDidNotDeserialize; a read-only authority fails with 2000; an
  unsigned authority with 3010.
- Every one of the 48 failing steps leaves Global byte-identical, including
  the 5-instruction transaction whose first four instructions succeeded.

**Logs and compute units: original and rebuild differ in 29 of 102 steps.**

- 73 steps have identical logs and identical compute units.
- The other 29 steps are exactly the steps that fail inside a handler body
  with an `AnchorError thrown in <file>:<line>` log. In all 29 the only
  differing log lines are that site line and the `consumed` line. The
  original reports `programs/pump/src/<file>:<line>`, the rebuild
  `src/<file>:<line>`; the line numbers are equal at all 13 sites reached
  (lib.rs 114, 121, 149, 1870, 1895, 1905, 1950, 1955, 1960, 1971, 1975, 1986
  and set_reserved_fee_recipients.rs 121). Each site line is 14 bytes longer
  in the original.
- Compute units: the original uses 14 more units in 26 of these steps
  (NotAuthorized from a toggle 10, QuoteMintNotWhitelisted 4,
  QuoteMintNotEligibleForWhitelist 3, BuybackBasisPointsOutOfRange 3,
  WrongBuybackFeeRecipientsCount 3, QuoteMintAlreadyWhitelisted 1,
  NotUniqueBuybackFeeRecipients 1, AllBuybackFeeRecipientsShouldBeNonZero 1),
  and 118 more units in the 3 QuoteMintWhitelistFull steps (8,300 vs 8,182 for
  a single add). The 14 NotAuthorized steps raised by the `has_one` account
  constraint log no file site and use equal compute units.
- The 104 units on the QuoteMintWhitelistFull path that are not accounted for
  by the 14-byte site difference are a measured difference only; this packet
  does not assert a mechanism for them.

## Reproduce

```
python3 producer.py --root <repo> \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' \
  --out <this packet directory>
python3 verify.py --images '{"original": "...", "candidate": "..."}'
```

`producer.py` reads only `evidence/upstream/pump.json` from `--root` (to check
the discriminators it hardcodes and to name error codes). `verify.py` needs
only this packet and the two images: it checks the manifest, part hashes,
image hashes, signatures and rollback, re-executes every case on both images,
requires byte-equal receipts and recomputes the report.

## Limits

- One Global layout, with one whitelist slot, built from the IDL; no captured
  production Global was used.
- Only the eleven admin instructions listed above; no trade, create or
  migrate instruction is measured here.
- The compute-unit difference on the QuoteMintWhitelistFull path is reported
  as measured; no source change is proposed.
