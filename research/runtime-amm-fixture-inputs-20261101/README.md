# Bind the AMM fixture files actually read

Base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5` allows sibling AMM differential commands to publish over caller-relative fixture files. `PumpReport` knows the checkout-root copies, while the shared liquidity fixture and three migration/creator consumers read files relative to the caller. Maintainer commit `8df31d79d612787e6383124f1a27efe2ff8956b0` already preserves this selection rule for the liquidity/trade publishers.

The fix declares the actual resolved trade fixture through the shared module's `REPORT_INPUTS`. Boost, migration-create, and creator-transfer also declare their actual Pump IDL and saved migration fixture paths. The publisher's existing loaded-module discovery now protects these files for each sibling consumer. Both separate output files and existing caller-relative selection continue to work.

The real CLI probe copies the three inputs into a private caller directory and compares retained original images against themselves. Before the fix, all four selected fixture-output runs exit0 and overwrite the copied input with a report. Afterward, those same paths reject before execution and retain all input bytes. Independent-output runs remain successful with identical case JSON hashes: collect148, migration-create37, creator-transfer267, boost100 (552 total). The probe uses actual existing full CLI matrices, not replacement runtimes or mocked outcomes.

```sh
python -B research/runtime-amm-fixture-inputs-20261101/reproduce.py --repo . --output /tmp/amm-fixture-after.json
python -B tests/test_pump_amm_caller_fixture_inputs.py
python -B -m unittest discover -s tests -p 'test_pump_amm_*publication.py'
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

Run the same probe on the base to reproduce the before result. It mutates only its own temporary copies. The retained receipts include per-input before/after hashes and per-corpus semantic hashes; local paths in diagnostics are shortened. Three new real-CLI test methods,52 existing publication tests,250 tooling tests, and9 capture checks pass. This is local report publication correctness, with no new source build or whole-program equivalence claim.

Link-alias tests explicitly skip when the platform denies link creation or does not support it; the recorded macOS run passes all three methods without skips.
