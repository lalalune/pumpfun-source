# w12b04-hop-errload: swap_hop (0x5b3b0) line-599 Err load order and the complete_fill `&Global` GEP

Target: `multi_hop_curve::swap_hop` at 0x5b3b0, pinned at 18,584 B
(`programs/pump/src/multi_hop_curve_swap.rs`, line 599).
Base: main e61df0357 (programs/ identical to 20a1ae9c0): swap_hop 0.99913 with 18 differing slots,
Pump Main 1033/1033 normalized/raw.

Outcome: the errload residual this lane was opened for does not exist on main, and a source change of
this lane (v3, a `#[cold]` helper) gave a swap_hop normalized and raw match (1034/1034, zero losses).
#2766 (w12b09-hop-hillclimb) landed an equivalent fix first (the `&Global` is carried in a tuple), so v3
is not proposed for landing. This PR adds notes and tools only.

## 1. Oracle: the line-599 Err load order is not a residual on main

The angle came from w9r2-swaphop-frame's chained oracle on 2abb99ccb. On that base, moving the GEP left
2 slots at +0x23f8/+0x2400 (orig `ldxdw r2,[r10-0xa00]; ldxdw r1,[r10-0xa08]` before
`ja` to the shared Err store, ours r1 first). On main, the line-599 block already loads r2 first.

`llc` on main's post-opt IR (`oracle/p_*.py`, about 5 s each, run with an orc.py like w12b03's) moves only
`%_218 = getelementptr inbounds i8, ptr %_618, i64 8`, the `&Global` argument of `complete_fill`:

| position of `gep %_618, 8` | bytes | ratio | slots_diff |
| --- | ---: | ---: | ---: |
| bb64 (call block), at the call (main) | 18,584 | 0.99913 | 18 |
| bb64, at the very top (`p_bb64top`, the InstCombine sink point) | 18,584 | 0.99913 | 18 |
| bb57, right after the `%_618` load (`p_bb57top`) | 18,584 | 1.0 | 0 |
| bb57, before the mayhem test (`p_bb57end`) | 18,584 | 1.0 | 0 |
| bb58, top / after whitelist gep / after memcmp / after icmp / after lifetime.end | 18,584 | 1.0 | 0 |

Every position in bb57 or bb58 gives the whole window with no Err-order flip. MachineSink moves the `add` to the
top of bb64. Any position inside bb64 keeps the 18 slots, because the SelectionDAG schedules it next to the call.

## 2. Mechanism: how the GEP ends up in bb64 (MIR dump plus per-pass LLVM trace)

Trial v1 (`let global: &Global = &a.global;` before the allowed block, `complete_fill(global, ..)`) builds
byte-identical to main. Traced with `-Zdump-mir=swap_hop` and
`-Cllvm-args=-print-changed=quiet -Cllvm-args=-filter-print-funcs=<swap_hop>` on an experiment copy
(`tools/dumps.py` splits the log and `tools/trace_gep.py` reports where the call argument is defined after each pass):

1. MIR building passes the binding as a reborrow: `_466 = &(*_434); complete_fill(move _466, ..)`
   (`_434` is `global`).
2. After `Account::deref` is MIR-inlined, `global = &((*box).account)` is a "constant place" (an SSA base with field
   projections only). ReferencePropagation rewrites the reborrow into `&((*box).account)`, so rustc emits a
   fresh `gep +8` in the call block. The binding's own gep in bb57 is dead.
3. LLVM `EarlyCSE` (004) replaces the call block's gep with the whitelist chain's `gep +8` in bb58 (`gep +8; gep +640`).
4. `InstCombine` (005) folds the whitelist chain to `gep +648`. The `+8` gep is left with one user in bb64,
   whose unique predecessor is bb58, so InstCombine sinks it to bb64's first insertion point. That is the
   `p_bb64top` position (18 slots).

So the `&Global` must be opaque to MIR ReferencePropagation and still be inlined by LLVM into bb57.

## 3. Two ways to make the `&Global` opaque to ReferencePropagation

- **Tuple carrier** (landed in #2766, w12b09-hop-hillclimb):
  `let (allowed, global) = { let global: &Global = &a.global; ..; (.., global) };`.
- **`#[cold]` helper** (this lane, v3), measured with `score.py` on a fastbuild build of the e61df03 base,
  against the then-current baseline b5975fa67:
  1034/1034 normalized and raw, gain 0x5b3b0, zero losses, swap_hop 1.0 / 0 slots / 18,584 B,
  unstripped sha256 59055a60…. Its post-opt IR has `%_0.i = getelementptr inbounds i8, ptr %a.val, i64 8`
  (the `.i` marks the LLVM-inlined helper) in bb57, right after the Box pointer load. That is the
  `p_bb57top` oracle position.

  ```rust
  #[cold] fn global_ref<'a>(a: &'a MultiHopCurve<'_>) -> &'a Global { &a.global } let global = global_ref(a); let allowed = { let user = a.user.key(); !c.is_mayhem_mode && user!=global.whitelist_pda }; require!(allowed,PumpError::NotEnoughTokensToBuy);
  match complete_fill(global,&a.fee_config,fee_config_len,cap,c,
  ```

  Why it works:
  - Without `#[cold]` (v2), the helper is MIR-inlined and the build is byte-identical to main. After its own
    MIR inlining of `Account::deref`, the helper body has no calls, so `cross_crate_inlinable` is true, and
    the MIR inliner may inline a local non-generic fn exactly when that holds.
  - `#[cold]` is one of the MIR inliner's refusals (`check_codegen_attributes`: "cold"). The call
    result is then an opaque SSA value, so the call-site reborrow collapses to `&(*ret)`, which is just
    that value.
  - The LLVM inliner still inlines the tiny internal helper into bb57. Its body is a load and a `gep +8`, far
    below even the cold call-site threshold.
  - The `+8` gep stays in bb57: its only user is in bb64, whose predecessor is bb58, so InstCombine cannot sink it.

### Reusable tool for other targets

A `#[cold]` plain fn is a source-level **"MIR-opaque, LLVM-inlined"** wrapper. MIR passes such as
ReferencePropagation, GVN and CopyProp cannot see through it, but LLVM inlines it before its function
simplification passes run. Caveat: until the inliner removes the call, BFI treats the call's block as cold, so
inlining decisions for call sites in the region it dominates can change. On swap_hop this changed nothing.
Other carriers that hide a reference from RefProp:
- a tuple field (#2766);
- a non-SSA local (w12b03 tried `&global`, which was byte-identical).

## Trials (ledger lane `w12b04-hop-errload`)

| trial | change on e61df03 | result |
| --- | --- | --- |
| oracle | gep position map (table above) | 0 slots in bb57/bb58, 18 in bb64 |
| v1 | `let global: &Global = &a.global;` before allowed, `complete_fill(global,..)` | byte-identical (sha 8cd7695c…) |
| v2 | plain block-local `fn global_ref(a) -> &Global` | byte-identical (MIR-inlined) |
| v3 | `#[cold]` `fn global_ref(a) -> &Global` | **1034/1034, swap_hop 1.0/0**, zero losses; superseded by #2766 |

Ledger keys: `0x5b3b0-w12-e61df03-oracle-gep-position-map-v1`,
`0x5b3b0-w12-e61df03-mir-trace-global-binding-reborrow-v1`,
`0x5b3b0-w12-e61df03-global-ref-Global-bind-before-allowed-into-complete-fill-v1`,
`0x5b3b0-w12-e61df03-global-plain-helper-fn-defeats-refprop-v1`,
`0x5b3b0-w12-e61df03-global-cold-helper-fn-blocks-mir-inline-v1`.

The scratch outputs live in `~/.cache/pumpfun-reconstruction/lanes/w12b04-hop-errload/` and are not in git:
- `t/v1ir/dumps/` (per-pass dumps);
- `mir_v1/` (MIR dumps);
- `t/v3ir/` (the v3 build and score).
