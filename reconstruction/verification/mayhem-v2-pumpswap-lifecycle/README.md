# Mayhem V2 and PumpSwap persistent lifecycle differential

## Coverage audit

The merged `mayhem-stateful-lifecycle` package deliberately limits its
persistent trade coverage to legacy native-SOL `buy` and `sell`. The retained
`mayhem_buy_v2_differential.py`, `mayhem_sell_v2_differential.py`, and
`mayhem_pump_swap_differential.py` tools each construct a new LiteSVM for every
case. They prove broad single-transaction admission behavior, but no successful
V2 or PumpSwap trade supplies state to a later transaction.

This package closes that specific gap. It executes authenticated Mayhem V2 and
Mayhem PumpSwap instructions in persistent, independent LiteSVM instances and
records the complete watched state before and after each signed transaction.
It does not duplicate legacy Mayhem coverage and does not change any program
source or reconstruction score.

The fixture is `synthetic_preinitialized`: canonical PDAs and genuine captured
programs are used, but Mayhem initialization is not claimed. Mayhem signs only
for its canonical `sol-vault` PDA during real Pump/PumpSwap CPIs. Ordinary
test-owned Ed25519 keys sign every outer transaction.

## Qualified images

- captured Mayhem allocation: 777,408 bytes, SHA-256
  `a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`
- exact meaningful-ELF candidate: 775,416 bytes, SHA-256
  `9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d`

The candidate is the artifact qualified by
`reconstruction/mayhem/native-linux-qualification/QUALIFICATION.json` and the
exact Windows build run recorded in `provenance.json`. No compiler run is
required by this package.

## Qualified persistent lifecycles

The bounded plan contains 14 transactions per image. Twelve captured-original
transactions succeed and two deliberately fail with exact Mayhem slippage error
6012. Every retry after a failure succeeds and observes only the transaction
fee from the rejected attempt.

| lifecycle | captured transitions | qualification |
| --- | --- | --- |
| `v2_buy_buy_sell` | `buy_v2`, `buy_v2`, `sell_v2` | three persistent successes |
| `v2_failure_retry_atomic` | buy, rejected sell, retry sell, atomic buy+sell | rollback, retry, and atomic success |
| `pumpswap_buy_buy_sell` | buy, buy, sell | three persistent successes with evolving pool reserves |
| `pumpswap_failure_retry` | buy, rejected sell, retry sell | exact rollback followed by success |
| `pumpswap_atomic_buy_sell` | atomic buy+sell | both real Mayhem instructions commit in one transaction |

The captured program rejected an investigated `sell_pump_swap ->
buy_pump_swap` ordering with Mayhem error 6001 after the sell exhausted the
fixture's allowed reserve boundary. It is not labeled a positive lifecycle.
The successful atomic pair therefore runs in its own independently constructed
VM rather than inheriting incompatible state.

The V2 fixture uses native wrapped SOL as quote, Token-2022 as the base-token
program, and real captured Pump/Pump Fees/SPL programs. The PumpSwap fixture
uses the captured pool, native wrapped SOL quote, Token-2022 base mint, and real
captured PumpSwap/Pump Fees/SPL programs. Existing isolated matrices already
cover SPL and Token-2022 quote admission. This package does not claim persistent
SPL or Token-2022 quote lifecycles or transfer-fee extension coverage.

## Runtime and economic checks

`runtime.py` constructs a new VM for every lifecycle and never writes fixture
accounts after construction. Each later transaction receives a fresh
blockhash, while account state persists. Both images receive the exact same
signed transaction bytes.

`verify.py` is independent of producer acceptance fields. It reconstructs and
checks:

- both Ed25519 signatures, required signer membership, complete messages,
  instruction order, transaction hashes, and fresh blockhashes;
- the exact case plan, executable identity, all captured dependencies, the
  complete Mayhem source tree, fixture inputs, and receipt file hash;
- full watched snapshot membership, owner/data metadata, state continuity,
  unique transaction identities, exact errors, events, inner instructions,
  return data, raw logs, and compute units;
- failed-transaction rollback with only the two-signature fee retained;
- base-token conservation, unchanged mint supply, Mayhem global/per-token
  signed accounting, V2 virtual/real reserves, PumpSwap pool reserves, wrapped
  SOL rent effects, and watched lamport conservation;
- exact original/candidate observations after excluding only the different
  Mayhem executable account bytes.

The verifier deliberately mutates ten independently meaningful receipt fields:
transaction signature, Mayhem vault balance, PumpSwap reserve, Mayhem
accounting, event, failure outcome, token owner, transaction sequence,
executable digest, and passing case count. All ten controls must be rejected.

## Qualification result

At upstream `e89d79aa8d0ad61cefa99b614390eca13500a743`:

- original-vs-original: 14/14 equal, 12 successful original transitions, 2
  expected failures, 28 verified signed transactions;
- original-vs-candidate: 14/14 equal, 12 successful original transitions, 2
  expected failures, 28 verified signed transactions;
- mismatches: 0; unsupported selected fixtures: 0; infrastructure failures: 0;
- negative controls: 10/10 detected;
- package regression tests: 21/21 passed with the exact candidate enabled;
- existing `mayhem-stateful-lifecycle`: 14/14 tests passed;
- existing Mayhem report publication suite: 8/8 tests passed.

The exact candidate has the same events, return data, inner instructions,
complete non-program account states, raw logs, and compute use for every case.
This finite result does not expand Mayhem's already-qualified 441/441
meaningful-ELF checkpoint and is not a claim of exhaustive semantic or security
equivalence.

## Reproduce

Retrieve the authenticated exact candidate:

```sh
candidate_dir=$(mktemp -d /tmp/mayhem-canonical.XXXXXX)
gh run download 40770208958 \
  --repo lalalune/pumpfun-source \
  --name mayhem-canonical-windows-40770208958-1 \
  --dir "$candidate_dir"
candidate="$candidate_dir/build/build/target/candidate-v154-strip.so"
shasum -a 256 "$candidate"
```

Run and independently verify the captured control:

```sh
package=reconstruction/verification/mayhem-v2-pumpswap-lifecycle
control=$(mktemp -d /tmp/mayhem-v2-control.XXXXXX)
uv run --offline --python 3.12 --with solders==0.27.1 \
  python "$package/producer.py" \
  --candidate evidence/original/mayhem/deployed.so \
  --original-control --output "$control/runtime"
uv run --offline --python 3.12 --with solders==0.27.1 \
  python "$package/verify.py" \
  --report "$control/runtime/report.json" \
  --candidate evidence/original/mayhem/deployed.so \
  --output "$control/verification.json"
```

Run the exact candidate comparison and tests:

```sh
comparison=$(mktemp -d /tmp/mayhem-v2-comparison.XXXXXX)
uv run --offline --python 3.12 --with solders==0.27.1 \
  python "$package/producer.py" --candidate "$candidate" \
  --output "$comparison/runtime"
uv run --offline --python 3.12 --with solders==0.27.1 \
  python "$package/verify.py" \
  --report "$comparison/runtime/report.json" --candidate "$candidate" \
  --output "$comparison/verification.json"
MAYHEM_EXACT_CANDIDATE="$candidate" \
  uv run --offline --python 3.12 --with solders==0.27.1 \
  python -m unittest discover -s "$package" -p 'test_*.py' -v
```

Output directories are exclusively created and never replace earlier evidence.
Reports and receipts use canonical JSON ordering and LF endings. Repeated
execution at the same revision produces byte-identical receipts.

## Limits

- The initial business state is deterministic synthetic state at canonical
  addresses, not a historical mainnet snapshot or initialization claim.
- Native wrapped-SOL quote behavior is qualified. Persistent SPL/Token-2022
  quote paths, transfer-fee extensions, reserve exhaustion, pause/authority
  variants, and cross-venue economic continuity remain outside this plan.
- Fee recipient token balances remain zero under the captured fixture's fee
  configuration; their unchanged state is verified, but nonzero creator,
  protocol, or withheld-fee accrual is not claimed.
- LiteSVM represents loaded program accounts locally and does not reproduce
  upgradeable-loader metadata. No RPC or mainnet transaction is used.
- Finite differential equality is bounded evidence, not broad semantic
  equivalence, security clearance, or a bytecode completion increase.
