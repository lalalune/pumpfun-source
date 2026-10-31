# w15a35-cto-pdafceiling: is the PDA-first collapse RA-recoverable? (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9120883a9 (origin/main 5b18ab780 has the same `programs/`): 0.67376, 3,124 slots, M 2,249, 1034/1034.
Angle (a wave-15 lane, run in wave 16): price the holder-rewards PDA-first head (w15a11 class A, 23 orig-only tokens at
orig 0x80-0x140) with the two tools the earlier PDA lanes did not have. These are w15a18's patched-greedy RA ceiling (queue
priority, cascade and spill-weight overrides, with no physreg pins) and w15a16's Mperm. The kill test: if PDA-first's greedy
ceiling is not above main's on the same tool, write the table and stop.
Ledger: approach `pdafceiling`, keys `0x22a10-w15-9120883-pdafceiling-*-v1`.

**Result: kill test met. Notes only, no source change.** PDA-first's best greedy-decision allocation is
M 2,206 @27,368 (0.66127, 5 decisions; the rescreen climbs were still running at this push). Main's ceiling on the same tool is M 2,260 @27,384 (5 decisions), and its whole-pool rescreen adds one decision for M 2,261 @27,368 (0.67776). Every PDA-first
cell is also below main on Mperm, Mhc and the legal tail-pin cells. PDA-first is skeleton-neutral: with registers and frame
masked it is main +1 true-LCS token (rf-), and main +12 with jumps masked too (rfj). So even a perfect allocation could not
make it more than about 12 tokens better than main's own perfect allocation. Class A is closed as an RA-only head order:
its +25-token entry gain is real, but the RA cost it starts (about 290 tokens over orig 0x2000-0x4800) is not recoverable
by greedy decisions, and no source lever is worth looking for.

## 1. Captures on 9120883 (raw-IR oracle: capraw + `opt -O3` + `llc`; `n0` gives `eq_main: true`)

Head orders: S = main's `shared` chain, L = creator-left `shared` (w14a09/w14a93 hL), P = holder-rewards PDA,
Q = `quote_locked`, F = curve bool locals read right after the head (w14a93 fl). `genes_pf.py` builds them on main's source.
True LCS is w14a128's DP (`lcschunk.py`): `---` unmasked, `-f-` frame masked, `r--` registers masked, `rf-` both, `rfj`
also jumps.

| variant | head order | bytes | M | ratio | Mperm | Mhc | `---` | `-f-` | `r--` | `rf-` | `rfj` |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **main `n0`** | S P Q | 27,400 | **2,249** | **0.67376** | **2,293** | **2,300** | **2,255** | **2,488** | **2,600** | **2,888** | **3,007** |
| `X_pdaf` (`m_pdaf`) | P S Q | 27,400 | 1,939 | 0.58089 | 2,024 | 2,024 | 1,976 | 2,234 | 2,495 | 2,889 | 3,019 |
| `X_pdaf3` (`m_pdaf3`) | P S Q | 27,400 | 1,938 | 0.58059 | 2,023 | 2,023 | 1,975 | 2,228 | 2,494 | 2,884 | 3,014 |
| `X_crl2pdaf` (`m_pdaf+m_crl2`) | P S Q | 27,464 | 1,938 | 0.57989 | 2,023 | 2,023 | 1,975 | 2,234 | 2,494 | 2,890 | 3,020 |
| `o_PLQ` (pda+hL) | P L Q | 27,400 | 1,939 | 0.58089 | 2,024 | 2,024 | 1,976 | 2,234 | 2,496 | 2,890 | 3,020 |
| `o_PQS` | P Q S | 27,352 | 1,947 | 0.58381 | 2,137 | 2,146 | 2,042 | 2,379 | 2,424 | 2,852 | 2,985 |
| `o_PQSF` (= `o_PQLF`) | P Q S F | 27,360 | 1,858 | 0.55704 | 2,143 | 2,151 | 2,014 | 2,366 | 2,405 | 2,847 | 2,975 |

Per-chunk true LCS of `X_pdaf` against main (orig 0x800 chunks):
- `---`: 0x0 +12, 0x2000 -13, 0x2800 -44, 0x3000 -121, 0x3800 -62, 0x4000 -28, 0x4800 -9, other chunks -5..+1.
- `rf-`: 0x0 +25, every other chunk -5..+1 (total +1).
- `rfj`: 0x0 +24, the rest -4..+1 (total +12).

Readings:
- The plain PDA-first order (P S Q, which is `m_pdaf`, `m_pdaf3`, `crl2+pdaf` and `o_PLQ`) has main's skeleton: `rf-` +1,
  `rfj` +12. The +25 `rf-` tokens at orig 0x0-0x800 are the class-A gain. About -24 small losses are spread over
  0x1800-0x6800, and 11 of those are jump offsets.
- Its whole loss is allocation. With the frame masked it is -254 tokens (registers), and with registers masked it is -105
  (frame), mostly in orig 0x2800-0x4000. Mperm, the best legal relabel of the build's own spill slots, recovers only
  +85 of the 310 M.
- Moving `quote_locked` ahead of `shared` (o_PQS, o_PQSF, w14a93's best order on 963d1ee) gives a worse skeleton: `rf-` -36
  to -41. On today's main those orders are 0.557-0.584, not 0.653.

## 2. The head mechanism, re-traced on 9120883 (`tools/evx.py`)

The private llc logs every greedy decision. `evx.py` names the head vregs from the pre-greedy MIR.
- Main: `curve@%0` is a 96-slot interval (main reloads the curve pointer after the PDA call). The sharing pointer takes R7
  at step 20, and `%0` (the accounts pointer) keeps R8 until step 423.
- PDA-first: the curve pointer (`%5 = LDD %0,56`, 18 uses, size 7,358) is live from the `shared` memcmp through
  `quote_locked` and the CtoState loads. It is dequeued at step 9 and takes R7. At step 22 the sharing pointer evicts `%0`
  from R8: `%0`'s weight is 1.3e-4 against the sharing pointer's 2.0e-3. This is w14a93's step-21 eviction, unchanged.
  `%0` is then split, and its big pieces over the TCF and sharing clone runs go to R6/R5 instead of R8.
- Direct head fixes are small:
  - `bot_5` (curve pointer dequeued last) keeps `%0` in R8 at the head. That gives M 1,962 (+23), true LCS +92.
  - `casc_0` (protect `%0`) gives 1,879, and `top_0` gives 1,844.
  - So `%0`'s head eviction is not the whole cascade. The clone-run pieces have their own eviction order.

## 3. Greedy-decision ceiling (`tools/fscr.py`, `fclimb.py`, `rclimb.py`; private RAPRIO llc, no physreg pins)

`fscr.py` is a light version of w15a18's `cell.sh` free cell: one private-llc run to an object, then the scorer's difflib
M. It reproduces w15a18's main cells exactly (base 2,248, `bot_2145` 2,253 @27,392 on 90300f9).
- Singles: top/bottom priority and cascade for all 1,621 queued vregs of X_pdaf, 4,863 jobs (`data/singles-pdaf.tsv`).
  277 raise M, 805 lower it, and the rest are no-ops. The best single is `bot_229` at M 2,098 @27,384 (+159). Main's best
  single on the same tool is +5.
  - The top 24 singles are all TCF / AccountInfo clone-run pieces (`LDD %0,184/192/200`, Rc `lamports`/`data` pointers
    `LDD %x,8/16`, flag bytes), plus one byte of `new` (`%121 = LDB %385,35`).
- Forward climb (top-80 singles, re-scored each round): `bot_229`, `bot_193`, `casc_195` give M 2,114 @27,400, then stop.
- Multi-start climbs from the next five singles reach 2,081-2,116. Starting from the head fix `bot_5`, `+bot_167` gives
  M 2,167 @27,360.
- Whole-pool rescreen climb from `bot_5+bot_167`, re-scoring all 1,104 code-changing singles each round: `+bot_130` 2,185 @27,360, `+bot_2106` 2,195 @27,376, `+bot_1071` 2,206 @27,368 (still running at this push).

| allocation | decisions | bytes | M | ratio | Mperm | Mhc | true LCS `---` | `-f-` | pinV | pinA |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| main as built | 0 | 27,400 | 2,249 | 0.67376 | 2,293 | 2,300 | 2,255 | 2,488 | 2,292 | 2,299 |
| **main greedy ceiling** (w15a18 `c5`) | 5 | 27,384 | **2,260** | **0.67726** | 2,304 | 2,311 | 2,265 | 2,494 | 2,301 | 2,308 |
| main `c5` + rescreen | 6 | 27,368 | 2,261 | 0.67776 | | | | | | |
| X_pdaf as built | 0 | 27,400 | 1,939 | 0.58089 | 2,024 | 2,024 | 1,976 | 2,234 | 1,984 | 1,989 |
| X_pdaf `bot_5` (head fix only) | 1 | 27,368 | 1,962 | 0.58813 | | | 2,068 | 2,385 | | |
| X_pdaf top-80 climb `c3` (`bot_229, bot_193, casc_195`) | 3 | 27,400 | 2,114 | 0.63331 | 2,189 | 2,191 | 2,152 | 2,404 | 2,159 | 2,164 |
| X_pdaf `bot_5 + bot_167` | 2 | 27,360 | 2,167 | 0.64968 | 2,228 | 2,237 | 2,175 | 2,427 | 2,207 | 2,211 |
| X_pdaf `bot_5 + bot_167` + rescreen (3 steps) | 5 | 27,368 | 2,206 | 0.66127 | | | | | | |

- Main's ceiling uses w15a18's 5 decisions (`bot_2145, bot_1617, bot_338, top_2058, casc_2073`; on 9120883 the vreg
  numbering is unchanged). Its whole-pool rescreen with w15a18's 767 code-changing singles adds only `bot_2072` (M 2,261 @27,368) and then stops, so main sits at a greedy local optimum.
- pinV/pinA are w15a18's legal tail-colour-pin cells (`w6/tools/cell.sh`).
- Where the climbed PDA-first still loses (true LCS against main, `---`): for `bot_5+bot_167` (2,175 against 2,255): 0x2800 -23, 0x3000 -39, 0x3800 -7, 0x5000 -6, 0x5800 -7, 0x6800 -11, entry 0x0 +10, 0x1000 +7. For `c3` (2,152): 0x2800 -26, 0x3000 -15, 0x3800 -10, 0x4000 -28, 0x2000 -13.

## 4. Comparison with the other ceilings

| tool | main | PDA-first | source |
| --- | --- | --- | --- |
| greedy decisions (this lane) | M 2,260 @27,384 (0.67726) | M 2,206 @27,368 (5 decisions) | w15a18 tool |
| sticky physreg forces | 0.68244 @27,400 (8 forces) | GPF 0.66667 @27,368 (14 forces) | w15a24, w15a28 |
| sticky forces + perfect spill colouring | Mhc 2,338 | GPF 2,306 | w15a28 |
| colour-target force climb | 0.68085 @27,384 | pda 0.65806 @27,312, o_PQSF 0.66977 @27,336 | w14a93 (on ecea702) |
| legal frame + perfect colouring (rfR) | 2,623 | pda 2,554-2,573 | w14a87 / w14a93 / w15a10 |
| splice bound (PDA head + main tail) | - | main + 0.005 | w14a09 |

All five tools agree: PDA-first's RA-recoverable level is below main's, and the gap is 30 to 150 M on every tool.

## 5. Why the w15a10 non-collapse mechanism does not apply

w15a10's Fa+fl and Fa+V2+qli avoid Fa's *layout* collapse, the w14a127 J flip (validate-exit join placement by MBP). Plain
PDA-first has no layout collapse: its `rf-`/`rfj` skeleton equals main's in every orig 0x800 chunk (within -5..+1 outside
the entry), which leaves no room for a moved block. Its loss is register and frame naming. PDA-first + fl (the original's P S F Q order) does flip J (w14a93), but undoing the flip with
`jfix` still leaves it far below main (w14a93: 0.59240). So there is no MBP chain to transplant. The kill test stops the
lane before the source-spelling step.

## 6. Next ideas (for whoever reopens class A)

- The only head-side lever with a large effect is the curve pointer's live range (`bot_5`: `%0` keeps R8). The original
  reloads the curve after the chain (`ldxdw r9,[r8+0x38]` at orig 0x268). A source form with that reload, a curve pointer
  that is not live across the `shared` chain, is still unfound: w14a93 section 4 tried 14 spellings. Even with it, the
  clone-run decisions in section 3 are needed, and those are spill-weight-density chains like w15a18's s1 ones, with no
  source lever.
- Reprice class A only together with a change that lifts main's own tail RA, so that the clone-run basin is shared.

## Tools (`tools/`, experiment only; they expect w15a16's tool set and w15a18's private llc copied into `$OUT`)

- `fscr.py <m.ll> <jobs.jsonl> <out.jsonl> [n]`: light greedy cell (free M only, one llc run per job). Use w15a18's
  `cell.sh` for pinV/pinA on finalists.
- `mkjobs.py <m.ll> <jobs.jsonl> [ops]`: writes top/bot/casc (or w10/w01) singles for every queued vreg, from `RAPRIO_LOG`.
- `fclimb.py`: forward selection over the top-K singles. `rclimb.py`: rescreen climb that re-scores the whole pool each round.
  Both use the spawn-safe `__main__` guard. On macOS, multiprocessing re-imports the main module.
- `evx.py <m.ll> <tag> [job]`: head-value greedy trace (dequeue step, evictions, `%0` split tree).
- `vname.py <pre.mir> <ralog> v...`: a vreg's defining instruction, block, Q line (size and weight) and use count.
- `genes_pf.py`: the head-order genes (`o_<order>` over S/L/P/Q/F) on main's source, on top of w15a16's library.
