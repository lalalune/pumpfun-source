# Lane asm-introspection (wave 2)

Approach: assembly / LLVM-IR introspection — build a precise structural model of
original vs candidate `fn cashback` and derive the minimal block-layout constraints,
then test source hypotheses that satisfy them.

## Outcome

The swarm GOAL (sell window raw-equal, 785/785, whole-ELF equal) was reached by the
**semantic-reconstruction** lane: key `c9f12a27649d78bb`, PR #1205. Winning source =
three line edits vs pristine `sell.rs`:

- L444: `if *user_volume_accumulator.owner != crate::ID { return err!(PumpAmmError::InvalidCashbackAccumulator); }`
- L467: `if ata.is_writable == false { return err!(PumpAmmError::InvalidCashbackAccumulatorAta); }`
- L468: `if ata.data_is_empty() == false {} else {` (create stays inside, `create(..)?;`)

This lane did not produce the winning build, but its introspection independently
identified all three of those levers (owner `!=` return, `is_writable == false` return,
negated `data_is_empty`) as the needed changes and explained *why* they work.

## Decisive findings (verified)

1. **The gap is 100% block layout.** `create_elseok`-alone (reorder `19b1fd23`, size 9024)
   vs the original have the *same 1075 instructions* and an *identical instruction
   multiset* except **exactly 3 conditional branches** that are inverted (`jeq`<->`jne`):
   the borrow test, the ATA `data_is_empty` test, and the create-result check. Every
   error-builder block and every `ja` is present in both, only reordered.

2. **Mechanism (corroborated).** The original emits the un-inverted `Jcc +1 ; JA` form at
   those 3 tests because at instruction-selection their layout successor was a *third*
   block (SBF `analyzeBranch` cannot re-fold, so the two-instruction form survives). The
   candidate's SimplifyCFG/placement makes the success block adjacent, so SelectionDAG
   emits the single folded `JNE`.

3. **Root cause = cold-block sinking.** The remaining diffs all reduce to the original
   *sinking* the cold Anchor error-builder blocks (err467, err502) and the shared
   error-return join `ldxdw r6,[r10-1304]; ja epilogue` to the function END; when sunk,
   the hot path falls through and the 3 tests come out un-inverted. `owner_ne`
   independently supplies the third block after the borrow test (confirmed). The ATA
   test needed the analogous restructuring of its preceding `is_writable` check **plus**
   the negated-empty idiom — which is exactly the winning combination.

## Dead ends (this lane)

- `try_from_unchecked(ata)` as explicit `match {Ok=>..,Err(e)=>return Err(e.into())}`:
  shrinks to 8992, worse (the `.into()`/match changes error-conversion codegen). Keep `?`.
- Converting *all* ATA-region `require!` to explicit `if {return err!}` (444+467) with
  `owner_ne`+`create_elseok`: 9040, does **not** trigger the cold-block sink.

## Files
- `attempts.jsonl` — this lane's logged builds + notes (via `attempts.py export`).
- `best_sell.rs` — closest DIFF1-fixed base analyzed (owner_ne + create_elseok, == reorder df86c3d6, size 9032); the winning solution is PR #1205.
