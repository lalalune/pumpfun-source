# Connect current constant-product and sell-accounting validation

The documented constant-product producer accepts its output location (the existing
README uses `work/pump-math-results.json`), while the sell-accounting consumer only
reads a removed historical `repro/pump/constant-product-differential.json`. A fresh
real producer report therefore cannot feed the next stage without recreating an
unrelated deleted directory.

Accept `--curve-report` for that actual producer output. Preserve the old default
for callers who already retain a historical report, and bind the exact bytes read
through the existing `fixture_report_sha256` output field. Before consuming cases,
require current arithmetic-source, original Pump/Fees and captured SPL identities,
complete case/count/comparison fields, zero producer mismatches and the producer's
existing minimum of 100 successful original comparisons. Error probes remain
retained as error probes; all existing 45 fee/buyback combinations still run.

Complete current workflow, using only standard-library Rust native hosts and the
repository's pinned Python VM dependencies:

```sh
mkdir -p work/native-accounting
rustc --edition=2021 -O programs/pump/recovered/constant_product_host.rs -o work/native-accounting/curve-host
rustc --edition=2021 -O programs/pump/recovered/sell_accounting_host.rs -o work/native-accounting/sell-host
python -B scripts/pump_validate_constant_product.py --host work/native-accounting/curve-host --output work/native-accounting/curve.json
python -B scripts/pump_validate_sell_accounting.py --host work/native-accounting/sell-host --curve-report work/native-accounting/curve.json --output work/native-accounting/accounting.json
```

The proof compiles both actual native hosts, executes the original SBF producer,
then connects that genuine 161-probe/160-comparison report to the full 206-case
accounting consumer. A real private native model with ceiling fees changed to
flooring must produce event/state mismatches and fail. Mutations of the genuine
report (wrong captured identity, removed case, false count, failed comparison)
must reject before publishing a result. No compiler, VM outcome or positive
report is simulated; original captures and maintained Rust remain unchanged.

```sh
python -B research/sell-accounting-report/reproduce.py
```

Actual compiler/VM process logs, full producer/consumer reports, malformed-report
copies and host compiler version remain under `work/scoped-proof`. This is partial
regular-SOL arithmetic/accounting validation, not rebuilt SBF/whole-program byte
identity, independent fee selection, token-quote coverage or security assurance.
The adjacent asset transition describes the single edited root script.
