# Pump admin_cto persistent differential

This package adds multi-transaction coverage that the maintained 388-case
`scripts/pump_admin_cto_differential.py` matrix intentionally does not provide.
That matrix creates a new LiteSVM per case; this suite retains state, expires the
blockhash, signs a new message for every step, and compares a captured Pump Main
image with a freshly built source candidate in independent VMs.

## Coverage and comparison contract

Nine deterministic lifecycles execute 20 unique signed transactions per image:

- native creator A→B→C, failure/retry, automatic and explicit fee collection;
- holder-reward conversion, immutable-holder rejection, and retry;
- SPL and Token-2022 creator settlement through captured dependency programs;
- shared creator A→B→C updates through genuine Pump Fees CPI;
- frozen wallet and frozen shared-vault behavior;
- an invalid Fees event-authority attempt followed by a successful retry;
- two mints in one VM, with the other mint's curve, pool, and sharing config
  required to remain byte-identical after every step.

Every receipt retains exact transaction bytes, signature verification results,
message and blockhash identity, errors, events, return data, inner instructions,
raw and normalized logs, compute units, and complete account-by-account state.
Semantic equality excludes only invoke/success scaffolding, compute-unit lines,
and the known `programs/pump/src/` source prefix. Failed transactions must roll
back all tracked state except the transaction payer fee. Three negative controls
alter an error, event, and post-state and must all be detected.

The fixture state is synthetic. It uses canonical PDAs and the captured PumpSwap,
Pump Fees, SPL Token, Token-2022, and Associated Token programs. PDA authority is
obtained only by real CPI; the outer transaction never marks a PDA as a signer.
The suite makes bounded runtime claims, not whole-program or ELF-identity claims.

## Reproduce

Requires the repository's pinned v1.44 toolchain and `solders==0.27.1`:

```sh
out=$(mktemp -d)
reconstruction/verification/pump-admin-cto-stateful/build_candidate.sh "$PWD" "$out/build"

uv run --python 3.12 --with solders==0.27.1 python \
  reconstruction/verification/pump-admin-cto-stateful/lifecycle.py \
  --candidate "$out/build/candidate.so" --output "$out/report.json.gz"

uv run --python 3.12 --with solders==0.27.1 python \
  reconstruction/verification/pump-admin-cto-stateful/verify.py \
  --candidate "$out/build/candidate.so" --report "$out/report.json.gz" --replay

uv run --python 3.12 --with solders==0.27.1 python -m unittest -v \
  reconstruction/verification/pump-admin-cto-stateful/test_lifecycle.py
```

The report is canonical JSON with deterministic gzip metadata and binds the
complete Pump source tree, IDL, candidate, original, and dependency identities.

## Receipt and publication admission

Each run snapshots every executed program before any case and names those exact
bytes. Source and fixture hashes remain separate from image identity; the
captured Global templates are decoded directly from the retained account input.
Case-specific real blockhash expiry keeps all twenty transaction identities
distinct across the suite, and both images execute the same signed messages.

The saved reader parses every transaction and verifies the positive header
signature count, exact successful result vector, payer, ordinary signer keys,
program/discriminator, signature and message hash. It recomputes account data
lengths/hashes and JSON types, state continuity, failed-step rollback, events and
semantic logs. Planned cases, steps, mint accounts and infrastructure dispositions
are checked independently of the report's cached booleans. `--replay` additionally
repeats all nine lifecycles and requires the complete deterministic report.

Publication uses an exclusive staged report. Existing files, late aliases and
failed staging do not replace inputs or a previous report. The added
`test_receipts.py` uses captured images on both sides to test these transport and
admission boundaries; that control makes no rebuilt-source parity claim.
