# Preserve new AMM ledger entries after interrupted appends

Tested base: `90300f9d2efe3ef014b116172251a41bfb104d78`.

Both `attempts.py note` and `try_sell.locked_append` previously appended a JSON
object directly after any existing bytes. If an interrupted prior append left
an unterminated tail, the new valid object became part of that damaged line.
The writer succeeded, but `attempts.py grep` skipped the entire joined line.
A complete JSON record missing only its final newline had the same problem.

`ledger_io.append_entry` adds a separator when necessary while the existing
`.attempts.lock` is held. It preserves every historical byte, including damaged
tails, and leaves normal newline-terminated logs unchanged. Both writers share
the framing rule so build bookkeeping and manual notes remain readable.

## Repeatable evidence

Run with Python 3.12 and the repository requirements:

```sh
python -B scripts/test_amm_sell_torn_tail_append.py
python -B reconstruction/diagnostics/amm-ledger-best/test_read.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The new test runs the real note CLI and build-ledger writer in subprocesses,
then reads each result through the real query CLI. Copy that test alone into
a clean checkout of the base revision to reproduce four failing subcases
(two writers, each with a damaged or complete unterminated tail). With the
fix, both test methods pass, covering eight append/readback cases including
empty and normally terminated logs. Every case checks retention of prior bytes.

The existing ledger suite passes all three tests. Required verification passes
all nine captures and 242 tooling tests. No native compiler or SBF build is
claimed: the failure and fix concern ledger persistence only. This does not
repair old damaged rows or guarantee durability across a power failure.
