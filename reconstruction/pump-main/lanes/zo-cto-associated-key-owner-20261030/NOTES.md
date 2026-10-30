# Admin CTO: associated-program key and owner before standard clone

Fresh main: `61f237c45603555c64dd9bb95e09334d23b624b0`.

In the payer-first fee-transfer CPI, copy the associated-token program through
`AccountInfo{key:x.key,owner:x.owner,..x.clone()}`. The two immutable references
are evaluated before the standard clone. Every field retains its value; the
lamports/data reference-count increments still occur once each in their original
order. The remaining fields come from the pinned standard Clone implementation.
CPI order, account order, arguments, signer seeds, validation and error macro
sites are unchanged. The landed #3028 composition is retained.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.62043 | 0.62103 |
| Aligned normalized instruction tokens | 2,071 | 2,073 |
| Handler bytes | 27,400 | 27,400 |
| Positional differing slots | 3,306 | 3,306 |
| Raw / normalized exact windows | 1,034 / 1,034 | 1,034 / 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls | 154 / 3 | 154 / 3 |

This is a two-token partial similarity gain, not a new complete-window match.

Two ordinary single-module identity source builds reproduce identical candidate
image hashes. The fresh-main/candidate full scorer returns empty gain/loss lists.
All 363 signed synthetic `pump_admin_cto_differential.py` cases match the captured
original with genuine dependency CPIs; this is runtime evidence, not complete
program equivalence. Build receipts are runtime-valid with no stack warnings.
No build inputs change. Newly added unlinked recovered modules on fresh main are
retained; its ordinary control build reproduces the prior control image.

SHA-256:

- Main unstripped:
  `b43cbe43dd6e096018ad6c2bf8db4d1046c9f8f7c26fa6e35ebbf2665eb917e0`
- Candidate unstripped, both ordinary builds:
  `136aee5b073f12b0013f0defe5938c87f48750a69eed03c4982fda8dbae09aef`
- Candidate runtime image, both ordinary builds:
  `459e4f3ca5be37b507c1be5f0586d5f6de552d7ac7c2e10b966d722bbd5a4a8f`

Reproduce using the pinned SDK/cache and identity recipe:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

Open PRs were checked before submission: no shared program-source diff found.
Merged #3028 changes this same transfer-CPI line; its payer-first initializer
order and outer/inner AMM program copies are preserved. The remaining source
changes from #3039, #3051, #3066 and #3049 are retained as present on fresh main.
