# Retired workflows: push/PR verifiers without entrypoints (2026-10-29)

These six workflows were removed because every Python entrypoint they run is absent
from `main`. Each run failed before any verification executed. No evidence, verifier
source, program source or maintained workflow is changed. The suites are retired
explicitly, not reported as passing or silently skipped.

Mechanism: merge [fce9f28](https://github.com/lalalune/pumpfun-source/commit/fce9f28dd1cc3257d65b3c20afe60acfa8955545)
("update and cleanup") took these workflow files from its second parent
[d75184e](https://github.com/lalalune/pumpfun-source/tree/d75184ea323be8a83ebe11fe5f26a13f3dcbe052/research),
where every entrypoint below exists, while its result tree has no `research/` packages
for them. This does not imply that the original contributions were defective.
Restoring a workflow requires restoring its package (for example from `d75184e`) or
maintained equivalent coverage.

This complements the three workflows retired in #1432.

| Workflow file | Name | Added in | Triggers | Missing entrypoints (present at `d75184e`) |
| --- | --- | --- | --- | --- |
| `verify-amm-sell-control-flow.yml` | Verify maintained AMM Sell control flow | dbe0e008b | pull_request, workflow_dispatch | `research/amm-sell-control-flow-boundary/test_audit.py`<br>`research/amm-sell-control-flow-boundary/verify.py`<br>`research/amm-sell-returned-key-20261028/tools/cfg_attribution.py`<br>`research/amm-sell-returned-key-20261028/tools/elf_reader.py`<br>`research/amm-sell-returned-key-20261028/tools/measure.py` |
| `verify-mayhem-legacy-sell-seeds.yml` | Verify Mayhem Legacy Sell seeds | b5a0b6ce3 | pull_request, push, workflow_dispatch | `research/mayhem-legacy-sell-seed-lifetime/test_scope.py`<br>`research/mayhem-legacy-sell-seed-lifetime/verify.py` |
| `verify-pump-exact-sol-guard.yml` | Verify Pump exact-SOL guard recovery | 7d4fcbbfc | pull_request, push, workflow_dispatch | `research/pump-exact-sol-guard-20261029/verify.py` |
| `verify-pump-v3-buy-fees.yml` | Verify Pump V3 buy fee-tuple recovery | e830e5342 | pull_request, push, workflow_dispatch | `research/pump-v3-buy-fees-20261029/audit_refs.py`<br>`research/pump-v3-buy-fees-20261029/test_verify.py`<br>`research/pump-v3-buy-fees-20261029/verify.py` |
| `verify-pump-v3-costs.yml` | Verify Pump V3 buy-cost source recovery | 1887bc8b0 | pull_request, push, workflow_dispatch | `research/pump-v3-costs-source-20261029/audit_refs.py`<br>`research/pump-v3-costs-source-20261029/test_verify.py`<br>`research/pump-v3-costs-source-20261029/verify.py` |
| `verify-pump-v3-key-copy.yml` | Verify Pump V3 accumulator key-copy recovery | fd3d1d52d | pull_request, push, workflow_dispatch | `research/pump-v3-key-copy-20261029/audit_refs.py`<br>`research/pump-v3-key-copy-20261029/test_verify.py`<br>`research/pump-v3-key-copy-20261029/verify.py` |
