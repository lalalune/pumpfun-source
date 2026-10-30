# Buy transfer error-path investigation

Target `0x83c00`, `trade::v3_execute_buy`, source base `4d4911e`. Original: 3440 bytes. Retained candidate: 3456 bytes, diagnostic ratio 0.9669. All 22 ordered immediate-callee signatures equal the original.

## Findings

At original `0x846e8`, a single `jne r1, 2` branches to the transfer error block. Our candidate uses `jeq` plus an unconditional jump. At original `0x84790`, the error block loads the error payload and jumps to `0x84428`, which reloads the output pointer and stores payload at offset 16 before the tag at offset 8. Our candidate reloads the output pointer in the transfer error block and jumps to a different shared tail, storing tag at 8 before payload at 16. These two additional instructions explain the 16-byte size excess; shifted branch offsets account for further normalized differences.

The optimized LLVM IR carries the transfer result as `{ i64, ptr }`, extracts the tag, and compares it with success tag 2. It writes the error tag at output offset 8 and payload at 16. The machine trace before scheduling retains those stores; the post-register-allocation scheduling trace has already merged this path with the tag-first return tail. The final block-placement trace retains both the local output-pointer reload and the two-instruction branch. This localizes the discrepancy to lowering/scheduling/return-tail sharing, but does not identify the original Rust spelling or establish which individual compiler pass caused it.

## Source checks

| Trial | Bytes | Ratio | Calls | Decision |
| --- | ---: | ---: | ---: | --- |
| Exhaustive success/error return | 3456 | 0.9669 | 22 | Identical stripped binary |
| Explicit error variants | 3448 | 0.92781 | 22 | Worse layout; same callee multiset but different order |
| Inline Result<u64> adapter | 3456 | 0.9669 | 22 | Identical stripped binary |
| Borrowed result in tuple | 3512 | 0.83705 | 23 | Extra cleanup call and worse layout |

All four retain 1020 normalized / 188 raw memberships without gains or losses. All builds have no stack warnings. None meets the improvement criterion. No rejected source is retained and no runtime equivalence is claimed for them. The previously qualified source was restored exactly and the retained 117-case / 351-signature evidence verifier passed.

These are diagnostic builds using the pinned toolchain with `--emit=link,llvm-ir`. Control stripped SHA-256 is `726d56ed8ea76d20cf1466de6c3387325a6d99739e366ea1970a6174bb5f79f7`, exactly the qualified candidate. Extra diagnostic emission changes the unstripped hash, so `BUY-ERROR-TRIALS.json` labels those hashes accordingly. Patches are independent and relative to this source base; do not apply together.

Further work should identify why the original shares the payload-first return tail before attempting another source rewrite. Simply changing `?` syntax, spelling both error variants, adapting the success payload, or borrowing the result has now been tested and does not solve it. No production compiler flags, branch hints, byte edits, or scorer changes were used.

## Selected compiler evidence

Control optimized IR around the transfer (function-local names only):

```llvm
; call pump_recovered::user_quote_payments::transfer_from_user
  %98 = call { i64, ptr } @_ZN14pump_recovered19user_quote_payments18transfer_from_user17h3fac8df13b77df42E(i1 noundef zeroext %is_sol, ptr noalias noundef nonnull readonly align 8 dereferenceable(48) %_99, ptr noalias noundef nonnull readonly align 8 dereferenceable(8) %40, ptr noalias noundef nonnull readonly align 8 dereferenceable(168) %_133, i64 noundef %_280.sroa.0.0, ptr noalias noundef nonnull readonly align 8 dereferenceable(8) %quote_token_program, i8 noundef %_102, ptr noalias noundef nonnull readonly align 8 dereferenceable(48) %_103, ptr noalias noundef readonly align 8 dereferenceable_or_null(48) %_281.sroa.0.0, ptr noalias noundef readonly align 8 dereferenceable_or_null(48) %_282.sroa.0.0) #28
  %99 = extractvalue { i64, ptr } %98, 0
  %100 = icmp eq i64 %99, 2
  br i1 %100, label %bb66, label %bb65

```

Control final block placement, transfer error block:

```text
bb.42.bb65:
; predecessors: %bb.38
  successors: %bb.21(0x80000000); %bb.21(100.00%)
  liveins: $r1
  $r2 = LDD_V1 $r10, -360 :: (load (s64) from %stack.23 + 8)
  $r8 = LDD_V1 $r10, -488
  JMP %bb.21

```

The alternative shared tail already present in the same candidate:

```text
bb.25.bb35:
; predecessors: %bb.48, %bb.35, %bb.24
  successors: %bb.26(0x80000000); %bb.26(100.00%)
  liveins: $r2, $r1
  $r8 = LDD_V1 $r10, -488

bb.26.bb35:
; predecessors: %bb.25, %bb.47, %bb.50
  successors: %bb.27(0x80000000); %bb.27(100.00%)
  liveins: $r8, $r1, $r2
  STD_V1 killed $r2, $r8, 16 :: (store (s64) into %ir.74), (store (s64) into %ir.122), (store (s64) into %ir.100), (store (s64) into %ir.84), (store (s64) into %ir.87), (store (s64) into %ir.39), (store (s64) into %ir.127), (store (s64) into %ir.124)
  STD_V1 killed $r1, $r8, 8 :: (store (s64) into %ir.73), (store (s64) into %ir.121), (store (s64) into %ir.99), (store (s64) into %ir.83), (store (s64) into %ir.86), (store (s64) into %ir.38), (store (s64) into %ir.126), (store (s64) into %ir.123)

```
