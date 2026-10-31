# w15a14-cto-holder465: is `!holder` %465 the upstream end of the wallet register chain? (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 90300f9d2 (`programs/pump/src` is unchanged up to b8586325a): 0.67346, M 2,248, skM 2,810, 3,124 slots, 1034/1034.
The post-opt capture `rx/m0/m.ll` (from w15a05) reproduces main exactly, with stock llc and with w14a84's private RAPRIO llc.
Angle: next idea #2 of w15a05 (#3643) and of w14a116 (#3517). The claim was that `%465 = !holder` holds r9 at greedy step 322,
so the ATA buffer %742 takes r7, the accounts piece %1671 takes r8, and so on down the wallet.
Ledger: approach `holder465`, keys `0x22a10-w15-90300f9-holder465-*` (8 IR/RA rows, 2 source rows, 2 climb/oracle rows).

**Result: notes only, no gain. The claim is false as an upstream lever.** Removing %465 never frees r9 for %742. Whatever is
the next long head-to-tail interval in the queue takes r9 instead: `st.cashback` %466, then the fee value, then the sharing tag
%56. r9 is free at D %742 only when all four are spilled. At that point %742 does take r9 and the accounts piece does load into
r7, as in the original, but M drops by 256. The wallet partner forces (`1671=r7` and do_coin `1864-1868=r8`) are worth the same
+0.0033 to +0.0036 on every base. So the partner is independent of %465. No joint cell comes near main + 15 M.

## 1. IR removals of %465 (post-opt edits, llc only; `tools/irmk.py`)

The cashback is `%cashback = and i1 %_0.sroa.0.0.off0.i.not, %extract.t` in the head. Its zext `%170` is at the
validate-exit join bb25, and its only use is the curve store in bb37. MachineSink moves the `and`/zext to bb37, so both
operands stay live from the head to bb37.

| edit | what | ratio | bytes | M | skM | L2 | wallet colouring |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| m0 | main | 0.67346 | 27,400 | 2,248 | 2,810 | 0.7855 | buffer r7, accounts r8 |
| rc / rch | `!holder` recomputed from the arg `%0` at bb37, `st.cashback` i1 from the head | 0.57674 | 27,368 | 1,924 | 2,871 | 0.77998 | unchanged; r9 at D742 = `%10` (sz 44,656) |
| rcl | `!holder(%0) && reload of the curve byte` at bb37 | 0.57537 | 27,384 | | | 0.77944 | unchanged |
| rclz | `select(!holder, reloaded curve byte, 0)` at bb37 | 0.57580 | 27,344 | 1,920 | 2,867 | 0.78003 | unchanged; r9 at D742 = fee `%388` (sz 49,056) |
| sj / sj8 | cashback stored to a new i8 / i64 alloca at bb25 and reloaded at bb37 (the original's `[r10-0x958]` def) | 0.56907 / 0.27808 | 27,272 | | | 0.775 | |
| nosink | `llc -disable-machine-sink` (global; not single-value) | 0.4766 | 27,504 | | | 0.593 | |

- Every removal gains skeleton (skM +57 to +61), but loses 320+ M. The frame loses a spill slot (113 slots at or below
  -2264, against 114 on main and 115 in the original), so every deep slot from -2336 to -3120 moves by 8 or 16 B
  (`tools/fmap.py`, `tools/frs.py`).
- The spill-permutation bound (w15a08 `relab.py`, `tools/mp.py`) confirms this is not a colouring accident: Mperm is 2,177
  for rc and 2,179 for rclz, against 2,292 for main. Inserting the missing 8 B slot at its best depth (`tools/ins.py`) gives rc only
  M 2,051.

## 2. Register-level removal (private RAPRIO llc `RAPRIO_FORCE`, `tools/grid.sh`)

| base | none | + accounts 1671=r7 | + do_coin pieces=r8 | + both |
| --- | ---: | ---: | ---: | ---: |
| main | 0.67346 @27400 | 0.67555 | 0.67496 | **0.67705** |
| rc (IR) | 0.57674 @27368 | 0.57884 | 0.57794 | 0.58004 |
| rclz (IR) | 0.57580 @27344 | 0.57760 | 0.57730 | 0.57910 |
| 465=spill | 0.66037 @27392 | 0.66217 | 0.66187 | 0.66367 |
| rc + 10=spill | 0.56672 @27352 | 0.56642 | 0.56248 | 0.56218 |
| rclz + 388=spill | 0.54156 @27408 | 0.54649 | 0.54208 | 0.54799 |

The wallet vregs are re-identified on each base (`tools/wv.py`: the first load at `%bb24.i` and the do_coin cluster
around `rp 97.1`).

**The r9 refill chain** (spill whatever long interval holds r9 at D %742, then repeat):

| spilled | r9 at D742 | %742 gets | accounts piece | ratio | bytes | M |
| --- | --- | --- | --- | ---: | ---: | ---: |
| 465 | %466 st.cashback (sz 45,486) | r7 | r8 | 0.66037 | 27,392 | 2,204 |
| 465,466 | %389 fee (sz 49,072) | r7 | r8 | 0.66037 | 27,392 | 2,204 |
| 465,466,389 | %56 sharing tag (sz 43,948) | r7 | r8 | 0.62455 | 27,432 | 2,086 |
| **465,466,389,56** | free (short pieces only) | **r9** | **r7** (`ldxdw r7,[r10-2272]`) | 0.59793 | 27,296 | 1,992 (Mperm 2,163) |
| + 1625 | %384 holder arg | r6 | r7 | 0.46878 | 27,544 | 1,569 |

So the original's wallet colouring (buffer r9, accounts r7) follows from a free r9. Reaching it takes four long-lived values
out of registers, not one. The original has no such intervals because holder and cashback are spilled per-arm phis
(`[r10-0x950]` / `[r10-0x958]`; the cashback slot is stored at 0x0db8, 0x1138, 0x1850 and 0x18b8, and loaded as `ldxdw r4,[r10-0x958]; and64 r4,1` at the curve store, 0x4aa8), and that is the per-arm phi family that
w13a38, w15a08 (`cbphi`, Mperm 2,118) and w14a142 already priced as losses.

**s465 skeleton note (new):** with %465 spilled, the sharing clone run at orig 0x3ec0-0x4360 aligns at skeleton level
(+63 skM, `tools/skd.py`), because the clone pieces spill at their def as in the original. The gain is not kept at M:
the 8 B shrink, the frame order and register naming cancel it. Colour-force climbs (top-40 colmap singles, 6 rounds,
`tools/climb2.py` with `BASEF`) priced it:

| climb | result |
| --- | --- |
| main, `--size 27400` | 0.67346 -> **0.68155** @27400 (1684=r6, 1671=r7, 1906=r6, 1617=r3, 1706=r4, 1384=r5) |
| 465=spill, any size | 0.66037 -> 0.67725 @27432; no 27,400 cell above main |

So s465 is dominated by 0.0043 at an equal number of forces.

## 3. Ordinary-source forms that end %465's interval (raw-IR capture + opt/llc, w15a05 `cs.sh`)

| trial | form | bytes | M | ratio | skM |
| --- | --- | ---: | ---: | ---: | ---: |
| cbcurve | `curve.is_cashback_coin=!holder.unwrap_or(false)&&curve.is_cashback_coin` (state re-derived; no head cashback) | 27,168 | 1,821 | 0.54792 | 2,817 |
| cbhv | block `cashback=st.cashback` (tuple-carried), `curve.is_cashback_coin=cashback&&!holder.unwrap_or(false)` | 27,256 | 1,851 | 0.55602 | 2,824 |

Both are worse than their IR oracles (rcl / rc), because MIR also reshapes the head. These forms were screened even though
the task's precondition (a joint cell of main + 15 M) does not hold. They show the source side is no better than the oracle.
The other options the task lists are covered elsewhere: the tuple-carried cashback is already on main (#2766 form). For the
`#[cold]` / non-inlined helper, see the w15a05 s1/s2 rows: a by-value bool helper outlines the wallet. For validate
returning the per-arm cashback, see the w13a38, w13a04, w12a06 and w15a02 T_pcb rows, and w15a08 `cbphi`.

## 4. Reading / next

- Drop "%465 is the upstream lever". The wallet rotation is set by how many long head-to-tail intervals compete for the
  callee-saved registers at step 322: !holder, st.cashback, fee, and sharing tag. Only all four together change it, and the
  original avoids all four by keeping holder and cashback as spilled phis. That is a whole-region shape (the original's
  per-arm validate), not a single-value lever.
- The wallet partner is still worth +0.0036 as isolated naming (w15a05). Its source must come from the queue, not from
  %465.
- Main's 6-force colour climb reaches 0.68155 at 27,400 (1684=r6 first). This is the current RA-only ceiling on main's code shape,
  matching w14a116's 0.68185 on ebe5387.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `irmk.py <name>..`: the section-1 post-opt IR edits on `rx/m0/m.ll`. The dead `%170` is kept, so unnamed value numbering stays valid.
- `grid.sh <name> <m.ll> [base-force]`: colmap (with the base force), wallet vregs (`wv.py`) and the 4-cell partner grid.
- `wv.py <colmap prefix>`: the accounts piece at `%bb24.i` and the do_coin pieces, as force strings.
- `mp.py <name> <m.ll> [force]`: object, PEI MIR, M, and Mperm (needs w15a08 `relab.py` beside it).
- `ins.py <dir>`: inserts one free 8 B frame slot at every depth and reports the best M.
- `fmap.py a.bin b.bin`: per original frame offset, the hits in a against b on skeleton-aligned instructions.
- `frs.py`: frame offset census. `skd.py a b lo hi`: skeleton hit and miss differences per original offset.
- `climb2.py`: w14a143 `climb.py` with a `BASEF` force prepended to every cell.
- `cbcurve.py`, `cbhv.py`: the section-3 source edits (EDITS format for w15a05 `cs.sh`).
