# w20-relay-C1-distribute-bps notes

Base: origin/swarm/w20-relay-scout dfcbfc6ae (545 of 571, 776,384 B, 0.91137). This branch merges C2's exact flows.

| step | functions | bytes | ratio | gains in this cluster |
|---|---:|---:|---:|---|
| split into prechecks, finish and transfer worker, `ctx` kept whole | 551 | 787,840 | 0.92482 | 0x18478 0x1a6d8 0x1b090 0x1d2d0 0x24578 (and C2's 0x8eb0) |
| remaining-accounts check as `if len<shares {Err}` then `&remaining[..n]` | 553 | 796,536 | 0.93502 | 0x18af0 0x1b810 |
| worker rows zipped on the left, `ctx.mint.key()` in the mint check | 554 | 800,960 | 0.94022 | 0x25f00 |
| merged with C2 | 559 | 816,744 | 0.95875 | C2's cluster and 0x1590 |

All 8 functions of the cluster match with `strict: true`. Losses: none at any step. These are normalized matches on the Mac route.

## Helper signatures (C2 shares these)

In `settlement_handlers.rs`, all `#[inline(never)]`:

- 0x18478 `distribute_after_prechecks(accounts:&DistributeAfterJustSwappingV1)->Result<()>`, lines 88, 93, 98
- 0x1a6d8 `distribute_after_finish(accounts:&mut DistributeAfterJustSwappingV1,signer_seeds:&[&[&[u8]];1])->Result<()>`
- 0x1b090 `distribute_non_swap_prechecks(accounts:&DistributeNonSwapOutputMintV1)->Result<()>`, lines 80, 85, 91, 96
- 0x1d2d0 `distribute_non_swap_finish(accounts:&mut DistributeNonSwapOutputMintV1,signer_seeds:&[&[&[u8]];1])->Result<()>`

`#[inline(never)]` is a reading, not a fact: the target keeps these out of line with two callers each, and the worker with one caller.

The handlers now sit in target order: prechecks, handler, exact handler, finish, for both flows. Moving the exact handlers removed 0x19c80 and 0x1c878 from
the `order.py` out-of-order list (LIS 496 to 498) with no change in any function.

## What decided each match

**0x18af0, 0x1b810: one token.** `remaining.get(..n).ok_or(..)?` compiles to `jle shares, remaining`. The target has `jge remaining, shares`, which is
`if remaining.len()<shares.len() {return Err(..)}` followed by `&remaining[..shares.len()]`. The slice's panic path folds away, so no `Location` appears.

**0x24578: keep `ctx` whole.** Destructuring it inlines the drops. Field access through `ctx.` gives one `drop_in_place<DistributionContext>` call (0x8eb0) at the single exit.

**0x25f00: the worker has three independent shape constraints.**

1. `rows.zip(ctx.remaining.iter())`, not the reverse. `cmp::min(a_len,b_len)` is `if b<a {b} else {a}`, and the target's `jlt remaining, rows` names `remaining` as `b`.
2. The amount and address are copied out at the top of the loop, before `try_from`, with the address words loaded first in the listing. Listing order is the reverse of IR order here.
3. **`token.mint!=ctx.mint.key()` by value, and again in `with_pubkeys`.** This is a block placement fact, and the masked diff did not show it: the compare listing is the same either way.
   `*ctx.mint.key` compares through `bcmp`, expanded into four blocks, and each `jne` leaves the loop with probability 1/32.
   `ctx.mint.key()` loads a temporary and folds to one `or.cond` branch, so the four jumps share one 1/32 exit.
   That raises the chance of reaching the amount check from 0.728 to 0.801.
   `findBestLoopTop` moves the latch above the header only when the back-edge frequency exceeds the preheader, exit and fallthrough losses, which needs about 0.793.
   That one change moved the latch, the `mov r0,2` exit block and the error blocks into the target's order, as `-print-before=block-placement` probabilities predicted.

## One generic worker

0x25f00 and 0x27048 both carry the literal lines 191, 196 and 201, and sit adjacent, so they are two instances of one function. `transfer_rows` over `Iterator<Item=ExactTransfer>`
gives both, at the target's sizes (4424, 4336) and order. The bps flow maps `(share,amount)` into an `ExactTransfer`. There `share_type` has its enum range, so the `Option` niche test folds away.
The exact flow uses `.copied()`, a plain copy with no range, so `share_type==3` stays in the listing at 0x27048+0x2d8. C2 reached the same shape in parallel and its closure spelling is kept.

## Line numbers

| site | old source | target |
|---|---|---|
| after: EpochNotClosed, InvalidState, InvalidMint | 91, 96, 101 | 88, 93, 98 |
| after: InvalidBalance total==0, amount<total | 110, 112 | 116, 118 |
| non_swap: EpochNotClosed, InvalidState, InvalidMint, InvalidMint | 83, 88, 94, 99 | 80, 85, 91, 96 |
| non_swap: InvalidBalance | 111 | 117 |
| shared.rs distribute: InvalidTokenAccountProgram | 74 | 82 |
| shared.rs worker: owner, mint, program | 98, 105, 112 | 191, 196, 201 |

## Reproduce

    $C/relay/tools/measure.sh <worktree>/programs/donation-relay $C/relay/lanes/C1-distribute-bps/work $C/relay/lanes/C1-distribute-bps/out
    python3 $C/relay/tools/relay.py diff <out>/unstripped.so 0x25f00 --sym 'shared::transfer_rows' -c 1

For the placement numbers, add `-C llvm-args=-print-before=block-placement -C llvm-args=-filter-print-funcs=<mangled>` to the rustc arguments and read the `successors:` probabilities. It changes printing only.
