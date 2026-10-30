# Pump migration lifecycle differential

This package extends the archived Pump migration matrices with persistent,
authenticated, multi-transaction lifecycles. It compares the captured Pump
Main image with a freshly rebuilt image while loading the captured PumpSwap,
SPL Token, Token-2022, and Associated Token binaries into local LiteSVM.

No RPC endpoint or live transaction is used. The only outer-transaction
signers are deterministic local `payer` and `user` keypairs. Program-derived
addresses are authorized only through real program CPIs; the harness never
injects a PDA signature.

## Why this is new

The maintained one-shot controls remain valuable, but they do not establish a
post-migration lifecycle:

- `scripts/pump_migrate_differential.py` executes 228 isolated fixture cases.
- `scripts/pump_migrate_v2_differential.py` executes 827 isolated fixture
  cases.
- Both probes create a new LiteSVM inside every `run()` call.
- Their `repeat` option sends the same serialized transaction again with the
  same recent blockhash and signature.

This package retains VM state across steps, calls `expire_blockhash()` before
each transaction, signs a new message, verifies every signature, and rejects a
sequence if any transaction signature repeats.

## Coverage

The v1 plan contains 27 lifecycle cases and 41 distinct signed transactions
per image (82 executions across original and rebuild):

- Legacy native migration: ordinary, mayhem, and `enable_migrate = false`
  success followed by an independent repeat; incomplete, missing-boost, and
  zero-base rollback.
- V2 native migration: SPL and Token-2022 base mints, disabled migration flag,
  retained mint authority, retained freeze authority, and repeat behavior.
- V2 token quote migration: SPL, Token-2022, and Token-2022 with a 100 bps
  transfer-fee extension; non-whitelisted quote behavior; insufficient quote
  and invalid quote-account ownership.
- CPI/account boundaries: missing boost accounts, readonly boost vault,
  readonly pool vaults, bad mint/token owners, zero base, and bad PumpSwap
  event authority.
- A three-step committed lifecycle: successful migration, a separately signed
  invalid post-migration attempt, then a separately signed valid repeat.

Every failed transaction compares the full tracked non-fee state before and
after. Every successful repeat must change no non-fee state and emit no event.
Every successful initial migration must drain the curve base account, fund the
PumpSwap base and quote vaults, create a PumpSwap-owned pool, and zero all four
curve reserve fields.

The original image is the outcome oracle. Two requested assumptions are not
encoded as expected failures because the captured program disproves them:

- Both legacy migration and `migrate_v2` accept the synthetic completed curve
  when `Global.enable_migrate` is false.
- `migrate_v2` accepts the synthetic stable quote even when that mint is
  removed from the Global quote-mint slots. Quote admission occurs earlier in
  the curve lifecycle, not in this migration handler.

The report records these outcomes as `*-observed` cases rather than describing
them as policy guarantees.

## Fail-closed report

Each saved case includes:

- fixture, IDL, and all executed program SHA-256 hashes;
- canonical initial-state hash;
- exact instruction and transaction bytes, signature, recent blockhash, and
  message hash for every step;
- signature-verification results;
- errors, events, semantic and raw logs, inner instructions, return data, and
  compute units;
- complete before/after snapshots of all named non-executable accounts;
- explicit original/rebuild mismatch fields and rollback/invariant failures.

Strict comparison includes transaction identity, errors, events, inner
instructions, return data, semantic logs, and account state. Raw compute-unit
and raw-log differences are retained as diagnostics because rebuilt source
paths and image-size charging can differ. The semantic-log normalization only
removes `consumed` lines, invoke/success scaffolding, and the known
`programs/pump/src/` versus `src/` path prefix.

The suite includes negative controls that alter one error and one after-state;
both must be detected. A missing receipt also fails the unit comparator.

## Reproduce

Requires Python with `solders==0.27.1`.

```sh
python reconstruction/verification/pump-migration-lifecycle/lifecycle.py \
  --candidate /path/to/candidate.so \
  --output /tmp/pump-migration-lifecycle.json.gz

python reconstruction/verification/pump-migration-lifecycle/verify.py \
  --report /tmp/pump-migration-lifecycle.json.gz \
  --candidate /path/to/candidate.so \
  --replay

cd reconstruction/verification/pump-migration-lifecycle
python -m unittest -v test_lifecycle.py
```

The current-main candidate was built with the repository's pinned identity
recipe:

```sh
python3.11 reconstruction/toolchain/bootstrap.py --sdk-check full
python3.11 reconstruction/harness/fastbuild.py \
  --src programs/pump \
  --work /tmp/pump-window-m-build \
  --out /tmp/pump-window-m-build/current \
  --recipe identity --timeout 1200
```

## Qualification identity

- Upstream source: `7e26cbf36c5c0c824e3eb36417ce8a35866f530a`
- Original Pump: `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`
- Current rebuild: `9dfc496c288be94d866cb96652ef4325e194a1cde30665e8414775a2dd2a9890`
- Captured PumpSwap: `6a7ad34596d83b4c435b32f458a56e718e9f82eb4ad38e4316616d15d24d8ff7`
- Captured SPL Token: `8190d3f7ceb6cb7a7a8d8924bff89f9f611e15ce1f806f2b6237f3311a98f697`
- Captured Token-2022: `15a2e615a42e20f31714bbaaee43002ae6f1cda2e8d7118243117ab3c1342e2d`
- Captured Associated Token: `6804554e69fd3a58caa191dc4a58f4c67223d30ca28ab8987f39fc18d2f7374d`
- Fixture: `b4894531409f1cb016c2993a061c99f4316140659f9cffb25cae0875b189dbfc`
- Pump IDL: `7616681ea557975f9f623ac211080f22a93060781eaf4765b0a488d980997207`

The full machine-readable receipts are in
`results/current-main.json.gz` and are revalidated by `verify.py`.

## Limits

- Initial curve and token state is synthetic and derived from the retained
  Surfpool fixture; it is not claimed to be a mainnet account snapshot.
- The suite observes disabled-flag behavior but cannot authorize the real
  administrative `set_params` transition, so it does not fabricate that
  signer or claim to test it.
- Tracked state covers every named instruction/remaining account and local
  signer, not arbitrary unreferenced VM accounts or executable program data.
- This is deterministic local-runtime evidence, not a comprehensive Solana
  filesystem/runtime sandbox and not a whole-program equivalence claim.
