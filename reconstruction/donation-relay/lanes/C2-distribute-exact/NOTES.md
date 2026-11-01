# w20-relay-C2-distribute-exact notes

Base: origin/swarm/w20-relay-C1-distribute-bps c0e7d2635 (553/571, 796,536 B, built on the scout tip), because C2 uses C1's prechecks and finish helpers.

## Result

559 of 571 functions, 816,744 of 851,888 `.text` bytes (0.95875, normalized), strict 541, losses none, against C1's tip. All five C2 functions are `match: true` and `strict: true`: 0x8eb0, 0x19c80, 0x1c878, 0x24ec0, 0x27048. 0x25f00 (C1's) and 0x1590 (C7's) close with them. Not byte identity: no function is at its final address and `whole_elf_equal` is false.

## What the source is

`tools/distribution/shared.rs`:

- 0x24ec0 `distribute_exact(ctx:DistributionContext,args:ExactDistributionArgs)->Result<()>`, lines 130, 131, 142, 148, 149, 158, 170.
- 0x25f00 and 0x27048 are **one generic**: `transfer_rows<I:Iterator<Item=ExactTransfer>>(ctx:&DistributionContext,rows:I,decimals:u8,expected_program:Pubkey,seeds:&[&[&[u8]]])`, `#[inline(never)]`, lines 191, 196, 201. Same lines in both instances, which is what first pointed there.
  - exact: `I=Copied<slice::Iter<ExactTransfer>>`, two scalars in registers.
  - bps: `I=Map<Zip<Iter<Share>,Iter<u64>>,closure>`, passed by pointer. The closure builds `ExactTransfer {share_type,address,amount}`.
- `ExactDistributionArgs` needs `DistributionArgs`'s declaration order (`transfers,total,decimals,seeds,expected_program`) and a `new` taking `expected_program:&Pubkey`, or the handlers' stores come out in another order.

## Facts checked by building

1. **`.key()` temporaries keep the first loop unrotated.** Target: count-down test at the loop top, `add r1,-1; jeq r1,0`, separate `add` after the overflow branch. `*info.key==*ctx.source.key` gives a rotated loop with `jge`. `info.key()==ctx.source.key()` gives the target. As I read LLVM's `LoopRotate` (not traced in this lane), the temporaries leave `lifetime.end` calls in the latch, so `simplifyLoopLatch` cannot fold it, and an exiting latch without that fold is not rotated.
2. **`zip` is right for the first loop; indexing is not.** `0..len` with `[index]` and `enumerate` with `[index]` both differ (the second keeps a bounds check). `transfers.iter().zip(remaining.iter())` with the `.key()` comparison is exact.
3. **`TokenAccount::try_deserialize_unchecked(&mut &ctx.source.try_borrow_data()?[..])?.amount` must be one expression.** With `let data=..?;` as its own statement the `Result<Ref,ProgramError>` temporary dies early and StackColoring merges it into the 160 B slot (`[r10-0x108]`). As one expression it spans the call and lands at `[r10-0x20]`, with the slice at `[r10-0x38]`, as in the target.
4. **The worker's item is `ExactTransfer`, not a tuple.** The exact instance has `ldxb r1,[r4+0x10]; jeq r1,0x3,exit`: `None` read from the `share_type` niche of `Option<(ExactTransfer,&AccountInfo)>`. It survives only when the element is copied as a whole, so `ExactTransfer` and `ShareType` derive `Copy` and the iterator is `.iter().copied()`. In the bps instance `share.share_type` is a scalar copy, and the check folds away.
5. **`expected_program` is by value.** With `&Pubkey`, `distribute` (0x24578) loses its stack copy and stops matching. By value, the exact instance's copy is still elided, and it passes `args+0x28`.
6. **`mint.key()`, not `*mint.key` and not a hoisted `let mint_key`.** A local changes the preheader; `*ctx.mint.key` flips the error-block order (mint, program, try_from, owner against the target's program, try_from, owner, mint) and the row pointer's register.
7. **Handlers.** Read `total` after `signer_seeds`, and put `config_id:config,mint` in the event from the locals: this fixes the load order. Epoch stays re-read from `accounts`.

## Order in settlement_handlers.rs

`distribute_exact_after` now sits between `distribute_after` and `distribute_after_finish`, and `distribute_exact_non_swap` between `distribute_non_swap` and `distribute_non_swap_finish`, which is the target's order (0x18af0, 0x19c80, 0x1a6d8 and 0x1b810, 0x1c878, 0x1d2d0). No gains or losses from the move.

## Trial integration, Mac route

Scratch merge of C7's tip d60cb0935 (C1 to C6 merged) with this lane's eacd6d9bd, not pushed: 569 of 571 functions, 851,168 of 851,888 B, 0.99915, losses none against this lane's base, strict 550, same_address 243, `.rodata` byte-equal, `.dynstr` equal. Open: 0xb3278 and 0xbcac0, the Linux-only pair. `.text` still has 42 functions out of order (`order.py`), none of them in this cluster except 0x8eb0, a `drop_in_place` instance. `merge-tree` shows no conflict between this tip and any of C1, C3, C4, C5, C6, C7.
