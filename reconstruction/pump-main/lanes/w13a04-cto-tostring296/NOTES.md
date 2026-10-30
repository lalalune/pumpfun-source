# w13a04-cto-tostring296: outlining `to_string` at 307/312 (admin_cto)

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: outline the two inlined `to_string` calls at 307/312 (the 2 extra `lddw` / `.rel.dyn` entries, the last
non-`.text` ELF difference), then repay the lost bytes with the original's data flow.
Bases: main 3912c47 (0.48772), 085e5df (0.48922), 4394685 (0.49071), ea78c08 (0.50929, entry copy of `new` + pfclimb-3). Ledger keys `0x22a10-w13-<sha7>-tostring296-*-v1`.

## 1. The 296 move is exactly the inliner what-if (no other effect)

On main 085e5df, moving only the 296 check into the holder arm (gene `IN296`, the #2370 form) gives **26,968 B, 0.43599**.
The raw-IR oracle (w12a06 `capraw.py` + `opt -O3` + `llc`; reproduces main exactly) with nothing changed except
`noinline` on the two `to_string` call sites at 307/312 in `validate`'s raw IR gives the same **26,968 B, 0.43599**.
So the source move changes nothing but the inliner's cold-call-site decision (w12a06's BFI finding), and the -432 B
is the two inlined `to_string` bodies.

## 2. The outline tax is the frame, not structure

`tools/mratio.py` scores the same difflib ratio as `target_metric.py` with progressively more masking
(frame offsets, then jump offsets, then register names):

| build (main 085e5df) | bytes | exact | frame-masked | +jumps | +regs |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 27,400 | 0.48922 | 0.60605 | 0.69053 | 0.87298 |
| IN296 (= noinline oracle) | 26,968 | 0.43599 | 0.61926 | 0.69414 | **0.88376** |
| IN296 + take306 | 27,104 | 0.46981 | 0.63033 | 0.68484 | 0.85770 |
| ELSEIF296 + take306 | 27,152 | 0.47089 | 0.61471 | 0.69294 | 0.87047 |

With frame offsets masked the outlined build is as close as main, and with registers masked it is the closest build
of all. The whole -0.053 is frame offsets: outlining frees the String/Formatter slots, the arg spills move from
main's `[r10-0x8f8]` to `[r10-0x8f0]` (original `[r10-0x928]`) and the 0x47d..0x540 objects are permuted
(`framedelta.py` main vs outlined: 218 of 412 offsets unchanged).

Frame-padding oracle (`tools/padalloca.py`: one extra escaped alloca at execute entry, raw IR, outlined base):

| pad | arg spill | bytes | ratio |
| ---: | --- | ---: | ---: |
| none | -0x8f0 | 26,968 | 0.43599 |
| 8 B | -0x8f8 (= main) | 26,984 | 0.44763 |
| 48 B | -0x920 | 26,984 | 0.43375 |
| 56 B | -0x928 (= original) | 26,984 | 0.42711 |

Depth alone does not help: the 56 B pad gives the original's spill offset and a lower ratio. The original's
extra frame objects have to sit where the original puts them (see w13a01's exact-IR slot moves).

## 3. Source forms that outline 307/312 (original to_string set, 86 lddw)

| trial | base | bytes | ratio | chunk-struct |
| --- | --- | ---: | ---: | ---: |
| main | 085e5df | 27,400 | 0.48922 | 0.8782 |
| `IN296` (296 inside holder arm) | 085e5df | 26,968 | 0.43599 | 0.8770 |
| `EL296` (`if hr{if !holder{289}} else if holder&&!enabled{296}`) | 085e5df | 27,024 | 0.43553 | **0.8806** |
| `IN296`+`TAKE306` (`validate(mut new)`, `new.take()` at the 306 let-else) | 085e5df | 27,104 | 0.46981 | 0.8693 |
| `EL296`+`TAKE306` | 085e5df | 27,152 | **0.47089** | 0.8706 |
| `EL296`+`TAKE306`+`OVMK` (override also in validate's arm) | 085e5df | 27,272 | 0.46983 | 0.8698 |
| `EL296`+`TAKE306` | 4394685 | 27,224 | 0.46304 | 0.8681 |
| `EL296`+`TAKE306`+`OVMK` | 4394685 | 27,264 | 0.47020 | 0.8672 |
| w13a06 a4 (`matches!(hopt,Some(true))`) | 4394685 | 27,024 | 0.43764 | 0.8541 |
| w13a06 a4 + `TAKE306` | 4394685 | 27,032 | 0.44753 | 0.8712 |

`take()` at 306 is worth +0.034 on top of the outline (it is the original's `ldxb; and64 1; jeq` 306 tag test).
The by-value keys of w12a06 z1 cost -0.005 (`IN296`+`BYVAL` 0.43052). `take()` also at 298 costs 0.005-0.012.

## 4. Things that do not work (all measured)

- A redundant `!holder&&` in front of the 307 (and 312) test, to cool those sites before the inliner and let
  JumpThreading remove it: byte-identical to main (folded before the inliner).
- Shared target override moved into validate's non-holder arm (the original copies `st.creator` there, +30 insns in
  orig chunk 0x0f20): every form collapses (0.17-0.30) because the sweep tail (`transfer_creator_fees_to_pump_v2`
  CPI, native path) is laid out after the post-sweep code. Seen with the transpose gate, `if shared&&holder{..}`,
  a phi `dosweep` flag and main's skip-flag gate. Keeping the override in execute as well (`OVMK`) avoids the collapse.
  In the post-opt IR the sweep blocks' frequencies are the same as main's (`print<block-freq>`), and 1:2000 / 2000:1
  weights on the sweep-exit tag branch do not move the tail: the flip is a machine-level placement effect.
- The z1 composite (296 in arm + `&mut new` take306 + by-value keys + `let su=new`) was 0.47234 on 3912c47
  but 0.39946 on 085e5df (native sweep path moves before the post-sweep code with the skip-flag gate).

## 5. Per-arm cashback (+0.007) and the best outlined builds per main

`CBA`/`CBAO`: `let (target,cashback)=if holder{..(*holder_key,false)}else{..(t,st.cashback)}` (the original computes the
cashback flag inside the non-holder arm right after the 312 compares, orig 0x0d78).

| build | main | bytes | ratio |
| --- | --- | ---: | ---: |
| `EL296`+`TAKE306`+`CBA` (n4c) | 4394685 (0.49071) | 27,232 | 0.46898 |
| `EL296`+`TAKE306`+`OVMK`+`CBAO` (n7c) | 4394685 | 27,320 | **0.47720** |
| `CBR` (validate returns `(Pubkey,bool)`) on n4c / n7c | 4394685 | 26,840 / 27,392 | 0.23759 / 0.23034 |
| n4c genes | ea78c08 (0.50929) | 27,096 | 0.30663 |
| n7c genes | ea78c08 | 27,000 | 0.43331 |
| `EL296`+`TAKE306` / `IN296`+`TAKE306` | ea78c08 | 26,952 / 26,904 | 0.2682 / 0.26421 |

`CBR` (n4r) has the best structure seen (chunk-struct 0.8903, frame-masked 0.638 vs main 0.606) but its exact ratio
collapses: see section 6.

## 6. Frame mechanism behind the outline collapses: the zero-size `unwrap_failed` slot (fi0)

`llc -stop-after=prologepilog` on the oracle's post-opt IR prints execute's stack objects with offsets
(`tools/mirframe.py <file.mir>`). Main keeps a zero-size alloca `_11.i` (the `&()` argument of `unwrap_failed`
inside every inlined `to_string` body) as its own object at `[r10-0x1]`; the original does too (18 `add64 rX,-0x1`).
Below it sits the 48 B `CtoState` at `-0x38`.

- Outlining 307/312 removes two of the ZST's lifetime intervals, so StackColoring can now merge it. On main ea78c08
  the noinline-307/312 oracle gives **0.29897** (26,904 B): the ZST is merged, the emit_cpi `authority_bump` byte
  `_121.i` takes an own slot at 0x449 instead, and every object from `-0x38` to `-0x448` moves 8 B shallower.
  Dropping only the ZST's lifetime markers in that IR gives 0.42443 (bottom restored, objects above 0x449 now 8 B deeper).
- n4r (validate returns the cashback): the same ZST merge. Dropping its lifetime markers: 0.23759 -> **0.45642**
  (frame offsets equal to the original 11 -> 152).
- p4c on ea78c08: 0.30663 -> 0.41898 with the ZST kept.

So a source outline on the newest main must also keep fi0 unmerged (the original does) and keep `_121.i` colored.
A scan that drops the lifetime markers of each of execute's 139 allocas in turn (outlined ea78c08 IR, llc only) finds
no single repair: best `_107.i` 0.43652, the 24 B `val.sroa.6.i`/`ix_data.i`/`inner_data.i`/`_114.i` 0.43622, fi0 0.42443.

## 7. Outline + the 24 B frame lever (w13a07 `nolt:_68`)

w13a07 found that one more unmerged 24 B slot above `holder_key` (e.g. no lifetime markers on execute's
require-410 `PumpError::name` String `_68`) lifts main 4394685 to 0.50869. On the outlined builds (same IR edit):

| build (4394685) | ratio | + 24 B slot |
| --- | ---: | ---: |
| main | 0.49071 | 0.50869 |
| n4 (`EL296`+`TAKE306`) | 0.46304 | 0.49910 |
| n4c (+`CBA`) | 0.46898 | **0.50473** |
| n7c (+`OVMK`+`CBAO`) | 0.47720 | 0.49670 |

The outline stays 0.004-0.012 below main with the same lever, and 168-80 B short.

## Conclusion

Outlining 307/312 is required for the final match (lddw multiset, `.rel.dyn`), and it is structurally neutral or
better, but every source form measured is below main at every base, mostly through frame offsets (8 B bottom
shifts from fi0 coloring and the lost `target.sroa.0` slot). It should be revisited once the frame lanes have the
original's 24 B host slot / 8-24 target split in source: then re-run `EL296`+`TAKE306`+`CBA` (n4c) and check fi0
with `mirframe.py`.

## Tools (`tools/`)

- `gv.py <name> <base> GENE..`: crate copy with genes from `genes.py` applied (line count asserted).
- `run.sh v1 [v2]`: measure.sh up to two variants, then chunk-structure score and `ToString` call count.
- `mratio.py orig_fn cand..`: exact / frame-masked / +jump / +register-masked ratios.
- `padalloca.py`, `addprof.py`, `llco.sh`: raw-IR frame-pad and branch-weight oracles (llc-only path ~5 s).
- `mirframe.py <file.mir>`: execute's frame objects after PEI; `nolt.py`: drop lifetime markers of named allocas.
- `mkann.sh <so> <out>`: annotated listing (uses w12a06 `ann.py`); `clen.py`: per-call-chunk instruction deltas.
- Also used: w12a06 `capraw.py`/`oracle.sh`/`objfn.py`/`oratio.py`/`errsites.py`, w12b11 `chunks2.py`/`framedelta.py`.
