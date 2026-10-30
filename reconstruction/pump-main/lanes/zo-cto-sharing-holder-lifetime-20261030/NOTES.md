# Admin CTO: sharing-program copy and pool-holder lifetime

Fresh main: `6ff770f7a8a2a74ff3a631b644f1ffef59640582`, including #3131 and #3155.

Compose the sharing CPI program copy with a pool-holder read before pool CPI
account construction, and a sharing-update-first inner tuple. Each tuple branch
maps the same sharing update, collect-old and skip values to its named binding.
The #3155 placement of `args` after holder/cashback calculations is preserved;
its inner tuple order is intentionally retuned. The sharing-program and sharing-authority lamports/data
Rc values are cloned into locals, in the same order, before copying metadata.
The pool bool was assigned to the curve before this call, with no intervening
mutation of the decoded field. Account values, Rc increment order, CPI order,
arguments, seeds, checks and state transitions remain equivalent. Macro coordinates
and source line count are preserved. No build-input changes.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.62403 | 0.62852 |
| Aligned normalized instruction tokens | 2,083 | 2,098 |
| Handler bytes | 27,400 | 27,400 |
| Positional differing slots | 3,325 | 3,260 |
| Raw / normalized exact windows | 1,034 / 1,034 | 1,034 / 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls | 154 / 3 | 154 / 3 |

This is an fifteen-token partial similarity gain, not a new complete-window match.
The positional difference count improves by 65. Measurements replace the earlier
0.62552 and 0.62732 candidates. The changes are assessed as a compiled composition; no
arithmetic additivity or individual-gene acceptance is assumed.

All 363 signed synthetic runtime cases match the captured original with genuine
dependency CPIs. Full scoring retains all 1,034 exact windows, with empty raw and
normalized gain/loss lists. Two ordinary single-module identity builds reproduce both candidate image
hashes and complete source-input hash. They are runtime-valid, without stack warnings. This supports the measured change, not complete program identity.

SHA-256:

- Fresh-main unstripped:
  `946b912b999620b45cf02d7976de52c8f1b116f747aae5d86af0a97898c8da17`
- Candidate unstripped:
  `3a3b551d802234d30d5ef49e03675f84b73124af240908d66521144c079cc654`
- Candidate runtime image:
  `f662d8d4bbbf79cb47c2ec7e09151dd616ca958ffe46708eb216ff5704d18451`

Reproduce with the pinned SDK/cache and identity recipe:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

The source extends merged #3066 and retains #3131's associated-program copy,
#3028/#3049's current transfer account ordering, control flow and event readback.

The separately measured composition with #3152 is 0.62403 -> 0.63062,
2,083 -> 2,105 aligned tokens, 27,400 bytes, 3,257 positional differences,
1,034 raw/normalized exact windows, empty losses and 363/0 runtime. Two ordinary
builds reproduce unstripped `1b653f0e2ea7ab0fa8a9c79ed944208b0402e48231eda659285d27c2ed278ab5`
and runtime `40c40f2197023f328ccbe54d1d520ba1c8e501c3aa227ccf651937579d2db0e2`.
Public PR descriptions record actual Git composition and overlapping open PRs.
