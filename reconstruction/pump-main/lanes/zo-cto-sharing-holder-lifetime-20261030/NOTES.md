# Admin CTO: sharing authority AccountInfo copy

Fresh main: `53abf28b1160e4509e0ead2a1daab1f987d92278` (merged #3168).

Copy the sharing CPI authority AccountInfo explicitly from admin_set_creator_authority. Clone lamports and data Rc values into locals, once each in the same order, and copy the same eight fields.
Account order, CPI inputs and order, signer seeds, checks and state transitions
retain their values. All #3168 shared-condition and grouped pool-argument changes,
#3155 args placement and collect-old-first tuple are preserved. Source line count
and every error/event macro coordinate remain unchanged. No build-input changes.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.62672 | 0.62792 |
| Aligned normalized instruction tokens | 2,092 | 2,096 |
| Handler bytes | 27,400 | 27,400 |
| Positional differing slots | 3,305 | 3,305 |
| Raw / normalized exact windows | 1,034 / 1,034 | 1,034 / 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls | 154 / 3 | 154 / 3 |

This is a 4-token partial similarity gain, not a new complete-window match.
Two ordinary single-module identity builds reproduce the complete source-input
hash and both image hashes. Full scoring has empty raw/normalized gain and loss
lists. All 363 signed synthetic runtime differential cases match the captured
original with genuine dependency CPIs. Runtime-valid receipts have no stack
warnings. This supports the measured source change, not complete program identity.

SHA-256:

- Fresh-main unstripped: `ee08c486f68867d36eec196c4a08650493ad502af58d170ef614fed301cd2e51`
- Candidate unstripped, both builds: `4a64f3879745f306066277894113270fadec74cd15c8dd2463e871a2f7e88cfe`
- Candidate runtime, both builds: `09d30aae3b78cbeb74dd52eb4012df16d92082ce5e7efc4cf551e824a86fd7e5`

## Current composition of #3144 and #3152

Both PRs touch the same source file at different CPI account-copy sites. Their
actual source composition was compiled normally and rebuilt independently:
**0.62672 -> 0.63002 (+11 aligned tokens)**, 2,092 -> 2,103 tokens,
27,400 bytes, 3,305 positional differences, all 1,034 raw/normalized exact windows,
empty losses and 363/0 runtime. Both builds reproduce:

- Unstripped: `dc00f164303b5f4b104cc603f619af05d450f3f0bfb03a2832af048ed64a3b5d`
- Runtime: `9197c225ecc2e57960dd43684ad7bfbf264d0214cef94fcbcc2155934052a9a0`

The merged #3168 source changes remain intact in this composition. #3153 is a
related tuple/pool-lifetime alternative in this file; integration with it was not
tested. Earlier 6ff measurements and sharing-program/holder-lifetime compositions
are historical and superseded by this fresh-main comparison.

Reproduce with the pinned SDK/cache and identity recipe:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```
