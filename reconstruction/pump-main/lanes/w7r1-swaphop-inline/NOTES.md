# w7r1-swaphop-inline: 0x5b3b0 multi_hop_curve::swap_hop (inlining boundary / callee census)

Base: origin/main 7e26cbf36 (1027/1035 normalized, 293 raw; unstripped 0560a482...).
Target on main: ratio 0.7332, 18,544 B (orig 18,584), calls 107/107 + 1 syscall.

## Census (callee multiset and order)
- The callee multiset is exact, closure identities included (census.py with depth-6 identities).
- MIR-level calls versus machine calls: LLVM inlines only `prepare_curve` (a forwarder), 2 of 12 `AccountInfo::clone`,
  `raw_eq`/`into_vec`/`into_iter`/`unlikely`, and one `to_string`. `uqp_transfer_native` folds into
  `migratenp_transfer_native`. The original makes the same choices, so no helper needs a different inline attribute.
- Call order: 105/107 align. In the buy arm the original runs `[590 err, closure 624, transfer_input, memcmp(whitelist), complete_fill]`.
  Ours places the memcmp straight after the mayhem test and `transfer_input` after `complete_fill`.

## Oracles (scratch only, tools/ here)
- `capir.py` hooks `fastbuild.run_compiler` to emit IR and MIR. Pass `llc -mattr=+store-imm,+jmp-ext` explicitly: without it the
  SDK llc ignores the function target-features, gives 19,112 B and never uses store-imm.
- Post-opt oracle: `llcsh.py`, then `extract.py`, then llc. This reproduces main's swap_hop token for token.
- Pre-opt oracle: `capir.py --extra=-Cno-prepopulate-passes`, then hybrid144 `opt -O3 -mattr=+store-imm,+jmp-ext`, then llc.
  This also reproduces main byte for byte (`preo.sh NAME EDIT.py`, about 12 s).
- `callseq.py`: maps llc call relocations to census callee names and aligns them with the original's 107-call order.

## Results
| id | change | result |
|---|---|---|
| prepare_curve #[inline] / #[inline(always)] / body inlined | source | byte-identical (2f31d832) |
| buy-arm single IR block moves, greedy 4 rounds, call-order objective | IR | no move gets past 105/107 aligned; exactish rises from 0.7695 to 0.7740 at best (8dd2cf51) |
| **drop `noalias` on swap_hop's `a`, or capture `a` once anywhere** | pre-opt IR | **exactish 0.7695 -> 0.8636, opregs 0.7796 -> 0.9244**, 18,600 B, 107 calls (e6117dd6) |
| drop noalias on `h` as well | pre-opt IR | 0.6654, so `h` stays noalias |
| `a: &MultiHopCurve` | source | 0.448 (rejected, 478e1e8e) |
| transfer_input / native_buyback take `&mut MultiHopCurve` | source | byte-identical (7ea4e5bc) |

## Key finding
The original reloads fields of `a` (`a.token_program`, `a.token_2022_program`, `a.fee_config`, `a.global`, `a.user`) at each use.
For example, it reloads `[a+0x40]` and `[a+0x48]` again before the second `token_program_for`, and `[a+8]` before each `get_fees`.
Ours loads each field once, keeps it, and spills it, because `a` is `noalias` and never captured. In the IR, making `a` escape
(or dropping its `noalias`) reproduces this pattern. That change alone moves the oracle further than every block-order or
spelling result so far. Where the capture sits in the body does not matter: inserting it before call #1, #2, #5, #6, #7, #10, #13 or #21
gives an identical result. So the original's swap_hop `a` either has a pointee type that blocks noalias, or `a` escapes somewhere
(passed to a callee whose parameter is not nocapture, stored, compared as a pointer, or returned).
`h` keeps noalias. The block-order residual (memcmp/complete_fill) remains after this change.

## Next ideas
- Find an ordinary-Rust form that makes swap_hop's `a` escape or lose noalias without changing the callee multiset. For example,
  pass `a` (or `&a.x`) to a helper whose parameter is not nocapture: `transfer_input`'s `previous` parameter is already not nocapture.
  Other options: a closure or struct holding `&a` that crosses a call, or an `Option<&MultiHopCurve>` argument.
- Re-run the block-order hill-climb on top of the capture variant (`PRE=` an edited pre-opt module).
