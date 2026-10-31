# Mayhem v2 / PumpSwap compressed receipt handoff

At base `ebe5387e12e948c2534618adf7a3cf0f27d9de51`, the documented
`--output file.json[.gz]` convention does not work for the buy_v2, sell_v2 and
PumpSwap differential producers. They always publish plain JSON. Their paired
verifiers decompress `.gz` input by suffix, so the next ordinary verification
command fails with `gzip.BadGzipFile` even after a successful signed comparison.

PRs #3417 and #3421 address the separate legacy buy and sell producers. Their
bodies explicitly leave these v2/PumpSwap producers unchanged. This packet
fixes all three remaining producer modules together, covering four instructions.
It changes no legacy producer, verifier, fixture, acceptance rule or program source.

The producer now UTF-8 encodes its existing report once, then uses
`gzip.compress(payload, mtime=0)` for `.gz`, matching existing Pump writers.
The same `PumpReport.write` still performs publication. Plain output follows
the existing path. The frozen root script set and historical packages remain
unchanged; `proposed-asset-transition.json` declares the three current hash changes.

## Actual before / after

Both runs use the identical `reproduce.py` with Python 3.12 and solders 0.27.1.
It executes the actual differential and paired verifier CLIs, with no replaced
VM, fabricated receipt or mocked producer. The deterministic owned `paused`
case is signed normally, with signature and blockhash checking enabled in
LiteSVM. Both comparison sides load the captured Mayhem ELF as an explicitly
labelled control, SHA256
`a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`.

| | Before | After |
| --- | --- | --- |
| Workflow | [41180673792](https://github.com/miracle2044/pumpfun-source/actions/runs/41180673792) | [41180694278](https://github.com/miracle2044/pumpfun-source/actions/runs/41180694278) |
| Actual tested revision | `246298e2ced747360aca0823afab2e9f03d49ec8` | `32d0ffd95e81fe31f13fc0497198f4a4175ce735` |
| Four plain report handoffs | verifier exits 0 | verifier exits 0 |
| Eight gzip-named handoffs, including repeats | producer exits 0, verifier exits 1 with `BadGzipFile` | both exit 0; actual gzip with zero mtime |
| Reported original/candidate VM sends | 24 | 24 |

Each stage runs buy_v2, sell_v2, buy_pump_swap and sell_pump_swap with native
quote controls, producing plain, gzip-named and repeated gzip-named output for
each. Each producer report contains one real signed original/candidate pair;
each admitted verifier confirms two signed transactions. No comparison reports
mismatches. Within each stage the decoded plain and gzip-named report bytes
are identical, and repeated gzip-named wire bytes are identical. Across stages,
all report content is identical except the updated producer hash under
`harness_sha256`. `comparison.json` records that check for every instruction.

Both hosted runs pass `scripts/verify_evidence.py` (nine captures) and
`scripts/test_tooling.py` (228 tests). The existing pin-before-cases AST check
passes on both revisions locally. The existing encoding test fails identically
before and after: it counts eight `write_text` sites while requiring more than
ten. Its unchanged baseline failure is retained in `receipts/existing-tests/`;
it is not presented as a passing check. These local checks use Python 3.11;
the supported Python 3.12 hosted CLI executions are the primary proof.

## Repeat

From a fresh checkout at either full tested revision, install the pinned root
requirements and run:

```sh
python -B research/mayhem-v2-compressed-receipts/reproduce.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The reproduction checks producer hashes against the reviewed transition before
selecting its expected admission outcome. It never substitutes the actual
verifier or changes a receipt to make it pass. It writes fresh outputs under
`work/scoped-proof`. `receipts/{before,after}-reports.tar.gz` retains all genuine
wire reports, verdicts, commands, stdout/stderr and the run summary, including
the intentionally mis-framed historical `.gz` files exactly as produced.
Readable summaries and workflow logs are retained separately; `receipt-files.json`
binds every retained file. Git attributes preserve their exact bytes on checkout.

This proves receipt framing and handoff for finite owned rejection controls.
It does not prove successful trade behavior, other quote-family behavior,
reconstructed-source equivalence, a new bytecode match or security acceptance.
There is no compiler build, public RPC or live transaction in this experiment.
