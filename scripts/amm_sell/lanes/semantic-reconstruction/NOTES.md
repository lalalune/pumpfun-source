# amm-sell swarm lane: semantic-reconstruction

**Result: the sell window is raw-equal and the whole ELF is equal (785/785 windows).**
Attempt key `c9f12a27649d78bb`, sell.rs sha256 `f115f36e05ad97b7d1ea40a72c16e891cb2d7fec0844d8024f8d26cd53a48a6b`.

## The fix (three lines changed in `fn cashback`; every error macro stays on its line)

| line | pristine | original-equivalent |
|---|---|---|
| 444 | `require!(*user_volume_accumulator.owner == crate::ID, ..)` | `if *user_volume_accumulator.owner != crate::ID { return err!(PumpAmmError::InvalidCashbackAccumulator); }` |
| 467 | `require!(ata.is_writable, ..)` | `if ata.is_writable == false { return err!(PumpAmmError::InvalidCashbackAccumulatorAta); }` (the spelling buy.rs uses) |
| 468 | `if ata.data_is_empty() {` | `if ata.data_is_empty() == false {} else {` (the `create(..)?;` body is unchanged) |

## Why it works
rustc adds LLVM blocks in the order they are first referenced. `require!(c)` lowers to a switch that
creates the error block first. `!=` / `== false` give success-first switches, so the error chain is
codegenned into the slot right after the test block. That puts a third block after the borrow test and
after the ATA data_is_empty test, which produces the original's `jeq/jne +1; ja` pairs.
`data_is_empty() == false {} else {create}` creates the create arm (and its `?` error tail) before the
try_from_unchecked join, so try_from_unchecked falls straight through to its success block, as in the original.
The line-444 fix was found at the same time by the brute-force-grammar and reorder lanes; the 467 spelling
came from buy.rs (inline-helpers/reorder notes); the 468 spelling is this lane's.

## Dead ends (this lane)
- `else { Ok(()) }?` around create on top of owner `!=` and `is_writable == false`: dist 171. It breaks the create-result branch.
- `match data_is_empty() { true => {create?;} false => {} }`: same as b2 (dist 169).
- Line 395 `is_writable == false`: dist 368.

## Reproduce
`python3 -B harness/try_sell.py --lane X --approach Y --hypothesis Z --sell scripts/amm_sell/lanes/semantic-reconstruction/best_sell.rs` -> exit code 3.
