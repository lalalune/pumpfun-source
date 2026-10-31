# Pump plain receipt output

The scripts directory documents `--output file.json[.gz]`. Eleven maintained
Pump differential producers instead always emitted gzip bytes. A successful
`--output report.json` therefore failed in a normal UTF-8 JSON reader.

The transition changes only the final writer expression: gzip with zero mtime
for a `.gz` suffix, otherwise the identical original JSON serialization. The
existing `PumpReport` publication path, cases, comparisons, signatures and
program images are unchanged. This is one format-contract correction, not
eleven contributions. Other producers and stopped research lanes are excluded.

## Real execution

The unchanged existing corpora run through the real CLI and LiteSVM, with the
captured Pump image on both comparison sides as a control:
`7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`.
No fabricated positive receipts, VM substitutes, live RPC or source builds are
used. Creation fixtures keep Mayhem mode zero; the stopped Mayhem initializer
is excluded.

| Stage | Exact tested revision | Workflow |
| --- | --- | --- |
| Before | `4b440b1b3603ce6098b130642701943e5f0640f7` | [41215666352](https://github.com/miracle2044/pumpfun-source/actions/runs/41215666352) |
| After | `7dd7f3efb87e8402ba255e85f98e79ed1fa75204` | [41215983031](https://github.com/miracle2044/pumpfun-source/actions/runs/41215983031) |

Base main is `9120883a957d7d9b2cab6140f66fb5bc9e6774d5`.
The complete 1,366-case corpus runs once per output format at each stage:

| Producer | Cases |
| --- | ---: |
| create | 87 |
| create_v2 | 110 |
| create_control | 85 |
| create_quote | 297 |
| create_nested | 48 |
| creator_collect | 119 |
| earned_cashback | 61 |
| extend | 308 |
| idl_authority | 171 |
| legacy_cashback | 14 |
| volume | 66 |

The proof retains actual output bytes, commands, process statuses and standard
JSON-reader results. Before, all eleven ordinary JSON readers fail with
`UnicodeDecodeError`; after, all eleven succeed. Within each tested revision,
plain/gzip-named output decodes to byte-identical JSON. Across revisions,
`cases`, calibration and every report value remain equal except the producer's
own source digest, which correctly changes after the edit. The comparison is
recorded in `comparison.json`; exact transitions are in
`proposed-asset-transition.json`.

Reproduce on either tested source revision from the repository root with the
pinned Python 3.12 requirements:

```sh
python -B research/pump-plain-receipts/reproduce.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The proof refuses a pre-existing `work/scoped-proof` directory and producer
hashes outside the recorded transition. Workflow logs and full wire reports
are retained in `receipts/`; `receipt-files.json` hashes every retained file.
Extract either reports archive into a fresh directory to inspect its original
`summary.json`, command receipts, `report.json` and `report.json.gz` files.
Run `python -B research/pump-plain-receipts/verify.py` to verify all retained
hashes, wire formats, capture bindings and the cross-revision comparison offline.

Both hosted runs verify all nine captures and pass 250 tooling tests. The
existing Pump report-encoding guard also passes locally. A separate Windows
sandbox Python 3.11 tooling run failed (4 failures, 24 errors, 7 skipped), with
directory-rename/symlink permissions and child-process encoding failures; it is
not a passing validation result. Full publication-failure suites were not rerun.

The aggregate's magic-detecting reader already accepts both encodings; no
aggregate failure is alleged. These captured-image controls prove report
framing and preserve the existing finite fixture behavior. They do not prove
rebuilt-source equivalence, new behavior coverage, full protocol behavior or
security acceptance. Original captures and immutable evidence are unchanged.

## Current metadata-compatible replay

The retained before/after reports and their source hashes remain historical. `current-reviewed-inputs.json` separately pins the current producer cohort after adding an explicit `case_count` to the creation report. `reproduce.py` admits that exact cohort as `current-reviewed` and repeats the same complete plain/gzip framing checks. It does not rewrite or relabel either historical run.
