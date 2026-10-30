# Lane w12a01-cto-frame: admin_cto::execute (0x22a10) stack-frame slot map

Base: main 20a1ae9c0 (baseline sha 8cd7695c..., admin_cto 0.43919 at 27,400 B, 3,352 slots).
IR/MIR of main: the identity build with `--emit=link,llvm-ir,mir` (candidate.so identical to the
baseline). `frameoracle.py` (w4-frame-oracle) reproduces the fastbuild bytes with llc (`True`).
Full oracle report: `frameoracle-main-20a1ae9c0.txt` in this directory.

## How to read the slot map

`T` = frame offset: an object at T occupies `[r10-T, r10-T+size)`. PEI places surviving objects in
frame-index (fi) order: first LLVM-inlined callee allocas (`*.i*`, last-inlined first), then the
function's own allocas in reverse MIR-local order, then 16-byte ISel call-return slots, then
register-allocator spills. A merged StackColoring group sits at its representative's position.

## Alloca region (T <= 0x6c0): original vs main

Original layout was read from the original's accesses (widths and overlapping 4-byte pieces), and
each piece's identity from what the original copies into and out of it.

| orig T | size | original object (value it carries) | main fi / T | main object |
| ---: | ---: | --- | --- | --- |
| 0x1 | 1 | `_11.i296` | fi0 0x1 | same |
| 0x38 | 48 | group: `st` (CtoState), `_77.i111`, buf.i | fi15 0x38 | same |
| 0x2d0 | 664 | group `_54.i` (+ 30 members) | fi22 0x2d0 | same |
| 0x450 | 384 | group `_131.i` (formatters, `_160`, `_23`, `_11`) | fi37 0x450 | same |
| 0x470 | 32 | `_120.i` (wallet emit_cpi seeds `[&[u8];2]`) | fi40 0x470 | same |
| -- | -- | (nothing) | **fi41 0x480** | **`_117.i74` 16 B: wallet emit_cpi signer `[&[&[u8]];1]`** |
| 0x488 | 24 | `_110.i` (wallet invoke_signed Result) | fi43 0x498 | same, -16 |
| 0x4b8 | 48 | `_94.i`, `t.i` (validate's `t`) | fi46 0x4c8 | same, -16 |
| 0x4d0 | 24 | `ix_data.i` | fi47 0x4e0 | -16 |
| 0x4e8 | 24 | `inner_data.i` | fi48 0x4f8 | -16 |
| 0x518 | 48 | `authority_info.i`, `dest.i`; also the holder_key copy used by validate | fi49 0x528 | -16 |
| 0x530 | 24 | `val.sroa.6.i` group; also holds validate's target tail (target = 8 B in r/spill 0x918 + 24 B here) | fi54 0x540 | -16; ours also merges `target.sroa.8` (9 B) into it |
| 0x538 | 7 (al 4) | A7: inner `sharing_update` payload bytes [1,8) | -- | -- |
| 0x548 | 9 | B9: inner `sharing_update` payload bytes [24,33) | (merged in fi54) | `target.sroa.8` |
| 0x550 | 7 | C7: outer `sharing_update` payload [1,8) (copied from A7 at 0x243e0) | -- | -- |
| 0x560 | 9 | D9: outer `sharing_update` payload [24,33) | -- | -- |
| 0x580 | 32 | E32: outer `target` (stored to curve.creator at 0x27518, `&target` to admin_cto_pool at 0x27820) | -- | -- |
| 0x598 | 24 | `_184` (emit_cpi `Result<(),ProgramError>`) | fi109 0x558 | +64 |
| 0x5c8 | 48 | `_169` (emit_cpi Chain iterator) | fi112 0x588 | +64 |
| 0x5e0 | 24 | `inner_data` | fi114 0x5a0 | +64 |
| 0x610 | 48 | `authority_info` | fi115 0x5d0 | +64 |
| 0x630 | 32 | `old_creator` | fi122 0x5f0 | +64 |
| 0x651 | 33 (al 1) | `val7` (`if let Some(val)=sharing_update`, passed by ref to admin_cto_sharing_config) | fi125 0x611 | +64 |
| 0x658 | 7 | F7: copy of `new` bytes [1,8), stored at ENTRY (0x22f00) | -- | -- |
| 0x668 | 9 | G9: copy of `new` bytes [24,33), stored at entry (0x22f38) | -- | -- |
| 0x680 | 24 | H24: target tail copy at the validation join (0x243b8), then -> E32; **`_117.i74` merges here** | -- | -- |
| -- | -- | -- | fi131 0x638 | `sharing_update2.sroa.3` 32 B, no lifetime (outer sharing_update payload) |
| -- | -- | -- | fi132 0x658 | `target1` 32 B al 4, no lifetime (outer target, MIR `_55`) |
| -- | -- | -- | fi137 0x660 | `target.sroa.0` 7 B (block target, MIR `_36`) |
| 0x6a0 | 32 | `holder_key` | fi144 0x680 | +32 |
| 0x6c0 | 32 | `mint` | fi145 0x6a0 | +32 |

So the 32 B offset of everything from holder_key down (the "+56" seen at the arg spills is +32 here
plus spill-slot reassignment) is: `-16` (`_117.i74` has no 24 B host) `+80` (A7 B9 C7 D9 E32 are
absent) `-32` (main has sharing_update2.sroa.3 + target1 + target.sroa.0 where the original has F7 G9 H24).

Data flow differences behind it (original vs main):
- The original keeps a COPY of `new: Option<Pubkey>` SROA-split 7/8/8/9 (F7, spill 0x900, r9, G9),
  made at function entry. Main reads `new`'s bytes straight from the argument pointer.
- The original's sharing_update payload is 7/8/8/9-split (A7/B9 inner, C7/D9 outer); main's is one
  32 B piece. Conversely the original's validate target is 8+24-split (r/spill 0x918 + 24 B at
  0x530 -> H24 -> E32); main's target is 7/8/8/9 (`target.i.sroa.0/9` -> `target.sroa.0/8` -> `target1`).
- The original's own allocas A7..E32 sit above the emit_cpi locals (`_184`), i.e. at the top of the
  own-alloca list: higher MIR index than the emit_cpi temporaries, which only MIR-inlined callee locals
  or codegen temporaries get. MemCpyOpt's stack-move merge keeps the merged alloca at the earlier
  (higher-index) of the two positions and drops its lifetime markers, so E32 can be `target` merged
  with such a top-of-list alloca.

## ISel call-return slots and spills (T > 0x6c0)

Main has 33 call-return slots (fi146..fi178, T 0x6b0..0x8b0) like the original (0x6d0..0x8d0), but in a
different order: most are +16 (fi155..fi171), fi149/150/151 sit at the end in the original
(0x8b0/0x8c0/0x8a0), fi152/153/177/178 move up. Spills start at 0x8b8 (orig 0x8d8, +32) and are
reassigned (the first arg spill is main 0x8f0, orig 0x928).

## What each fix is worth (same code, r10 offsets remapped; `tools/remap.py`)

| remap | ratio |
| --- | ---: |
| none (main) | 0.43919 |
| 0x488..0x540 by -16 only (`_117.i74` gone from fi41) | **0.48892** |
| + 0x541..0x6a0 by +32 | 0.49371 |
| every alloca at its implied original T, rest +32 | 0.49491 |
| allocas + ISel slots implied, spills +32 | 0.51228 |
| every surviving object at its implied original T | 0.56980 |
| abstracted ratio (all offsets equal) | 0.6465 |

IR oracle (no source): `frameoracle.py --move-alloca _117.i74:holder_key` (the 16 B slot placed just
above holder_key, as an own alloca would be) reproduces **0.48892** with llc, code unchanged. So the
single biggest frame lever is giving the wallet emit_cpi signer array `_117.i74` a home that is not
at fi41: a >=16 B own alloca, lifetime-marked, whose live range avoids the wallet's emit_cpi (the
original's H24), or any other way to move it out of the inlined-alloca block.

## Tools (this directory, `tools/`)

- `nosc.py <module.ll> <sym-rx> [name]`: per-alloca implied original slot from a `-no-stack-coloring`
  llc run (every alloca keeps its own slot), all rows, not only confident ones.
- `acc.py <so|orig> [lo hi]`: r10 accesses of the window grouped by offset (width, load/store, lea).
- `remap.py <so> 'lo-hi:+d,...'`: masked ratio after remapping r10 offsets piecewise.
- `capture.py`, `trial.sh`: lane-local IR capture build of a crate copy plus frame oracle and metric.
