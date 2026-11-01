This is an authorized build of the pump.fun project by the pump.fun community.

## Scope: on-chain bytecode reconstruction only

The only goal of this repository is exact reconstruction of the bytecode of
pump.fun's deployed on-chain Solana programs (Pump Main, PumpSwap/AMM, Fees,
Mayhem, Donation Relay). See CONTRIBUTING.md.

At this stage, the only accepted contributions are those that hillclimb
reconstruction completion percentages toward 100% by resolving remaining
bytecode differences against the target binaries while preserving existing matches.

Modify tooling, build infrastructure or surrounding architecture only when a
concrete blocker prevents reverse-engineering progress. Make the smallest
necessary change, document the blocker and how to reproduce it, and demonstrate
the reconstruction progress the fix enables. These improvements are not
independent goals.

Window dressing, cosmetic cleanup, speculative refactoring, documentation churn
and other inconsequential PRs and submissions will be closed.

Agents working here must not:

- add, recover or re-implement frontend, app, website or UI code;
- add backend, API, indexer or off-chain service code;
- add SDK or client-library code, or comparisons against published SDKs;
- capture web traffic, websockets, third-party APIs or other off-chain data.

Pull requests that do any of the above are closed without review.

Agents should work on `programs/`, `reconstruction/`, `scripts/`,
`evidence/`, `research/` and `tests/`, and score every program change with
`reconstruction/harness/score.py` against a fresh main build (no losses).
Report the target mismatch, reproducible before-and-after completion percentages
and byte comparisons, and any `losses` or `raw_losses` accurately. Passing tests
or normalized matches alone do not establish byte-for-byte completion.
