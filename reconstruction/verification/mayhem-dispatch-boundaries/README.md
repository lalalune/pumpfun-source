# Mayhem dispatch and decode boundaries

This package compares the captured Mayhem program with a rebuilt candidate at
the instruction-admission layer. It uses fresh LiteSVM state and a normally
signed transaction for every side of every step. It does not initialize Mayhem
administration state or claim handler-body coverage.

## Authenticated inventory

`evidence/dispatch-map.json` records one dispatcher comparison for each of 25
Anchor `global:<name>` selectors in the captured ELF
`a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`.
`inventory.py` requires its literal selector table to equal that captured map;
it then supplies the maintained Rust argument layouts and Accounts order. This
is an evidence fixture, not an invented IDL.

| argument contract | confirmed instructions |
|---|---|
| no arguments | `burn_tokens`, `extend_account`, `initialize_global_params`, `initialize_mayhem_state`, `reset_sol_deployed`, `reset_stable_deployed`, `reset_state`, `resume_trading`, `stop_trading`, `sweep_fees`, `sweep_fees_admin` |
| `u128, u16, u16` | `buy`, `buy_pump_swap`, `buy_v2`, `sell`, `sell_pump_swap`, `sell_v2` |
| `u64` | `update_max_sol_per_sweep`, `update_max_stable_per_sweep`, `withdraw_admin`, `withdraw_quote_admin` |
| `Pubkey` | `update_admin`, `update_trader` |
| `u8` | `initialize_fee_recipient` |
| 16 Borsh `Option` fields | `update_global_params` |

No confirmed instruction argument contains a bool, enum, or vector. Those
decoder families are reported as not applicable rather than synthesized from
unrelated state types.

## Matrix and comparison contract

The plan has 26 cases and 450 paired steps (900 executions):

- 14 dispatcher steps: empty and 1/4/7-byte data, three unknown selectors,
  event-CPI and IDL reserved selectors, and legitimate signer/seed failures.
- Every recognized instruction: discriminator only, complete arguments,
  trailing data, truncation where applicable, source-order accounts, one account
  short, extra and duplicate accounts, missing signer, read-only mutable account,
  wrong owner, wrong account discriminator, wrong PDA, and wrong fixed program.
- Numeric zero/max cases for `u8`, `u16`, `u64`, and `u128`; zero/`ff` pubkeys;
  all-None/all-Some option sets; all 16 invalid option tags; and all 16 truncated
  option payloads. No case asks the host to allocate from an attacker length.

Each receipt compares the signed transaction and instruction hashes, exact
error, return data, events, inner instructions, payer lamports, and watched
account state. Full logs and compute units are reported separately. The target
program account is intentionally not a watched mutable account: its ELF bytes
are different by definition and both image hashes are bound in provenance.

The event-authority PDA is never injected as an outer signer and signature
verification is never disabled. Therefore the event-CPI success branch is
explicitly unsupported; its no-account, unsigned-PDA, and wrong-signer admission
boundaries are covered.

## Qualification result

On upstream `255a0fd2e431627bb01e139aabb51b56eaa0357a`, the local macOS qualification
used the captured original and a genuine v1.54 SBF build with SHA-256
`5af84936cdfcba42158464f07afb4e6e35ef898200ced992538db018e312fbb7`.
All 450 steps matched in every behavior field, full logs, and compute units.
Both comparator negative controls detected their deliberate error/state change.

Important limitation: the official exact Mayhem builder is Windows-only. Its
authenticated stage succeeded locally, but macOS cannot inject the retained
historical Anchor proc macro. The qualification build used a disposable current
source copy with exactly one host-compatibility change in
`curve-accounts/src/interface_definition.rs`:
`historical_anchor_program::declare_program!(pump)` became
`anchor_lang::declare_program!(pump)`. The canonical current exact-build hash
declared by `programs/mayhem/build_exact.py` is
`9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d`;
this packet does not falsely claim that identity for the portable ELF. The
change affects a Pump CPI type generator, not Mayhem's generated entrypoint,
but canonical-Windows replay remains a follow-up qualification.

Observed decoding rules were equal on both images: the 14 argument-bearing
instructions reject discriminator-only and one-byte-truncated inputs with 102;
all 25 accept trailing bytes and then fail on the first missing account; all 16
invalid Option tags and all 16 truncated Option payloads return 102. The
captured Mayhem dispatcher treats the reserved IDL selector as unknown (101).

## Reproduce

Install the repository-pinned requirements in an isolated environment, provide
the two ELF paths, then run:

```sh
python3 producer.py --root ../../.. \
  --images '{"original":"<original.so>","candidate":"<candidate.so>"}' \
  --out <output>

python3 verify.py \
  --images '{"original":"<original.so>","candidate":"<candidate.so>"}' \
  --runtime <output>/runtime

python3 -m unittest discover -s . -p 'test_*.py' -v
```

`producer.py` writes deterministic gzip files (`mtime=0`) for the plan,
line-delimited receipts, and report. Repeating the complete run with the same
images produced byte-identical output hashes.
