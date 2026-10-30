# Retain complete nonzero Pump suite output

The parallel driver checks a child exit code before copying its JSON from a
TemporaryDirectory. A genuine differential mismatch produces the complete case
report and exits nonzero, after which the temporary report is deleted. The
aggregate failure report retains a traceback and stdout, but loses the complete
failed case/state results required to diagnose the reconstruction difference.

Retain the child's exact output bytes before checking its exit code or parsing
its JSON, and bind the rejected output path, SHA256, byte count and actual child
return code in the aggregate failure report. It remains rejected evidence, not a
successful differential receipt. Passing-report validation and loader admission
remain unchanged. Existing outputs and historical captures are preserved.

`python -B research/failed-suite-evidence/reproduce.py` runs two genuine current
Pump builds with the official v1.44 Mac compiler and pinned Linux SBPF libraries.
The positive control executes the complete 11-suite fourth shard (2605 cases).
An isolated source copy changes initialize's handler to return custom error 777;
the genuine build producer records the exact changed inputs. First the unchanged
initialize suite executes directly to prove it writes all 40 actual cases and
exits nonzero. Then the normal build-bound, captured-loader parallel driver runs
the same shard. It must still fail, while preserving the complete actual failed
report equal to the direct execution, plus its actual hash/count/exit status.

The proof retains actual ELF files, compiler receipts/logs, source-only negative
input and VM reports. It does not alter maintained Rust, fabricate a build
receipt, simulate compilation/VM execution, or claim new byte matching or
whole-program equivalence. The source mutation is a test-only negative control,
never a matching candidate, and is not submitted as a program change.
