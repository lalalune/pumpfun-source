# PumpSwap (pump_amm) instruction dispatch, Borsh decode and first-account checks

## Question

Do the original PumpSwap image and the rebuild act the same before any handler body
runs? This layer covers the Anchor dispatcher (short and unknown discriminators, the
event-CPI tag, the IDL tag), Borsh argument decoding for each of the 38 IDL
instructions, and the first account-validation error each instruction reports. The
existing PumpSwap packets all start from well-formed instructions with populated
accounts (the `amm-multi-hop-*` series, liquidity rounding, admin_cto_pool). Pump and
pump_fees already have decode-layer packets. This packet is the matching one for
pump_amm.

| image | sha256 |
|---|---|
| original `evidence/original/pump_amm/deployed.so` | `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7` |
| rebuild `<candidate.so>` (recipe `scripts/build_partial_candidate.py`, platform-tools v1.44 / cargo-build-sbf 2.1.21, source tree `755200a0d9fffe6f82a43fb65cc452d164f6e90b`) | `384737bdc6c54cca4330fd5ce15f8c556a40a78afa6a93a69fe47d2b18527ab5` |

## Method

`producer.py` reads `evidence/upstream/pump_amm.json` and builds 39 cases: one
dispatcher case plus one per IDL instruction. Together they hold 372 steps. Each
step runs in a fresh LiteSVM, with only the pump_amm image loaded and a payer from
a fixed seed (229). The variants are:

- dispatcher (17 steps): empty data, 1/4/7-byte prefixes, all-zero and all-0xff
  discriminators, the event-CPI tag `e445a52e51cb9a1d` with no account, an unsigned
  event authority and a wrong signer, the same tag with the event-authority PDA
  marked as signer (3 steps, run with signature verification off because a PDA
  cannot sign: bare, with a 32-byte payload, with one extra account), the IDL tag `40f4bc78a7e9690a` with no
  account and with a Create payload, and 7-byte prefixes of both tags.
- every instruction (8 steps each): `disc-only`, `valid-args` (no accounts),
  `trailing-byte`, `one-account-short`, `unfunded-accounts`, `payer-every-slot`,
  `idl-resolved` (signers = payer, fixed addresses and constant-seed PDAs from the
  IDL, others unfunded), and `idl-resolved-extra-account`.
- instructions with args: `last-byte-removed`. Each `bool`, `Option<u64>` and
  `OptionBool` tag is also set to 2. Each `Option` gets `none` and
  `none-with-stale-body`. Each trailing `OptionBool`/`OptionU64` field (the
  `track_volume` arg of `buy` and `buy_exact_quote_in`, and four `create_pool`
  fields) is `omitted`, and `creator_fee_bps` is `half-present` (4 of 8 bytes).

Each step records the transaction hash, error, return data, events, inner
instructions, payer lamports, the post-state of every account touched, full logs
and CU, on both images.

A third run of each step uses a **control image**: the original, patched in memory
so that its 245 references to `programs/pump-amm/src/*.rs` strings skip the 18-byte
`programs/pump-amm/` prefix. This is the same transform as in the open packet
`pump-amm-admin-cto-pool-boundaries-20261030`. It isolates the known AnchorError
file-path difference. The rebuild crate has its own `[workspace]`, so `file!()` there
is `src/...`.

## Results

| measure | value |
|---|---|
| cases / steps / receipts | 39 / 372 / 744 |
| steps with any behavior-field difference | **0** |
| steps with a log difference | **0** |
| steps with a CU difference (histogram `candidate - original`) | **0** (`{"0": 372}`) |
| control image: CU / logs / behavior equal to rebuild | 372 / 372 / 372 |
| steps whose logs contain `AnchorError thrown in <file>:<line>` | 0 |
| steps that panicked / succeeded | 0 / 3 (signed event-CPI steps) |
| CU range on the original (min / max) | 1197 / 11078 |

**On all 372 steps the original and the rebuild match**: same error, same logs and
same CU. In `pump-amm-admin-cto-pool-boundaries-20261030` the rebuild uses 18 CU
less on every `require!` error path. That difference comes only from the `AnchorError thrown in
<file>:<line>` string, which is emitted by `require!`/`error!()` sites inside
handler bodies. None of the errors reached here (101, 102, 2002, 2004, 2006, 3005,
3007, 3008, 3010, 3012, 6005) carries a file path. They are either
`AnchorError occurred` or `AnchorError caused by account: <name>`, so the
path-prefix difference does not reach this layer, and the CU is identical. The
control is equal here as well, which agrees with that explanation.

### Outcome by variant (original = rebuild on every row)

| variant | steps | outcome (Anchor error number: count) |
|---|---|---|
| `disc-only` | 38 | 102: 22 (instructions with args), 3005: 16 (no args) |
| `valid-args`, no accounts | 38 | 3005: 38 |
| `trailing-byte` | 38 | 3005: 38 (extra data accepted) |
| `last-byte-removed` | 22 | 102: 19, 3005: 3 (`buy`, `buy_exact_quote_in`, `create_pool`: trailing optional field read as absent) |
| `*-bool-tag-2` | 11 | 102: 11 |
| `*-opt-tag-2` (`Option<u64>`) | 2 | 102: 2 |
| `*-optbool-tag-2` | 5 | 102: 5 |
| `*-none`, `*-none-with-stale-body` | 2 + 2 | 3005 (stale bytes after a None tag accepted as trailing data) |
| `*-omitted` (trailing `OptionBool`/`OptionU64`) | 6 | 3005: 6 |
| `creator_fee_bps-half-present` | 1 | 102 |
| `one-account-short` / `unfunded-accounts` | 38 / 38 | 3010: 19, 3012: 19 (each) |
| `payer-every-slot` | 38 | 3007: 35, 3008: 3 (`create_config`, `extend_account`, `init_user_volume_accumulator`: system_program checked first) |
| `idl-resolved` / `+extra-account` | 38 / 38 | 3012: 35, 2004: 1 (`extend_account`), 2006: 1 (`init_user_volume_accumulator`), 6005: 1 (`create_config`, InvalidAdmin) |

### Dispatcher

| step | outcome | CU (both images) |
|---|---|---|
| empty, 1/4/7-byte prefixes, 7-byte event/IDL tag | 101 InstructionFallbackNotFound | 1197 |
| zero / 0xff 8-byte discriminator | 101 | 1320 |
| zero discriminator + 1 account | 101 | 1615 |
| event-CPI tag, no accounts | `NotEnoughAccountKeys` (ProgramError) | 1270 |
| event-CPI tag, unsigned event authority | 2002 ConstraintSigner (`event_authority`) | 1947 |
| event-CPI tag, payer as signer | 2006 ConstraintSeeds (`event_authority`) | 4010 |
| event-CPI tag, event-authority PDA as signer (sigverify off) | success, no program log | 2116 |
| same + 32-byte payload after the tag | success | 2116 |
| same + one extra account | success | 2372 |
| IDL tag, no accounts | 102 | 1601 |
| IDL tag + Create payload, 1 account | 3005 (`to`) | 2030 |

`create_pool` is the only instruction whose `valid-args` 3005 is logged as
`AnchorError occurred` with no `caused by account:` name. Every other instruction
names its first account. Both images do this.

All per-step outcomes, blamed accounts and CU values are in
`runtime/report.json.gz` (`outcome_by_instruction`, `blamed_account_by_instruction`)
and `runtime/receipts.jsonl.gz`.

## Conclusion

Across 372 steps, the rebuild's dispatcher, Borsh decoding and account-constraint
layer is byte-equal in behavior, logs and CU to the original. The CU deltas that
other AMM packets measure therefore start inside handler bodies, at error sites
that log the file path. They do not come from the generated entry, decode or
validation code.

## Reproduce

```
python3 producer.py --root <repo> --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}' --out .
python3 verify.py --images '{"original": "<repo>/evidence/original/pump_amm/deployed.so", "candidate": "<candidate.so>"}'
```

`producer.py` is deterministic: two runs gave byte-identical `runtime/` files.
`verify.py` needs only the packet files and the two images. It checks
MANIFEST.json and the image sha256 values, replays all 372 steps on both images and
the control, requires each receipt to equal the stored one, and recomputes the
report. It exits 0 on success and 1 otherwise. Requires `solders` 0.27.1
(`solders.litesvm`).
