# Lane y1-cv2-callee

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (15,576 B, 125 internal calls).
Family: callee and inline boundary (argument marshalling).
Base: origin/main e61baa928 (program sources identical to 0bcf7223c), baseline
`y-baseline/0bcf7223c/score.json` = 1032 normalized / 347 raw.

## Result

| Build | Bytes | Ratio | slots_diff | Official |
| --- | ---: | ---: | ---: | --- |
| main (base) | 15,576 | 0.99892 | 4 | 1032 / 347 |
| optret-unwrapor | 15,672 | 0.44397 | - | 1032 / 347, rejected |
| **sol-arg-byval** | 15,576 | **1.00000** | 0 | **1033 / 347**, gain `0x1e7c0`, 0 losses, 0 raw losses |

Candidate sha256 `7333e785e3ad82a5f6f2be8d715e1c11d524ba15dfed377092e33679418d93fc`.

## Change

`validate_quote_mint` takes the Sol quote key as a by-value argument (`sol: Pubkey`); `execute`
passes `Pubkey::default()`, and both Sol returns write `Ok((sol, None, QuoteSource::Sol))`.
Edits stay on their own lines, so no line numbers move.

## Why it works

The residual was the order of the `mov r2,0` / `mov r7,0` phi copies at the join of the two
Sol returns and the main Ok path of the inlined `validate_quote_mint` (w7r1-execute-inline
"residual A"). Root cause found there: both Sol returns wrote the zero quote as one 32-byte memset over
[16,48) of the result, and [16,24) is a separate ptr-typed partition (it overlaps the Err `Box`
pointer). SROA rewrites a memset that spans several partitions in a later round, so the quote word0
phi was created last. A 32-byte `Pubkey` argument is passed indirectly, so `validate_quote_mint` keeps a
memcpy from the argument pointer instead of a constant memset. After LLVM inlines it into `execute`,
SROA sees a memcpy from the caller's temp, which it splits per partition, and the phis come out in
the original's offset order. The call multiset does not change: the function is still inlined, and
`Pubkey::default()` folds away.
