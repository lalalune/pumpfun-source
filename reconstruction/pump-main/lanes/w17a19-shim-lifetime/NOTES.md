# w17a19-shim-lifetime: explicit llvm.lifetime.start/end markers (shim track)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Ledger approach `shim-lifetime`, keys `0x22a10-w17-<sha7>-lifetime-*`.

**Result: two landed gains (+3 M each), 0.68514 -> 0.68604 (#4040, merged by land.py as 2f3597f99) and
0.68634 -> 0.68724 (#4050, merged through #4054 as 357523c1a).** After that, every single-marker family below is
exhausted on main aab087f / 53ec7fb (about 9,000 variants, no further gain).

| step | main | admin_cto | slots | bytes | normalized / raw | differential | unstripped sha16 |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| before | 4d09af488 | 0.68514 | 3,092 | 27,400 | 1034 / 1034 | | |
| creator flip (#4040) | 4d09af488 + r3a | **0.68604** | 3,092 | 27,400 | 1034 / 1034, 0 losses | 388 / 0 | 4ad326fd57505151 |
| t at the 312 error (#4050) | 2f3597f99 + t312 | **0.68724** | 3,092 | 27,400 | 1034 / 1034, 0 losses | 388 / 0 | 8e7e505382d975b7 |

## The construct

Line 8 declares the two intrinsics next to `expect`, `pt64` and the rest (unused, byte-identical: capture `n0`):

```rust
extern "C"{#[link_name="llvm.lifetime.start.p0"]fn lts(n:i64,p:*mut u8);#[link_name="llvm.lifetime.end.p0"]fn lte(n:i64,p:*mut u8);}
```

The size argument stays an `immarg` constant. A call lowers to the same `call void @llvm.lifetime.*` that rustc emits
for StorageLive/StorageDead, survives `opt -O3`, and emits no instruction. It acts in two places:

- **StackColoring.** A slot with more than one START or END marker (or a use outside start..end) is *conservative*:
  it is live from its first START, not from its first use. On main 50 of execute's 137 marked slots are conservative
  (every local that crosses a `?` gets a second END on the Err path). An extra END ends a conservative slot early on one
  path; an extra START makes a slot conservative or moves its front.
- **SelectionDAG.** Each marker becomes a LIFETIME_START/END node chained on `getRoot()`, so it sits between the pending
  loads and the next memory operation of its block. That changes the list-ilp order of independent stores
  (a memcpy's direction) without any instruction of its own.

## Gain 1 (#4040): the CtoState creator copy ascending

The original writes the creator ascending (`stxdw [r10-0x38]`, `-0x30`, `-0x28`, `-0x20`, orig +0x470). Main wrote
it descending. A START of another, already conservative slot between the `fee_configurable` load and the creator
memcpy flips it. Post-opt probes (main 8330455, llc only):

| probe | creator stores | M |
| --- | --- | ---: |
| main | -0x20 -0x28 -0x30 -0x38 | 2,278 |
| START(st) moved to bb5, or a second START(st) before the copy | unchanged (byte-identical) | 2,278 |
| START(sk1 / target.sroa.0 / target.sroa.8 / _51.sroa.11) right before the memcpy | -0x38 -0x30 -0x28 -0x20 | **2,281** |
| the same START before the global-pointer or the `fee_configurable` load | unchanged | 2,278 |
| END(q) moved from bb12's head to right before the memcpy | ascending | 2,281 |
| START(q) before the memcpy (q is not conservative: it recolours) | ascending, frame collapses | 1,874 |

Source (line 339, no line added): validate's key becomes `let mut skm=core::mem::MaybeUninit::<Pubkey>::uninit();`
declared just before the CtoState literal; the creator field is
`creator:{unsafe{lts(32,skm.as_mut_ptr() as *mut u8)}/*shim: ...*/;a.bonding_curve.creator}`; and
`let sk:&Pubkey=unsafe{skm.as_mut_ptr().write(a.sharing_config.key());&*skm.as_ptr()};` replaces `let sk=..key();`.
The capture has the exact signature of the post-opt probe "sk1 START before st's START plus one more START before the
copy".

## Gain 2 (#4050): end `t` at the 312 InvalidCreator error

validate's non-holder `t` (32 B, `t.i`) is conservative, so StackColoring keeps it live through the 312 error block,
where it is dead. `||t==*holder_key{unsafe{lte(32,&t as *const Pubkey as *mut u8)}/*shim: ...*/;return Err(..)}`
ends it at the head of that block. The host list is unchanged; that block's error temps (160 B AnchorError, 24 B
name, to_string buffer and formatter) recolour and reschedule. It was found by the "early END" screen below (one hit in
1,202), and the source capture has the probe's exact signature.

## Priced marker table (what each family moves)

All post-opt screens run llc only on the slimmed post-opt module (~0.1-1 s); pre-opt screens run the w17a06 slim oracle
(opt -O3 + llc, ~2-4 s). M is the scorer's matched-token count at 27,400 B; "nfd" counts frame host changes.

| family | base | variants | best | what it shows |
| --- | --- | ---: | --- | --- |
| pre-opt S2/MV/E/X on execute locals (mint sk hkx q st sk1 target sharing_update pargs e ix ix_data _48 _51 _52 _296 _81 _445), 17 anchors | 8330455 | 307 | = main | S2/MV byte-identical (conservative or no class change); every X extension into wallet/sweep adds a host: M 1,215-1,893 |
| pre-opt S2/E/Ex on validate/wallet/sweep locals, block-start anchors | 8330455 | 184 | = main | |
| post-opt flip: move/duplicate a following START before each >=16 B memcpy | 4d09af4 | 173 | +3 (creator copy only) | the DAG lever exists for one copy |
| post-opt marker moves within the block (+-25 lines, deduped) | 4d09af4, 2f3597f, t312 | 1,308 + 1,843 + 1,843 | +3 (END(q), same lever) | |
| post-opt extra START in the free region (START..first use) | 2f3597f | 869 | = main | DAG-only perturbations elsewhere do not pay |
| post-opt early END at earlier block heads (back to the last use) | 2f3597f | 1,202 | **+3 (t at 312)** | landed as #4050; rerun on t312: none |
| post-opt END at every LIVE_IN block head of named slots | t312 | 818 | = main | |
| post-opt early START (front extension, MaybeUninit-early) of named slots | t312 | 582 | = main | |
| post-opt START/END wrap of a carrier around each memcpy | aab087f | 1,081 | = main | |
| post-opt extra END of a dead named slot before each memcpy | aab087f | 534 | = main | |
| pairs of the 45 best near-neutral singles | t312 | 990 | = main | neutral edits compose neutrally or collapse (-358..-454) |
| pre-opt dead-but-live END frontiers (every valid `lte` at an error/exit block head) | aab087f | 89 | = main | 67 byte-identical |

## Frame-host shift repairs (for b01 / e79v / pf)

- **b01** (validate takes holder_key by value): on 8330455 it is M 1,858 @27,384. It recolours exactly toward the
  original (sk1 -> FI39 -0x470, names -> FI40 -0x488), but the cascade
  names -> FI40, _85/_70/_58 -> FI45, _51.sroa.11 -> FI46, target.i.sroa.9 -> FI52, target.sroa.8 -> FI54 leaves the
  7 B `target.i.sroa.0` homeless (new host at -0x548, +8 below). **Repair:** move the `?` residual piece
  `_51.sroa.11`'s START from bb12 to its only use in bb79 (post-opt): the host list comes back exactly (nfd 0), M 2,019.
  b01 is still -259 in code shape, so the repair is not worth realising; `_51` is a compiler temp, and the manual
  `match` spelling of the `?` collapses (ledger `docoinr8-pm0`).
- **Why sk1 cannot be moved to FI39 by markers alone:** FI47 (authority_info.i, dest.i, _309) has to be blocked for it
  while FI39's host `_112.i` (wallet, [31648, 32032]) must not overlap. The only source-placeable segment is
  [after wallet, after sweep] (covers dest.i's start). The validate names then still cascade as in b01, and without a
  slot live across validate in FI47 (the original's hk2 copy) they move into FI47 instead of FI40.
- **e79v** (w17a10) collapses through a MachineBlockPlacement cliff in the sweep join plus RA, not a frame shift; no
  marker repairs it. **pf** (w17a14) keeps main's frame; its loss is the clone-run register allocation.
- The single-member hosts (`_284`, the event's `authority_info`, `old_creator`, `val7`, `sharing_update15.sroa.3`,
  `target14`, `inner_data`, `_299`) have no lifetime markers at all, so StackColoring never merges anything into them.

## Peel notes

- Gain 1 needs a START of a dead, already conservative slot between the `fee_configurable` field and the creator copy.
  A plain `let x` inside the creator field does not do it (MIR CopyProp removes its storage markers), nor does a
  deferred `let st;` (the START of the copy's own destination has no effect).
- Gain 2 needs `t`'s storage to end before the 312 error is built; a scope that ends `t` before `return Err(..)`
  while keeping it for the `Ok` path is the ordinary-Rust candidate.

## Tools (lane cache `$C/lanes/w17a19-shim-lifetime/tools`, experiment only)

`cap.sh` (capture + slim + fx), `mk.py` (source variant with the extern on line 8), `lscr.py`/`gen1-3.py` (pre-opt
screens), `pscr.py` (post-opt llc + frame diff), `lmove.py`, `xstart.py` (`--mode xstart|early|earlys`),
`liveend.py`, `pairscr.py`, `endscr.py`, `flipscr2/3.py`, `pairs.py`, `scint.py` (StackColoring classes with
intervals), `fpairs.py` (aligned frame-offset differences per region). `framemap.py`, `fshift.py`, `rc.py` are
w17a14's; `preslim.py`, `fx.py`, `oracle.py`, `capraw.py` are w17a06's.
