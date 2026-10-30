# Reject definite frame diagnostics before verified Pump publication

The v1.44 backend can emit `exceeded max offset` and still return zero. The
ordinary fastbuilder already rejects this exact diagnostic, but the separate
`pump_build_verified.py` producer checks only the process status before copying,
stripping and publishing the compiler output and a successful comparison report.
An actual source iteration can therefore publish despite the definite backend
error. This is the full main-Pump producer, distinct from the native AMM publisher.

Inspect the closed actual compiler log before copying/stripping/publication.
Record its hash, exact matching lines and a separate diagnostic-gate result in
the existing attempt. Preserve the real compiler return code and target ELF.
Reject via the producer's existing explicit check, which also remains active
under optimized Python. Accept unrelated warnings, including the different
`overwrites values in the frame` class; absence of this diagnostic is not runtime
or stack-safety acceptance. No maintained Rust, recipe or captured bytes change.

`python -B research/pump-stack-diagnostic/reproduce.py` executes two actual current
Pump builds with the authenticated official v1.44 Mac compiler and pinned Linux
SBPF libraries. The normal current source is the control. A private source copy
exports an 8192-byte volatile stack probe. The actual compiler must diagnose that
named function's offset versus the 4096 maximum, return zero, and retain the
nonempty diagnosed function in its actual ELF. The producer must exit nonzero
without publishing `unstripped.so`, `candidate.so` or `build-comparison.json`,
while retaining its real attempt, compiler log and target ELF for diagnosis.

`work/scoped-proof` retains the real source-only probe, logs, source/tool-bound
producer records and both actual compiler outputs. No process/ELF result is
simulated, no original bytes enter compilation and no executable is patched.
This proves a publication gate, not VM execution, a window gain, whole-program
equivalence or security acceptance. The root-script asset transition is adjacent.
