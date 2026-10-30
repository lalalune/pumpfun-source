# Lane w3-v3costs: `trade::v3_buy_costs` (original 0x80df8, 2,120 B)

Base: origin/main 665499915 (1022 normalized / 276 raw). The source is unchanged: no source trial improved the target.

| Build | Bytes | ratio | '-' slots | calls | normalized / raw |
| --- | ---: | ---: | ---: | ---: | --- |
| base 665499915 | 2,136 | 0.920 | 19 | 17/17 | 1022 / 276 |
| coldfn375, inlfn375 | byte-identical ELF to base | | | | 1022 / 276 |
| coldnoinl375 | 1,728 | 0.543 | 126 | 15/17 | 1022 / 276 |

## IR-oracle results (prior lane's llc oracle, re-captured on 665499915)

The oracle reproduces the base exactly (2,136 B). `branch_weights 1:2000 .. 1:2e5` on `%43`, the Display::fmt
failure branch in the line-375 error closure, gives 2,120 B and 0 differing lines. New this round:

* The same hint on the line-371 `to_string` branch (`%16`) alone does not flip it (2,136 B at 1:2000, 1:2e4, 1:2e5).
  The lever is specific to the 375 path.
* 1:2000 on every branch into a cold or panic block (`all2000`, the front `protocol_fee_split` ones included) gives
  2,144 B. So "this toolchain marks all cold branches" does not explain the original. The original's IR had a leak
  only on the 375 path, or an equivalent difference.
* Hints in either direction on the mid-function branches (`%or.cond` net check, `%_54.1` total_buyback overflow,
  `%35` pre_fee Result, `%_91.not` gross-up) never flip it. They only change layout (2,088-2,136 B).
* In this rustc (1.79.0-dev, LLVM 18.1.7), only MIR `Assert` terminators emit `!prof`: there are 19 nodes in the
  module, all bounds or overflow asserts. `checked_add`'s `unlikely!` emits nothing. An Assert that folds away
  takes its weight with it (see the prior lane's napm-ifsub, byte-identical). So no source construct on this
  toolchain is known to leave a 1:N weight on the 375 `to_string` branch without adding code.

## Source trials (ledger keys `0x80df8-main-665499915-<trial>-v1`)

* coldfn375: the line-375 error as a nested `#[cold]#[inline(always)] fn` item. Byte-identical ELF: `cold` is lost when the function is inlined.
* inlfn375: the same as a nested `#[inline(always)] fn`. Byte-identical ELF.
* coldnoinl375: a nested `#[cold]` fn item that is not inlined. The error builder is outlined (15 calls, 0.543).

Analysis row: 12fa6de7e00245f5a72476580b8fb42f.
