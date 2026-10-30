# Pump Main: instruction dispatch, argument decoding and first account checks (original vs rebuild)

## Problem

The existing Pump Main differentials send well-formed instructions to one handler at a
time. None of them measures what the program does with malformed or minimal input,
before a handler body runs or right at its start:

- the Anchor dispatcher: empty data, short or unknown discriminators, and the event-CPI
  and IDL tags;
- Borsh argument decoding: truncated arguments, trailing bytes, the `OptionBool` /
  `CreationOptionU64` tails that can be omitted, and `bool` / `Option` tags of 2;
- the first account constraint each instruction rejects.

These paths are shared by every instruction, and they need only the pump image. No step
gets as far as a CPI to pump_fees, Metaplex or pump_amm.

## Cases

There are 57 cases and 580 steps. Each step was run on both images, giving 1,160
receipts.

- **`framework-dispatch`** (12 steps):
  - empty data, and 1-, 4- and 7-byte prefixes of the `buy` discriminator;
  - unknown discriminators (8 × `00`, 8 × `ff`, and 8 × `00` with 4 payer accounts);
  - the event-CPI tag `e445a52e51cb9a1d` alone, with the payer, and with an unfunded key;
  - the IDL tag `40f4bc78a7e9690a` alone, and as IDL `Create` with 5 payer accounts.
- **One case per instruction in `evidence/upstream/pump.json`** (56 instructions). Each
  case uses the following variants, where they apply.

  With no accounts:
  - `disc-only`: the discriminator with no arguments.
  - `args-zero`: the smallest valid encoding (zeros, empty strings and vecs, `None`, `false`).
  - `args-zero-plus-trailing-byte`
  - `args-zero-minus-last-byte`
  - `optional-tail-omitted`: drops the trailing `OptionBool` / `OptionU64` arguments.
  - `optional-u64-partial-3-bytes`: `create_v2` only.
  - `bool-2-<arg>`, `option-bool-2-<arg>` and `option-tag-2-<arg>`
  - `length-1-no-body-<arg>`: a string, bytes or vec that declares length 1 but has no body.

  With accounts (`args-zero` data):
  - `accounts-placeholder-readonly`: N × one unfunded key.
  - `accounts-payer-all`: N × the signing payer.
  - `accounts-payer-one-short`: N−1 × the signing payer.
  - `accounts-resolved-no-global`: each slot is filled from the IDL. Fixed `address`
    values and const-seed PDAs are used as given. Signer slots get the payer, the
    `program` slot gets the pump id, and any other slot gets one unfunded key.
  - `accounts-resolved-global-foreign-authority` and
    `accounts-resolved-global-payer-authority`: the same slots, plus a synthetic 1,088-byte
    Global. It uses the same layout and values as `pump-global-admin-sequences-20261030`,
    with authority set to a foreign key or to the payer. The Global is written before the
    step and removed after it.

All steps run in one LiteSVM instance per image. Each step uses a fixed clock and a
fresh blockhash, and the payer comes from a fixed seed. These fields are compared as
behavior:

- transaction bytes
- error
- return data
- `Program data` events
- inner instructions
- Global after the step
- payer lamports after the step

Logs and compute units are compared separately.

## Results

**Behavior matches in all 580 steps** (`mismatched_steps` is empty).

Logs and compute units are equal in 570 of 580 steps. The 10 steps that differ all take
an `AnchorError thrown in <file>:<line>` path that is reached only once Global exists:

| step | error | CU original / rebuild |
|---|---|---|
| add_quote_mint / resolved-global-payer-authority | QuoteMintNotEligibleForWhitelist (6069) | 8768 / 8754 |
| remove_quote_mint / resolved-global-payer-authority | QuoteMintNotEligibleForWhitelist (6069) | 8771 / 8757 |
| remove_quote_control_mint / resolved-global-payer-authority | QuoteMintNotEligibleForWhitelist (6069) | 14415 / 14401 |
| set_quote_control_mint_reserves / resolved-global-payer-authority | QuoteMintNotWhitelisted (6068) | 13587 / 13573 |
| set_params / resolved-global-payer-authority | NotEnoughRemainingAccounts (6027) | 9627 / 9613 |
| set_reserved_fee_recipients / resolved-global-payer-authority | NotEnoughRemainingAccounts (6027) | 9386 / 9372 |
| toggle_cashback_enabled / resolved-global-payer-authority | NotAuthorized (6000) | 9011 / 8997 |
| toggle_mayhem_mode / resolved-global-payer-authority | NotAuthorized (6000) | 9020 / 9006 |
| create_v2 / resolved-global-foreign-authority | TryingToInitPayerAsProgramAccount (4101) | 8701 / 8687 |
| create_v2 / resolved-global-payer-authority | TryingToInitPayerAsProgramAccount (4101) | 8701 / 8687 |

In each of these 10 steps:

- the only differing log lines are the error site and the `consumed` line;
- the original reports `programs/pump/src/<file>:<line>` and the rebuild reports
  `src/<file>:<line>`, at the same line number;
- the original uses 14 CU more.

There are 9 distinct sites (`anchor_error_sites` in the report), including
`create_v2.rs:27`, `fee_recipient.rs:47`, `quote_control/state.rs:92` and `:113`, and
`lib.rs:121`, `:149`, `:1950` and `:1975`. This is the same site-path effect reported by
`pump-global-admin-sequences-20261030`. Every other error path in this packet logs no
file site, and there the logs and CU are identical.

### What both images do (measured, identical on both)

| variant | outcome (steps) |
|---|---|
| empty, 1/4/7-byte prefix, unknown 8-byte discriminator | InstructionFallbackNotFound (101), 7 of 7 |
| event-CPI tag, no accounts | `NotEnoughAccountKeys` (runtime error, not an Anchor code) |
| event-CPI tag, unfunded non-signer / payer as `event_authority` | ConstraintSigner (2002) / ConstraintSeeds (2006) |
| IDL tag alone / IDL `Create` with payer accounts | InstructionDidNotDeserialize (102) / InvalidProgramId (3008) on `system_program` |
| `disc-only` | 102 for the 35 instructions with arguments; AccountNotEnoughKeys (3005) for the 21 without |
| `args-zero`, `args-zero-plus-trailing-byte` | 3005 in 56 of 56 for each: trailing bytes are accepted |
| `args-zero-minus-last-byte` | 102 in 28; 3005 (accepted) in 7: `buy`, `buy_exact_sol_in`, `buy_v2`, `buy_exact_quote_in_v2`, `buy_v3`, `buy_exact_quote_in_v3`, `create_v2` |
| `optional-tail-omitted` | 3005 (accepted) in 7 of 7 (same 7 instructions) |
| `optional-u64-partial-3-bytes` (`create_v2`) | 102 |
| `bool-2`, `option-bool-2`, `option-tag-2` | 102 in 8 of 8, 7 of 7 and 2 of 2 |
| `length-1-no-body` | 102 for `create`, `distribute_fee_to_holders` and `multi_hop_curve_swap`; 3005 (accepted) for `create_v2`, the only one of the four with an omittable tail |
| `accounts-placeholder-readonly` | AccountNotInitialized (3012) in 39, AccountNotSigner (3010) in 16, InvalidProgramId in 1 |
| `accounts-payer-all` | AccountOwnedByWrongProgram (3007) in 51, InvalidProgramId in 5 |
| `accounts-payer-one-short` | 3007 in 51, InvalidProgramId in 3, 3005 in 2 |
| `accounts-resolved-no-global` | 3012 in 51, ConstraintSeeds in 2, ConstraintOwner (2004) in 1, success in 2 (`initialize`, `initialize_quote_control`) |
| `accounts-resolved-global-foreign-authority` | 3012 in 31, NotAuthorized in 18, system `Custom(0)` in 2, ConstraintSeeds in 2, ConstraintOwner, InvalidProgramExecutable (3009) and 4101 in 1 each |
| `accounts-resolved-global-payer-authority` | success in 9, 3012 in 31, and the handler-level errors listed above |

The 9 successful steps with a payer-authority Global are:

- `set_max_curve_depth`
- `set_quote_control_admin`
- `set_quote_control_reserves_admin`
- `set_virtual_quote_reserves`
- `toggle_create_v2`
- `update_buyback_config`
- `update_creator_fee_config`
- `update_global_authority`
- `update_holder_reward_config`

Global bytes after the step differ from the bytes written before it in 4 steps:

- `initialize/accounts-resolved-no-global` (creates Global)
- `set_virtual_quote_reserves`
- `toggle_create_v2`
- `update_global_authority`

The Global after-state is equal on both images in every step.

Notes on reading these outcomes:

- `initialize` and `initialize_quote_control` with an existing Global or QuoteControl
  fail with the System program's `Custom(0)` ("already in use").
- With the payer as Global authority, `toggle_mayhem_mode(false)` and
  `toggle_cashback_enabled(false)` fail with NotAuthorized (6000). The log shows
  `Left: false Right: false`, the comparison against the stored flag.
- The 4101 on `create_v2` comes from this packet's slot resolver. The resolver puts the
  payer into both the `mint` and `user` signer slots.

The packet does not explain why `optional-u64-partial-3-bytes` returns 102 on both
images while a fully omitted tail is accepted. It reports this as a measurement only.

## Reproduce

```
python3 producer.py --root <repo> \
  --images '{"original": "<repo>/evidence/original/pump/deployed.so", "candidate": "<candidate.so>"}' \
  --out .
python3 verify.py --images '{"original": "...", "candidate": "..."}'
```

- **Images measured:**
  - original sha256 `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
  - rebuild sha256 `1cbf63aed735e3859e6019f297b946596ed54c9cb86cc32fedf7360d39ab81c6`
    (source tree `33e7c00467df9d7506b53fc9f3759664d0bd5863`)
- **IDL:** `evidence/upstream/pump.json`, sha256
  `7616681ea557975f9f623ac211080f22a93060781eaf4765b0a488d980997207`.
- **producer.py:**
  - The output is deterministic. Two runs produced byte-identical `runtime/` files.
  - It writes `runtime/plan.json.gz`, the explicit data and account metas for every
    step, so `verify.py` does not need the IDL.
- **verify.py:**
  - It checks the image hashes against the report, then checks MANIFEST and the
    receipt-part hashes.
  - It replays the plan on both images and requires every receipt field, including logs
    and CU, to be equal.
  - It then recomputes the summary and compares it to `runtime/report.json.gz`.
  - Exits 0 on success, 1 otherwise.

## Files

- `producer.py`, `verify.py`
- `runtime/plan.json.gz`: 57 cases, 580 steps.
- `runtime/receipts-part01..06.jsonl.gz`: 1,160 receipts.
- `runtime/report.json.gz`: per-step summary, error histograms, CU deltas and log-difference kinds.
- `MANIFEST.json`
