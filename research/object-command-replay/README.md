# Replay local-object compiler receipts with their selected paths

Two maintained partial-object builders serialize their actual compiler argv by
global string substitution. In `build_fee_selection.py`, a valid relative SDK
argument `.` replaces every filename period with `<toolchain>` while failing to
label the compiler operand. A repository-contained absolute output also loses its
output label after the parent repository prefix is replaced. In
`pump_build_constant_product.py`, a repository-contained SDK similarly loses its
toolchain label. Successful actual compilation can therefore yield a command
that cannot replay, cannot write a selected fresh output, or still references an
old SDK after the supplied toolchain has moved.

Resolve the fee builder's selected SDK/output paths and label only the three
known path operands: compiler, source and object output. Keep every flag and
non-path argument unchanged. Explicit operand identities avoid both filename
rewrites and parent-prefix collisions; no compiler source, original bytes,
target, optimization, object transformation or function comparison is changed.
The adjacent proposed transition binds the two existing frozen root scripts.

The actual proof performs four SDK compilations: an absolute-path control,
relative SDK `.` from that SDK directory, an output inside the repository, and
an owned SDK clone inside the repository. It strictly expands only the report's
existing `<toolchain>`, `<repo>` and `<output>` labels and actually invokes the
recorded argv into a new directory. For the nested SDK case it relocates only its
owned clone before replay, then supplies that new SDK location. Every successful
replay must create the requested fresh object with the identical full raw hash.
No source/compiler/process result is simulated and no command is manually repaired.

```sh
python -B research/object-command-replay/reproduce.py
```

Actual build and replay logs, receipts, expanded argv and original/replayed object
files are retained in `work/scoped-proof`. The authenticated SDK and its owned
clone stay outside the artifact. Relocation entries remain unresolved and all
original comparison limits stay intact: this proves object-receipt replay, not
function matching improvements, VM execution or whole-program byte identity.
