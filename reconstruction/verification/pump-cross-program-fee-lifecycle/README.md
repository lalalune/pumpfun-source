# Pump cross-program creator-fee lifecycle differential

This package compares a captured Pump Main image with an immutable rebuilt Pump
Main image while executing PumpSwap trades, PumpSwap creator-fee settlement,
and Pump Main `admin_cto` in independent persistent LiteSVM instances. All
transactions are signed by deterministic ordinary keypairs. Pump and PumpSwap
PDAs are never inserted as top-level signers; Pump Main obtains the canonical
pool-authority signature only through its real CPI.

## Coverage audit and gap

The following merged work was treated as prior art and was not duplicated:

- PR #3933, `pump-admin-cto-stateful`, retains state across 20 signed
  transactions per image. It exercises Admin CTO and collection over seeded
  balances, but does not execute a trade that creates the collected fee.
- PR #3928 ranks paired SBPF residuals and does not execute economic state
  transitions.
- `pump-migration-lifecycle` retains state through migration and repeat
  attempts, but does not trade against the resulting pool or reassign its
  creator.
- The maintained Pump/PumpSwap buy, sell, creator-collection, sweep, and Admin
  CTO differentials create a fresh VM for each case.

The new boundary is a fee created by a genuine captured PumpSwap trade and
consumed by later transactions before and during a Pump Main Admin CTO. A later
trade observes the reassigned creator. The package also places a successful
trade before a failing Admin CTO in one transaction and proves that the trade
is rolled back atomically.

## Executed lifecycle

One deterministic fixture executes 11 distinct transactions per image:

1. `buy_v2` for creator A; this also creates the user volume accumulator.
2. `sweep_creator_fee` drains the accrued pool fee into A's creator vault.
3. `collect_coin_creator_fee` pays A.
4. Pump Main `admin_cto` changes A to B through captured PumpSwap CPI.
   The Fees image is loaded but this fixture does not invoke the Fees program.
5. A later `buy_v2` accrues fees for B.
6. One transaction runs `buy_v2` and then attempts B-to-C Admin CTO without a
   sweep. Captured execution returns `CreatorFeesNotSwept`; every tracked
   non-fee account, including the earlier trade effects, rolls back.
7. The valid retry atomically runs `sweep_creator_fee` and B-to-C Admin CTO.
   The downstream Admin CTO path forwards the swept fee into B's token account.
8. A later B collection is an observed successful empty no-op, proving the fee
   was already consumed.
9. A later `buy_v2` accrues fees for C.
10. `sweep_creator_fee` drains C's accrued pool fee.
11. `collect_coin_creator_fee` pays C.

This is 22 executions for the original/candidate comparison: 20 successful
transactions and two expected program failures. Two transactions per image
contain more than one economic instruction. The producer retains exact signed
transaction bytes, blockhashes, signatures, errors, events, semantic and raw
logs, inner instructions, return data, compute use, and complete before/after
snapshots of every tracked non-executable account.

## Accounting and admission

The independent validators recompute:

- signature validity, signer membership, message hashes, unique transaction
  identities, state hashes, and continuity between every transaction;
- full rollback after the expected failure, excluding only the payer fee;
- base and quote token reserve direction for every committed trade;
- positive creator-fee accrual, zero fee state after every sweep, and creator
  agreement between the Pump curve and PumpSwap pool after the retry;
- creator A/B/C payouts and the observed empty B recollection;
- wrapped-SOL token/lamport delta equality and total tracked-lamport
  conservation after transaction fees;
- binary, IDL, fixture, producer, current source-tree, and reused-candidate
  provenance hashes.

Four negative controls independently alter an error, event, inner-instruction
record, and post-state. All four must be detected by the strict comparator.
The unit suite additionally rejects signature, summary, provenance, state, and
publication tampering.

Reports classify results as exactly one of `equal_observed_behavior`,
`different_behavior`, `unsupported_fixture`, or `infrastructure_failure`.
An original-side receipt or invariant failure is never reported as candidate
equivalence.

## Historical author qualification inputs

- Captured Pump Main: `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
- Rebuilt Pump Main: `9dfc496c288be94d866cb96652ef4325e194a1cde30665e8414775a2dd2a9890`
- Captured PumpSwap: `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`
- Captured Pump Fees: `4f2955d0f6b40cc9ff7daa18ccad7d19119ba1249759f4e7e3bb691beee6b35e`
- Captured SPL Token: `8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697`
- Captured Associated Token: `6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d`

The rebuilt image is reused from the merged migration-lifecycle qualification,
which recorded 41 matching migration transactions per image. Its source
revision and retained build-receipt hashes are in `candidate-provenance.json`.
The current checkout source manifest is bound as review context only: this work
did not rebuild Pump and does not claim that the historical candidate was built
from the current head.

## Current supplied-image admission

Any candidate image may now be compared as `supplied-candidate-input-v1`.
That label binds the immutable executed bytes only. It explicitly leaves the
candidate source revision unknown and the current source manifest as review
context; a build/source acceptance must come from its independent build receipt.
The original retained `results/current-qualified.json.gz` and
`candidate-provenance.json` are preserved byte-for-byte as historical author
receipts. They are not resealed for the reviewed producer and therefore do not
claim current helper/source admission after these repairs.

The current reader reconstructs each complete signed message from the fixed
11-step plan and its before-state: instruction data, account ordering and flags,
program routing, compute budget, payer and exact signer membership must agree.
Every constructed fixture account must appear in each snapshot. Signature flags
and count/summary claims use exact JSON value types, and duplicate JSON fields
are rejected. The producer and reader compile their execution-bearing local
modules from admitted source bytes rather than accepting executable bytecode
caches, and producer inputs and source review context are checked again after
execution. Reports cannot be created inside the source input tree.

These checks establish retained receipt consistency. The `--replay` gate runs
fresh VMs and is the separate deterministic execution check; saved JSON alone is
not evidence that an arbitrary claimed VM execution occurred.

## Reproduce

Use Python 3.12 and the repository-pinned `solders==0.27.1`.

Original-vs-original qualification:

```sh
out=$(mktemp -d)
uv run --offline --python 3.12 --with solders==0.27.1 python \
  reconstruction/verification/pump-cross-program-fee-lifecycle/lifecycle.py \
  --candidate evidence/original/pump/deployed.so \
  --output "$out/original-control.json.gz"
```

Rebuilt comparison and independent replay:

```sh
candidate=/path/to/reviewed-candidate.so
out=$(mktemp -d)
uv run --offline --python 3.12 --with solders==0.27.1 python \
  reconstruction/verification/pump-cross-program-fee-lifecycle/lifecycle.py \
  --candidate "$candidate" --output "$out/report.json.gz"
uv run --offline --python 3.12 --with solders==0.27.1 python \
  reconstruction/verification/pump-cross-program-fee-lifecycle/verify.py \
  --candidate "$candidate" --report "$out/report.json.gz" --replay
```

Regression tests (17 tests):

```sh
uv run --offline --python 3.12 --with solders==0.27.1 python -m unittest -v \
  reconstruction/verification/pump-cross-program-fee-lifecycle/test_lifecycle.py
```

## Limits

- The account fixture is deterministic and synthetic. Its pool values and fee
  table are derived from retained captured-program fixtures, not claimed as an
  archival mainnet pre-trade state.
- PumpSwap, Pump Fees, SPL Token, and Associated Token remain captured
  dependencies on both sides. This package differentially isolates Pump Main;
  it does not compare rebuilt dependency programs. The observed fixture invokes
  Pump, PumpSwap, SPL Token and Associated Token; no Pump Fees CPI is observed.
  Loading the Fees image and reading its fee-config state do not establish Fees
  execution coverage.
- Complete snapshots cover every account constructed or addressed by the
  lifecycle, not arbitrary unreferenced VM accounts.
- Raw compute units and source-path-bearing log scaffolding are diagnostic.
  Errors, semantic logs, events, inner instructions, return data, and account
  state are strict.
- This is bounded lifecycle evidence, not whole-program equivalence or ELF
  identity evidence.
