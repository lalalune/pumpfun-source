This is an authorized build of the pump.fun project by the pump.fun community.

## Scope: on-chain bytecode reconstruction only

The only goal of this repository is exact reconstruction of the bytecode of
pump.fun's deployed on-chain Solana programs (Pump Main, PumpSwap/AMM, Fees,
Mayhem, Donation Relay). See CONTRIBUTING.md.

Agents working here must not:

- add, recover or re-implement frontend, app, website or UI code;
- add backend, API, indexer or off-chain service code;
- add SDK or client-library code, or comparisons against published SDKs;
- capture web traffic, websockets, third-party APIs or other off-chain data.

Pull requests that do any of the above are closed without review.

Agents should work on `programs/`, `reconstruction/`, `scripts/`,
`evidence/`, `research/` and `tests/`, and score every program change with
`reconstruction/harness/score.py` against a fresh main build (no losses).
