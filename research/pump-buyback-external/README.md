# Admit explicit external ELF inputs in the buyback-recipient replay

The existing 42-case recipient CLI includes its selected candidate in the input
manifest but labels every input with `relative_to(ROOT)`. A valid candidate staged
outside the checkout raises ValueError before VM execution. The same assumption
also breaks the after-run input-integrity check.

Use the existing `bound_input_key` convention for both manifests: existing inputs
keep repository-relative labels, and explicit external files use absolute labels.
Bind the newly imported label helper as another script input. Keep all 42 cases,
synthetic accounts, actual signatures, VM operations and comparison fields intact.

`python -B research/pump-buyback-external/reproduce.py` actually builds current
Pump using the authenticated v1.44 Mac SDK and pinned Linux SBPF libraries. It runs
the internal-path control, copies those exact compiler bytes to an owned external
temporary directory and runs the same CLI. All 42 original/candidate case outcomes
must be identical between locations, the external input must retain its hash and
the report must bind it. A different real captured program at an external path
must still produce actual mismatches and a nonzero exit. It is a diagnostic
negative input, never a claimed reconstructed Pump candidate.

Real compiler records, ELF outputs, logs and complete VM reports are retained in
`work/scoped-proof`. No compiler/VM result is simulated and no executable or oracle
is changed. This fixes path handling for this bounded replay, not source recovery,
whole-program equality or security acceptance. Existing finite-comparison limits
remain in each actual report.

The CLI resolves its admitted candidate path once, so retargeting an input symlink
cannot change the executed input between cases. The CLI and reproduction driver
refuse optimized Python before work, preserving their input-integrity checks.
`python -B tests/test_pump_buyback_external_candidate.py` exercises the real
42-case internal/external controls, wrong-program negative, and symlink retarget.
