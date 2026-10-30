# Admin CTO: sharing CPI account-copy layout

Base: fresh main `b04ed6c312bffc65495480674351b109af4df6b8`, including the
maintainers' composition of #3051 and #3049.

The sharing CPI now explicitly copies the pool-authority, global and mint
AccountInfo values, and refines metadata read order in its existing program
copy. All eight fields keep their values. Lamports/data `Rc` increments retain
their order; only plain metadata read scheduling changes. CPI account order,
arguments, seeds, validation and state transitions are unchanged. Source line
count and error macro sites are preserved.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| `admin_cto::execute` bytes | 27,400 | 27,400 |
| Target sequence similarity | 0.59197 | 0.59916 |
| Aligned normalized instruction tokens | 1,976 | 2,000 |
| Positional differing 8-byte slots | 3,312 | 3,313 |
| Raw exact windows | 1,034 | 1,034 |
| Normalized exact windows | 1,034 | 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls in handler | 154 / 3 | 154 / 3 |

This is partial sequence-similarity progress, not a new complete-window match.
The positional difference count rises by one even though aligned tokens rise
by 24; these are different measurements.

## Validation

- Ordinary single-module identity source builds of fresh main and candidate;
  complete scoring preserves every raw and normalized exact window, with empty
  gain and loss lists.
- A second ordinary candidate build independently reproduces both hashes below.
  Multi-copy search binaries are not the publication artifacts.
- 363 signed synthetic `pump_admin_cto_differential.py` cases against the
  captured original with genuine dependency CPIs, zero mismatches. This corpus
  is runtime evidence, not a proof of complete program equivalence.
- Runtime-valid build receipt, no stack warnings, no build-input changes.

SHA-256:

- Fresh-main unstripped:
  `75c12d8b0fe28e3275fd391e5b4fdc74cfe98f88edd08339fbef9890a226c826`
- Candidate unstripped, both ordinary builds:
  `b73b4b8d0478855af8990f347cd09d3b86ad9998a73224106efaec3e381ffd68`
- Candidate runtime image, both ordinary builds:
  `e72c28eb494ee2ce249ae1d69156b13c37d8464168371f76c41b7a944fdb8364`
- Captured original:
  `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`

With the pinned SDK and dependency cache configured as documented by the harness:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

## Related work

Open PRs were checked before submission: no shared program-source files found.
Merged [#3019](https://github.com/lalalune/pumpfun-source/pull/3019) introduced
the existing explicit sharing-CPI copies. Merged
[#3039](https://github.com/lalalune/pumpfun-source/pull/3039) and
[#3051](https://github.com/lalalune/pumpfun-source/pull/3051) improved the fee
transfer CPI in this same source file; those changes are retained. The
[#3049](https://github.com/lalalune/pumpfun-source/pull/3049) cashback tuple and
scalar sweep bump, incorporated through #3051 before #3049 was closed as
superseded, are preserved and included in both builds reported here.
