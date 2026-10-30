# Restore the current build-bound ordinary two-curve replay dependency

`scripts/pump_tokenkeg_two_curve_differential.py` adapts the original 20-case VM
harness to the actual current compiler input manifest. Its import still points
at the deleted `repro/pump/tokenkeg-two-curve-fortyeight/harness/` module, so the
current CLI fails before argument parsing or VM execution. The maintained suite
catalog still selects these 20 cases. The documented ordinary two-curve routes
remain supported; this does not resume a stopped recovery lane.

Retain the exact historical module and adjacent synthetic input fixture under
this research directory and change only the current wrapper's import location.
`provenance.json` records their historical Git commit, paths, blobs and SHA256.
No old outcome/candidate receipt is adopted as current evidence. No cases, VM
operations, comparisons, signature checks or source/build-admission logic change.
The existing wrapper continues to override the module's historical 36-input
binding with its current exact workspace/source-manifest validation. Invoke the
maintained root CLI, rather than the historical module's original-only entry.
Both maintained entry points reject optimized Python before imports, external
commands or output creation: the exact historical fixture uses assertions for
its signature and prestate checks. Run without `-O` or `PYTHONOPTIMIZE`.

`python -B research/pump-two-curve-inputs/reproduce.py` genuinely builds current
Pump, supplies its actual producer report and staged compiler inputs, and runs
the unchanged 20 original/candidate comparisons through the root CLI. All 40
normal test-owned outer signatures must verify; 18 cases reach Pump through the
captured AMM's real CPI signer and 16 original outcomes succeed. Wrong actual ELF
with the genuine report and a temporarily missing real build attempt must both
be rejected without a passing result. The attempt is restored after the check.

Compiler logs/receipts, both actual ELF outputs and complete VM results stay in
`work/scoped-proof`. No compiler/VM result is simulated, no provenance record is
fabricated and no executable/capture is modified. This is this specific existing
build-bound suite's availability, not whole-corpus availability, general routing,
new source matches, whole-ELF equality or security assurance. Arbitrary hops,
other quotes, Token-2022/extensions, holder/Mayhem/cashback and completion remain
outside its original bounded scope.
