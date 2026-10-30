# Admin CTO: sharing-program copy and cached pool holder value

Fresh main: `6ff770f7a8a2a74ff3a631b644f1ffef59640582`, including #3131 and #3155.

Two source changes compose: clone the sharing CPI program's lamports/data Rc
values into locals before copying its remaining metadata, and pass the existing
`holder` bool to the pool CPI. The bool was written to the curve before this call;
no intervening instruction changes that field. Both account copies, increment
order, CPI account/argument order, seeds, checks and state transitions retain
their values/behavior. The #3131 associated-program copy remains unchanged.

The changes were independently motivated by sharing-copy allocation and the
original pool caller's cached holder value. On the earlier 52c control, the sharing form alone was 32 bytes
short; cached holder alone was 32 bytes long. Their actual compiled composition
restores size and raises similarity; additivity was not assumed.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.62403 | 0.62552 |
| Aligned normalized instruction tokens | 2,083 | 2,088 |
| Handler bytes | 27,400 | 27,400 |
| Positional differing slots | 3,325 | 3,325 |
| Raw / normalized exact windows | 1,034 / 1,034 | 1,034 / 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls | 154 / 3 | 154 / 3 |

This is a five-token partial similarity gain, not a new complete-window match.
The positional difference count is unchanged on this fresh comparison.

Two ordinary single-module candidate builds reproduce both image hashes. A new
ordinary main build uses the new #3155 entry-copy and tuple layout. Complete fresh comparison
has empty gain/loss lists. All 363 signed synthetic runtime cases match the
captured original with genuine dependency CPIs, and the full scorer retains all 1,034 matched windows. This is evidence for
the measured change, not proof of complete program equivalence. No stack warnings
or build-input changes. Source line count and macro coordinates are preserved.

SHA-256:

- Fresh-main unstripped:
  `946b912b999620b45cf02d7976de52c8f1b116f747aae5d86af0a97898c8da17`
- Candidate unstripped, both ordinary builds:
  `9051345b03250323c6dc7c5d52017372b56c73df3546bd7a039855b870fbb9f1`
- Candidate runtime image, both ordinary builds:
  `55e003e288d1507eb5180671c9f37424b7e48c2034da4ae8f7bb3b57aee58d39`

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

Fresh composition with #3152: 0.62403 -> 0.62762, 2,083 -> 2,095 aligned tokens, 27,400 bytes, unchanged 3,325 positional differences, 1,034 raw/normalized windows and 363/0 runtime. Two ordinary builds reproduce unstripped `7f555a26b6ae203c5358c9afdebf58b35f2e0b823fa030f7b709640657901b49` and runtime `a2c564a7c109e2068cf7175e969de529d52d6995e8b43a2ebba5d4310cec9cbc`. #3155 is retained in both candidate and composition.
