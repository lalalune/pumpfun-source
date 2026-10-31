# Keep loader receipts separate from wrapped artifacts

At base `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`, `pump_with_captured_loader.py` protects its wrapper, harness, and captured input files, but the receipt may alias the wrapped command's candidate image or output. The actual93-case `pump_validate_admin.py` corpus exits successfully before the wrapper replaces that candidate ELF or differential report with loader receipt JSON.

The wrapper now checks the documented `--candidate` and `--output` paths before execution, accepting separate-value and `--flag=value` forms. Repeated options use the last value as argparse does. These are path boundaries, not new receipt input-hash fields. Distinct receipts can still be replaced on repeated runs; existing atomic publication and failure behavior remain intact.

The portable probe uses private copies of the captured Pump image and runs the unchanged administrative differential through the real captured loader. Before the fix, both aliases exit0 and replace their selected artifact. Afterward, both exit2 before the child runs, preserve the candidate, and create no child output. The independent-path control still returns93cases, zero mismatches, and `ok=true` on the loader receipt.

```sh
python -B research/runtime-loader-artifact-paths-20261101/reproduce.py --repo . --output /tmp/loader-artifacts-after.json
python -B tests/test_pump_loader_wrapped_artifacts.py
python -B -m unittest discover -s scripts -p 'test_pump_with_captured_loader*.py'
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

Run the same probe on the stated base for the before result. Local temporary paths are shortened in the retained receipts. Five new tests exercise12 path/option combinations and three genuine93-case successful runs, including receipt reuse and repeated-option precedence. Link creation explicitly skips where denied or unsupported; none skipped in the recorded macOS run. All20 existing wrapper tests,250 tooling tests, and9 capture checks pass.

Scope is the two documented full option names. The patch does not infer a generic schema for arbitrary wrapped scripts or add signature, source-build, whole-program equivalence, or on-chain claims.
