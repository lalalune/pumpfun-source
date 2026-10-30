# y1-cv2-llvm: create_v2::execute (0x1e7c0)

Family: LLVM decision trace. Branch `swarm/y1-cv2-llvm` from origin/main e61baa928 (its
`programs/` tree is the same as the baseline 0bcf7223c).

## Result: official gain

| Build | 0x1e7c0 ratio | Bytes | slots_diff | Normalized / raw | Losses (norm / raw) | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- | --- |
| baseline 0bcf7223c | 0.99892 | 15,576 | 4 | 1032 / 347 | | |
| v1 `system_program::ID` + `mem::zeroed()` source (rejected) | 0.94847 | 15,640 | | 1032 / 347 | 0 / 0 | 90de58b3 |
| **v2 zero key passed by reference (this branch)** | **1.00000** | 15,576 | 0 | **1033 / 347** | **0 / 0** | 7333e785 |

Gain: `0x1e7c0` normalized. The window is not raw-equal yet.

## Change

`validate_quote_mint` takes a `sol:&Pubkey` parameter, and both Sol returns copy `*sol`.
`execute` passes `&Pubkey::default()`. No line count changes, and no new generic instances
(`ordered.ld` is unchanged).

## Why it works (LLVM decision)

Earlier lanes traced the residual (`mov r7,0; mov r2,0` versus the original
`mov r2,0; mov r7,0`, at two predecessors of the validate join) to SROA promotion order in
execute's post-inline SROA. With `Pubkey::default()`, validate's own pipeline (run before
validate is inlined) lowers each Sol quote to `memset(_84+16, 0, 32)`. That memset spans the
[16,24) partition (quote word0 shares it with the Err Box pointer), so SROA re-queues that
slice and promotes it in a second batch. mem2reg then creates the quote-word0 phi last, and the
phi copies come out in the wrong order.

Every zero-key spelling inside validate folds to that memset before inlining. That includes
`static`, `const`, `system_program::ID`, `new_from_array` and helper functions, because
MemCpyOpt turns a memcpy from a zero constant into a memset. Passing the key in by reference
makes the Sol copy a memcpy from an opaque argument while validate is being optimized.
MemCpyOpt cannot fold that. After inlining, execute's first SROA sees a memcpy from a
zeroinitializer constant rather than a memset. This matches the "memcpy from a zeroinitializer
global" IR-oracle fix that earlier lanes found. The quote-word0 slice is now promoted together
with the others in offset order, which gives the original bb112 phi order.

Rejected v1: the 34-byte merged memset (with the tag and payload zeroed through `mem::zeroed()`)
makes the payload byte a defined 0, so the payload gets its own phi register and an extra
`mov`. This is the same outcome as w9r1 t1t2.
