# w14a47-cto-sharestruct: structure of the sharing CPI (admin_cto_sharing_config) in admin_cto::execute

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs` lines 745-751), pinned at 27,400 B.
Base: main 28ab23a9f (0.65488, 3,279 slots, 1034/1035 normalized and raw). Ledger approach `sharestruct`,
keys `0x22a10-w14-28ab23a-sharestruct-*-v1`.

No source change is proposed. This PR holds the classified miss table, the structural bound and the screens.

## Tools (tools/, experiment only)

- `splice.py`, `lst.py`, `cdis.py`, `segdiff.py`, `capraw.py`, `capvar.sh`, `rx.py`: w14a38's splice map and w14a01's
  raw-IR oracle, repointed to this lane (`capvar.sh <name> <edits.py> <slot>` = source EDITS -> capture -> opt -> llc
  -> score; `m0` reproduces main, `eq_main: true`).
- `cls.py <fn.bin|unstripped.so> lo hi [--show]`: masked-level split (fm/rm/jm/sk, as splice.py) of an original range
  against the candidate range found by call landmarks, plus an instruction-class count of the L3 misses. Works on
  rx.py's `fn.bin`, so it scores variants of any size.
- `sdiff.py`: the same diff with the original and candidate listings side by side.
- `batch.sh <res.jsonl> name...`: capvar runs, two at a time. `rec.py`: ledger recorder.
- The accounts-pointer reload probe is w14a01's `accprobe.py` (`ACC=%_217` on s1, `%_266` on main) scored with
  w14a01's `fbsplit.py` ("all" = perfect frame remap).

## 1. What the original sharing region is

Orig 0x3c40-0x4a78 (from the From<ProgramError> join after the sweep to the `admin_cto_sharing_config` call) has
455 instructions. Main has 446.

The original clone run is uniform for all 8 AccountInfo clones (CpiContext program 0x98, then the accounts struct in
field order 0x68, 0x0, [0x8], 0x10, 0x90, 0xa0, 0x98):

```
ldxdw acc,[r10-0x8d8]        ; accounts pointer reloaded before EVERY clone
ldxdw X,[acc+off]
ldxdw L,[X+8]; Rc inc of L (ldx/add 1/mov 1/jeq/mov 0)
<scalar reads of the PREVIOUS clone: +42 +41 +40 +32 +24, each spilled>
ldxdw K,[X+0]
stxdw [L],cnt; jne ovf,1,+1; ja abort
ldxdw D,[X+16]; Rc inc of D; stxdw [D]; jne; ja
```

That is exactly the derived `AccountInfo::clone` of `to_account_info()`: after `data.clone()`'s overflow branch the
remaining field copies (owner, rent_epoch, flags) share a block with the next clone's key/lamports, and the scheduler
emits them after the next lamports load. w14a05 already found this (s1); it holds on 28ab23a.

## 2. Classified miss table (orig 0x3c40-0x4a78, segdiff seg 72, matches against the original out of 455)

| form | bytes | ratio | L0 raw | L1 frame masked | L2 +regs masked | L3 +jumps masked |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main 28ab23a (6 literal `AccountInfo{..}` + 1 to_account_info) | 27,400 | 0.65488 | 224 | 285 | 277 | 279 |
| s1: all 7 plain `to_account_info()` | 27,376 | 0.61741 | 99 | 251 | 374 | 389 |
| main + accounts-pointer reload per clone (IR probe) | 27,496 | (frame moved) | 147 | 286 | 281 | 325 |
| s1 + accounts-pointer reload per clone (IR probe) | 27,456 | (frame moved) | 140 | 281 | **381** | **396** |

cls.py over orig 0x3c38-0x4a78 (fm / rm / jm / sk = misses removed by masking frame, then registers, then jumps; sk =
what is left):

| form | miss | fm | rm | jm | sk |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 231 | 61 | 0 | 0 | 170 |
| s1 | 356 | 152 | 123 | 15 | 66 |
| main + probe | 308 | 139 | 0 | 39 | 130 |
| s1 + probe | 315 | 141 | 100 | 15 | 59 |

Main's 170 structure misses, by cause:

| cause | misses | evidence | source-expressible? |
| --- | ---: | --- | --- |
| literal `AccountInfo{..}` read orders (w14a30 coordinate descent) break the canonical per-clone interleave | ~104 | s1 removes them (sk 170 -> 66) | yes: s1, but it costs 0.037 (section 3) |
| accounts pointer reloaded before each clone (orig 8 `ldxdw rX,[r10-0x8d8]`; main loads it once into r5) | ~8 (+ the 9-insn length deficit) | probe on s1: sk 66 -> 59, L2 374 -> 381 | no (w14a01: RA, callee-saved occupancy) |
| `val` (Option<Pubkey>) payload copy: orig 4+4(overlap)/8/8/8/1 pieces from `new`'s SROA pieces (2 of them in spill slots), ours 4 aligned 8 B loads from a Pubkey alloca | 6 | orig 0x3d28-0x3d80 vs main 0x3d00-0x3d38 | global `new` representation (w12 frame notes, w13a41/w14a39 "entry copy of new"), not sharing-local |
| sharing tag in r6 and swept in r9 across the arm (orig) vs reloads from spill slots (ours: `ldxdw r1,[r10-0x8e8]` x2, swept spilled to `[r10-0x968]` at once) | 4 | orig 0x3c40-0x3c58, 0x3d00 vs main 0x3c10-0x3c28, 0x3cc8-0x3cf0 | no (w14a01 / w14a06 / w13a44: RA) |
| remaining spill-store / reload placement inside the clone run | ~45 | s1 --show: the 37/38-insn moved block at orig 0x4330 is clone F/G with spill stores in other places | no (RA) |

Equal in all forms (0 misses): the pool-authority signer-seeds build (orig 0x3c70-0x3cf8), the CpiContext tail
(remaining_accounts `Vec::new()` = 0/8/0 stores, seeds ptr/len at -0x138/-0x130, the 5 B `_121.sroa.11` copy), the
AccountInfo array offsets (-0x2b8..-0x138). The instruction data, AccountMeta Vec and invoke are inside the
non-inlined `pump_fees::cpi::admin_cto_sharing_config`, which is byte-matched outside the window.

### The "0x30 B lower AccountInfo array" label is not a frame object

w14a38 labelled the tail orig 0x46b8-0x4970 "AccountInfo array 0x30 B lower in ours". The array is at the same offsets
in both (stores to -0x13e..-0x2b8 are identical). Every tail miss is the *source* spill slot of a reload feeding an
array store. Of 54 array stores, 16 read the same spill slot, and the other 38 deltas are scattered
(-8 x7, -48 x6, -32 x5, -24 x5, plus eleven others from -336 to +240). That is per-value spill coloring decided by the
clone run above, not a 48 B object to remove or move. There is nothing source-expressible to screen for it apart from
the clone run itself.

## 3. Bounds

- Perfect-frame bound (`fbsplit all`): main 0.62822, s1 0.60393, main+probe 0.61304, s1+probe 0.61469. The original's
  sharing structure (s1 + per-clone reload) stays 0.0135 below main even with a perfect frame.
- Raw matches in seg 72: s1+probe 140 vs main 224 while L2 is 381 vs 277. Main's literal forms trade structure for
  register and spill-slot coincidences. With registers and frame masked, the true structure matches 104 more
  instructions. Without masking it matches 84 fewer. The register assignment is what is missing: acc in r5 vs reloaded,
  and r6/r9 free vs holding the sharing tag and swept. That is the same RA state w14a01, w14a05, w14a06 and w13a44
  describe. No sharing-local source form reaches it.

## 4. Screens (raw-IR capture + rx oracle; all at or below main)

Single literal reverted to plain `to_account_info()` on 28ab23a (main 0.65488):

| reverted field | ratio | bytes |
| --- | ---: | ---: |
| program | 0.65398 | 27,400 |
| authority | 0.65159 | 27,400 |
| pool_authority | 0.65039 | 27,400 |
| global | 0.64098 | 27,360 |
| mint | 0.63691 | 27,400 |
| event_authority | 0.63028 | 27,352 |
| all six (s1) | 0.61741 | 27,376 |

All 56 two- to five-field combinations (`lat_*`, the fields in the name reverted to `to_account_info()`; ledger
`0x22a10-w14-28ab23a-sharestruct-lat_*-v1`) are below main. Best: authority + program 0.65069, pool_authority + program
0.64979, pool_authority + authority + global 0.64689 (27,392 B). So main's all-literal form is the optimum of the
literal-vs-plain lattice, and no partial return to the original's plain form pays at the current RA.

`val` (the `Option<Pubkey>` CPI arg) spellings on main 0fbf8da (0.65578; s1 there is 0.61831):

| variant | form | ratio | bytes |
| --- | --- | ---: | ---: |
| v_map | `val.map(\|k\|k)` | 0.65221 | 27,496 |
| v_flat | `if sharing_update.is_some(){let val=sharing_update.flatten();..}` | 0.54442 | 27,392 |
| v_asref | `if let Some(val)=sharing_update.as_ref(){.. *val}` | 0.53889 | 27,376 |
| v_new | `Some(_)=>` + arg `if holder{None}else{new}` (the payload straight from `new`) | 0.50968 | 27,296 |
| v_newarm | `Some(_)=>{let val=if holder{None}else{new};..}` | 0.43168 | 27,216 |

v_new / v_newarm sink the 33 B `val` build into the CPI block (the 7/8/8/8/1 copy moves, sk 119-133), so
`new` used directly does not reproduce the original's piece copy either.

## 5. Register census of the faithful form (tools/regperm.py)

Over orig 0x3c38-0x4a78, instructions aligned at L2 whose registers differ: main 79 of 277, s1 127 of 374,
s1+probe 121 of 381. There is no dominant permutation in s1+probe (top pairs: orig r2->r1 16, r7->r9 15, r3->r2 12,
r1->r3 9, r5->r7 9). This is a different allocation, not a renaming, so no single source lever (one value pinned to one
register) closes it.

## Conclusion and next ideas

- The sharing CPI's original source form is plain `to_account_info()` for all seven accounts plus the CpiContext program
  (s1). Its remaining residual is the RA state: the accounts pointer is spilled across the arm and reloaded per clone, the
  sharing tag is in r6, swept is in r9, and the register assignment of the clone run differs. Main's literals are a
  local optimum that buys register and spill coincidences at the cost of ~104 structural misses. Getting to identity
  will need s1 back. That only pays once the RA state is right.
- So the sharing region is not a standalone lever. It should be re-screened (s1 vs main's literals) whenever a landing
  changes the callee-saved occupancy at the sweep join (swept in r9: w14a06/w13a44; tag in r6: w14a01). Re-run
  `capvar.sh s1 e/s1.py` plus `segdiff.py` seg 72 after each such landing.
- `cls.py` and `regperm.py` work on any rx `fn.bin` and need no splice-able size. They are useful for other regions'
  structure-vs-register questions.
