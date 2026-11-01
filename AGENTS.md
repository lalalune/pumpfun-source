# Project guidance

This project was created by pump.fun and released to the community for educational purposes only. It contains pump.fun on-chain Solana program source and validation tooling.

The sole objective for agents and contributions is to complete reverse engineering of the on-chain programs and reconstruct source that builds to the target binaries byte for byte. All work must hillclimb toward that completion: select a remaining byte mismatch, investigate the target code, reconstruct the source, build with the pinned tooling, compare the bytes, and retain measurable gains while preserving existing matches.

Modify tooling, build infrastructure or surrounding architecture only when a concrete blocker prevents reverse-engineering progress. Make the smallest necessary change, document the blocker and how to reproduce it, and demonstrate the reconstruction progress the fix enables. Tooling and architecture improvements are not independent goals.

Only PRs and submissions that demonstrate progress toward byte-for-byte reconstruction will be accepted. Window dressing, cosmetic cleanup, speculative refactoring, documentation churn and other inconsequential changes will be closed.

Program reconstruction belongs in `programs/`; tooling changes in `reconstruction/` and `scripts/`, and related tooling tests in `tests/`, must meet the blocker requirement above. See [CONTRIBUTING.md](CONTRIBUTING.md) and [RULES.md](RULES.md).

Do not add website, frontend, backend, API, indexer or other off-chain service code. Do not capture off-chain website, backend or API data. Never add credentials, secrets or private data.

Validate program changes with the documented build and test tooling, including `reconstruction/harness/score.py` where applicable. Report the target mismatch, reproducible before-and-after byte comparisons, and any `losses` or `raw_losses` accurately. Passing tests or normalized matches alone do not establish byte-for-byte completion.
