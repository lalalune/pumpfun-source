# Admin CTO: one aligned token from transfer payer copy

Fresh main: `022dc450f96563e9b5d5aa5d794a57e4ac9cf40c`.

The transfer CPI's payer AccountInfo copy now reads rent epoch and flags between
the lamports/data `Rc` increments. All eight values and both increment order and
CPI argument/account order are preserved. No validation, seeds, state transition,
source line count or error macro site changes.

| Identity build measurement | Main | Candidate |
| --- | ---: | ---: |
| Target sequence similarity | 0.59916 | 0.59946 |
| Aligned normalized instruction tokens | 2,000 | 2,001 |
| `admin_cto::execute` bytes | 27,400 | 27,400 |
| Positional differing slots | 3,313 | 3,313 |
| Raw / normalized exact windows | 1,034 / 1,034 | 1,034 / 1,034 |
| Raw / normalized losses | 0 / 0 | 0 / 0 |
| Internal / syscall calls | 154 / 3 | 154 / 3 |

This is a small partial similarity gain, not an additional complete-window match.

Two ordinary single-module identity builds reproduce both candidate image hashes.
The full scorer returns empty gain/loss lists. All 363 signed synthetic runtime
cases in `scripts/pump_admin_cto_differential.py` match the captured original with
genuine dependency CPIs. These cases are runtime evidence, not complete program
equivalence. The build reports runtime-valid and no stack warnings.

SHA-256:

- Main unstripped:
  `b73b4b8d0478855af8990f347cd09d3b86ad9998a73224106efaec3e381ffd68`
- Candidate unstripped, both ordinary builds:
  `738f26b4fb17b5ee4a889a9b6d8e48b916c0ee81d86b0f8ba4f9b87504af6f9c`
- Candidate runtime image, both ordinary builds:
  `77d10bd52368b834c4fb555aff86ee3b27a1bb0858c0fecae4b30151bf51148d`

Reproduce using the pinned SDK/cache and identity recipe:

```sh
python3 reconstruction/harness/fastbuild.py --src programs/pump --work <work> --out <candidate> --recipe identity
python3 reconstruction/harness/target_metric.py <candidate>/unstripped.so 0x22a10 --sym 'admin_cto::execute$'
python3 reconstruction/harness/score.py <candidate>/unstripped.so --baseline <fresh-main-score.json> --json <candidate>/score.json
python3 scripts/pump_admin_cto_differential.py --candidate <candidate>/candidate.so --output <runtime-report.json>
```

Open PRs were checked before submission: no shared program-source diff found.
Related notes-only [#3093](https://github.com/lalalune/pumpfun-source/pull/3093)
studies holder-PDA lifetime and a different payer-first initializer-order change.
This change retains main's initializer order; integration with those unlanded
experiments is not claimed. Merged #3039, #3051, #3066 and #3049 in the same source
file are preserved.
