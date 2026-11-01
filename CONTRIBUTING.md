# Contributing

## Scope

This repository reconstructs the **on-chain bytecode** of pump.fun's deployed
Solana programs: Pump Main, PumpSwap/AMM, Fees, Mayhem and the Donation Relay.
The goal is source and a pinned build recipe that rebuild to the same bytes as
the program binaries that are publicly deployed on-chain.

Nothing else is in scope. This project does not reconstruct, capture or
reproduce pump.fun's website, mobile apps, backend services, APIs, SDKs,
indexers, branding or any other off-chain material.

## Pull requests we accept

At this stage, the only accepted contributions are those that hillclimb
reconstruction completion percentages toward 100% by resolving remaining
bytecode differences against the target binaries while preserving existing matches.

- Program source changes under `programs/` that raise a window's match score
  with no raw or normalized losses against a fresh main build.
- Build-input changes (crate metadata, `Cargo.lock`, dependencies, profiles, flags,
  linker settings, toolchain version and build recipe) that move a build closer to the
  deployed bytes, when they are pinned and reproducible. See
  [reconstruction/pump-main/README.md](reconstruction/pump-main/README.md#build-inputs-are-in-scope-2026-10-30).
- Toolchain, build-harness and scoring fixes under `reconstruction/` and
  `scripts/` that remove a concrete reconstruction blocker and demonstrate the
  byte-for-byte reconstruction progress enabled by the fix.
- Differential tests that compare a rebuilt program against the captured
  original binary and support demonstrated reconstruction gains.
- Research packets that help resolve a remaining byte difference in a program
  and demonstrate measurable reconstruction gains.

Changes to tooling, build infrastructure or surrounding architecture must be
the smallest necessary fix for a concrete reconstruction blocker. Document the
blocked task, how to reproduce the blocker, and the reconstruction progress
enabled by removing it. These improvements are not independent goals.

## Pull requests we close without review

- Window dressing, cosmetic cleanup, speculative refactoring, documentation
  churn and other changes that do not demonstrate reconstruction progress.
- Frontend, UI, app or website work, including recovered or re-implemented
  components.
- Backend, API, indexer or off-chain service work.
- SDK or client-library work, including comparisons against published SDKs.
- Capture of web traffic, websockets, third-party APIs (for example PumpPortal)
  or other off-chain data.

## Scoring a change

Build a candidate and score it against a fresh main build:

```bash
python3 reconstruction/harness/fastbuild.py --src <worktree>/programs/pump --work <work-dir> --out <out>
python3 reconstruction/harness/score.py <out>/unstripped.so --baseline <main score.json> --json <out>/score.json
```

Include the target program and function or window, the byte mismatch being
resolved, and reproducible before-and-after completion percentages and byte
comparisons in the PR description. Include the score summary and state any
`losses` or `raw_losses`. A change that loses any window will not be merged.

Behavioral equivalence, passing tests and normalized matches alone do not
establish byte-for-byte completion. Report partial gains as partial gains and
keep raw-byte progress distinct from normalized scores.
