# x1-sroa-debug-requeue-trace: create_v2::execute (0x1e7c0)

## Result: official gain

`0x1e7c0` (`create_v2::execute`, 15,576 B) is now normalized-equal (raw not yet).

| Build | Bytes | Ratio | Slots diff | Normalized / raw | Losses | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| origin/main e61baa928 | 15,576 | 0.99892 | 4 | 1032 / 347 | | 3ca6911a64bd |
| R1: `sol_key()` with a `u64` word0 store | 15,576 | 0.99731 | 11 | 1032 / 347 | 0 / 0 | 112f4076e8c9 |
| **R2: `sol_key()` with a null-pointer word0 store** | 15,576 | **1.0** | **0** | **1033 / 347** | **0 / 0** | 7333e785e3ad |

The scores are against the shared baseline `x-baseline/1852a872e/score.json` (1032 / 337).
The only gain is `0x1e7c0`. Against a fresh build of main e61baa928, R2 also gains only
`0x1e7c0`, with no normalized or raw change anywhere else.

## Source change

Both Sol returns in `validate_quote_mint` now build the zero key with an `#[inline(always)]`
helper, `sol_key()`. The helper writes bytes 8..32 with `write_bytes(0, 24)` first, then writes
bytes 0..8 as a null `*const u8`. The helper sits on the `QuoteSource` line, so the line count
does not change.

## Why the original phi order failed (traced with `-debug-only=sroa`)

Tools: an assertions-enabled `opt` and `llvm-extract` built from the anza LLVM tree
(`~/.cache/pumpfun-reconstruction/llvm-dbg`, v1.44 / 08aedd64, LLVM 18.1.7). They ran on
execute, extracted from the `-print-before=sroa -print-module-scope` dump taken after the
inliner. That dump reproduces the exit phis 31,51,47,18,0. The capture and trial scripts are in
`scripts/`.

1. `%146` is the 56-byte result of the inlined `validate_quote_mint`. Its partitions are
   `[0,8)`, `[8,16)`, `[16,24)` (ptr type: the Err Box pointer, also the quote word0),
   `[24,48)`, `[48,49)`, `[49,50)` and `[50,56)`.
2. Each Sol return writes the quote as one `memset(+16, 0, 32)`. That is a split slice
   covering `[16,48)`.
3. `AllocaSliceRewriter::visitMemSetInst` for partition `[16,24)`:
   - `IntTy` is null: `isIntegerWideningViableForSlice` rejects the memset slice because
     RelEnd 32 > Size 8.
   - `VecTy` is null: there is no vector load or store.
   - `CanContinue` then needs `canConvertValue(<Len x i8>, ptr)`, with **Len = 32**, the full
     memset length rather than the 8-byte slice. That check fails.
   - So it emits `memset(.sroa.31, 0, 8)` and returns false, which makes `Promotable = false`.
4. `rewritePartition` then calls `Worklist.insert(.sroa.31)`. This is the plain worklist, not
   `PostPromotionWorklist`, and no PHI or select users are involved. `.0`, `.18`, `.47` and
   `.51` were already pushed to `PromotableAllocas`.
5. The worklist pops `.46` (`[24 x i8]`, never promotable) and then `.31`. The second rewrite
   sees `memset Len 8`, converts it to a store, and appends `.31` last.
6. All five allocas are promoted in the same `promoteAllocas` batch. mem2reg inserts each new
   phi at the front of the block, so the processing order 0,18,47,51,31 becomes the phi order
   31,51,47,18,0. That phi order is the `mov r7,0` / `mov r2,0` swap.

Rule: a memset that runs past the end of the `[16,24)` partition on either Sol path delays that
partition. The tail memset of 24 bytes is harmless. Split memcpys are rewritten to load/store
pairs and do not re-queue.

## What R1 taught

R1 wrote word0 as a `u64`. The partition type became i64 (the Err pointer stores turned into
`ptrtoint`), so the phi order was fixed but word0's `mov r2,0` was scheduled above the `stdw`
block. Writing word0 as a null pointer keeps the partition ptr-typed, which reproduces IR edit
e1 exactly.

The helper's two writes survive validate's MemCpyOpt and are not merged back into one
`memset 32`. This was verified in the execute pre-SROA dump: `store ptr null` followed by
`memset 24`.
