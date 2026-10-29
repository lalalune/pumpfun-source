# Lane brute-force-grammar (AMM sell swarm, wave 2)

Approach: combinatorial grammar of line-preserving micro-spellings over `fn cashback`
(`grammar.py`: sites -> alternatives; every error macro stays on its line, checked by
`grammar.check`), driven by `search.py` (singles / list / beam) through `harness/try_sell.py`.

## Key finding: Difference 1 (borrow test) is fixed by the owner check spelling

Line 444 `require!(*user_volume_accumulator.owner == crate::ID, E);` ->
`if *user_volume_accumulator.owner != crate::ID { return err!(PumpAmmError::InvalidCashbackAccumulator); }`
(also `owner != &crate::ID`) reproduces the original borrow test bit-for-bit at the original
offsets: `jeq r2,r3,+1 ; ja +201 -> 0x1358`. The whole window then matches structurally up to
sell+0x1ae8; only Difference 2 (ATA data_is_empty / try_from_unchecked block placement) remains,
and the window is 9032 bytes (+8), which shifts rodata so align_distance reads 186.

`require!(!(a != b))`, `if !(a == b)`, `require!(a.eq(b))`, `require!(a == b)` all keep JNE: it is
the `!=` (`PartialEq::ne`) spelling - the MIR SwitchInt target order of the owner test - that
changes the creation order of later blocks.

`best_sell.rs` = pristine + that one line.

## Outcome (12:23 UTC)

The swarm goal was reached by lane semantic-reconstruction (attempt key c9f12a27649d78bb, sell
sha f115f36e...): this lane's line-444 `!=` owner check, plus line 467
`if ata.is_writable == false { return err!(..) }` and line 468
`if ata.data_is_empty() == false {} else {`. This lane stopped its search at that point.

Results from 153 grammar builds (see `attempts.jsonl`):
- Of about 110 single-site alternatives, the 444 `!=` spelling (`owner != crate::ID` or `owner != &crate::ID`) is the only one that flips the borrow test. `!(a == b)`, `.eq`, `require!(!(a != b))`, `.ne()` and `crate::ID != *owner` were all tried.
- With owner `!=` in place: ata_w `== false` / `!= true` -> 169 (9040 bytes); else-if chain + `else { Ok(()) }?` family -> 134-136 (9000/9008); data_len()==0 -> 140, but it calls data_len rather than data_is_empty, so it is not allowed.
- `.ok_or_else(|| error!(..))` at 502 emits a second cashback closure symbol (harness_error).
- `let Ok(data) = .. else` at 445 -> size 9024, dist 136, still not JEQ.
