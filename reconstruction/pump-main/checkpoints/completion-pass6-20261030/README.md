# Completion checkpoint, sixth pass — 2026-10-30

Pump Main remains **1,033/1,035 windows (99.81%)**, with all 1,033 matches
raw-equal. The repaired #2642 source was rebuilt with the identity recipe and
scored against a fresh main `319a7d10f` build. There are no normalized or raw
losses, and main `5fb5acf5b` has the exact tested source inventory.

The remaining `admin_cto::execute` window stays at its original 27,400 bytes;
its instruction-token similarity improves from **36.13% to 43.92%**. This does
not add a matched window. The first combination with main's previous state
layout lost 686 raw matches; the accepted source replaces that superseded
layout and preserves every existing match.

Two windows remain unmatched:

| Address | Function | Bytes |
| --- | --- | ---: |
| `0x22a10` | `admin_cto::execute` | 27,400 |
| `0x5b3b0` | `multi_hop_curve::swap_hop` | 18,584 |

Across all five maintained checkpoints, **3,336/3,338 windows (99.94%)** match,
covering **5,167,144/5,213,128 code bytes (99.12%)**. Whole meaningful ELF
equality remains **4/5**; Pump Main is not yet equal. The four other program
counts retain their [existing provenance](../completion-20261030/other-programs.json).

## Verification

- [summary.json](summary.json) records the source, binary and tool hashes,
  score comparison, runtime boundary and Fees packet verification.
- [baseline-score.json.gz](baseline-score.json.gz) and [score.json.gz](score.json.gz)
  retain the complete official window inventories.
- [source-inputs.json](source-inputs.json) binds the tested Pump source.
- Build/scoring tool hashes refer to baseline revision `319a7d10f`, used for
  these builds; the later warm-cache portability fix leaves its macOS command unchanged.
- The candidate passed **363/363** signed synthetic admin-CTO differential
  cases against the captured original with genuine dependency CPIs. These
  fixtures do not establish general runtime or whole-program identity.
- [Fees #2647](../../../../research/fees-linux-fresh-rebuild-20261030/README.md)
  supplies two reported native Linux cold-build receipts. The repaired verifier
  binds their source, qualified-source, input-mapping and macro inventories to
  current canonical inputs and checks the captured meaningful ELF prefix.
  Its 19 tests pass both normally and under Python optimization. This review
  did not rerun the native compiler; the reported builds used a bubblewrap
  shim instead of the pinned container image.

To reproduce the Pump comparison, build the baseline and candidate separately
with `reconstruction/harness/fastbuild.py --recipe identity`. Score the baseline
with `reconstruction/harness/score.py --no-baseline`, then score the candidate
with `--baseline` pointing to that fresh report. Run
`scripts/pump_admin_cto_differential.py --candidate <candidate.so> --output <report.json>`
for the bounded runtime check.
