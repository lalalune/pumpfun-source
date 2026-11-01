# w19b24-cto-nat-err-slots: the cashback fee test on the byte, unmerged from the holder guard

Target `0x22a10` `admin_cto::execute`, 27,400 B. Base main fad4cb028 (0.92962, M 3,104).

## Mechanism

The fee error temps (-0x710 -0x720 -0x730) are SDAG sret-demotion frame objects, created in IR reverse post order at ISel. Original order is 330 338 334; ours was 338 334 330.
The root cause is the branch of the line 330 test. The original has `br (icmp eq byte,0), cont, err`, a one-use compare of the byte that InstCombine flips, with `cont` first in IR text. Main branched on the multi-use `cashback` phi value: `br %x, err, cont`.
With `if !holder&&st.cashback` SimplifyCFG merges the two tests into `or.cond` before JumpThreading and the holder arm stops threading past the test. An unmerged guard gives the original's shape:
- JT threads the holder arm through the test, so the phi `[false, holder], [%x, non-holder]` stays at the fee join (r5, orig 0xb20 and 0x1520). GVN cannot fold `%x` there because `%x` does not dominate the join.
- The compare `%x` stays above the shared split (orig 0xd78).
- A non-speculatable zero-footprint `llvm.assume` in the guarded block blocks the merge. It folds to `assume(true)` after inlining.

The separate `let nh=!holder` puts `cont` before the test block in IR text. Without it the test block is followed by `cont` and ISel inverts the branch (err out of line).

## Result

M 3,104 to 3,228, U 71 to 12, slots to 424, the last fill read removed. Everything in V5, J1, J2, S1, T1, S2, W2 is exact.

## Left

- `640 jne r8,0,+87` against ours `jeq r8,0,+1; ja +87` (polarity or IR text order at that holder test).
- `e28 jeq; e30 ja` against ours `jne +219` with `mov r7,0` before the `is_holder` store (shared arm fee test).
- C1 spill colours and store positions (0x3ec0, 0x40f8, 0x4238, 0x44b8, 0x4538, 0x45f0).

Oracle tools on the lane branch history: `rpo.py` (IR RPO of sret-demoted calls), `tr.py`, `trb.py` (pass-by-pass trace).
