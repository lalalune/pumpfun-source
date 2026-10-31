# Honor compressed output names in nine Fees producers

The root scripts guide documents `--output file.json[.gz]` for differentials.
These nine unoccupied Fees producers instead publish ordinary JSON bytes under
`.gz` names. A normal `gzip.open` consumer fails with `BadGzipFile` after a
successful producer run. The aggregate's magic-based compatibility reader can
accept the misnamed plain JSON; this is not a claim that the aggregate fails.

Encode the original payload once and apply `gzip.compress(payload, mtime=0)`
when the suffix is `.gz`, then use the unchanged `PumpReport.write` interface.
Other output names retain their exact previous bytes. The reviewed transition
lists all nine current root-script hashes. No root script is added, and no
fixture, verifier, captured image, program source or historical packet changes.
The other Fees producers have separate work in review and are outside this PR.

## Real before/after runs

The identical `reproduce.py` invokes all nine actual CLIs with their complete
existing case generators, once for `.json` and once for `.json.gz`. Both sides
use the captured Fees ELF as an explicitly labelled control, SHA256
`4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`.
There is no VM substitution or fabricated positive report. The existing owned
signed local fixture implementations execute unchanged; no public RPC is used.

| Producer | Existing cases per output format |
| --- | ---: |
| administration | 444 |
| admin transfer | 56 |
| admin CTO through captured Pump CPI | 63 |
| buyback | 1,249 |
| configuration | 625 |
| extension | 297 |
| upsert | 578 |
| social claim v2 | 627 |
| social create | 588 |
| Total | 4,527 |

| Run | Exact tested revision | Result |
| --- | --- | --- |
| [Before 41205325752](https://github.com/miracle2044/pumpfun-source/actions/runs/41205325752) | `ad7b032742bc68e6c743c1033489803faac578c5` | all ordinary producers succeed; nine gzip consumers fail with `BadGzipFile` |
| [After 41205366094](https://github.com/miracle2044/pumpfun-source/actions/runs/41205366094) | `9c69b26dc4f0684b54fc5bc08d4bd4b5fd49175b` | all ordinary producers and nine gzip consumers succeed |
| [Current-main compatibility 41206632778](https://github.com/miracle2044/pumpfun-source/actions/runs/41206632778) | `62865f6501a945c777e3051ae89bacbbbacafb33` | complete replay succeeds after merging upstream `ba2eba327c327c768c56decdb49947837a632573` |

At the original base `ebe5387e12e948c2534618adf7a3cf0f27d9de51`, both primary
runs pass nine capture checks and all 228 tooling tests. Upstream then merged
reviewed tool updates, including a directory-destination check in the shared
publisher and an updated encoding guard. All nine producer base hashes were
unchanged. After integrating that main, the complete replay again passes nine
capture checks and all 231 tooling tests.

For every producer, the complete ordinary JSON report is byte-identical across
all three runs. Within every run, plain and decoded gzip-named report bytes are
identical. Thus cases, original/candidate results, transactions, account state,
errors and events are preserved, without filtering fields to obtain equality.
Every compressed output has real gzip magic and zero mtime. Each CLI exits 0,
and every retained report has an empty mismatches list.

The old encoding guard's `9 not greater than 10` failure is recorded on both
original revisions. After upstream's guard update, the encoding and existing
admin-CTO candidate-pinning tests both pass locally. These supplemental checks
use Python 3.11; the primary full CLI proofs use hosted Python 3.12 and the
pinned solders 0.27.1. Full publication-failure suites were not rerun.

## Reproduce and inspect

Install the pinned root requirements in a fresh checkout at a tested revision:

```sh
python -B research/fees-compressed-receipts/reproduce.py
python -B scripts/verify_evidence.py
python -B scripts/test_tooling.py
```

The proof selects the expected framing from the declared exact producer hashes,
then runs the actual CLIs and a separate standard-library gzip/JSON reader.
It writes fresh results under `work/scoped-proof`; it never repairs reports to
make them pass. The source-bound comparison in `comparison.json` and every
retained file digest in `receipt-files.json` are independently inspectable.
`receipts/{before,after,current}-reports.tar.gz` retains the genuine wire reports,
all commands/stdout/stderr and the summary. Historical misnamed `.gz` files
inside the before archive are preserved exactly as produced. Readable summaries,
workflow logs and supplemental test outcomes are retained alongside them.

This is a receipt-framing fix, counted as one contribution. It does not add new
program cases, rebuild source, prove reconstructed-source equivalence, establish
complete protocol coverage or provide security acceptance. The captured image
on both sides is a control for the output contract, not a reconstruction claim.
