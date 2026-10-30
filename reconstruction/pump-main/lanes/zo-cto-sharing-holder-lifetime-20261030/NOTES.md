# Admin CTO: sharing-program copy and pool-holder lifetime

Fresh main: `6ff770f7a8a2a74ff3a631b644f1ffef59640582`, including #3131 and #3155.

Compose the sharing CPI program copy with a pool-holder read before pool CPI
account construction, and a sharing-update-first inner tuple. Each tuple branch
maps the same sharing update, collect-old and skip values to its named binding.
The #3155 placement of `args` after holder/cashback calculations is preserved;
its inner tuple order is intentionally retuned. The sharing-authority lamports/data Rc values are cloned into locals before
copying metadata; the sharing-program copy uses an always-inlined field-copy
helper. Both clone each Rc once, in lamports-then-data order. Metadata initializer
order is intentionally selected for the measured source composition.
The pool bool was assigned to the curve before this call, with no intervening
mutation of the decoded field. Account values, Rc increment order, CPI order,
arguments, seeds, checks and state transitions remain equivalent. Macro coordinates
and source line count are preserved. No build-input changes.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.62403 | 0.63062 |
| Aligned normalized instruction tokens | 2,083 | 2,105 |
| Handler bytes | 27,400 | 27,400 |
| Positional differing slots | 3,325 | 3,260 |
| Raw / normalized exact windows | 1,034 / 1,034 | 1,034 / 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls | 154 / 3 | 154 / 3 |

This is an twenty-two-token partial similarity gain, not a new complete-window match.
The positional difference count improves by 65. Measurements replace the earlier
0.62552, 0.62732, 0.62852 and 0.62912 candidates. The changes are assessed as a compiled composition; no
arithmetic additivity or individual-gene acceptance is assumed.

All 363 signed synthetic runtime cases match the captured original with genuine
dependency CPIs. Full scoring retains all 1,034 exact windows, with empty raw and
normalized gain/loss lists. Two ordinary single-module identity builds reproduce both candidate image
hashes and complete source-input hash. They are runtime-valid, without stack warnings. This supports the measured change, not complete program identity.

SHA-256:

- Fresh-main unstripped:
  `946b912b999620b45cf02d7976de52c8f1b116f747aae5d86af0a97898c8da17`
- Candidate unstripped:
  `3d28a04fefa4f622cac4019fa3b9b4a42eacd73d55a1a9c0297f1f95cab7221e`
- Candidate runtime image:
  `31602ac50ae8f015c2fcbb5848a44df9791953da05f4549e4454d359c70a281f`

Reproduce with the pinned SDK/cache and identity recipe:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

The source extends merged #3066 and retains #3131's associated-program copy,
#3028/#3049's current transfer account ordering, control flow and event readback.

The separately measured composition with #3152 is 0.62403 -> 0.63271,
2,083 -> 2,112 aligned tokens, 27,400 bytes, 3,257 positional differences,
1,034 raw/normalized exact windows, empty losses and 363/0 runtime. Two ordinary
builds reproduce unstripped `956bccc592d596d30adf1c6f5a468b10d5c5344407638af07dfe13dd2cb487a0`
and runtime `50ec0d7165c1afcc87fe1c8d0189b4b9b37a07341d70116074beb24cb2cd16f7`.
Public PR descriptions record actual Git composition and overlapping open PRs.
