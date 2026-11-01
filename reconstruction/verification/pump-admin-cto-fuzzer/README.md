# Pump Admin CTO deterministic differential fuzzer

This package generates compositional, seed-addressed `admin_cto` inputs, executes
them against two Pump Main images in independent LiteSVM instances, compares
authenticated behavior, and reduces reproducible behavioral differences. It is
an addition to, not a replacement for, the maintained 388-case
`scripts/pump_admin_cto_differential.py` matrix and the nine fixed persistent
lifecycles in `pump-admin-cto-stateful`.

The fixtures are synthetic and no network RPC or mainnet transaction is used.
Every outer transaction is signed normally with retained deterministic wallet
keypairs. PDAs are never added as outer signers. Captured PumpSwap, Pump Fees,
SPL Token, Token-2022, and Associated Token images perform genuine CPI behavior.

## Case model and comparison

`case_model.py` uses a versioned SHA-256 counter stream rather than Python's RNG.
The unsigned 128-bit root seed, unsigned 64-bit index, derived 128-bit case seed, canonical input,
and content-derived case ID are retained. A corpus removes duplicate case IDs.
`--start-index` permits non-overlapping bounded tranches.

The fixture grammar rejects unknown fields, integer substitutes for booleans,
duplicate step names and account indices, invalid ownership/target combinations,
and noncanonical hexadecimal data. It permits one to eight retained steps and
zero to eight mutations; account byte edits are bounded at 16,384 bytes and
instruction edits at 1,024 bytes. These are fixture limits, not protocol limits.
Campaigns accept 1–1,000 cases and reduction budgets of 1–10,000 executions.

Generated compositions cover native, SPL Token, and Token-2022 quote modes;
optional argument tags and values; creator/holder/fee transitions; sharing,
pool, curve, global, mint, and token account data; owner, lamport, amount, state,
length, and byte mutations; account replacement, writability, omission, and PDA
errors; and one-to-three sequential transactions. Some compositions are
intentionally invalid. A fixture mutation that cannot be represented is
`unsupported_fixture`, never successful equivalence.

For every executed transaction, receipts retain the exact transaction and
signature, message/blockhash, instruction bytes and account metas, error and
outcome, events, return data, inner instructions, account owner/lamports/data,
pre/post persistent state, rollback evidence, raw logs, and compute units.
Strict comparison includes every item except raw logs and compute units. Those
two are diagnostics because recovered source locations and instruction layout
can legitimately differ; semantic logs remove only invoke/success scaffolding,
compute-unit lines, and the known `programs/pump/src/` prefix.

The four dispositions are:

- `equal_observed_behavior`: all strict observations match;
- `different_behavior`: at least one strict observation differs;
- `unsupported_fixture`: the composition cannot be represented safely;
- `infrastructure_failure`: receipt invariants, runtime infrastructure, or
  extension execution failed.

Finite cases establish only the retained observations. They do not establish
whole-program semantic or bytecode equivalence.

## Run and replay

Use Python 3.12 and `solders==0.27.1`. Always run an original-vs-original
control before a candidate campaign:

```sh
tool=reconstruction/verification/pump-admin-cto-fuzzer/campaign.py
original=evidence/original/pump/deployed.so
out=$(mktemp -d)

uv run --offline --python 3.12 --with solders==0.27.1 python -I -B "$tool" run \
  --original "$original" --candidate "$original" \
  --expected-original-sha256 7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d \
  --expected-candidate-sha256 7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d \
  --seed 20261101 --count 16 --output "$out/control"

uv run --offline --python 3.12 --with solders==0.27.1 python -I -B "$tool" run \
  --original "$original" --candidate /path/to/provenance-verified/candidate.so \
  --expected-original-sha256 7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d \
  --expected-candidate-sha256 EXPECTED_SHA256 \
  --seed 20261101 --count 16 --output "$out/candidate"
```

`cases.json` is the replayable corpus. Detailed receipts are deterministic gzip
files by default; `--omit-detailed-receipts` retains compact per-case progress
instead. Replay one retained case with:

```sh
uv run --offline --python 3.12 --with solders==0.27.1 python -I -B "$tool" replay \
  --case /path/to/case.json --original "$original" \
  --candidate /path/to/candidate.so
```

The original image must match the captured Pump SHA-256 above. Every executable, dependency, IDL, fixture, and producer is copied to an
immutable temporary snapshot before execution and rehashed at completion.
Source modules are compiled from the hashed `.py` bytes in private namespaces;
timestamp bytecode caches and preexisting canonical module aliases cannot
replace the local producer graph. The report binds the exact generated corpus,
the complete artifact and directory census, and the actual executed source
hashes. Every receipt is checked against its canonical case, constructor state,
complete signed message, account roles, watched keys, and transaction continuity.
Destination publication uses a POSIX advisory lock, exclusive files, fsync, and
an atomic directory rename. Complete output is never overwritten. A normal
exception marks the hidden `.NAME.partial-*` directory interrupted; SIGKILL or
machine loss can leave it `in_progress`. Partial attempts are retained for
inspection. Advisory locking and directory fsync are POSIX-specific, and no
claim is made that storage survives physical machine loss.

## Counterexample reduction

Every `different_behavior` result is automatically passed to `reducer.py`
unless `--no-reduce` is explicit. Each proposal reruns both images and must
preserve the same mismatch fields and directional outcomes. It removes account
mutations, fields, transactions, optional arguments, list elements, and then
shrinks numeric values. Qualified results include the original seed, reduced
case, program hashes, replay command, all trials, and retained receipts.

The reducer claims only **one-minimality over its enumerated immediate reduction
neighborhood**. It never claims a global minimum. Budget exhaustion or any
unchecked/preserving neighbor leaves `minimality.demonstrated` false.

## Independent verification and tests

The v2 verifier regenerates the exact seeded corpus and recomputes artifact and summary hashes, executable/producer identity,
transaction signatures, instruction identity, account snapshots, continuity,
rollback, derived fields, strict comparison, classifications, counts, and
negative controls. `--reexecute` additionally reruns every case:

```sh
uv run --offline --python 3.12 --with solders==0.27.1 python -I -B \
  reconstruction/verification/pump-admin-cto-fuzzer/verify_report.py \
  --report /path/to/campaign --original "$original" \
  --candidate /path/to/candidate.so --reexecute

uv run --offline --python 3.12 --with solders==0.27.1 python -I -B \
  -m unittest discover -s reconstruction/verification/pump-admin-cto-fuzzer \
  -p 'test_*.py' -v
```

Compact reports require either `--reexecute` or the explicit `--provenance-only`
option. Provenance-only admission never returns runtime verification. Detailed
receipts can be admitted offline; `--reexecute` also independently reproduces
the retained observations. A saved reduction is a retained mismatch witness;
its local one-minimality claim is independently checked only with reexecution.
Corrupt receipts, changed executable identities, mutated
inputs, invalid case IDs, invalid reductions, publication races, and extension
panic handling have deterministic regressions.

See `QUALIFICATION.md` for the bounded campaign results used to qualify this
implementation.
