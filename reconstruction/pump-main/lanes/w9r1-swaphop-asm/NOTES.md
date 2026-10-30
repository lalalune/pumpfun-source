# w9r1-swaphop-asm: 0x5b3b0 multi_hop_curve::swap_hop (assembly-first)

Base: origin/main 255a0fd2e (fresh build: 1031/1035 normalized, 337 raw). swap_hop 18,544 B (orig 18,584), ratio 0.7332, calls 107/1.

## Result 1: swap_hop takes `ctx: &Context<MultiHopCurve>` (ledger 33eed5a8)

Assembly evidence: the original's r2 is the accounts struct and r3 the event-authority bump, but
every field of `a` is reloaded after calls (w7 lanes: `a` is not `noalias` in the original).
An a-derived capture is nowhere visible in the call arguments (every a-derived pointer argument is
the same in both builds), so the missing noalias has to come from the parameter itself.

Mechanism: `swap_hop(ctx: &Context<'_,'_,'info,'info,MultiHopCurve<'info>>, h, ..)` with
`let a = &*ctx.accounts; let event_bump = ctx.bumps.event_authority;` in the body. `ctx` is
only loaded from, so LLVM's ArgumentPromotion (internal function, single caller) replaces it with
the two loaded values `(accounts ptr, bump)`: exactly the original's r2/r3. The promoted accounts
pointer was loaded from memory, so it carries no `noalias`, and a's fields are reloaded after every
call. This reproduces the w7 pre-opt "drop noalias on a" oracle byte for byte.

| | main 255a0fd2e | ctx1 |
|---|---:|---:|
| swap_hop ratio | 0.7332 | **0.83042** |
| bytes (orig 18,584) | 18,544 | 18,600 |
| calls | 107/1 | 107/1 |
| normalized / raw | 1031 / 337 | 1031 / 337, no losses |

## Result 2: w7 sibling mechanisms composed on the &Context base

| trial | change (on ctx1) | bytes | ratio | ledger |
|---|---|---:|---:|---|
| m1 | `require_gt!(base,0,BuyZeroAmount)` (590) | 18,608 | 0.83242 | 33b8eb21 |
| m2 | `raw_output = base_amount.checked_add(match &post_fill{..})` | 18,576 | 0.83184 | 2156ce51 |
| m3 | buyback `else` without `paid_buyback != 0` guard | 18,600 | 0.83217 | 46869e80 |
| m4 | `const NO_FEE` for native quote_fee | 18,624 | 0.83293 | 1ce5d202 |
| all4 | m1+m2+m3+m4 | 18,608 | 0.83636 | e044b7e7 |
| **a5** | all4 + scoped user key `let allowed = { let user = a.user.key(); .. }; require!(allowed, ..)` | **18,640** | **0.84043** | 2c888585 |
| a7 | all4 + complete_fill Some arm returns its `TradeFees` whole | 18,640 | 0.8365 | f4a2f821 |
| a57 | a5 + a7 | 18,672 | 0.83795 | 462472b7 |
| a5n1 | a5 without m1 | 18,632 | 0.82271 | fcade5ba |
| a6 | all4 + `v3_can_cross` | compile error (private) | | a11be097 |

The w7 u2 scoped key lost ratio on the old base (-3.2 pts) but gains on the &Context base.
Raw 948 (611 raw gains) on a5 is an artifact: swap_hop +56 B cancels admin_cto's -56 B shift, so
every function after swap_hop is at its original address. That will reverse once admin_cto grows,
unless swap_hop reaches 18,584 B.

## Result 3: mutation hill-climb on the &Context base (w7 hillclimb tool, mutations re-pooled)

The w7r1-swaphop-hillclimb mutation set (84 mutations that were not inert on the old base and still apply), climbed on a5:

| state | bytes | ratio | slots_diff |
|---|---:|---:|---:|
| a5 | 18,640 | 0.84043 | (size differs) |
| + `qm-09`: `let cap = match crate::buy_fee_market_cap(c,&h.base_mint) { Ok(v) => v, Err(e) => return Err(e) };` | 18,592 | 0.8494 | |
| + `completed-inline`: `if h.bonding_curve.real_token_reserves==0 {` (no `completed` binding) | **18,584 = orig** | **0.85352** | 1023 |

On the old base both mutations did nothing useful. `qm-09` takes buy_fee_market_cap's error edge out of the shared u128-error
return block. The original's early error-return block has exactly 3 predecessors (sell_quote, tokens_for_quote,
buy_fee_market_cap); ours had 15, because the buy-arm errors were merged into it (see `errs2.py` census below).
Official: 1031/347 (10 raw gains, no losses) vs fresh main.

Error-return census (`errs2.py`: predecessors of each `stb [sret+0x5a],2` block): orig has early=3, late=32; a5 has
early=15, late=20. The buy-arm error edges (net_quote, sub3, get_fees, 590 with_values, complete_fill, transfer_input,
uqp_transfer_native, apply_buy, transfer_base_out) belong to the late block in the original.

## Result 4: post_fill as a tuple output (ledger 21dc079e): 0.89006, call order exact

IR census (post-opt IR of h1): almost every error edge has its own `store err -> sret; tag=2` block. They are
merged after register allocation by tail merging, so the two machine "return" groups are decided by registers.
One IR block, bb216, had 13 buy-arm predecessors joined by phis, because it also carried
`lifetime.end(post_fill.sroa.*)`: the deferred `let post_fill;` at the start of the buy arm keeps the
post_fill pieces' allocas alive across the whole buy arm.

Fix: no deferred binding. post_fill is the 5th element of the reserves `if` tuple
(`(reserves,quote,..,Some(post))` / `(..,None)`), so its storage starts after the `if`.
Result: swap_hop 0.85352 -> **0.89006**, 18,520 B (-64), and the 107-call order now equals the original's.
The early u128 error block (orig: sell_quote, tokens_for_quote, buy_fee_market_cap) is now merged into the
late block (33 preds). Its re-separation is the next target, and probably why we are 64 B short.

`let post_fill;` moved to just after the 590 check (p1, e22923cb): 0.85658, 18,528 B.

### Merge review (main c39655328)
Head 5e9a02804 (post_fill reserves-if tuple, ratio 0.89006) builds swap_hop at 18,520 B, which is further from the original 18,584 B than main (18,544 B), and it loses the 10 raw gains (1032/337, the same as main). It therefore fails merge acceptance. The merged source is restored to 8073709c6's `multi_hop_curve_swap.rs`. Against a fresh build of main c39655328 it scores 1032 normalized / 347 raw (+10 raw, 5,152 B, zero losses), and swap_hop is 18,584 B = original, ratio 0.85352, slots_diff 1023, calls 107/1. regen.sh reproduces ordered.ld. The 0.89006 variant is kept in history (5e9a02804) for later size work.
