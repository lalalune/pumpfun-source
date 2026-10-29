# Lane exactsol-sibling-analogy

Target: `0x14f4e0` `buy_exact_sol_in` (programs/pump/src/buy.rs, 13,224 B).

## Result

| Metric | Before (main d2cb88d) | After |
| --- | --- | --- |
| target slots_diff | 2 (offsets 0x1f58/0x1f60) | 0 |
| target ratio | 0.9994 | 1.0 |
| target bytes | 13,224 | 13,224 |
| official normalized / raw | 1019 / 188 | 1020 / 188 |
| gains / losses | | `0x14f4e0` / none |
| unstripped sha256 | | `43896614c48b0942490c55827d29b0b11b99c8994259ccdc9ebefe4873afe058` |

Ledger attempt: `ecf6c3c202fc4e50993966467c962681`
(dedupe key `0x14f4e0-main-d2cb88d-inline-total-into-require-gte-v1`).

## How it was found

A census of every `call with_values` in the original ELF classified the two loads that follow by
which word comes first: the Error tag (sret+0) or the Box pointer (sret+8). Most sites load the
pointer first. Inside the buy family, the tag-first sites are exactly the `TooMuchSolRequired`
guards:

- `0x14cab0` in `buy` (lib.rs:654, already normalized-matched): same `r3` tag, `r1` ptr, `ja join` shape.
- `0x151430` in `buy_exact_sol_in` (buy.rs:133): the target.
- `0x13d3e0` in `buy_v2::buy_handler` (window 0x13b9b8, unmatched).

`buy` writes the checked_add total straight into the macro:
`require_gte!(max_sol_cost, sol_cost.checked_add(..).ok_or_else(..)?.checked_add(..).ok_or_else(..)?, TooMuchSolRequired)`.
`require_gte!` expands `$value2` twice (in the comparison and in `with_values(($value1,$value2))`), so the
`?` chain is also evaluated on the error path. That extra error edge changes the PHI/load order at the
merge. `buy_exact_sol_in` had bound `let total=...?;` first (line 117), which gives pointer-first order.

## Change

In buy.rs, line 117 (`let total=...`) becomes a `// layout-pad` and the chain moves into the
`require_gte!` at line 133, so every line immediate stays where it was.

## Next idea for other lanes

`buy_v2::buy_handler` (0x13b9b8) has the same tag-first TooMuchSolRequired site at 0x13d3e0. Writing
its total inline in `require_gte!` is likely what the original author did there too.
