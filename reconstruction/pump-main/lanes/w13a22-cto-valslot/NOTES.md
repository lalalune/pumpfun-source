# w13a22-cto-valslot: sharing CPI `val` late in the frame (dead) and validate's `t` below `sk` (+0.0069)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.

## Result

| main | admin_cto ratio | slots | bytes | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| 1043a51 (#2974, base) | 0.53206 | 3,324 | 27,400 | 1034 / 1034 | |
| 1043a51 + this change | **0.53895** | 3,223 | 27,400 | 1034 / 1034 | none |

Runtime differential: 363/363, no mismatches. Unstripped sha `5c0dca771de3ab8c`.

Source change (same lines, newline count kept):

```rust
fn validate(.., sharing:&Pubkey, tb:&mut Pubkey) -> Result<Pubkey> { ..
  *tb=if let Some(t)=new{t}else{return Err(..CtoNewCreatorRequired..)};let t=&*tb;
  if *t==Pubkey::default(){ .. with_pubkeys((*t,Pubkey::default())) }
  if *t==*holder_key||*t==*sharing{ .. }*t};
// execute, state block:
let mut tb=Pubkey::default();let sk=a.sharing_config.key(); .. validate(&st,hopt,fee,new,&holder_key,&sk,&mut tb)?
```

## The val angle is dead on current main

w13a01's recipe step 3 (`mv:val5:_179`, the sharing CPI `val` below `old_creator` like the original's val7, +0.0075
on 4394685) no longer pays. Checked with a fresh raw-IR capture (w13a01 `capraw.py`/`rx.py`, `eq_main` true) and a
post-opt alloca-move llc oracle (`tools/px.py`):

- main 62eb841 (0.52277): val late (`old_creator`, `_136`) 0.52217; val above the final emit_cpi temps 0.52247;
  best val-only position 0.52307 is val *earlier*. On top of E32 (`mv:target1+sharing_update.sroa.3:_182`, 0.52936)
  every val position ties or loses.
- main 1043a51 (#2974 E32 landed, 0.53206): val ties anywhere from `_115.sroa.11` down to `st`; later is
  monotonically worse (old_creator..e 0.52936, ix_data 0.52786, final emit_cpi temps 0.52487, next to
  target11/sharing_update12 0.52307). val late + any one other move <= 0.52936 (258 pairs).
- Source forms (raw-IR capture + oracle on 62eb841): `Ok::<_,Error>(val)?` in the arm (enum, MIR SROA does not split
  it: same position, same ratio); `match val{Some(k)=>Some(k),None=>None}` 0.49761/27,496 B; deferred `let val;`
  same ratio; `let (val,)=Ok::<_,Error>((val,))?;` works as a mechanism (val becomes the highest-index head, top of
  the alloca list) but loses 0.0003; `Ok(sharing_update)?` before the match: same ratio.

No single execute-level alloca move beats 1043a51 (481 + 300 moves/nolts). The frame lever left was in the inlined
validate region.

## Mechanism of the gain: stack-coloring group of validate's `t`

Oracle scan of the 103 inlined allocas on 1043a51: `mv:t.i:st` (validate's 32 B new-creator copy `t` placed anywhere
below `sk` in the alloca list) gives **0.55183** (+0.0198); `target.i.sroa.9` below `sk` +0.0003; nothing else.
Equivalently `mv:sk:<above t.i>` gives the same 0.55183. Debug llc (`-debug-only=stack-coloring`, `scgroups.py`):
on main t.i joins the `_77.i` 48 B group; with `sk` ahead of `t.i` in the size-sorted slot order, `sk` (32 B, live
through validate) is merged into `_77.i` first, so `t.i` can no longer join it and lands in the
`_92.i`/`_103`/`old.i` group instead. So the lever is the relative frame-index order of `sk` and `t`.

Source: make `t` an execute local declared before `sk` (`&mut Pubkey` scratch). The local keeps a lifetime from its
declaration (plus a memset of the default), so the build reaches 0.53895, not 0.55183. IR checks on t1a:
lifetime.start moved to the copy 0.54973; memset removed 0.53595 (the memset helps: MaybeUninit form t1m = 0.53595);
both 0.54733; tb above sk 0.53206 (= main exactly, so the rest of the reshaping is neutral).

| trial | form | ratio | bytes |
| --- | --- | ---: | ---: |
| t1a | `let mut tb=Pubkey::default();` just before `let sk` | **0.53895** | 27,400 |
| t1b | same at the start of the state block | 0.53895 | 27,400 |
| t1m | `MaybeUninit<Pubkey>` scratch, `tb.write(..)` | 0.53595 | 27,400 |
| t1c | `tb` declared before the CtoState literal | 0.33643 | 27,400 |

Next: a form that puts `sk` ahead of `t.i` without widening `t`'s lifetime (oracle 0.55183), e.g. `sk` computed
inside validate after `t` (an inlined alloca created later than `t`), or a `tb` whose StorageLive is at the copy.

## Tools (tools/)

- `px.py <m.ll> SPEC...`: post-opt llc oracle on rx.py's slimmed `m.ll` (`mv:A:B`, `mv:A:END`, `nolt:A`), 4 runs in
  parallel; same tokens as rx.py/target_metric.
- `als.py <a.ll> <b.ll>`: diff of execute's alloca lists between two modules.
- `capsrc.sh <name> <crate> <slot>`: raw-IR capture of any crate directory + rx.py score.
- `edits/`: the source edits (`capvar.sh` format, w13a01).

Ledger keys: `0x22a10-w13-62eb841-valslot-*`, `0x22a10-w13-1043a51-valslot-*`.
