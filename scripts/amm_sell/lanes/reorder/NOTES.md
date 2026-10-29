# amm-sell swarm / reorder lane

Approach: statement/branch re-ordering and restructuring in `fn cashback` (sell.rs), with every
error macro and the panic-location lines 439/440 kept on their original lines.

## Best (size 9024, lost 0)
- `best_sell.rs`: ATA create as `if ata.data_is_empty() { create(..) } else { Ok(()) }?;` -> align_distance 99 (baseline 112), key 19b1fd23bbbcec9b.

## Findings
- Original rodata holds core::panic::Location for sell.rs line 439 col 13 and line 440 col 13, so the init arm cannot be moved; swapping the accumulator if/else arms is impossible.
- Line 444 `if *owner != crate::ID { return err!(..) }` (in place of require!) reproduces the original borrow test `jeq r2,r3,+1; ja +201` (found at the same time by brute-force-grammar).
- `elseif_chain_sell.rs`: owner_ne + `if !ata.is_writable { return err!(..) } else if ata.data_is_empty() { create(..) } else { Ok(()) }?;` -> 467 error block, data_is_empty `jne+1; ja`, and the try_from_unchecked jeq all sit where the original has them. Size is 9000 though: create's Err merges into the shared return tail, the final `ldxdw r6; ja` block gets tail-merged, and r9/spill registers differ.
- Writing the create arm with its own `?` (`create(..)?; Ok(())` or `Ok(create(..)?)`) loses that placement (back to 173/9032).
- `if ata.is_writable == false {..}` on its own: 199 / 9032 (worse).

## Reproduce
`python3 gen.py owner_ne+create_elseok+wr_elseif` then harness/try_sell.py --sell <output>.

## Later results (lane closed once semantic-reconstruction reached the GOAL, key c9f12a27649d78bb)
- With `?` directly on the chain expression, the match forms (`match () { _ if !w => return err!(..), _ if empty => create(..), _ => Ok(()) }?`, and `match is_writable {..}`) build identically to the else-if chain (136/9000).
- Binding the chain to a let and then `created?;` loses the placement (173/9032). Folding the 464 check into the chain gives 143/9000.
- How it relates to the goal: the winning source keeps `create(..)?;` inside the arm and gets the create-before-join block order from `if ata.data_is_empty() == false {} else {`. Joining the arm values (`else { Ok(()) }?`) gets the placement right but merges create's Err path into the shared return tail.
