# Restore writable lookup-loaded accounts in reused VMs

Base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5` documents that `_ResettableVM` records all writable transaction accounts before execution and restores them before the next case. Its `send_transaction` accepts a `VersionedTransaction` through LiteSVM, but only records static `message.account_keys`. Writable addresses loaded from a V0 address lookup table are omitted.

The real API probe acquires the existing AMM harness, submits a correctly signed local System transfer of123lamports from its funded payer to its funded outsider using an actual lookup table, then acquires the same cached harness again. The transfer succeeds, but the recipient remains123lamports above its starting balance at the base. The fix resolves writable lookup indexes before execution so the existing reset restores them too. Missing/malformed/out-of-range tables retain LiteSVM's transaction error results.

The same eight-scenario probe has one reset mismatch before and none after. Legacy and static-only V0 transfers retain their behavior. Readonly, missing-table, malformed-table, out-of-range-index and wrong-owner rejections retain exact errors. All transactions are locally signed and verified. Five regression methods cover nine scenarios, including multiple writable tables.

```sh
python -B research/runtime-versioned-reset-20261101/reproduce.py --repo . --output /tmp/versioned-reset-after.json
python -B tests/test_amm_versioned_reset.py
python -B scripts/test_amm_harness_content_cache.py
python -B tests/test_amm_pinned_candidate.py
python -B tests/test_amm_acquire_caller_pinned_image.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

Run the same probe on the stated base for the before result. It selects the existing cached mode and starts each scenario with an independent real harness. No runtime outcomes are mocked. The5 new test methods,2 cache tests,1 candidate-pinning test,2 caller-pinning tests,250 tooling tests, and9 capture checks pass.

Existing corpus callers inspected use legacy transactions; this is a direct reusable-API regression, not a claim that a retained AMM corpus already used V0. The harness loads the retained AMM image, while the probe transactions execute the local System program. No new transaction format, configuration option, source build, AMM handler equivalence or on-chain action is introduced.
