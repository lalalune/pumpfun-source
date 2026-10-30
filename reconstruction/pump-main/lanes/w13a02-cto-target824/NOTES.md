# w13a02-cto-target824: the original's X24 slot and the wallet emit_cpi signer slice

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 3912c47 (0.48772), then 43946852 (0.49071), cb298d5 / 9eb6c00 (0.49101 / 0.49131).
Scratch and IR captures: `~/.cache/pumpfun-reconstruction/lanes/w13a02-cto-target824/` (not in git).
Ledger approach `target824-*`, keys `0x22a10-w13-*-target824-*`.

## Result: source form that reproduces the original's X24 host

The original keeps a 24 B slot directly above `holder_key` (T 0x680). At the validation join it copies
the target tail into it and immediately copies it out again (orig 0x243b0..0x24458: A at -0x530 -> X24
at -0x680 -> full target at -0x580). Later the same slot holds the wallet `emit_cpi!` signer slice
(`_114.i`, 0x29108). On main that slice is a standalone 16 B slot at fi 40/41 (T 0x480). Moving it
out of the inlined region alone is worth +0.028 in the llc oracle (`mv:_114.i:holder_key`:
0.48772 -> 0.51558 on 3912c47, 0.49071 -> 0.51917 on 43946852).

This source form makes StackColoring merge the slice into a new X24, as in the original:

```rust
fn validate(..)->Result<(Option<u64>,Pubkey)>{ .. Ok((fee,target))}            // fee first: 8/24 split
let (holder,cashback,target,sharing_update,collect_old,skip)={let x;               // scoped deferred init
  let (holder,cashback,sharing_update,collect_old,skip)={let st=CtoState{..}; ..
    let mut target=validate(..)?.1; ..override target=st.creator in the shared arm..
    if st.quote_locked{x=target}else{x=target};                                    // x is assigned twice
    (holder,cashback,sharing_update,collect_old,skip)};
  (holder,cashback,x,sharing_update,collect_old,skip)};let mut target=target;
```

`scmerge.py` on the captured IR shows the group `{_114.i, x.sroa.6}` with the representative at fi 136/137, directly
above `holder_key`, and `_11.i` (the 0 B to_string alloca) returns to fi 0 with the wallet bump.

## Why each piece is needed (StackColoring + MIR facts, checked with scmerge and IR edits)

1. StackColoring sorts slots by size and merges a slot into the first earlier, non-conflicting representative.
   The 16 B slice can only land in a slot of at least 24 B that sorts before it and is dead during the wallet emit.
   A new execute-level 24 B slot sorts after the wallet's 24 B groups (`ix_data.i`, `inner_data.i`, `val.sroa.6.i`).
   Each of those groups must therefore already hold a member that conflicts with X24.
2. With `LifetimeStartOnFirstUse`, a slot's interval starts at its first store. The exception is a "conservative" slot, one with more
   than one `lifetime.start` or `lifetime.end`, whose interval starts at the marker. A MIR local with
   StorageLive before the validation block and StorageDead both on the `?` path and after the join becomes a
   conservative slot that spans validation, so it conflicts with every group that holds validate temporaries. IR emulation
   (`v1`..`v7`): a short-lived X24 is absorbed by `_54.i`. A conservative X24 conflicts with everything except the
   `ix_data.i` group while the target pieces are 7/16/9.
3. The fee-first `Result<(Option<u64>,Pubkey)>` puts the Pubkey at payload offset 16 (8/24 split). The validate
   tail, the `?` tail and the block target tail are then 24 B pieces that land in `ix_data.i`,
   `inner_data.i` and `val.sroa.6.i`. `let mut target=validate(..)?.1` must stay a simple binding: its StorageLive then
   precedes the inlined validate, and the override keeps it non-SSA. Its tail lands in `val.sroa.6.i`, which is the
   original's A at -0x530. `let (_,mut target)=` makes the piece short-lived and it is absorbed.
4. MIR CopyProp unifies `a = copy b` when both are SSA, and removes the class head's storage markers. In main the
   tuple field, the outer binding and `let mut target` are one marker-less local (`target1`). The extra copy only
   survives with markers if `x` is non-SSA, which is why `x` is assigned twice. `if C{x=target}else{x=target}`
   with a condition that MIR cannot thread works (`st.quote_locked`, `fee.is_some()`: identical bytes). `if holder` /
   `if shared` / `if skip` are threaded into the sharing arms (code -0.04 abstracted). `x=if shared{target}else{target}` folds away.

## Measurements (llc oracle on captured IR; ratio = target_metric tokens)

| build | bytes | ratio | abstracted | slice host |
| --- | ---: | ---: | ---: | --- |
| main 9eb6c00 | 27,400 | 0.49131 | 0.68993 | none (fi 40) |
| fee-first only (`?.1`) | 27,312 | 0.24876 | 0.68957 | none, `_11.i` merges into it (frame top -8) |
| + x (`if st.quote_locked`), = q16/r0 | 27,368 | 0.4958 | 0.69185 | X24 |
| r0 + old-before-bump (r1) | 27,384 | 0.49565 | 0.69314 | X24 |
| r1 + `v_new_match` (t8) | 27,384 | 0.49805 | 0.69314 | X24 |
| t8 + `s_frozen_first` (w8) | 27,392 | **0.50007** | 0.68105 | X24 |
| w8 + `w_ev_creator_first` + `sh_key_borrow` | 27,400 | 0.49041 | 0.67945 | X24 |
| flat block, `let x;` after `CtoState` (y3) | 27,296 | 0.50368 | 0.68228 | X24 |

Not composable as measured: entry-copy `g8` (`let args=&(new,)`) with x drops the abstracted ratio to 0.53, which suggests the inlining changed.

## Open

- Size: every X24 form found so far is 8..104 B short of 27,400 B. The known size knobs either keep the size or lose ratio.
- The original's E32 (full target, T 0x580) sits in front of `_184`. Ours (`target1`, marker-less) does not move.

## Tools

- `ir/x24lib.py`, `ir/w1.py`: IR emulation of a conservative X24 (llc oracle + `w12b12-cto-cpi/tools/scmerge.py`).
