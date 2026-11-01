# Donation Relay multi-donor stateful differential

This finite synthetic fixture compares the captured Donation Relay with a
supplied executable in independent persistent LiteSVMs. Three test-owned donors,
a distinct payer, two configurations and two mints exercise shared accounting
and isolation beyond the preceding single-donor stateful fixtures.

The suite authenticates runtime inputs and receipts. Its `supplied_binary_only`
mode does not authenticate a source build or establish whole-program byte
identity. The optional builder and JSON build-receipt admission from the initial
proposal were removed: a report cannot prove compilation merely by naming tools
and claiming output hashes. `--build-receipt` is explicitly refused.

The production relayer private key is unavailable. Successful closure,
distribution, whitelist changes and Jupiter settlement remain unsupported;
only the actual unauthorized close rejection is tested. No production or PDA
signer is fabricated. No RPC is contacted.

| Case | Sequence | Captured-program observation |
| --- | --- | --- |
| `same_epoch_a_then_b` | A, B | success, success |
| `interleaved_a_b_a` | A, B, A | three successes |
| `three_donors_one_transaction` | A+B+C atomically | success, four real signatures including payer |
| `a_success_b_fail_c_success` | A, invalid B, C | success, custom6009, success |
| `atomic_rollback_invalid_third` | A+B+invalid C | custom6009 at instruction3, full rollback |
| `different_balance_boundaries` | exact, overdrawn, zero | success, token1, success |
| `authority_substitution` | B signs for A's source, B retry | custom2015, success |
| `separate_configurations` | A/configA, B/configB | isolated successes |
| `separate_mints` | A/mintX, B/mintY | isolated successes |
| `zero_and_u64_boundary` | zero, u64MAX, one | success, token1, success |
| `rejected_close_between_donors` | A, outsider close, B | success, custom2012, success |
| `failed_donor_retry` | A, overdrawn B, fresh B | success, token1, success |

A successful run contains twelve equal cases, 28 distinct signed transactions
per image, sixty individual signatures in those shared transactions, and eleven
cases with a positive original execution. This is bounded runtime evidence.
Raw compute consumption is diagnostic; errors, semantic logs/events, return
values, inner instructions, balances, ownership and full watched state are
strict. First prestates are independently reconstructed from the canonical
constructor without executing a transaction. Executable membership and metadata
are bound separately to each actual image. Each complete signed message,
compute prefix, account flags, required signers, blockhash, fixture role, plan,
fee delta, error index/code, rollback, state transition and summary is rechecked.

Raw source modules are loaded into private temporary namespaces; executable
Python caches and canonical module aliases are not admitted inputs. Production
and verification pin their complete code/source/image inventories before and
after use. Saved receipt bytes are also checked after verification. Outputs must
remain outside the repository, and existing outputs are refused. Normal Python
is required; optimized execution exits before transactions.

Fourteen negative controls include the seven initial observable mutations plus
seven fully consistent false-admission cases: integer signature flags, omitted
program snapshots, a newly signed one-unit compute prefix, incorrect fee scalar,
foreign constructor state, substring-only error text and a fabricated build
claim. Additional tests cover executable cache poisoning, missing executable
rows represented by null, code/image/report mutation, strict JSON and optimized
startup.

Use a supplied candidate from separately retained actual build evidence. The
review qualification uses the independently retained earlier source build
`810df19bdae4af7540a844f8873bf09196cb5e42a867b77e3e007f3f1363dd92`
(747480 bytes), whose sixty recorded Relay source files match this checkout.
Its historical Cargo log and source snapshot are separate build context. This
suite performs no new compilation and grants no new Relay identity acceptance.
The captured original is
`367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563`.
The repaired finite report is retained at [results/current-qualified.json.gz](results/current-qualified.json.gz).
Thirty focused tests include admission and mutation controls.
The author-retained initial qualification remains historical in
`evidence/qualification.json`; it predates the repaired v2 admission.

```sh
candidate=/absolute/path/to/retained-source-built-relay.so
out=/absolute/path/outside/repository/relay-multidonor
python -B reconstruction/verification/donation-relay-multidonor/producer.py \
  --root "$PWD" --candidate "$candidate" --output "$out/report.json"
python -B reconstruction/verification/donation-relay-multidonor/verify.py \
  --root "$PWD" --candidate "$candidate" --report "$out/report.json"
python -B reconstruction/verification/donation-relay-multidonor/controls.py \
  --root "$PWD" --candidate "$candidate" --report "$out/report.json" \
  --output "$out/controls.json"
python -B -m unittest discover \
  -s reconstruction/verification/donation-relay-multidonor -p 'test_*.py'
```

Install the pinned `solders==0.27.1` runtime first. Repeat production to a fresh
output and compare complete report bytes for deterministic replay. Retained
qualification reports are runtime observations, not an equivalence proof.
