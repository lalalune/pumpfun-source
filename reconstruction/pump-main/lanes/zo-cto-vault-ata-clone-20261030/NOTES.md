# Admin CTO: fee-transfer vault ATA account copy

Fresh main: `52c0b087c7e345766b67b8fdeb8d4784079a955d`.

The fee-transfer CPI's `pump_creator_vault_ata` value is now copied explicitly
from `a.creator_vault_quote_token_account`. Key/rent epoch are read before the
lamports Rc clone, signer metadata between lamports/data clones, and remaining
metadata afterward. All eight field values, both reference-count increments and
their order, account order, CPI inputs, seeds, checks and transitions are retained.
Source line count and error macro coordinates do not change.

| Identity build measurement | Fresh main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.62103 | 0.62313 |
| Aligned normalized instruction tokens | 2,073 | 2,080 |
| Handler bytes | 27,400 | 27,400 |
| Positional differing slots | 3,306 | 3,306 |
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
  `136aee5b073f12b0013f0defe5938c87f48750a69eed03c4982fda8dbae09aef`
- Candidate unstripped, both ordinary builds:
  `6938db6edb6bb69a002369ff1fd62f7cfd61fccad3fa34fd0379bab14dbbd995`
- Candidate runtime image, both ordinary builds:
  `8750531cf95539e89fa240b328fb5142ad19448d6b6005397166183de0afba7d`

## Composition with #3144

Both PRs touch `admin_cto.rs`, at different CPI consumer sites. The actual source
composition with #3144 head `1a29df783888787d233572abd5d4088a347cd55c` was compiled
normally and rebuilt independently: 0.62133 -> 0.62343, 2,074 -> 2,081 aligned
tokens, 27,400 bytes, 1,034 raw/normalized windows, empty losses, and 363/0 runtime.
Positional differences remain 3,313 on that composition.

- Composed unstripped SHA-256:
  `f27cbd7aa2d9fb54c7687e8f4de647feee7d2fdf82cc22d0c51b7f727ef9b54a`
- Composed runtime SHA-256:
  `43061b076807fddd80c9255bc5c55cf935632392796a153d3941e6e5a3a2ae0b`

Merged #3131's associated-program copy and #3028's current transfer initializer
order remain intact. Other open PR overlaps are checked at submission.

Reproduce with the pinned SDK/cache and identity recipe:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```
