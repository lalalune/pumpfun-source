# w17a14-shim-shimwhole: whole-function shim view of admin_cto::execute (notes, tools)

Target: `admin_cto::execute` at 0x22a10 (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 7d5e14d (0.67735, M 2,261, 3,141 slots). Earlier trials in this lane ran on 442ae70 (0.67615).
Ledger: approach `shimwhole`, keys `0x22a10-w17-<main7>-shimwhole-*`.

The lane's brief was a complete unsafe replacement of `execute` shaped like the original (from the w17a01 Ghidra
outputs). It did not get there. What it found is the reason every whole-region rewrite so far "collapses": the frame.
It also built the tools to see that directly. No source change is proposed; every measured variant is below main.

## Tools (all in `tools/`, experiment only)

| tool | what it does |
| --- | --- |
| `rc.py <ref.so> <cand.so>... [--mask r,f,s,a,j,...]` | true-LCS matched original tokens per Ghidra region (E1..W2, the w17a01 map), cand minus ref, plus the scored difflib ratio. Masks: `r` registers, `f` all frame offsets, `s` spill-slot offsets only (< -0x8e0), `a` alloca offsets only, `j` jump offsets. |
| `adiff.py <cand.so\|main> <lo> <hi> [--mask rj]` | aligned listing of an original window against the candidate (`=` exact, `~` masked-only match, `-`/`+` unmatched). |
| `blk.py <cfg.json> <lo> <hi>` | block list from the w17a01 Ghidra CFG with calls, successors and the PumpError code of each error block. |
| `fshift.py <ref.so> <cand.so>` | histogram of frame-offset deltas over matched instruction pairs, split alloca/spill. A collapse shows up as one dominant non-zero delta. |
| `capopt.py <crate> <work> <out>` | identity build that also emits rustc's post-opt IR and writes `<out>/m.ll`, the module slimmed to `execute`. Its binary is the normal build's (checked), and `llc` on `m.ll` reproduces main byte for byte (checked on 7d5e14d). |
| `framemap.py <m.ll>` | the backend's alloca frame: runs the assertions `llc` with `-debug-only=stack-coloring,prologepilog` and prints every surviving host frame index with its r10 offset, size and the allocas StackColoring merged into it (IR names). |
| `capvar.sh <name> <edits.py> <slot>` | apply edits to a crate copy, `capopt`, `framemap`, diff against main's frame. |
| `run.sh <name> <edits.py> <slot>` | apply edits, `measure.sh`, `rc.py` exact and rfj against main. |

`frame-main-7d5e14d.txt` is main's frame map.

## Where main's 1,072 missing tokens are (rc.py on main 7d5e14d)

LCS-matched original tokens per region. Each "+" column is what masking only that field would add. "structural gap"
is what is left with registers, frame offsets and jump offsets all masked.

| region | orig tok | exact | +regs | +spill slots | +alloca offs | +jumps | rfj | structural gap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| E1 entry PDA/shared | 77 | 34 | +8 | +2 | +0 | +2 | 48 | 29 |
| E2 quote_locked | 51 | 35 | +5 | +0 | +1 | +0 | 44 | 7 |
| E3 CtoState/new | 90 | 21 | +19 | +0 | +5 | +3 | 55 | 35 |
| V1 | 119 | 72 | +1 | +1 | +14 | +5 | 103 | 16 |
| V2 | 105 | 50 | +1 | +1 | +7 | +5 | 76 | 29 |
| V3 | 121 | 57 | +2 | +0 | +16 | +4 | 93 | 28 |
| V4 | 65 | 49 | +4 | +0 | -5 | +2 | 43 | 22 |
| V5 | 101 | 67 | +6 | +4 | +0 | +6 | 84 | 17 |
| J1 | 50 | 21 | +2 | +1 | +7 | +1 | 37 | 13 |
| J2 | 91 | 62 | +2 | +1 | +13 | +3 | 83 | 8 |
| W1 | 86 | 74 | +5 | +0 | +0 | +1 | 81 | 5 |
| S1 | 228 | 194 | +8 | +1 | +0 | +14 | 219 | 9 |
| T1 TCF clones | 685 | 482 | +119 | +32 | +1 | +20 | 660 | 25 |
| C1 sharing clones | 458 | 232 | +65 | +50 | +7 | +14 | 399 | 59 |
| P1 | 115 | 89 | +13 | +3 | +0 | +1 | 107 | 8 |
| EV | 220 | 187 | +22 | +0 | +1 | +3 | 213 | 7 |
| TL | 141 | 125 | +6 | +0 | +3 | +2 | 137 | 4 |
| S2 | 63 | 41 | +7 | +3 | +0 | +4 | 62 | 1 |
| W2 | 473 | 375 | +46 | +8 | +3 | +21 | 461 | 12 |
| all | 3339 | 2267 | +341 | +107 | +73 | +111 | 3005 | 334 |

- Registers alone are worth 341 tokens, 184 of them in the two clone runs (T1, C1).
- Spill-slot numbering is worth 107, 82 in T1/C1. That is the w17a04 lever: StackSlotColoring sorts spill intervals by
  weight.
- Alloca offsets are worth 73, nearly all in validate/join (V1 14, V3 16, J2 13, J1 7, V2 7). That band is untouched by the
  other w17 lanes, and the frame map below says exactly why it differs.

## Why whole-region rewrites collapse: one frame host changes and everything below it moves

`framemap.py` shows main's frame is the original's host structure almost slot for slot. Every host start offset in main
(`frame-main-7d5e14d.txt`, -0x1 down to -0x8d0) is also an object start in the original's access map (w17a01
`frame_map.json`), with one exception: main's long-lived PDA tuple `hk` (33 B at -0x679, kept alive on purpose since
#3011). It fills exactly the space where the original accesses a 9 B object at -0x668 (new[24..33)) and a 24 B one at
-0x680. What differs elsewhere is which allocas StackColoring merges into which host.

So any change that adds, removes or resizes a host shifts every alloca below it, and with them all the spill slots.
That moves nearly every frame token. `fshift.py` on this lane's trials:

| trial | change | exact LCS | rfj LCS | dominant frame delta |
| --- | --- | ---: | ---: | --- |
| vr | validate returns `Result<Option<Pubkey>>` | -878 | -51 | allocas -0xb..-0x450 +8, spills -0x18/-0x10 |
| p8 | validate returns `Result<P8>` (`repr(C,align(8))`) | -748 | -11 | allocas +8 (773 of 981), spills +8 |
| sut | sharing payload `Some(Some(target))` | -384 | -35 | spills scattered (RA) |
| b01 | validate takes `holder_key` by value | -277 | +0 | allocas -8 below -0x548 (139), spills -8 (188) |

The structure of these variants is close to main (rfj -51..+0), but the exact score drops by hundreds. Earlier lanes
recorded the same "collapses" without a frame map (for example b01 at -428 M on 9120883 and S3n).

### b01 is the right recolouring for validate, and it breaks on one 7-byte object

On 7d5e14d, `framemap.py` for b01 (`validate(..., holder_key: Pubkey, ...)`) gives:

- the by-value holder_key copy (`_52`, 32 B) joins FI47 at -0x518, where the original keeps hk2;
- `sk1` moves to FI39 at -0x470, where the original keeps sk2;
- the validate error-name Strings (`_44.i _34.i _24.i _12.i buf.i35/42/49.i`) move to FI40 at -0x488, where the original has
  them (V1 +7 exact, V3 +8 frame-masked, E3 +3/+6).

The recolouring cascades down the 24/16 B hosts:

- FI45 takes `_83/_68/_56.i`;
- FI46 takes `_48.sroa.11`;
- FI52 takes `target.i.sroa.9`;
- FI54 takes `target.sroa.8`.

At the end, validate's 7-byte target piece `target.i.sroa.0` has no host left and becomes a new one (FI94, 8 B at -0x548).
Everything below it moves 8 bytes down. With frame offsets masked b01 is -81 (T1 registers -33), so it also perturbs
register allocation. A b01 that keeps the frame needs a home for that 7 B piece (or one 8 B host fewer below -0x548).
`capvar.sh` shows the effect of each attempt in about one build.

## Data-flow findings (post-opt IR of main + Ghidra pseudo-C)

- **The 8-byte piece boundaries come from `Result<Pubkey>`.** `validate` returns `Result<Pubkey>`: the tag is at 0, the
  Pubkey at 1, and the Err payload is an i64 pair at [8,24). SROA therefore splits the returned target into
  [1,8) 7 B, [8,24) and [24,33) 9 B pieces: main's `target.sroa.0/_48.sroa.11/target.sroa.8` and `target.i.sroa.0/9`.
- **The original has the same "offset-1" pieces, but on the sharing payload and on `new` at E3, not on target.**
  - Original `new` pieces at E3: [1,8) to -0x658, [24,33) to -0x668, [8,16)/[16,24) in registers. They are loaded before
    the mayhem test, at the validate call.
  - Sharing-payload pieces: -0x550/-0x560 at J2, -0x650.. at the C1 CPI arg.
  - The original's target travels as 4 aligned u64 words: -0x918 spill, -0x530, -0x528, -0x520, and the J2 copy at -0x580.
  - Main has the roles swapped: target gets the offset-1 pieces and the sharing payload is a 32 B blob (`sharing_update16`,
    `val8`). Moving the pieces by source (vr, p8, w4, sut) is structurally neutral but collapses the frame (table above).
- **`Ok::<_,Error>((target,sharing_update,cashback))?` is folded away.** Re-carrying it as `repr(C)` or
  `repr(C,align(8))` structs is byte-identical (j1, j8), so that round trip cannot steer SROA.
- **`black_box(&new)` keeps the E3 copy (E3 +5, V1 +8) but its memory clobber wrecks everything after it** (bba, bbb:
  T1 -479, +184..+280 B).
- **Validate error-block layout** (`blk.py` on the Ghidra CFGs):
  - original: 289, 306, 298, 326, 296, 312/307 (outlined to_string, one block each), 330, 338, 334;
  - main: 298, 296, 289, 326, 312, 306, 307, 330, 338, 334.

## Next

1. **Frame-preserving b01.** b01 is the faithful recolouring (sk2/hk2/name temps where the original has them). Find a
   home for `target.i.sroa.0` (7 B) so that no new host appears. One way is a validate target spelling whose [1,8) piece
   merges like main's (FI54). Another is to drop one 8 B host below -0x548 (the 7 B `target.sroa.0` at -0x658 is the
   candidate: the original has new[1..8) there). Then compare b01's frame-masked gain (+8 V3, +7 V1, +6 E3) against its
   T1 register loss.
2. **`hk` is a frame stand-in.** The 33 B PDA tuple at -0x679 holds the space of the original's 9 B new[24..33) host and
   24 B target-copy host. A faithful E3 copy of new plus the J2 target copy would make `hk` short-lived (PDA first, as
   the original does) without moving the frame, if their sizes and frame indices land in that slot.
3. **Score structure with the frame masked.** `rc.py --mask f` (or `a`/`s`) separates real structural gains from frame
   shifts. A variant that wins under `f` is worth a compensation search, and `framemap.py` shows exactly which host moved.
