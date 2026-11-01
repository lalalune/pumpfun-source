# Behavior-guided corpus qualification — 2026-11-01

The behavior-guidance implementation was executed from commit
`16ed5f2b40` on fresh upstream
`1e5e58d27200aba794079374590ec897a9c1d60e`. It changes no program source,
captured image, signer rule, strict comparison field, reducer property or score
normalization.

Both final campaigns used seed `20261101`, pool indices 0–63 and a retained
corpus limit of 16. Captured-original observation admitted 56 cases and
classified eight as `unsupported_fixture`; zero observations were
infrastructure failures. Unsupported cases were excluded before selection.

The guided corpus retained **16 distinct observed fingerprint classes**, while
generator order retained **13** under the same 64-case observation pool and
same 16-case corpus limit. This is a three-class retention improvement, not an
instrumented coverage or bytecode-branch claim. The exact selection was shared
by both campaigns and has SHA-256
`23f6ef54465fe6118202293e55fcfc7f2ccfcff8c513d3b1fb9b022ec31d0550`.
It includes four all-success original sequences and twelve mixed/failing
sequences, including success, failure and numeric-boundary anchors.

| Measure | Original vs original | Original vs qualified candidate |
|---|---:|---:|
| Original pool cases | 64 | 64 |
| Supported original observations | 56 | 56 |
| Unsupported original fixtures | 8 | 8 |
| Selected cases | 16 | 16 |
| Selected observed classes | 16 | 16 |
| Unguided observed classes | 13 | 13 |
| `equal_observed_behavior` | 16 | 16 |
| `different_behavior` | 0 | 0 |
| `infrastructure_failure` | 0 | 0 |
| Selected transactions per image | 32 | 32 |
| Total signed transactions, including selection observations | 167 | 167 |
| All-success original selected sequences | 4 | 4 |
| Negative controls detected | 3/3 | 3/3 |

The candidate is the existing PR #4056/#4067 qualified image, reused without a
new build:

- captured original SHA-256:
  `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`;
- candidate SHA-256:
  `6f439f1e539ec8156aba443e9a464eedee0996c88720b3eae789e148e4fef7be`.

The candidate predates later Admin CTO source hillclimbs on fresh main. It is
used here only as the immutable provenance-qualified runtime control already
accepted by the merged fuzzer; this qualification makes no current-source build
or score claim.

Control report identities:

- artifact manifest:
  `c79e53fd6d40659277732f19ae40fc1324a77859d78c077fb4becd9979b7692a`;
- summary:
  `2940df6129c5f08ddf33cfe3cab657cd132938163329969daab6c7022f427df7`.

Candidate report identities:

- artifact manifest:
  `df28896d2e7888d91f75eff6ae03e16a14c17d76197042a17144dfe69a632b05`;
- summary:
  `e1042e226dad4ecde0cd6d3328cf314f2c417e8cea1a394a16cacef4899885f1`.

`verify_guided.py --reexecute` independently admitted all 64 original
observations and all 16 differential receipts for each report, then reexecuted
all 80 cases with zero failures or warnings. Each report contains 103 signed
selection-observation transactions plus 32 selected transactions per image.
The reports are retained locally under
`~/.cache/pumpfun-reconstruction/daybreak-admin-cto-behavior-guided/`; they are
not canonical repository inputs.

The fixed Admin CTO differential was rerun against the same candidate: 388
cases, zero mismatches. The existing stateful package passed ten tests,
including a genuine 20-transaction receipt-admission control. The complete
fuzzer package now passes 96 tests. Adversarial tests independently detect
forged fingerprints, corrupt outcomes/events, omitted cases, duplicate IDs,
altered ranks, false passing totals, invalid signatures and missing evidence
after outer receipt hashes are recomputed.

The fingerprint engine hashes observed error/outcome sequences, success/failure
stage, events, inner CPI sequences, Token/Token-2022/ATA paths, signer roles,
return data and account-class state transitions. It intentionally does not
infer source branches, historical control flow, runtime safety, whole-program
equivalence or bytecode improvement. Selection quality is finite and seed- and
grammar-dependent; the demonstrated gain applies only to the recorded pool and
budget.

# Independent v2 admission qualification — 2026-11-01

The repaired implementation at `3b424eb0efca63d417852dc97284857afd6f60ed`
was qualified separately from the author's historical v1 record below. The
original and candidate images retain the SHA-256 identities listed there;
this tooling review reused the already qualified candidate bytes and did not
perform or claim a new compiler build.

Two fresh detailed campaigns used seed `20261101`, indices 0–15, and corpus
SHA-256 `82ab889b9dfa79f4243e53f5539ead984264079c44daca1245f364e4cb8f5e1f`.
Both original-vs-original and original-vs-candidate reports observed 15 equal
cases, one independently admitted unsupported fixture, zero behavioral
differences, and zero infrastructure failures. Each executed 30 signed
transactions per image, including one all-success sequence. All three negative
controls were detected. Each report was independently read and all 16 cases
were reexecuted with no failures or warnings. The unsupported fixture is
excluded from matching execution counts. No real counterexample was found;
reducer witnesses and local-neighborhood checks were qualified with finite
positive and adversarial regression cases.

The v2 summary SHA-256 values are:

- control: `3f9b63a05765f8002599669ede4a8fce861d80d6d78549e47a6011c0e4b246ab`;
- candidate: `5dd3cde499281958442e42cc539ac35822a8e180926541ee2c49f3e866ec185e`.

The counted CI command passed 71 tests with zero skips. Regressions cover
strict fixture types, fully resealed signed unrelated messages, integer
signature flags, omitted/foreign state, empty runs, fabricated unsupported
exclusions, zero-case corpora, false aggregates, extra manifest members,
duplicate JSON keys, links, and input/report mutation. An independent model
check retained byte-identical generated corpora for 640 cases across five
seeds and rejected 20 previously admitted malformed cases.
An actual dependency-bootstrap edit control also reproduced an early v2
self-source timing gap, then proved the final producer rejects the edited
disk bytes while retaining the SHA-256 of its actual compiled source. That
control and nonfinite JSON rejection also passed with `-O` and `-OO`.

Actual producer-generation and reader CLIs also passed under normal Python,
`-O`, and `-OO` with executable timestamp caches planted for the lifecycle and
comparison helper. Standard-loader controls first proved those six caches
executable; the source-only CLIs left every execution marker absent and
admitted all 16 retained candidate case results. These cache checks performed
no additional program executions.

Detailed reports and proof logs are retained under the local pass111 artifact
directory `tools/4056/{control16-final,candidate16-final}`. The earlier
`5da27f7` campaign reports remain separately retained and are not resealed.
The final reports bind ten declared tool/data
inputs, all captured dependency images, the exact semantic artifact census,
canonical case/message/constructor state, and pre/post input bytes. These are
finite synthetic observations, not whole-program equivalence or increased
bytecode-completion evidence.

# Author's historical v1 qualification record — seed 20261101

The record below is retained as authored. Its v1 reader and reported 64-case
campaigns are not substituted for the independent v2 qualification above.

The final bounded campaign was produced from implementation commit
`d84ebbe0cca77febd97187215cd6924b39053756` on upstream base
`53ec7fb538c1bce0571eab731ab925d8530c40fa`.

Program identities:

- captured original: `7a19affaa2c6187e04a5fe0ea298cee81fa5eb8c24cfcc30d85f615e89f7b02d`;
- fresh identity candidate: `6f439f1e539ec8156aba443e9a464eedee0996c88720b3eae789e148e4fef7be`;
- matching unstripped image: `54344822ddef0bd4b1f7b4e8a6c80e5aae7e7fb804c5c82c67e7ebff369e9229`.

The candidate was built after the final rebase with the identity recipe and two
compiler jobs. Its source manifest is
`124807d11a9266f52253c2e4a369a50d6ded4f1a7e097be0befed9889d7e5374`;
the ordered linker script is
`6954d9901b005312be6e7f980cb5e74a1440c174547c2040a881acf2e5c25b45`;
the pinned `rust-lld` is
`a4d765c822f68b267e87765771da87a0fd4d640d9df27884bd10c0750d1b58f4`.
The build completed with runtime validation and no stack warnings. The campaign
independently bound the exact candidate bytes rather than trusting its path.

## Results

Both final reports used root seed `20261101`, indices 0–63, and the same case
manifest.

| Measure | Original vs original | Original vs candidate |
|---|---:|---:|
| Generated cases | 64 | 64 |
| `equal_observed_behavior` | 56 | 56 |
| `different_behavior` | 0 | 0 |
| `unsupported_fixture` | 8 | 8 |
| `infrastructure_failure` | 0 | 0 |
| Transactions per image | 103 | 103 |
| All-success original sequences | 4 | 4 |
| Raw-log/compute diagnostic cases | 0 | 22 |
| Negative controls detected | 3/3 | 3/3 |
| Reduced counterexamples | 0 | 0 |

Control summary SHA-256:
`bc8772891e6548ea4cc5aa4667d95aa883ef0404eaa7203672606ea5e1a2561a`.

Candidate summary SHA-256:
`2c4c5c67f54c8028a9d92886dd51ee8881900edc541d1e13b3eee24106340fa9`.

The independent verifier loaded every receipt and re-executed all 64 cases in
each report. Both verifications returned zero failures and zero warnings. The 8
unsupported cases were excluded from equivalence counts. No candidate
counterexample was found, so no on-chain vulnerability or broad semantic
equivalence is claimed, and the automatic reducer was qualified through its
deterministic positive/negative regression controls rather than a fabricated
program mismatch.

The maintained 388-case single-transaction differential also reported no
mismatches for this exact candidate. The nine-scenario stateful suite executed
20 transactions per image with no behavioral, oracle, invariant, or
infrastructure failures; its independent deterministic replay verified. The new
package passed 32 tests, the stateful package passed 10 tests, and the optimized
Python admission package passed 3 tests.

The retained local reports are:

- `~/.cache/pumpfun-reconstruction/daybreak-admin-cto-fuzzer/main-53ec7f-original-control-seed-20261101-n64`;
- `~/.cache/pumpfun-reconstruction/daybreak-admin-cto-fuzzer/main-53ec7f-candidate-seed-20261101-n64`.

They are intentionally not committed: each contains compressed full account and
transaction receipts, while this record remains compact and reproducible.
