# Lane w4-createv2 (wave 4)

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 125 direct calls).
Base: origin/main 630a074 (1023 normalized / 277 raw); target 0.75114, 15,632 B, 125 calls.

## Result

| Build | Bytes | Ratio | Calls | Official | Notes |
| --- | ---: | ---: | ---: | --- | --- |
| base 630a074 | 15,632 | 0.75114 | 125 | 1023/277 | x27 form |
| r1nc (R1 rep: `Option<u64>` reserves, `Nested(u8)`) | 15,528 | 0.50862 | 125 | 1023/276 | raw loses 0xa868 |
| s1 = r1nc + `let initial_virtual_quote_reserves=global.…;` before the test | 15,544 | 0.54281 | 125 | 1023/276 | source form of the w3 "sel" IR edit |
| t3 = s1 + curve init moved into `fn init_curve(...)` taking `quote_mint: Pubkey` by value | 15,600 | 0.80355 | 125 | 1023/276 | frame layout = original; raw loses 0xa868 (layout) |
| v9 = t3 with the helper taking the accounts struct (global/bonding_curve bound inside) | 15,592 | 0.80484 | 125 | 1023/276 | |
| **w1 = v9 + `let sol=Pubkey::default();` before the ivqr let (`impl CreateV2 { fn init_curve(&mut self, ..) }`)** | **15,544** | **0.81260** | 125 | 1023/276 | ivqr load now after the memcmp, in the else block, as in the original |
| g1 = w1 with `let mut fee=0; if .. { require!..; fee=creator_fee_bps.0; }` | 15,552 | 0.81454 | 125 | 1023/276 | |
| **g7 = g1 with `matches!(source,Controlled\|Nested(_)) && creator_fee_bps.0>0`** | **15,544** | **0.82553** | 125 | 1023/276 | fee-branch polarity now as original (`and 2; jne 2` falls into the configurable check) |

g10 (`!matches!(source,Sol|Whitelisted)` in g7) scores 0.82597 but lowers the tag test to `jlt tag,2`, unlike the
original's `and64 2; jne 2`, so g7 is kept. Fee spellings with no effect: nested ifs, if-let, `!=0`, negated
condition with `0` first; non-mut matches-first 0.82359. Depth position/spelling, helper binding order, param
order, creator by ref: byte-identical or worse. Later (all on g7): mutable depth / ctx.accounts spelling / `==true`:
identical; holder store outside helper 0.81862; vqr as mutable default 0.716/0.723; `quote_mint!=sol` with the
non-SOL arm first 0.73021; else-if-let 0.81733; validate tuple reorders 0.749/0.756.

Other trials (all 1023/276, raw -0xa868): plain `unwrap_or` in helper 0.75485 (sink.split back); ivqr let inside
else 0.7558; depth computed inside helper 0.80365/0.80829; creator stored after tts / `OptionBool` holder /
`&mut Account` param / method form: byte-identical; legacy-create store order 0.80237 (15,584 B, raw 283 by layout luck).

## Mechanisms

1. **sel (eager default, select)**: binding `global.initial_virtual_quote_reserves` to a local *before* the
   `quote_mint == Pubkey::default()` test puts its load ahead of the `Pubkey::default()` memset, so InstCombine
   can no longer sink it into the empty `None` arm; SimplifyCFG then forms `select isNone, ivqr, r`
   (no `sink.split` block), which BPF lowers to the original diamond.
2. **swap (quote_mint at the top frame slot, compared in place)**: the w3 oracle needed the compared/stored
   32 B Pubkey alloca *above* every execute-local alloca, with the user local `quote_mint` reduced to a dead
   24 B tail. That is exactly what a by-value `Pubkey` argument to a function that the MIR inliner refuses
   (too big: the whole curve initialisation) but LLVM inlines (single call site) produces: rustc creates the
   indirect-argument copy during codegen, so its alloca is emitted at the start of the entry block (after the
   LLVM-inlined `.i` allocas, before all MIR-local allocas); after LLVM inlining the callee compares that copy
   in place and stores it into the curve. In the caller `quote_mint` is no longer borrowed, so it is SROA'd to
   `_83.sroa.12` (the original's untouched 24 B object at -0x4d8). Frame now equals the original through -0x508.
3. **default first**: with `let sol=Pubkey::default();` before the eager ivqr load, the memset precedes the
   load and only the readonly memcmp follows it, so after SimplifyCFG has formed the select InstCombine sinks
   the load into the non-SOL block (original: `ldxdw r3,[global+0x428]` after the memcmp branch).
5. **fee as a mutable default**: `let mut fee=0; if matches!(..) && creator_fee_bps.0>0 {..; fee=..}` gives the
   original's fee-check block layout.
6. Remaining diff (g7): 1,808 of 1,859 original instructions align abstractly; 214 aligned lines differ only in
   registers and 34 in spill offsets. A single rotation of callee-saved roles (cand r7->orig r6 = is_holder_reward,
   cand r9->orig r7, cand r6->orig r9) would lift the ratio to 0.8697: in the original, is_holder_reward is assigned
   r6 before ctx/accounts, which in our build gets r6 first (it carries the $r2 copy hint, so greedy RA queues it
   first). Not found: a natural source change that flips this. Other residuals: depth select kept in a register
   (`jlt tag,3; mov r9,r5`), creator stores scheduled after the u64 fields via a data pointer kept in r4 (IR oracle
   reproduces the pointer but not the order), the validate-time bonding-curve Account pointer reused at the end.
7. Older note is register assignment (orig keeps is_holder_reward in r6/ctx in r7, global ptr spilled at
   -0x720, depth as `jlt tag,3; mov r9,r5`) and the curve-store schedule.

## Raw-layout caveat

`0xa868` (`<&T as Debug>::fmt`, 24 B) is a raw match only because the net size of all functions between it
(0xa7b0 in the build) and its callee (0x1a24f8) equals the original distance. execute lies in between, and
base is +56 B over the original, compensated elsewhere. Any change of execute's size (including reaching the
original size) flips this raw membership; it is a layout coincidence, not a code regression.

## Tools

`scripts/`: `build.sh` (fastbuild + IR/MIR capture via `capmir.py`, score, target metric), `mk.py` (apply an
edit file to a crate copy), `trial.sh`, `ir.py` (slim IR -> llc oracle, 0.2 s), `ren.py` (renames numbered
SSA values so IR edits can move instructions), `an.sh` (frame + register/offset maps), `rec.sh` (ledger).
`ed/`: source edits (`r1nc.py`, `s1.py`, `t3.py`) and IR edits (`ir_sel*.py`, `ir_bc.py`).
