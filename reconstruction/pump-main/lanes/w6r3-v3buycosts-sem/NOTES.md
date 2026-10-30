# w6r3-v3buycosts-sem: v3_buy_costs (0x80df8)

Base: origin/main 6484b2837 (1027/1035 normalized, 293 raw, after #2251 sibling link order).

## Result

| Metric | Base 6484b28 | This branch |
| --- | --- | --- |
| 0x80df8 bytes (orig 2120) | 2136 | 2120 |
| 0x80df8 ratio | 0.920 | 1.000 |
| 0x80df8 slots_diff | n/a (size differs) | 0 |
| callee multiset | [17, 0] | [17, 0] (orig [17, 0]) |
| official normalized | 1027 | 1028 (+0x80df8) |
| official raw | 293 | 293 |
| losses (normalized / raw) | - | none / none (0xa868 kept) |
| unstripped sha256 | - | 2ef4591161dc00f70fa7402b9a2b83607dcd2c404a6aa0e8f4fbcd3c6473ee64 |

Ledger attempt: a5eed7579d5d498a87b595d2836532fc
(dedupe key 0x80df8-main-6484b28-labeled-block-add3-pair-join-v1).

## Mechanism

Prior ledger rows already held the answer: PR #2272 (w7r1-v3buycosts-blockorder) and an
independent reproduction by w7r1-v3buycosts-inline both reached a normalized match on a418dd3
by joining the two `add3` Err arms at MIR level in `v3_buy_costs` itself with a labeled block
(`'s: { match add3(..) { Ok(v) => v, Err(e) => break 's Err(e) } ... Ok((first, second)) }`,
then one `?`). rustc appends LLVM blocks in first-reference order, so the 371 error region
stays right after the add3#1 call block; that is the order the IR oracle showed is needed for
the original's `jeq +1 / ja` Err test and the original sret register assignment. An inlined
helper or closure gives the same phi join but LLVM splices its blocks after the call block
(2112 B, ratio 0.982), so the join has to exist in MIR.

This lane's addition is checking that the same source still matches on the new main (after
#2251 changed the link order and raw went 276 -> 293): it does, with zero normalized and zero
raw losses. The edit replaces two lines with two lines, so later `line!()` sites keep their
values.

## Raw residual for 0x80df8 (not local)

`raw_equal` is false only because of 30 relative-call and `.rodata` `lddw` immediates. In the
candidate the function sits at 0x89b60 (+0x8d68 from the original) and the `.rodata` references
are shifted by +0x218. Both offsets come from whole-program layout (the 7 windows still
unmatched elsewhere), so no change to this function can fix them. Every opcode, register and
non-relocated immediate already matches.
