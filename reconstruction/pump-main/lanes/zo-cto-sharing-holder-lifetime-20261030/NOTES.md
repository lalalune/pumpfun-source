# Admin CTO: sharing-program copy and cached pool holder value

Fresh main: `52c0b087c7e345766b67b8fdeb8d4784079a955d`, including #3131.

Two source changes compose: clone the sharing CPI program's lamports/data Rc
values into locals before copying its remaining metadata, and pass the existing
`holder` bool to the pool CPI. The bool was written to the curve before this call;
no intervening instruction changes that field. Both account copies, increment
order, CPI account/argument order, seeds, checks and state transitions retain
their values/behavior. The #3131 associated-program copy remains unchanged.

The changes were independently motivated by sharing-copy allocation and the
original pool caller's cached holder value. The sharing form alone was 32 bytes
short; cached holder alone was 32 bytes long. Their actual compiled composition
restores size and raises similarity; additivity was not assumed.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.62103 | 0.62133 |
| Aligned normalized instruction tokens | 2,073 | 2,074 |
| Handler bytes | 27,400 | 27,400 |
| Positional differing slots | 3,306 | 3,313 |
| Raw / normalized exact windows | 1,034 / 1,034 | 1,034 / 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls | 154 / 3 | 154 / 3 |

This is a one-token partial similarity gain, not a new complete-window match.
The positional difference count worsens by seven; the metrics are distinct.

Two ordinary single-module candidate builds reproduce both image hashes. A new
ordinary main build reproduces #3131's validated image. Complete fresh comparison
has empty gain/loss lists. All 363 signed synthetic runtime cases match the
captured original with genuine dependency CPIs, and the independent call audit
retains all 1,034 matched windows without a hidden mismatch. This is evidence for
the measured change, not proof of complete program equivalence. No stack warnings
or build-input changes. Source line count and macro coordinates are preserved.

SHA-256:

- Fresh-main unstripped:
  `136aee5b073f12b0013f0defe5938c87f48750a69eed03c4982fda8dbae09aef`
- Candidate unstripped, both ordinary builds:
  `e5b6c42aa80cbffb7f9cd35c24f708396322cb55a8379f976fd44c76f8971ce1`
- Candidate runtime image, both ordinary builds:
  `37dd5164c153e8a5cd41ce8ed0224d8b1295f3705e3c54275e041fe314c91886`

Reproduce with the pinned SDK/cache and identity recipe:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

This extends merged #3066's sharing-program copy and preserves merged #3131.
Merged #3028/#3049's current control-flow, transfer account ordering and event
readback remain intact. Open PR overlaps are checked at publication.
