# AMM lane baseline selection and reset

The native AMM builder seeds a new lane from explicit `--source-root`, then
immediately overwrites that workspace from the global PRISTINE when available.
When no PRISTINE is available, later attempts instead inherit prior mutations.
Both contradict the documented lane-seeded-once / reset-before-each-attempt flow.

Store the selected workspace as `lane/baseline-ws` before any attempt can patch
`ws`, then reset each attempt from that same baseline. An explicit initial source
root wins over global canonical inputs. Existing canonical callers retain their
default. Baseline publication is atomic after complete staging. An old workspace
with no known source is preserved and requires an explicit source root, rather
than being guessed to be pristine. Use a new lane for a different source baseline.

`tests/test_amm_lane_baseline.py` copies the actual retained AMM and local fee-crate
sources, adds ordinary comment markers in temporary copies, runs the real staging
recipe and actual POSIX rsync, then checks full workspace input inventories.
The SDK path is deliberately absent to stop exactly at the compiler boundary.
No compiler result, binary, score or VM outcome is simulated or claimed.

Before at base `6edd839eacedb837b281ebbd344f204bea4779f5`, the three source-selection/
reset regressions fail on actual bytes. The later canonical positive control and
unknown-legacy preservation control cover the intended boundary behavior.

```sh
python -B research/amm-lane-baseline/reproduce.py
```

The driver refuses to count a missing rsync as success, retains the real process
output in `work/scoped-proof`, and runs the existing publication-preservation and
workspace-containment suites. Those existing publication tests use synthetic
compiler outcomes for their own scope; they are not the source-selection proof.

No program source, prior output, original capture or immutable checkpoint changes.
