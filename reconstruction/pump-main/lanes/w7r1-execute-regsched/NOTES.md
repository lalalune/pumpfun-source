# w7r1-execute-regsched: 0x72810 `sweep::execute` (register allocation / scheduling lane)

Base: origin/main 2b85821 (1027/1035 normalized, 276 raw). Target 7,832 B, 39 calls.

| metric | base (main) | this branch |
|---|---|---|
| ratio (target_metric) | 0.88669 | **0.94951** |
| cand bytes (orig 7832) | 7880 | **7856** |
| calls | 39/39 | 39/39 |
| fullmask diff lines (llc oracle, regs+stack+jumps masked) | 64 | 50 |
| official normalized / raw | 1027 / 276 | 1027 / 276 (no gains, no losses) |

## Oracle

`scripts/t.sh NAME file.rs` builds a crate copy with `sweep_fees.rs` replaced, captures the
final LLVM IR (`--emit=link,llvm-ir`, lane-local only), extracts execute into a one-function
module (`mkone.py`) and runs platform-tools v1.44 `llc` on it (`oracle.py`): the llc output is
identical to the build (965 insns, ratio 0.8867 on main). `fm.py`/`sdiff.py` give masked diffs.

## Finding: the transfer_to_owned join loads decide the register assignment

Most of the register-only diff in the second half (bb27 protocol-native clone, creator clone,
join) comes from one placement difference. The original loads `base_mint.info` (`[box+0x58]`),
`quote_mint.decimals` (`[box+0x30]`) and `quote_mint.info` (`[box+0x58]`) in the call block
after the Option diamond, from phi'd Box pointers (the base box is spilled to -0x320 in the
preds). main loads them in the preds before the diamond (arg evaluation order), so the
registers of every pred differ.

IR oracle `ed/sinkjoin.py` (move those loads into the join, phi the box pointers):
0.8867 -> 0.9495 (quote mint only 0.8716, base only 0.9371).

## Rust spelling

A plain (non-inline) `pay_owned` helper, like `sell_v2::pay_owned`, taking `&InterfaceAccount`
base/quote mints: the helper is LLVM-inlined and the field loads happen in its body, after
the Options. With `token_program:&Interface` passed as `&a.quote_token_program` (w1, the same as
w7r1-execute-anchor's t01) the token-program gep becomes a phi (hoisted into bb26 and
jump-threaded as bb26.thread), and the layout breaks (0.7488). Oracle `ed/w1gep.py` shows that
gep is the only blocker. Passing the accounts struct `a` instead and borrowing
`&a.quote_token_program` inside the helper (w2) puts the gep in the call block: 0.9495, 7856 B,
zero losses.

## Remaining residuals (oracle on w2)
1. Admit branch polarity (`jeq r1,2,+1; ja` vs `jne`), block order only (w4-sweep residual 1).
2. Rent region: payload copy before the tag branch, and the original places the legacy transfer
   call block after the protocol-native clone (w6r1-sweep-ir: CGSCC inlining of a plain rent helper).
3. Event: two byte-store / reload order lines near +0x1988.
