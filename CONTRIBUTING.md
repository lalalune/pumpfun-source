# Contributing

This project was created by pump.fun and released to the community for educational purposes only. The sole focus of contributions is reverse engineering the pump.fun on-chain Solana programs to recover source that rebuilds the target binaries byte for byte.

## Acceptance criterion

Only PRs and submissions that demonstrate progress toward complete, byte-for-byte reconstruction will be accepted. Every contribution must hillclimb toward that goal by resolving remaining byte differences and preserving existing matches.

Changes to tooling, build infrastructure or surrounding architecture are allowed only when a concrete blocker prevents reverse-engineering progress. Such changes must be the smallest necessary fix, identify the blocked reconstruction task, reproduce the blocker, and demonstrate the reconstruction progress enabled by removing it. General tooling improvements and architectural redesigns are not independent reasons for acceptance.

PRs and submissions consisting of window dressing, cosmetic cleanup, speculative refactoring, documentation churn or other inconsequential changes will be closed. Passing tests, cleaner tooling or a better-looking repository alone do not qualify as reconstruction progress.

## Contribution rules

- Focus on reverse engineering the code and reducing the remaining byte differences against the target binaries.
- Do not add website, frontend, backend, API, indexer or other off-chain service code.
- Do not capture or add off-chain website, backend or API data.
- Do not include credentials, secrets or private data.
- Document build and test commands, inputs and results so others can reproduce them.

For changes that meet the acceptance criterion, program source belongs in `programs/`; build and validation tooling belongs in `reconstruction/` and `scripts/`; tooling tests belong in `tests/`.

## Validation

Build and test changes using the documented pinned tooling. For program changes, compare against a fresh main build where applicable:

```bash
python3 reconstruction/harness/fastbuild.py --src <worktree>/programs/pump --work <work-dir> --out <out>
python3 reconstruction/harness/score.py <out>/unstripped.so --baseline <main score.json> --json <out>/score.json
```

Include the target program and function or window, the byte mismatch being resolved, and reproducible before-and-after byte comparisons in the pull request. Include the relevant test and score summaries, including any `losses` or `raw_losses`. For a blocker fix, also include the failing command or evidence of the blocker and the reconstruction result obtained after the fix. Do not merge changes with unexplained regressions.

Behavioral equivalence, passing tests and normalized matches alone do not establish byte-for-byte completion. Report partial gains as partial gains and keep raw-byte progress distinct from normalized scores.
