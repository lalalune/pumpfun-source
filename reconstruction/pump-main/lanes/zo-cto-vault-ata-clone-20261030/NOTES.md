# Admin CTO: fee-transfer vault ATA account copy

Fresh main: `6ff770f7a8a2a74ff3a631b644f1ffef59640582`.

The fee-transfer CPI's `pump_creator_vault_ata` value is now copied explicitly
from `a.creator_vault_quote_token_account`. Key/rent epoch are read before the
lamports Rc clone, signer metadata between lamports/data clones, and remaining
metadata afterward. All eight field values, both reference-count increments and
their order, account order, CPI inputs, seeds, checks and transitions are retained.
Source line count and error macro coordinates do not change.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.62403 | 0.62612 |
| Aligned normalized instruction tokens | 2,083 | 2,090 |
| Handler bytes | 27,400 | 27,400 |
| Positional differing slots | 3,325 | 3,325 |
| Raw / normalized exact windows | 1,034 / 1,034 | 1,034 / 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls | 154 / 3 | 154 / 3 |

This is a seven-token partial gain, not a new complete-window match.

Two ordinary single-module identity builds reproduce the candidate hashes below;
complete scoring has empty gain/loss lists. All 363 signed synthetic runtime cases
match the captured original with genuine dependency CPIs. Receipts are runtime-
valid with no stack warnings; no build inputs change. This evidence does not
prove complete program equivalence.

SHA-256:

- Main unstripped:
  `946b912b999620b45cf02d7976de52c8f1b116f747aae5d86af0a97898c8da17`
- Candidate unstripped, both ordinary builds:
  `ca35d1c0e57abd4afb35b948612fe8c7680bada6ee8c03195e0cdcc32d447383`
- Candidate runtime image, both ordinary builds:
  `4a748bce9790df9182d44a32776785583a9b284ed5026bbdf4aa48c77db7048a`

## Composition with #3144

Both PRs touch `admin_cto.rs`, at different CPI consumer sites. The actual clean
Git composition with #3144 head `860e619885f7b2ca6339afa9b7499eebf45b9b93`
exactly equals the normally compiled and independently rebuilt source. Relative
to #3144 alone, adding this vault copy raises similarity 0.63062 -> 0.63271,
2,105 -> 2,112 aligned tokens, and reduces positional differences 3,260 -> 3,257.
Relative to fresh main, the combined result is 0.62403 -> 0.63271 (+29 aligned
tokens). Handler size remains 27,400 bytes; all 1,034 raw/normalized windows are
retained, gain/loss lists are empty, and all 363 runtime cases match.

- Composed unstripped SHA-256, both ordinary builds:
  `956bccc592d596d30adf1c6f5a468b10d5c5344407638af07dfe13dd2cb487a0`
- Composed runtime SHA-256, both ordinary builds:
  `50ec0d7165c1afcc87fe1c8d0189b4b9b37a07341d70116074beb24cb2cd16f7`

These measurements supersede the earlier composition with #3144 head e25dd438.

Merged #3131's associated-program copy and #3028's current transfer initializer
order remain intact. Other open PR overlaps are checked at submission.

Reproduce with the pinned SDK/cache and identity recipe:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

This branch preserves #3155's args placement and collect-old-first tuple. The
composition preserves that args placement while incorporating #3144's intentional,
value-equivalent sharing-update-first tuple order. Earlier 52c and e25dd438
composition results remain historical only.
