# Admin CTO behavior-guidance gap audit

Audited upstream: `1e5e58d27200aba794079374590ec897a9c1d60e`.
Target: Pump Main `admin_cto::execute`, captured address `0x22a10`, size
27,400 bytes.

## Maintained evidence

- PR #4056 supplies the deterministic, seed-addressed differential grammar,
  authenticated LiteSVM execution, strict four-way classification and
  execution-backed reducer.
- PR #4067 binds generated cases, complete signed messages, fixture state,
  source bytes and report membership. Its final counted command passed 71
  tests and independently reexecuted two 16-case campaigns.
- `scripts/pump_admin_cto_differential.py` retains the fixed 388 signed cases.
- `pump-admin-cto-stateful` retains nine persistent scenarios and 20 signed
  transactions per image.

The existing generator intentionally executes cases in seed-stream order.
Neither the fixed suites nor the fuzzer defines a canonical behavioral
fingerprint, groups generated cases by captured-original observations, selects
representatives under a corpus bound, or compares that retained corpus with a
same-pool/same-size unguided baseline.

## Qualified addition

The new layer may reuse the existing grammar, authenticated executor, strict
comparison and reducer, but must add only behavioral observation and selection:

1. a versioned canonical fingerprint computed from captured-original receipts;
2. deterministic grouping and representative selection with explicit support,
   failure, boundary and tie-breaking rules;
3. a same-observation-pool, same-retained-size unguided baseline;
4. a provenance-bound guided campaign whose selected cases retain their
   original root seed, case index and case ID; and
5. an independent verifier that regenerates the pool and recomputes every
   fingerprint, rank, aggregate and differential classification.

The fingerprint is an observed-behavior partition. It is not instrumented code
coverage and cannot establish a new bytecode branch, path count, broad semantic
equivalence or reconstruction gain. Unsupported fixtures are excluded from the
behavior census and cannot improve the guided score. Infrastructure failures
are retained as failures, never novelty.

## Safety and resource boundaries

- No program source, captured executable, dependency image, score rule or
  signer policy changes.
- No PDA is used as an outer signer. Existing transaction and receipt
  validation remains authoritative.
- Observation pools and retained corpora are explicitly bounded. Complete
  reports publish atomically through the existing campaign publisher.
- The qualification must demonstrate retained behavioral-class improvement
  over the same-pool/same-size generator-order baseline before making an
  improvement claim.
