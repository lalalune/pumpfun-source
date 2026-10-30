# w13a04-cto-tostring296: outlining `to_string` at 307/312 (admin_cto)

Target: `0x22a10 admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: outline the two inlined `to_string` calls at 307/312 (the 2 extra `lddw` / `.rel.dyn` entries, the last
non-`.text` ELF difference), then repay the lost bytes with the original's data flow.
Bases: main 3912c47 (0.48772), 085e5df (0.48922), 4394685 (0.49071). Ledger keys `0x22a10-w13-<sha7>-tostring296-*-v1`.

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

## Tools (`tools/`)

- `gv.py <name> <base> GENE..`: crate copy with genes from `genes.py` applied (line count asserted).
- `run.sh v1 [v2]`: measure.sh up to two variants, then chunk-structure score and `ToString` call count.
- `mratio.py orig_fn cand..`: exact / frame-masked / +jump / +register-masked ratios.
- `padalloca.py`, `addprof.py`, `llco.sh`: raw-IR frame-pad and branch-weight oracles (llc-only path ~5 s).
- `mkann.sh <so> <out>`: annotated listing (uses w12a06 `ann.py`); `clen.py`: per-call-chunk instruction deltas.
- Also used: w12a06 `capraw.py`/`oracle.sh`/`objfn.py`/`oratio.py`/`errsites.py`, w12b11 `chunks2.py`/`framedelta.py`.
