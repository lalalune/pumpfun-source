# x1-cto-cashback-after-validate-holder-and1 (admin_cto 0x22a10)

Base: origin/main 31855c9e0. Scored against the shared baseline 1852a872e score.json.

Kept change (programs/pump/src/creator/admin_cto.rs): the state block no longer computes
`let cashback=!holder&&st.cashback;` before `validate`. It returns the raw `st.cashback`,
and the curve update computes `curve.is_cashback_coin=!holder&&cashback;`.

| Build | admin_cto bytes | ratio | normalized | raw | losses |
| --- | ---: | ---: | ---: | ---: | --- |
| main 31855c9e0 (unchanged) | 27,344 | 0.37637 | 1032 | 347 | 0 / 0 |
| (a) `!holder&&st.cashback` as tuple element after validate | 27,392 | 0.34007 | 1032 | 347 | 0 / 0 |
| **(b) `!holder&&cashback` at the curve update (kept)** | 27,344 | **0.38866** | 1032 | 347 | 0 / 0 |
| (b) + `holder.unwrap_or(false)` | 27,176 | 0.37004 | 1032 | 347 | 0 / 0 |
| (b) + execute takes `holder:bool` (lib.rs passes `==Some(true)`) | 27,096 | 0.30340 | 1031 | 293 | 1 / 44 |
| (b) with `cashback&!holder` | 27,360 | 0.38345 | 1032 | 347 | 0 / 0 |

Call multiset is unchanged in every build (154 internal + 3 relocated). Original is 27,400 B.

Notes:
- Moving the cashback evaluation late helps; evaluating it right after validate (a) hurts.
- unwrap_or still loses even with no early `&&` for MIR jump threading to use, so the
  earlier unwrap_or failure was not only caused by threading through the early cashback branch.
- The bool signature inlines the Option comparison into the dispatcher and costs raw windows.
