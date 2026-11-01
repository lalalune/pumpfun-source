# Admin CTO differential-fuzzing gap analysis

Authored lane base: `53ec7fb538c1bce0571eab731ab925d8530c40fa`.
The initial audit was performed at `638fce2a3470d2505522f7e73e416d56daef86c5`;
the lane was rebased and fully requalified after upstream Admin CTO and harness
changes landed.
The independent v2 admission repair is recorded in `QUALIFICATION.md` and
retains this initial coverage rationale. It adds strict fixture grammar,
case-bound signed receipts, exact corpus/artifact membership, source-only
loading, and explicit provenance-only admission for compact reports.
Target: Pump Main `admin_cto::execute`, original offset `0x22a10`, original
size 27,400 bytes.

## Existing qualified coverage

- `scripts/pump_admin_cto_differential.py` contains 388 deterministic,
  signed, single-transaction cases. It already covers fixed optional-argument,
  account-count, ownership, truncation, token-state, fee, PDA, and malformed
  account boundaries through genuine captured dependency programs.
- `pump-admin-cto-stateful` contains nine fixed persistent scenarios and 20
  signed transactions per image. It verifies state continuity, rollback,
  SPL/Token-2022 behavior, frozen accounts, cross-mint isolation, strict
  receipt fields, input provenance, and negative controls.
- `pump-cross-program-fee-lifecycle` supplies another fixed signed lifecycle
  with independent receipt verification and captured dependencies.
- `minimize_experiment.py` reduces source patch sets by repeatedly running an
  external oracle. It does not understand transaction fixtures, account fields,
  or behavioral mismatch properties.
- `residual_analysis.py` compares machine-code structure. It is not a runtime
  input generator or behavioral reducer.

## Missing capability

No maintained tool currently provides all of the following for Admin CTO:

1. versioned, seed-driven generation that composes multiple fixture mutations;
2. case identities and duplicate elimination independent of case names;
3. replay of one generated case by root seed and case index;
4. strict four-way classification of equal, different, unsupported, and
   infrastructure outcomes;
5. automatic reduction of accounts, fields, optional arguments, numeric
   values, sequence length, and transaction steps with differential replay for
   every proposal;
6. an explicit one-minimality statement scoped to the reducer grammar;
7. standalone mismatch manifests binding the original seed, reduced case,
   executable hashes, and replay command;
8. compact summaries plus optional bounded compressed receipts and an
   independent verifier.

The new lane therefore reuses the authenticated stateful fixture and captured
program images, but does not copy its fixed scenario list or replace the
maintained 388-case matrix.

## Safety boundaries

- Every transaction remains signed by the fixture payer and real configured
  admin key. PDA accounts are never injected as transaction signers.
- Original and candidate execute in independent LiteSVM instances with the
  same immutable image snapshots and synthetic starting state.
- Unsupported fixture construction is distinct from successful equivalence.
- Raw logs and compute units remain diagnostics; semantic logs, events, return
  data, inner instructions, errors, transactions, and complete tracked state
  are strict.
- Finite generated campaigns establish only observed behavior for their exact
  corpus. They do not establish whole-program semantic equivalence.
