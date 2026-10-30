# Contributing

## Scope

This repository reconstructs the **on-chain bytecode** of pump.fun's deployed
Solana programs: Pump Main, PumpSwap/AMM, Fees, Mayhem and the Donation Relay.
The goal is source that rebuilds, with a pinned toolchain, to the same bytes as
the program binaries that are publicly deployed on-chain.

Nothing else is in scope. This project does not reconstruct, capture or
reproduce pump.fun's website, mobile apps, backend services, APIs, SDKs,
indexers, branding or any other off-chain material.

## Pull requests we accept

- Program source changes under `programs/` that raise a window's match score
  with no raw or normalized losses against a fresh main build.
- Toolchain, build-harness and scoring fixes under `reconstruction/` and
  `scripts/`.
- Differential tests that compare a rebuilt program against the captured
  original binary.
- Research packets that explain a remaining byte difference in a program.

## Pull requests we close without review

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

Include the score summary in the PR description and state any `losses` or
`raw_losses`. A change that loses any window will not be merged.
