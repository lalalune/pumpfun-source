# Repair the existing WSOL withdraw fixture

The root Fees withdrawal differential already has a `wsol` case. It used the
canonical legacy Token native mint but created ordinary token accounts:
`is_native=None`, rent-only lamports and a six-decimal mint. The captured programs
successfully transferred token quantities while moving no backing SOL. This
repair makes that existing case execute a native transfer.

For legacy Token plus the canonical WSOL mint, the fixture now sets nine mint
decimals, records each account's rent reserve in `is_native`, and funds the account
with the reserve plus its token amount. Ordinary Token and Token-2022 cases retain
their existing representation. Explicit case overrides are still applied after
initial construction.

The [Solana native-token documentation](https://solana.com/docs/tokens/basics/sync-native)
describes the reserve and backing balance. The official Token
[account codec](https://github.com/solana-program/token/blob/program%40v9.0.0/interface/src/state.rs)
and [native mint definition](https://github.com/solana-program/token/blob/program%40v9.0.0/interface/src/native_mint.rs)
define the layout and nine decimals.

## Reproduction and validation

On base `ebe5387e12e948c2534618adf7a3cf0f27d9de51`, the new three-method test fails
four subtests: both original and candidate runs report six decimals and zero
lamport movement instead of 12,345. The same test passes after the repair. It runs
the real CLI over all 113 existing cases, using the captured Fees image for both
inputs and the captured dependency programs in LiteSVM.

```sh
python -E -X utf8 -B tests/test_fees_withdraw_native_fixture.py -v
python -E -X utf8 -B scripts/fees_withdraw_differential.py \
  --candidate evidence/original/pump_fees/deployed.so --output /tmp/withdraw-report.json
python -E -X utf8 -B tests/test_fees_runtime_image_per_case.py -v
python -E -X utf8 -B tests/test_fees_withdraw_output_inputs.py -v
python -E -X utf8 -B tests/test_fees_differentials_normal_python.py -v
python -E -X utf8 -B scripts/verify_evidence.py
python -E -X utf8 -B scripts/test_tooling.py
```

The saved summary in `results.json` records the before/after balances and capture
hashes. The source now loses 12,345 lamports and the destination gains 12,345.
The source retains its 2,039,280-lamport reserve. A complete JSON-row comparison of
the two full reports found only `wsol` changed; all other 112 rows were identical.
Both full runs reported zero mismatches. Existing CI discovers the new test in
the `contract-tests` job.

The earlier [PR #1969](https://github.com/lalalune/pumpfun-source/pull/1969) adds a
separate persistent-state buyback/withdraw sequence packet. It does not repair this
root fixture, and its sealed packet is unchanged. This is an existing-case
fidelity correction, with no claim of new program behavior or vulnerability.

The root-script hash transition is proposed in `proposed-asset-transition.json`.
Captured assets, program source, historical packets and their recorded hashes are
unchanged. Local validation used macOS arm64, Python 3.12.13 and solders 0.27.1.
Captured-versus-same-capture equality validates this fixture; it does not establish
rebuilt-source equivalence. No compiler or live transaction was used.
