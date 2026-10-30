# Lane w7r1-buyexactquote-inline (wave 7, round 1)

Target `0x1489f8` `trade::buy_exact_quote`, original 7856 B. Base origin/main 42babccf8 (1029 normalized / 293 raw):
7856 B, ratio 0.9895, 66/66 calls, 10 differing slots (stack offsets only).

## Callee census
The callees and their order already match (66/66 calls, 952/952 instructions, same block order). The only
residual on main is StackColoring: `fees10` (the 32 B TradeFees that `v3_emit_buy` borrows) and `_301`
(the v3_execute_buy result) are coloured into different groups than in the original.

## Mechanism found (llc oracle, then source)
* Oracle (ledger `ir-oracle-post23-live-past-execute`): remove the lifetime.end of `post23` (the
  `Some(mut post)` PostComplete that fit_post_complete mutates) on the fit Ok edge, and end it after
  v3_execute_buy or at the function exit. Result: **exact (952/952, 0 differing slots)**. Ending it at the merge
  (before execute) fixes only fees10 (0.9947). The fit PostComplete therefore has body scope in the original.
* Source s1: a body-scope deferred local `let mut fit_post;` (on the existing `let curve` line, so no line moves)
  assigned in the fit arm: `Some(post)=>{fit_post=post;fit_post_complete(..,&mut fit_post,..)?}`.
  fees10 and _301 now colour exactly. **0.9895 -> 0.9958**, 7856 B, 66/66 calls, official 1029/293, no losses.
  Same values, same calls: no runtime change.

## Residual (s1)
A single 4-instruction move: the two head stores of the copy into `fit_post` (`[r10-0x38]`,`[r10-0x40]`) come after
the 48 B tail memcpy, while the original has them before it. Oracle: swap them in the s1 IR -> exact.
Cause (opt -print-after-all on raw IR): MIR has two copies, `post = (estimate as Some).0; fit_post = post`.
SROA emits the copy in ascending order, then MemCpyOpt forwards the 48 B memcpy chain
(estimate.sroa.6 -> post.sroa.3 -> fit_post+16) and puts it before the stores. The base had only one copy, so it had no chain.
Spellings tried that keep the chain (= s1): `{fit_post=post;&mut fit_post}` as the argument, `fit_post=estimate.unwrap()`.
Spellings that change more: `ref`/`&estimate` (0.9753), `if let` (0.9869), an Option-typed body local (0.49),
a declaration at the top of the body (0.75, MIR local order).

Next idea: a MIR shape that writes `fit_post` straight from `(estimate as Some).0` with no binding temporary.
