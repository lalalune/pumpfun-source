# w15a19-cto-c1b01frame: c1 x b01 x {v01, g1, g3} composite grid (notes only, no gain)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 86e2a6b74 (0.67376, 3,124 slots, M 2,249). `programs/pump` is unchanged on 9120883a9.
Angle: a joint composite of w15a09's per-arm cashback gene `c1` (#3668) and w15a11's `b01`, which passes `holder_key` to
`validate` by value (#3683). The hypothesis was that their two standalone losses are frame shifts in opposite directions
and cancel. Ledger: approach `c1b01frame`, keys `0x22a10-w15-86e2a6b-c1b01frame-<cell>-v1` (46 rows).

**Result: the shifts do not cancel. The hypothesis is false.** c1 does not shift the alloca frame at all. Its loss is
register assignment. b01's shift is a new 7-byte alloca that pushes every alloca below it 8 B deeper. The two act on
different parts of the frame. Combining them also adds a layout break of its own, worth -45 true-LCS tokens. No cell of
the 46-cell grid reaches main on M, Mperm or the alloca-shift + spill-permutation bound. Main is still the best zero-loss
measurement: 0.67376 @27,400.

## Method

- **Oracle:** w15a11's raw-IR capture + SDK `opt -O3` + `llc` (`tools/cv2.sh`, `t2/rx.py`). `m0`, the unedited capture,
  reproduces main exactly (`eq_main: true`, 0.67376 @27,400).
- **Metrics:**
  - true-LCS `---`/`rfj` deltas per orig 0x800 chunk (`tools/evall.py`, the whole-function version of w15a11's `ev.py`);
  - Mperm / Mhc (`tools/relab.py` + `tools/permhc.py` from w15a08, on a `llc -stop-after=prologepilog` dump, via `tools/mp.sh`);
  - r10-offset delta histograms over matched pairs (`fhist.py`, `fpair.py`);
  - a new joint bound, `tools/shperm.py`: undo an alloca-band shift, then find the best spill-colour permutation;
  - a frame-object diff, `tools/fobj.py`.
- **Grid** (`tools/gen2.py`):
  - cashback form ∈ {main, c1, c2, c5, c6};
  - key form ∈ {main, b01, b02 = b01 + v01 (312 holder-first)};
  - creator binding ∈ {main, g1, g3}.

## 1. Grid (main: M 2,249, Mperm 2,293, Mhc 2,300, true-LCS `---` 2,255 / `rfj` 3,007)

c1, c2, c5 and c6 give identical bytes in every combination, so only the c1 rows are listed (`data/grid.jsonl` has all of them).

| cell | ratio @ bytes | M | Mperm | Mhc | true-LCS `---` / `rfj` | rfj chunk deltas (orig) |
| --- | --- | ---: | ---: | ---: | --- | --- |
| main (m0) | 0.67376 @27,400 | 2,249 | 2,293 | 2,300 | 0 / 0 | |
| c1 | 0.56379 @27,288 | 1,878 | 1,979 | 1,979 | -342 / -12 | small, spread over 0x2800-0x6800 |
| b01 | 0.54595 @27,360 | 1,821 | 2,063 | 2,067 | -268 / 0 | 0:+5 |
| b02 (b01+v01) | 0.54744 @27,360 | 1,826 | 2,068 | 2,072 | -266 / 0 | 0:+5 |
| **c1b01** | 0.56890 @27,344 | 1,897 | 2,030 | 2,030 | -275 / **-50** | 0:+5 **4800:-45** 5800:-9 |
| c1b02 (c1+b01+v01) | 0.57040 @27,344 | 1,902 | 2,035 | 2,035 | -273 / -50 | same as c1b01 |
| g1 | 0.67284 @27,520 | 2,251 | 2,290 | 2,297 | +2 / +7 | 0:+2 1000:+2 1800:+2 |
| g3 | 0.67265 @27,464 | 2,248 | 2,292 | 2,302 | -1 / +3 | |
| b01g1 / b02g1 | 0.529 / 0.531 @27,464 | 1,768 / 1,773 | 2,022 / 2,027 | 2,027 / 2,032 | -303 / 0 | |
| b01g3 / b02g3 | 0.532 / 0.534 @27,416 | 1,778 / 1,783 | 1,973 / 1,978 | 1,990 / 1,995 | -330 / +7 | 0:+6 |
| c1g1 | 0.56282 @27,352 | 1,877 | 1,977 | 1,977 | -343 / -3 | |
| c1g3 | 0.47694 @27,600 | 1,598 | 1,700 | 1,700 | -630 / -513 | 2000..5000 collapse |
| c1b01g1 / c1b02g1 | 0.530 / 0.531 @27,472 | 1,770 / 1,775 | 2,024 / 2,029 | 2,026 / 2,031 | -323 / -41 | 4800:-45 |
| c1b01g3 / c1b02g3 | 0.533 / 0.534 @27,504 | 1,782 / 1,787 | 2,024 / 2,029 | 2,025 / 2,030 | -337 / -36 | 4800:-45 |

Notes on the grid:
- On 86e2a6b, c1 lands at 27,288 B, not the 27,264 B that w15a09 measured on 90300f9.
- c1b01 is 27,344 B, about 56 B under the pin, as the angle expected.
- Step 3 of the angle (spend the byte room on faithful +B forms) required Mperm(c1+b01) > 2,299 or a true-LCS gain over
  main. Mperm is 2,030 and true LCS is -275 / -50, so step 3 was not run.
- Only b01g3 and b02g3 (+7 rfj, at 27,416 B) and g1 (+7 rfj, at 27,520 B) have a skeleton above main's. Both sit
  230-300 M below main in M, and below it in Mperm (b01g3) or level with it (g1).

## 2. Why the frame shifts do not cancel

`data/fhist.txt` histograms the r10-offset delta (orig - cand) over true-LCS-matched memory instructions.
`data/fpair-main-c1-b01-c1b01.txt` gives the orig-to-cand slot maps from orig -0x4f0 to -0x9a0.

| build | r10 pairs equal | +8 (cand 8 deeper) | -8 | regs-equal pairs |
| --- | ---: | ---: | ---: | ---: |
| main | 963 | 24 | 22 | 2,542 |
| c1 | 881 | 41 | 57 | **2,210 (-332)** |
| b01 | 760 | **202** | 30 | 2,478 (-64) |
| c1b01 | 819 | 104 | 47 | 2,385 (-157) |

- **c1 leaves the alloca band alone.** In the band orig -0x535..-0x8d0, every slot maps to the same offset in c1 as in
  main. c1 removes one spill slot (107 against 108) and renumbers the spill region (orig -0x930 -> c1 -0x918). Its loss
  is registers: 332 fewer register-equal pairs. Mperm, which permutes spill colours freely, still leaves it 314 M below
  main (1,979 against 2,293). This is the `!holder` (`%465`) live-range change of w15a14 #3673 and w15a12 #3686, written
  as source. Those lanes bound it below main (joint bound 0.66367).
- **b01's shift is one new alloca.** The frame-object diff (`data/fobj-main-vs-b01.txt`, via `tools/fobj.py`) shows
  b01 adds `%target.i.sroa.0 = alloca [7 x i8]` at -0x548. It is a 7-byte SROA piece of validate's inlined `target`. Its
  7-byte memcpys come from `new` and from `hk` (the PDA result), and it is copied into execute's `target.sroa.0`. Stack
  coloring does not merge it, so every alloca from `sharing_update16.sroa.3` (-0x560 -> -0x568) down to the last 16 B
  object (-0x8d0 -> -0x8d8) moves 8 B deeper. The object count is otherwise the same. Main's alloca band from orig -0x548 down
  to -0x8d0 already equals the original's offsets. So the original has no unmerged 8 B object there, and this shift
  has nothing to cancel against.
- **The joint bound stays below main.** `tools/shperm.py` undoes the +8 over (-0x8d8, -0x568], leaving spill slots alone,
  then runs the vote/assignment permutation plus the swap climb over spill colours:

| cell | M | after alloca unshift | + best spill perm (Mshperm / Mshhc) | ratio at Mshhc |
| --- | ---: | ---: | --- | ---: |
| main (shift 0) | 2,249 | 2,249 | 2,293 / 2,300 | 0.68904 |
| b01 | 1,821 | 1,945 | 2,150 / 2,155 | 0.64608 |
| c1b01 | 1,897 | 1,950 | 2,083 / 2,083 | 0.62468 |
| c1b02 | 1,902 | 1,958 | 2,091 / 2,091 | 0.62708 |

  Even with a perfect frame (alloca shift undone and spill colours at their best), b01 is 145 M below main and c1b01 is
  217 M below. The rest is register naming and the layout break below. For comparison, every RA-only bound on main's
  structure is +9 to +27 M: w14a84 RAPRIO 0.68155, w15a12 sticky +9 M.
- **c1+b01 adds a layout break that neither piece has alone** (`data/sbs-c1b01-orig4800-unmatched.txt`). The
  original's curve-state store block sits at orig 0x4aa0-0x4c50:
  - it starts at `jne r7,2`;
  - it reloads `[r10-0x958]`;
  - it runs the `stxb [r1+0xa5]`/`[r1+0xa3]` creator, holder and cashback flag stores, then the `0x1b79ff` memcmp.

  In c1b01 this block moves ahead of 0x3d40 and is reached by `jeq r9,2,3d40`, which costs 45 rfj tokens in orig
  0x4800-0x5000. c1 alone keeps the block in place (-12 in total), and so does b01 alone (0). The per-arm cashback
  phi feeds this block. Why it moves only in the combination was not isolated.
  The g1/g3 variants keep the break.

## 3. Verdict and pointers

- The c1 x b01 composite is dominated. Its pieces lose for unrelated reasons: c1 on registers, b01 on one unmerged
  alloca plus registers. Together they also break the curve-store layout. No size knob or RA climb can close a 200+ M
  gap, so step 4 (the private RAPRIO climb) was not run. The patched llc from w15a12 is no longer on disk.
- The b01 alloca is a concrete, fixable residual for any lane that keeps holder_key by value. The original's
  alloca band equals main's, so the 7-byte `target.i.sroa.0` must disappear or be merged by stack coloring. One way is a
  spelling where validate's target is not SROA-split away from execute's target, for example by not memcpy-ing
  `hk`'s first 7 bytes into a validate-local. Even then, b01's joint bound is 0.64608, below main.
- The only cells whose skeleton beats main are g1 (+7 rfj) and b01g3/b02g3 (+7 rfj). That is +0.2% of 3,007 tokens, and
  M stays 230-300 below main.

## Tools (`tools/`, experiment only)

- `gen.py`, `gen2.py`: the edit sets (`gen2.py '[["","c1",..],["","b01","b02"],["","g1","g3"]]'` writes the whole grid).
- `cv2.sh`, `bat.sh`: w15a11's capture + oracle runner (paths changed to this lane).
- `evall.py`: true-LCS totals and rfj deltas per 0x800 chunk over the whole function.
- `mp.sh <rx>...`: `pei.mir` dump plus `permhc.py` (Mperm / Mhc). `relab.py` is w15a08's, adapted to `oracle.py`.
- `shperm.py <rx> <lo> <hi> <d>`: the joint bound (alloca band shifted, then best spill colouring).
- `fobj.py <a.mir> <b.mir>`: side-by-side frame objects with names, plus spill counts and ranges.
- `rec2.py`: ledger rows with M / Mperm / Mhc and true LCS.
