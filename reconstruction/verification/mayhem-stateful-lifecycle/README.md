# Mayhem stateful trading lifecycle differential

This package adds the persistent Mayhem coverage that the existing trade
differentials do not provide. It runs genuine signed transactions against the
captured Mayhem executable and a provenance-qualified rebuilt executable in
independent LiteSVM instances. Account state survives from one transaction to
the next inside each lifecycle.

## Coverage qualification

The prior `mayhem_buy_*`, `mayhem_sell_*`, and PumpSwap scripts construct a
fresh VM for every case. They are broad single-transaction admission and
economic controls, but a successful trade never supplies state to a later
trade. `scripts/mayhem_burn_sequence.py` is persistent, but covers only burn
and repeated-burn rejection. `mayhem-dispatch-boundaries` stops at instruction
admission and explicitly makes no handler-body claim.

This package covers two new captured-program lifecycles:

| lifecycle | persistent transactions | observed captured behavior |
| --- | --- | --- |
| `buy_buy_sell` | buy, buy, sell | all three succeed; the second buy consumes the first buy's reserve/counter state, and sell consumes both buys' resulting state |
| `admin_gate_atomic_retry` | stop, rejected buy, unauthorized resume, resume, atomic stop+buy, retry buy, atomic buy+sell | pause and authority gates reject with rollback; the failed two-instruction transaction rolls back `stop`; retry and a two-trade transaction succeed |

The plan executes 10 transactions per image: 7 successful transitions and 3
expected failures. Two transactions contain multiple Mayhem instructions:
the failing `stop+buy` atomic rollback and the successful `buy+sell` pair are
the nontrivial atomic cases (the compute-budget instruction is not counted as
a Mayhem instruction).

Every transaction uses ordinary Ed25519 signers, runtime signature checking,
runtime blockhash checking, a new blockhash after the prior transaction, and a
different signed message. Mayhem signs its Pump CPI only for the canonical
`sol-vault` PDA through the real program runtime. The fixture never injects a
PDA signature.

## Initialization boundary

The fixture is deliberately and prominently classified
`synthetic_preinitialized`. Mayhem initialization requires the Pump
`mint-authority` PDA as a signer, which cannot legitimately sign an outer
LiteSVM transaction. This package does not bypass that constraint and makes no
initialization-success claim.

Instead, deterministic `GlobalParams`, `MayhemState`, token vault, and
supporting Pump accounts are installed at canonical addresses. The fixture is
qualified only because the unchanged captured Mayhem program then performs
seven real successful state transitions, including captured Pump and token
program CPIs. An unsupported initializer is never counted as a passing case.

## What the independent verifier checks

`producer.py` records observations; it does not decide acceptance.
`verify.py` independently recomputes:

- every transaction signature, transaction hash, and recent blockhash;
- the exact planned success/error outcome and captured error code;
- fresh transaction identity within each persistent lifecycle;
- full before/after snapshots for every watched account;
- rollback of every failed transaction, allowing only the two-signature fee;
- exact errors, events, return data, inner instructions, logs, and compute use;
- token-vault, curve-token-account, and mint-supply conservation;
- virtual/real token and SOL reserve deltas;
- Mayhem per-coin and global signed accounting deltas;
- SOL conservation across the Mayhem vault, curve, fee recipient, and creator;
- pause/resume byte transitions and isolation of the two lifecycle VMs;
- captured/rebuilt executable hashes, every dependency executable/capture,
  the complete 68-file Mayhem source tree, fixture, harness, and verifier;
- deliberate outcome and account-state negative controls.

The reader binds the complete current input inventory, admitted report mode,
synthetic fixture classification, and exact plan. It reconstructs every signed
message, account meta, and required signer from the canonical fixture and the
declared before-state curve. For an atomic transaction both trade references
use that transaction's before-state, as they do in the producer. Signature
claims require actual booleans and the exact signature vector. Every watched
snapshot key, data length/hash, role, executable metadata, constructor prestate,
and per-side state link is checked. Input code is loaded directly from admitted
source bytes, without reading Python bytecode caches. The producer rechecks the
entire input inventory and both images around execution and publication;
outputs must be outside the repository.

Regression controls reseal modified receipts and reject an unrelated correctly
signed compute-only transaction, integer signature flags, omitted inputs,
invented mode/plan/fixture, missing watched accounts, false role/data metadata,
disconnected states, and self-consistent false initial states. They also check
mid-production input/image changes, timestamp-valid injected bytecode, and
optimized Python. These admission checks are bounded receipt validation, not a
cryptographic proof that arbitrary supplied observations came from execution.

Each case is classified as `equal_observed_behavior`, `different_behavior`,
`unsupported_fixture`, or `infrastructure_failure`. Unsupported cases never
increase the equal count.

## Qualified executable

The original is the 777,408-byte captured allocation payload with SHA-256
`a87fa9f866272514e6acb852b668c4a08aeb173d56c883039991d114d1199bdb`.
The candidate is the 775,416-byte meaningful ELF rebuilt from maintained source
with SHA-256
`9af9e3b1cbc9d89340af4d9d46e4c88d3dc2fc67e0090f9370047d97532ff09d`.
The remaining 1,992 captured bytes are an all-zero ProgramData allocation tail,
not linker output. The candidate is authenticated by the merged native Linux
qualification and the earlier exact Windows build; both produced the same
meaningful ELF. No build is needed for this verification.

Retrieve the retained exact-build artifact:

```sh
candidate_dir=$(mktemp -d /tmp/mayhem-canonical.XXXXXX)
gh run download 40770208958 \
  --repo lalalune/pumpfun-source \
  --name mayhem-canonical-windows-40770208958-1 \
  --dir "$candidate_dir"
candidate="$candidate_dir/build/build/target/candidate-v154-strip.so"
shasum -a 256 "$candidate"
```

## Reproduce

Start with the captured original-vs-original control:

```sh
package=reconstruction/verification/mayhem-stateful-lifecycle
control=$(mktemp -d /tmp/mayhem-control.XXXXXX)
uv run --offline --python 3.12 --with solders==0.27.1 \
  python "$package/producer.py" \
  --candidate evidence/original/mayhem/deployed.so \
  --original-control --output "$control/runtime"
uv run --offline --python 3.12 --with solders==0.27.1 \
  python "$package/verify.py" \
  --report "$control/runtime/report.json" \
  --candidate evidence/original/mayhem/deployed.so \
  --output "$control/runtime/verification.json"
```

Then compare the captured image with the qualified rebuild:

```sh
comparison=$(mktemp -d /tmp/mayhem-comparison.XXXXXX)
uv run --offline --python 3.12 --with solders==0.27.1 \
  python "$package/producer.py" \
  --candidate "$candidate" --output "$comparison/runtime"
uv run --offline --python 3.12 --with solders==0.27.1 \
  python "$package/verify.py" \
  --report "$comparison/runtime/report.json" \
  --candidate "$candidate" \
  --output "$comparison/runtime/verification.json"
```

Run the deterministic replay and tamper regressions:

```sh
uv run --offline --python 3.12 --with solders==0.27.1 \
  python -m unittest discover \
  -s reconstruction/verification/mayhem-stateful-lifecycle \
  -p 'test_*.py' -v
```

The producer refuses an existing output directory. JSON receipts use sorted
keys and LF endings; repeated runs with the same repository revision and image
path produce byte-identical `receipts.jsonl` and `report.json`.

## Limits

- The package does not claim Mayhem initialization coverage.
- It covers legacy native SOL buy/sell, pause/resume, authority rejection,
  rollback, and retry. V2, PumpSwap, sweep, withdrawal, and burn retain their
  existing single-transaction or specialized sequence coverage and are not
  duplicated here.
- The fixture is deterministic local execution, not historical transaction
  replay and not proof that its synthetic prestate existed on mainnet.
- LiteSVM loads executable bytes under its local loader representation; the
  on-chain upgradeable-loader account metadata is not claimed.
