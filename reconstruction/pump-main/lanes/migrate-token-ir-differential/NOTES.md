# Lane migrate-token-ir-differential

Target: `0x4c158` `migrate_v2::create_token_account_v2` (programs/pump/src/migrate_v2.rs:415), original 8,368 B.
Approach: compiler-IR differential. MIR, final LLVM IR and MachineIR (finalize-isel, before greedy,
after virtregrewriter, before/after block-placement) were captured in scratch crate copies with
`capture.py` (extra rustc flags only in scratch builds, never in proposed source).

## Mechanism of the shared r8 reload (diagnosis)

- Before greedy, the four return predecessors (nn-ok bb27, nn-err bb26, native-ok bb17, native-err bb16)
  all jump to one return block bb15 that stores `{i64, ptr}` through the hidden output pointer.
- After virtregrewriter both non-native blocks still reload r8 (output pointer) from the spill slot
  separately, like the original.
- The shared reload appears in BranchFolder (control-flow optimizer, post-RA, before placement):
  nn-err bb26 is the **layout predecessor that falls through into bb15**, and `ProfitableToMerge`
  accepts any non-terminator common tail with the fall-through predecessor. The common tail of nn-ok
  and nn-err is exactly the one reload, so it is split into a new block (`bb.133.bb15`).
- The return block sits right after nn-err because rustc creates LLVM blocks on first reference while
  codegenning MIR in reverse postorder: the nn-err `?` chain is the first to `goto` the return block.
  When some outer-scope local keeps a `StorageDead` in the shared return drop tree after GVN, the
  `?` exits jump to that shared block instead, and the return block is created after the native result
  blocks. Then the fall-through predecessor is native-err (no common tail), the 2-instruction
  effective tail is below the merge threshold of 3, and no shared reload is created.
- `token_program`'s own StorageDead markers are removed by MIR GVN, so it does not provide this.

## Results (official builds, zero losses unless stated)

| Trial | Bytes | ratio | calls | Tail merge | Notes |
| --- | ---: | ---: | --- | --- | --- |
| baseline d2cb88d | 8,424 | 0.5628 | 10/1 | yes | |
| `let bump_seed=[bump];` before the branch (current branch) | 8,432 | 0.5781 | 10/1 | no | 1019/188, no gains/losses; bump slot moves, entry r1->r9 copy remains |

Diagnostic-only captures (not proposed): `if !native` (identical), `match native` (identical),
`if let true=native` (identical), Ok in each arm (identical), nn early return (identical), hoisted
ATA program id (identical), inline helper for nn invoke (drop6 coalesced, 9 callees), hoisted signer
seeds (no tail merge, but key load hoisted, ratio 0.486), `match native as u8` (native codegenned first,
tail merge remains, 0.424).

Ledger attempt ids: 46e85036 (diagnosis), befa8c29, d5d12cc4, 4d00c855, 0d9630a6, c1ca73a3, 7b4cd0d1,
89b9e78f, f3d293a4, f76ec415, 1bfb7e9d (bump_seed).

## Remaining residual

Entry register choice: the original keeps `token_program` in r9 and spills the output pointer r1 between
the two Rc increments; ours copies r1 to r9 first. Untouched by the block-order fix.
