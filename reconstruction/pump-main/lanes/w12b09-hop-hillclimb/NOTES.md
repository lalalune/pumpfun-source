# w12b09-hop-hillclimb: swap_hop (0x5b3b0) complete_fill `&Global` argument

Target: `multi_hop_curve::swap_hop` at 0x5b3b0, pinned at 18,584 B
(`programs/pump/src/multi_hop_curve_swap.rs`, lines 599-605).
Base: main e61df0357 (programs/ identical to 20a1ae9c0), swap_hop 0.99913 with 18 differing slots.

## Oracle: the GEP is the only residual

`llc` on main's post-opt IR (lane tool `orc.py`, about 1 s on the reduced module) with one edit:
move `%_218 = getelementptr inbounds i8, ptr %_618, i64 8` (the `&Global` argument of
`complete_fill`) out of the call block `bb64`:

| placement of `gep %_618, 8` | bytes | ratio | slots_diff |
| --- | ---: | ---: | ---: |
| bb64, at the call (main) | 18,584 | 0.99913 | 18 |
| bb57, right after `%_618 = load` of the `Box<Account<Global>>` pointer | 18,584 | 1.0 | 0 |
| bb58, right after the whitelist `gep %_618, 648` | 18,584 | 1.0 | 0 |

With the GEP in either earlier block, MachineSink moves the `add` to the top of `bb64`, giving
the original's `ldxdw r2,[r10-0xb28]; add64 r2,8` right after the whitelist `memcmp` test.
On the current main the older 2-slot line-599 load-order residual is gone, so this one move
gives the whole window.

## Mechanism: MIR ReferencePropagation re-derives the borrow at the call

A hoisted `let global: &Global = &a.global;` passed as `complete_fill(global, ..)` builds
byte-identical to main (w12b04 v1, and this lane). Its first LLVM dump (rustc's own IR,
before any LLVM pass; w12b04 `t/v1ir/dumps/001_*`) already shows:

- `bb57: %global = getelementptr inbounds i8, ptr %_619, i64 8` — dead;
- `bb64: %_219 = getelementptr inbounds i8, ptr %_619, i64 8` — the actual call argument.

So no LLVM pass sinks the GEP: MIR already computes the argument at the call. Passing a
`&Global` local to a `&Global` parameter is a coercion site, and with distinct lifetimes the
coercion inserts a reborrow `&*global`. `ReferencePropagation` knows the SSA local
`global = &(*box).account` (a "constant place": SSA base and field projections only) and rewrites
the reborrow `&(*global)` into `&((*box).account)` at the call. That is the GEP in `bb64`.
`let global=&*a.global` (an `&Account<Global>`) is worse still: the `Account -> Global` deref
coercion itself happens at the call.

To keep the early GEP, the `&Global` local must be opaque to ReferencePropagation. Passing it
through a tuple field does this: RefProp only follows SSA locals assigned `&place` or a copy of
another such local, and `Use(Copy(_tup.1))` is neither. The measured result shows that MIR SROA
does not undo this before RefProp runs.

## Result: swap_hop normalized and raw match

Line 599 (lines and error sites unchanged):

```rust
let (allowed, global) = { let global: &Global = &a.global; let user = a.user.key(); (!c.is_mayhem_mode && user!=global.whitelist_pda, global) }; require!(allowed,PumpError::NotEnoughTokensToBuy);
match complete_fill(global,&a.fee_config,fee_config_len,cap,c,
```

| metric | main 20a1ae9c0 | this change |
| --- | ---: | ---: |
| swap_hop ratio | 0.99913 | 1.0 |
| swap_hop slots_diff | 18 | 0 |
| swap_hop bytes | 18,584 | 18,584 |
| normalized / raw (of 1,035) | 1033 / 1033 | 1034 / 1034 |
| gains / losses | | +0x5b3b0 (normalized and raw) / none |
| admin_cto | 0.43919 / 27,400 B | unchanged |
| unstripped sha256 | 8cd7695c… | cbd9bf08d09967f71921acaf2b89ad576abd96654a192834a268cd1e18f59269 |

`measure.sh` output: `t/tup_allowed_global` in the lane out dir. Ledger keys:
`0x5b3b0-w12-e61df03-hc-oracle-gep8-bb57-or-bb58-v1` (oracle),
`0x5b3b0-w12-e61df03-hc-tuple-allowed-global-refprop-blocker-v1` (this change).

## Trials

See `SUMMARY.json` and the ledger (lane `w12b09-hop-hillclimb`).
