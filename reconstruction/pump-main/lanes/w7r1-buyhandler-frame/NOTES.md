# Lane w7r1-buyhandler-frame (wave 7, round 1): stack-frame / slot oracle for 0x13b9b8

Target: `0x13b9b8` `buy_v2::buy_handler` (original 15,480 B). Base: origin/main 6edd839
(1027 normalized / 276 raw; buy_handler 0.97998 / 15,512 B).

## Frame map (frameoracle.py + stack_access.py on base)

- `stack_access.py` (orig vs cand, direct r10 accesses): no differences in the access sets.
- `frameoracle.py`: 120 allocas, 91 surviving slots, PEI rule ok, llc reproduces fastbuild.
  Every alloca and every StackColoring group sits at the original T. r10 pairs 807, equal 800.
  The only "delta break" (fi113/fi114, the two `ok_or_else(||error!(Overflow))` return slots
  of the gross+pf+cf `require_gte!` chain) is an alignment artifact: both blocks use the same
  slots as the original (err2 -> -0x6c0, err1 -> -0x6d0); only the blocks are placed
  differently (add-chain block placement, see below). So there is no missing, extra, merged
  or reordered alloca left in buy_handler.
- Remaining r10 mismatches were two register-allocator spill slots (-0x7d0/-0x7d8):
  the original computes the `is_sol` selects in machine order real_sol, virtual_sol, quote;
  ours virtual_sol, real_sol, quote. Machine order is the reverse of the IR select order,
  so the original's IR order was quote, virtual_sol, real_sol.

## Result 1: TradeEvent literal in declaration order (sol reserves)

IR oracle (`edits/swapsel.py`, swap the two selects): 0.97998 -> 0.98209.
Source: write the TradeEvent literal's reserve fields in the struct's declaration order
(`timestamp, virtual_sol_reserves, virtual_token_reserves, real_sol_reserves,
real_token_reserves`). Same line, no line!() change, no behaviour change (struct literal).
Build: buy_handler 0.97998 -> 0.98209 (15,512 B), 1027/276, 0 losses. r10 equal 800 -> 804 of 807.
Ledger 060a7948bb2b47a89dbbf2c79e89be7a.

## Remaining residual (not frame)

- gross+pf+cf checked-add block placement (add1/add2/err1/err2/cmp), +32 B.
- zero-mov order after `call 0xeccc` (r3/r1 vs r1/r3).
- Complete-if branch sense and terminal `jne r8,2` (known: helper vs inline complete).
