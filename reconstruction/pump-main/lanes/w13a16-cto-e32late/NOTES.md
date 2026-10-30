# w13a16-cto-e32late: target1 and the sharing payload P2 late in the frame

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.

## Result

| main | admin_cto ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| 74b3171 (base) | 0.51348 | 3,334 | 27,400 | 1034 / 1034 | |
| 74b3171 + this change | **0.52307** | 3,334 | 27,400 | 1034 / 1034 | none |
| 62eb841 (w13a06 #2903) | 0.52277 | 3,324 | 27,400 | 1034 / 1034 | |
| 62eb841 + this change | **0.53206** | 3,324 | 27,400 | 1034 / 1034 | none |

Runtime differential: 363/363, no mismatches.

Source change (one statement after the state block, same line):

```rust
...(holder,cashback,target,sharing_update,collect_old,skip)};
let (target,sharing_update)=Ok::<_,anchor_lang::error::Error>((target,sharing_update))?;
let mut target=target;
```

## Mechanism (MIR, checked with `--emit=mir` on each capture)

- On main, `target1` is MIR `_61`, the operand temp of the block-tail tuple expression (`_61 = copy _38`, where `_38`
  is the inner `let mut target`, non-SSA because of `target=st.creator`). CopyProp makes `_61` the head of the class
  {tuple field, outer binding, `let mut target` rebinding} and strips its storage markers. P2
  (`sharing_update.sroa.3`) is `_47`, the inner destructure binding (copy of the non-SSA `_408`, the MIR SROA field of
  the if-tuple = P1). A copy-class head keeps the index of the statement that created it, so both sit in the
  middle of the frame order.
- MIR SROA appends its new locals after every other local (after the inlined ones), and the MIR local index fixes the
  LLVM alloca order. A field of a tuple that SROA splits becomes a high-index head only if the field is
  assigned from something that is not a plain local copy. Otherwise CopyProp keeps the older local as head (`u1`:
  using `r.2`/`r.3` of the block tuple directly is byte-identical; `m1`/`m2`: an `Option` wrapper is folded by GVN).
- `Ok(..)?` inlines `Try::branch`; GVN does not fold the `(ControlFlow::Continue).0` variant projection, so the
  `val` binding is assigned from a projection. MIR SROA splits it into two new highest-index locals, which become the
  marker-less heads of `target` and `sharing_update`. In LLVM `target1`/P2 then sit above the final emit_cpi temps.
  This is exactly the IR oracle step `mv:sharing_update.sroa.3:_186` + `mv:target1:_186`: 0.52307 = oracle 0.52307.
  A 1-tuple for one value alone gives the single-move oracle values: target alone 0.51408, P2 alone 0.51438.

## IR oracle on 74b3171 (llc on post-opt IR, `w12a02` iredit.py)

| edit | ratio |
| --- | ---: |
| none | 0.51348 |
| `mv:target1:_186` | 0.51408 |
| `mv:sharing_update.sroa.3:_186` | 0.51438 |
| both | 0.52307 |
| both, anchored before ix/_178/_171 | 0.52097 |
| both, before ix_data/inner_data | 0.51797 |
| both, before old_creator .. e | 0.51618 |
| `mv:_114.i:_186` (F1) | 0.53685 |

Any anchor at or above `_186` (the final emit_cpi sret) gives 0.52307.

## Other trials (raw-IR capture + opt oracle; ledger keys `0x22a10-w13-74b3171-e32late-*`)

| trial | form | ratio | bytes |
| --- | --- | ---: | ---: |
| u1/u2 | outer tuple kept as `r`, `r.2`/`r.3` read directly | identical | 27,400 |
| n1/n2 | `let r;` assigned in two arms (non-SSA aggregate) | 0.44072 | 27,504 |
| n3 | n1 + inner if-tuple read as `s.0..` | 0.4718 (abs 0.70157) | 27,472 |
| n5 | `r = if shared{..}else{..}` (no inner tuple) | 0.23464 | 27,384 |
| h0 | whole block value `Ok((6-tuple))?` | 0.36184 | 27,408 |
| h1/h2 | block as an immediately-called closure / nested fn | 0.45399 / 0.33037 | 27,632 / 27,944 |
| m1/m2 | `Some(block)` let-else / match | same as main | 27,400 |

n3 places holder_key/mint at the original T 0x6a0/0x6c0 and shifts the middle region to 8 B short of the original,
but adds 2 spill slots (deep spills +8), so it scores lower.

## Original join (0x243b0..0x24458), for the next step

At the validation join the original copies P1 (7 B at -0x538/-0x535, 8 B at -0x548, 1 B at -0x540; middle 16 B in
spills) into P2 (-0x550/-0x54d, -0x560, -0x558) and builds E32 at -0x580 from a spilled first word (-0x918) and the
24 B X24 tail (-0x670..-0x680, itself copied from A at -0x520..-0x530). E32 is passed by pointer to admin_cto_pool
(0x27820 `add64 r3,-0x580`) and read word by word for the curve store (0x27518). P2 is SROA'd (pieces), not a 32 B
memcpy source as ours.

## Tools (tools/)

- `offmap.py <m.o>`: aligns original and candidate on abstracted tokens and lists, for each original r10 offset, the
  candidate offset it maps to (frame vote).
- `frame.sh <m.ll>`: `llc -stop-after=prologepilog` + w13a04 `mirframe.py` frame map.
- `exmir.py`: extracts execute from `--emit=mir` output. The capture is w13a01's `capraw.py`/`capvar.sh`, with
  `--emit=link,llvm-ir,mir`. Adding mir does not change the IR (main capture `eq_main`).

## After landing (#2974, merge 1043a51e8)

Landed: main 62eb841 0.52277 -> 1043a51 **0.53206** at 27,400 B, no losses. Main then moved to 6af878b (#2989, 0.53895).

Frame map of 1043a51 (`tools/frame.sh`): target11 (E32) at T 0x580, then _193 0x598, _178 0x5c8, inner_data 0x5e0,
authority_info 0x610, old_creator 0x630 and val6 0x651. These are all the original's offsets. What remains in the named region:
- `st` (48 B, T 0x688) sits where the original has the 7/9 B entry-copy pieces of `new` (T 0x658/0x668) and X24 (T 0x680).
  holder_key and mint, plus the spills that originally sat at T 0x6e0..0x8c8, are therefore at +8. In the original these are
  `st.creator` copies, kept by the `memcmp` for `st.creator!=Pubkey::default()`.
- In the original, P1 (the inner sharing payload, 7/9 pieces at T 0x538/0x548) sits where our wallet signer slice
  `event_signers.i` is. Ours P1 is 32 B and stack-colored into `_54.i`. Giving it its own slot (`nolt`) costs 0.037.

Size-pinned frame-only single-move scan on 1043a51 (44 execute allocas x 11 anchors + nolt, 511 runs): the best is
`mv:target.i.sroa.9:END` at 0.53235 (+0.0003). Every other move is <= 0.53206. F1 (signer slice near holder_key) now
loses (0.52277). So single alloca moves are exhausted after this change.

More `Ok(..)?` trials (ledger `0x22a10-w13-{1043a51,6af878b}-e32late-*`):

| trial | ratio | bytes |
| --- | ---: | ---: |
| + cashback in the tuple (1043a51) | 0.53235 | 27,400 |
| same on 6af878b | 0.53895 (= main) | 27,400 |
| + holder (1043a51 / 6af878b) | 0.52242 / 0.5275 | 27,344 / 27,376 (size knob) |
| + collect_old / skip | = main | 27,400 |
| old_creator, (old_creator,old_fee), pool_updated, swept, holder_key, quote_locked, shared | = main | 27,400 |
| mint | 0.49431 | 27,432 |
| inner if-tuple through Ok (6af878b) | 0.4976 | 27,400 |
| validate result through Ok((..,))? (6af878b) | 0.33109 | 27,392 |
| w13a02 fee-first `?.1` / + scoped x / x only (1043a51) | 0.31873 / 0.27792 / 0.5009 | 27,304 / 27,360 / 27,528 |
