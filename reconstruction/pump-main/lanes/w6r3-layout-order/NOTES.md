# Lane w6r3-layout-order (wave 6, round 3): function order and placement for raw

Base: origin/main 6484b2837 (1027/1035 normalized, 293 raw, unstripped `5d8296db`), the first base with
the pinned U+D link order (`programs/pump/link/ordered.ld`, #2251). Scratch:
`~/.cache/pumpfun-reconstruction/lanes/w6r3-layout-order/`. Model tools are w8-sibling-recipes
`fastmodel.py`/`m13.py`/`refine.py` (copied there with census.py repointed at this worktree's harness);
`tools/scen.py`, `tools/bh.py` and `tools/nb.py` here are new.

Result: analysis only. On this base no source-order change can raise official raw. Every one of the
742 normalized-but-not-raw windows fails because of a size delta (8 unmatched windows plus the 512-B
ours-only unit), and none fails because of order.

## 1. Full original order, real build: +0

`regen.sh` reproduces `ordered.ld` byte for byte on 6484b28 (default rustc order alone: 1027/276).
`genld.py --mode all` (1037 selectors: U, then L in the original's order, then D) built through fastbuild
scores **1027/293 with exactly the base raw set** (unstripped `54d3a48c`). The full original order of
all three blocks is the upper bound for any source-order change that moves functions to their original
positions. At today's sizes that bound is the base.

## 2. Size deltas gate everything (`tools/scen.py`, base build order)

`.text` is 552 B longer than the original. 40 B of that comes from the 8 unmatched windows (create_v2 +8,
buy_handler +32, buy_exact_quote_in +32, admin_cto -56, swap_hop -40, sweep +48, v3_buy_costs +16,
buy_exact_quote v3 0; ours - original). The other 512 B is the ours-only unit
`v2_native_payments::ensure_rent_exempt`.

| scenario (our order, model) | raw |
| --- | ---: |
| as built | 293 |
| all 8 unmatched at original size, 512-B unit kept | **293** |
| 512-B unit dropped, no size fixed | 293 |
| 512-B unit dropped, all 8 at original size | 477 |
| 512-B unit dropped, any subset summing to +40 (e.g. create_v2 + buy_exact_quote_in) | 477 (`.text`-size coincidence) |

So the 512-B unit blocks every size-fix gain. Removing it is PR #2168 (w6r1-layout-order).

## 3. PR #2168 on the link-script main

#2168 head b588742e5 merges cleanly into 6484b28:
- with the committed `ordered.ld`: 1027/293, 0 losses (unstripped `9a5da01f`);
- with a regenerated script: 1027/293, 0 losses (`ded0585d`). The regenerated script has two selector changes:
  `Error::with_account_name::<String>` is added to U, and `Vec::clone` is replaced by `ConvertVec::to_vec`.
  #2168 adds or renames those U instances, so the script should be regenerated when #2168 lands.
  Without the regen they fall into the root glob. That costs nothing today, but the fixed-size model loses them.

Model on #2168 + regenerated script (`tools/bh.py`): `.text` delta 40 (the 512 B are gone).
| scenario | raw |
| --- | ---: |
| as built | 293 |
| all 8 at original size, our order | 607 |
| + buy_handler moved between program fns `create` and `buy_exact_quote_in_v2` | **1027** (every matched window) |
| buy_handler moved, today's sizes | 293 |

`resid.py`: under full order and fixed sizes, nothing fails on #2168. On base only sell_v2 fails (its call to the 512-B unit).

## 4. buy_handler is the only order item left, and it is not a layout-only move

rustc 1.79 orders a CGU by `(LocalDefIndex, symbol)`. The original's slot between program fns `create`
and `buy_exact_quote_in_v2` can only be taken by items that DefCollector collects in the `#[program]`
fragment itself. A nested fn in program fn `buy_v2` would qualify, but it carries lib.rs spans. Items from
`include!`, macro_rules (including a late `mod buy_v2;`) and derive outputs are collected after the whole
fragment, so they land after `sell`. buy_handler's error sites need buy_v2.rs `file!()`/`line!()`
immediates, and `file!()` inside a macro reports the first invocation site. So the standalone 15512-B body
cannot sit at the program position. The only source-level way is the original program-fn form (handler
LLVM-inlined into program fn `buy_v2`), which costs +8 B of codegen (w6r1-layout-order `d6daced5`,
w7r1-buyhandler-inline). That work belongs to the handler lanes.

## What raw now needs (in order)
1. Merge #2168 (512-B unit gone) and regenerate `ordered.ld` (`w8-sibling-recipes/tools/regen.sh`).
2. The 8 unmatched windows at their original sizes: model 607.
3. buy_handler in program-fn form at its original size: model 1027.

## Attempts (ledger)
| id | trial | result |
| --- | --- | --- |
| `244adfcc` | regen.sh on 6484b28 | script reproduced |
| `fdb3523b` | full original L+U+D order (`--mode all`), real build | 1027/293, same raw set |
| `0c2a1ff1` | size-fix subset model with/without the 512-B unit | 293 gate / 477 |
| `6d4be17f` | #2168 merged on 6484b28, existing + regenerated script | 1027/293, 0 losses |
| `5e738ee1` | #2168 ceiling model | 607 / 1027 with buy_handler |
| `fb891d7b` | standalone buy_handler at program position by DefIndex | not reachable (analysis) |
