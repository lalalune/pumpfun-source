# w16a15-cto-tcfprofile: TCF clone-run per-clone length profile and the c2 tax (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (admin_cto source = 1f4e396b5): 0.67436, M 2,251, 3,141 slots at 27,400 B, 1034/1034.
Ledger approach `tcfprofile`, keys `0x22a10-w16-1f4e396-tcfprofile-<cell>-v1` (one row per capture, plus
`-census-v1` and `-kill-v1`).

**Result: notes only, no landing. The kill test holds on both counts.**
- 110 raw-IR captures on main (103 single-literal spellings, 6 composites, 1 compile error; 8 singles byte-identical to
  main). No composite fixes 6 or more abort jumps without losing M elsewhere. Under the additive model (exact: splice
  and the six composite captures agree with it to +-1 M) nothing beats main; the best non-main cell is pdoKL
  (`P:doKLRSWE`, jump 19 fixed, M 2,248), and every composite with at least 17 of 41 jumps right costs 275+ M (section 5).
- The c2 marker (accounts+232 Rc pointer in r6, flag temps in r0) appears in none of the 109 spellings, 23 of them
  lamports-first pcva forms (c2 and its neighbour combinations) (section 6).
- Both have the same cause: the per-clone drift is spill code placed by greedy, and its odd 8 B steps come from single
  spills that the literal levers cannot add or remove (section 4). The r6 that the original gives the accounts+232
  pointer is held in main by the through-live `&a.holder_creator_vault` piece (section 6), the head fact that w15a07
  (#3651) bounded below main.

M is the masked difflib match count from the raw-IR oracle (`tools/scr.py`: rsync crate copy, gene, `capraw.py` identity
capture with `-C no-prepopulate-passes`, `rx.py` SDK opt -O3 + llc). `main` reproduces `$BASE` (eq_main).
ratio = 2M / (6676 + (bytes - 27400)/8).

## 1. The abort-jump profile (`tools/prof.py`)

The Rc-overflow abort block is the first TCF clone's `call abort` (orig 0x26e0, main 0x26b0). It is the target of
**41** `ja` jumps, not 25: the 25 TCF clone checks (orig 0x2728-0x3430) **and the 16 sharing-CPI clone checks** (orig
0x3de0-0x45d0) all jump back to it. A jump's displacement is right exactly when the code between the abort block and the
jump has the original's length, so the profile is the cumulative drift `cum[k] = (jump_k - abort) - (orig_jump_k - 0x26e0)`.

Main (cum in B; 0 = displacement right):

| jumps | values | right |
| --- | --- | ---: |
| TCF 0-24 | 8 8 8 0 0 -8 -8 0 0 -8 -8 0 0 8 8 0 32 32 8 16 32 32 24 40 40 | 7 |
| sharing 25-40 | 0 0 0 0 40 40 24 24 16 24 -56 -64 -80 -80 -104 -40 | 4 |

Main has 11 of 41 right. The 4 sharing jumps are right only because the TCF tail (+40) and the gap between the last TCF
jump and the first sharing jump (-40: the TCF CPI struct build, the post-call `jeq r7,2` / `ja` pair that the original
has as three jumps, the sharing head) cancel. So any -8 B TCF variant (every lamports-first pcva form) loses those 4.

**Parity.** In 8 B units, 13 of the 18 wrong TCF jumps have an odd drift (jumps 0-2, 5-6, 9-10, 13-14, 18, 22-24), and
8 of the 12 wrong sharing jumps are odd. An odd drift can only be fixed by a net odd number of 8 B changes before the
jump.

## 2. Per-clone census (`tools/census.py`, `data/census_main.json`)

Segment k ends at abort jump k. Each AccountInfo clone is two segments (lamports Rc, data Rc). Clone order (= original):
1 ctx program (a1 manual), 2 payer, 3 quote_mint, 4 token_program, 5 system_program, 6 associated_token_program,
7 coin_creator, 8 coin_creator_vault_authority, 9 coin_creator_vault_ata (a2 manual), 10 pump_creator_vault,
11 pump_creator_vault_ata (a3 manual, the only data-first clone), 12 event_authority, 13 program (a4 manual).

| seg | clone/part | main-orig B | main-only / orig-only instructions |
| ---: | --- | ---: | --- |
| 0 | 1 dat | +8 | main spills the ctx-program data Rc pointer (`stxdw [r10-0x9c0],r4`); orig keeps it in r0 |
| 3 | 3 lam | -8 | orig spills two held values after clone 2 (`[r10-0x970] r6`, `[r10-0x978] r5`), main one |
| 5 | 4 lam | -8 | orig spills two (`[r10-0x988] r7`, `[r10-0x990] r9`), main one |
| 7 | 5 lam | +8 | main spills two (`[r10-0x988] r7`, `[r10-0x980] r5`), orig one |
| 9 | 6 lam | -8 | orig `stxdw [r10-0x9a8],r6` |
| 11 | 7 lam | +8 | main `stxdw [r10-0x9a8],r7` |
| 13 | 8 lam | +8 | main `stxdw [r10-0x998],r5` |
| 15 | 9 lam | -8 | orig reloads the cvata lamports Rc pointer (`ldxdw r1,[r10-0x9b8]`); main keeps it in r1 |
| 16 | 9 dat | +32 | main loads the cvata key in the data part and shuffles r5/r9 (`mov64 r9,r5`, `ldxdw r5,[r2]`, an extra slot, `ldxdw r5,[r10-0x998]`) |
| 18 | 10 dat | -24 | orig has three dead reloads into r3 (`[r10-0x9b0]`, `[r10-0x978]`, `[r10-0x8e0]`) |
| 19/20 | 11 lam/dat | +8/+16 | pcva clones data first in main (lamports first in orig); four dead reloads vs three |
| 22 | 12 dat | -8 | orig `stxdw [r10-0xbf0],r1` |
| 23 | 13 lam | +16 | main loads and spills the event-authority owner (`ldxdw r8,[r1+0x18]; stxdw [r10-0xbf8],r8`); orig does it after the run |

Every instruction in the run outside the Rc increments is spill code (the flag/owner copies are spills at definition:
`STD_V1 %x, %stack.N` inserted by greedy). The +-8 rhythm over clones 3-8 is the placement of single spills of values
held across one or two clones (the original spills two at clones 3, 4 and 6, main at 5, 7 and 8; the totals are equal).

## 3. Library scans

- `tools/scanprof.py`: abort profile of all 10,463 cached captures (all lanes). Best TCF profile: w15a26
  `k_ev_reset_shared` (19 of 25 TCF jumps right) at 27,264 B; a TCF-window transplant of it into main is M 2,131.
- `tools/tcfsplice.py`: every unique TCF window (1,339) transplanted into main with splice v2 (hunks inside main
  0x2658-0x3b60 only). The only windows above main are forced-RA builds (w16a04 `Ltc2ra` 2,261 @27,424, w16a12 `Tra`
  2,261 @27,376, w16a11 `P0_Tra` 2,258 @27,376, w16a08 `e1p2__ra` 2,255 @27,392, w15a07 `fs_1617_r3` 2,253 @27,400);
  none from a source capture (`data/tcfx_top40.json`, `data/abortprofile_top40.json`).

## 4. Single-literal table (raw-IR captures on main; `data/singles.md`, `data/singles.json`)

Genes (`tools/genes_tp.py`): `P:`/`Q:`/`G:`/`H:` rebuild the pcva (a3) / cvata (a2) / program (a4) / ctx-program (a1)
literal from a field spec over K L D O R S W E (key lamports data owner rent_epoch is_signer is_writable executable;
lowercase = read through the account path, a re-read), `T<n>:` turns the n-th TCF `to_account_info()` field into a
manual literal, `c2` is w15a24's lamports-first pcva. The lever classes:

| class | examples | segment effect | M |
| --- | --- | --- | --- |
| owner-first literal of a `to_account_info()` clone | T0/T2/T3/T4/T6:OKLDRSWE | +16 into clone c's lam segment, -16 out of clone c+1's (the owner copy pair moves one clone earlier) | -2 to -18 |
| cvata (a2) orders | Q:KLDORSWE, LDKORSWE, LKODRSWE, OLKDRSWE, LOKDRSWE | +-16 moves among segs 15/16/17 | -1 to -8 |
| program (a4) orders | G:KLDORSWE, OLKDRSWE, LKDORSWE | seg23 -16/-32, paid in seg24/25 | -3 to -13 |
| event authority literal | T10:LKDORSWE | seg21 -8, seg22 +8 (the only cheap odd move, and it cancels) | -2 |
| pcva data-first paths | P:doKLRSWE, KDoLRSWE (= main), KdOLRSWE, DKOLRSWE | seg19 -16 / seg20 +16; doKL fixes jump 19 | -3 to -15 |
| pcva lamports-first (c2 family) | c2, P:LKDORSWE, KOLDRSWE, LDKORSWE, KLODRSWE, ... | -8 B, segs 19-22; loses the 4 sharing jumps | -14 to -45 |
| RA-disrupting | H:KLDORSWE, T5 (coin_creator), T8 (pump_creator_vault), P:KRSWELDO, P:RSWEKOLD | many segments incl. seg0/seg16 odd moves | -51 to -224 |
| derive-order literal of a `to_account_info()` clone | T0:KLDORSWE, T10:KLDORSWE (on c2) | byte-identical | 0 |

The cheap levers (dM >= -10) are all even moves (+-16 between two segments) except T10:LKDORSWE (+-8 inside clone 12).
Even moves cannot change the parity of any drift, so they cannot fix any of the 13 odd TCF jumps. The odd steps (one
spill more or less in a clone) only appear in RA-disrupting variants, which cost 50-220 M.

## 5. Joint search (`tools/beam.py`, `tools/joint.py`, `splice.py`, captures)

Objective = the full 41-jump profile. One spelling per literal group (H, T0..T10, Q, P, G). Additive model:
pred M = M_main + sum(w_i) + right(cum_main + sum dcum_i) - right(main), where w_i = dM_i - (right_i - right_main) is a
single's non-jump cost. Beam width 5,000 over all groups (exact for the model).

Best predicted composite per number of right jumps (of 41; main 11):

| right | TCF right | pred M | bytes | composite |
| ---: | ---: | ---: | ---: | --- |
| 0 | 0 | 2216 | 27408 | x03_hOKld + t2O + t4O |
| 1 | 1 | 2204 | 27400 | qRSWE + t0O + t6O |
| 2 | 2 | 2225 | 27408 | x03_hOKld + t4O |
| 3 | 3 | 2224 | 27400 | qRSWE + t6O |
| 4 | 4 | 2231 | 27392 | x02_pKdOL + qKLD + t3O |
| 5 | 5 | 2232 | 27392 | x02_pKdOL + t3O |
| 6 | 6 | 2238 | 27392 | x02_pKdOL + qKLD |
| 7 | 7 | 2239 | 27392 | x02_pKdOL |
| 8 | 4 | 2243 | 27400 | qKLD + t3O |
| 9 | 5 | 2244 | 27400 | t3O |
| 10 | 6 | 2250 | 27400 | qKLD |
| 11 | 7 | 2251 | 27400 | main |
| 12 | 8 | 2248 | 27400 | pdoKL |
| 13 | 10 | 2197 | 27376 | gOLK + pKRSWE |
| 14 | 11 | 2196 | 27376 | gKLD + pKRSWE |
| 15 | 12 | 2195 | 27376 | gKLD + pKRSWE + t10L |
| 16 | 13 | 1974 | 27376 | gOLK + pKRSWE + t5O |
| 17 | 14 | 1976 | 27376 | gOLK + pKRSWE + t5L |
| 18 | 15 | 1975 | 27376 | gKLD + pKRSWE + t5L |

Top predicted composites (all at or below main):

| pred M | right | composite |
| ---: | ---: | --- |
| 2251 | 11 | main |
| 2250 | 10 | qKLD |
| 2249 | 11 | t10L |
| 2249 | 11 | t10_LKDORSWE |
| 2249 | 11 | t4O |
| 2249 | 11 | t4_KOLDRSWE |
| 2249 | 11 | t6_KLODRSWE |
| 2248 | 11 | gOKLD |

Composite captures (real builds, RA interactions included) against the model:

| capture | genes | bytes | M | right (TCF/sh) |
| --- | --- | ---: | ---: | --- |
| J_qKLD_t4O | `Q:KLDORSWE+T4:OKLDRSWE` | 27400 | 2248 | 10 (6/4) |
| J_qKLD_t10L | `Q:KLDORSWE+T10:LKDORSWE` | 27400 | 2248 | 10 (6/4) |
| J_t10L_t4O | `T10:LKDORSWE+T4:OKLDRSWE` | 27400 | 2247 | 11 (7/4) |
| J_gOKLD_qKLD | `G:OKLDRSWE+Q:KLDORSWE` | 27400 | 2247 | 10 (6/4) |
| J_pKRSWE_t10L | `P:KRSWELDO+T10:LKDORSWE` | 27376 | 2200 | 13 (10/3) |
| J_gKLD_pKRSWE_t10L | `G:KLDORSWE+P:KRSWELDO+T10:LKDORSWE` | 27376 | 2194 | 15 (12/3) |

## 6. The c2 tax is the through-live `&holder_creator_vault` in r6

Debug-llc regalloc logs (`-debug-only=regalloc` on the rx `m.ll`; it reproduces the captures byte for byte;
`tools/dbgocc.py`):

- The original keeps the accounts+232 Rc pointer (`pump_creator_vault` data, orig 0x3078 `ldxdw r6,[r8+0xe8]`) in r6,
  moves it to r7 at 0x32f8, takes the event-authority lamports Rc pointer in r0 (0x3228), moves it to r6 at 0x3328, and
  then uses r0 for the flag/owner spill temps at 0x3370-0x33b8.
- Main and c2: at the accounts+232 load (`%2186` main, `%2185` c2) **r6 is held by `%1726`/`%1725` = `accounts + 264` =
  `&a.holder_creator_vault`**, a region-split piece over [34592, 54132] (defined at the sweep head, spilled only in clone
  10, main 0x3098). Over the clone run r6 is held by it for 5,596 of 9,500 slot units, and r9 by the bump `%2048`
  (`ctx.bumps.creator_vault`, [33552, 49728], 4,444 units). So the accounts+232 pointer takes r0; in c2 the
  event-authority lamports pointer piece `%2181` (`LDD %223, 8`) then holds r0 over the temps (45892-46440), and the
  temps take r5. The c2 tax force (`2178=r0` on 9bd38c7, an is_signer temp = `%2179` here) breaks that chain by force.
- So the source lever behind the tax is upstream of the run: the original spills `&holder_creator_vault` and the bump at
  their definitions (0x1f48, 0x1f70; w15a07). w15a07 priced ending those live ranges (B, A, ABN, spill-at-def, RAPRIO
  forces) at -9 to -250 M. No TCF literal spelling can free r6 there.

Marker tally over this lane's captures (`tools/mktable.py`, column `0x3078 / 0x3370`; original `r6 / r0`):

| accounts+232 reg / temps reg | captures | examples |
| --- | ---: | --- |
| r0 / r5 | 82 | main, c2, pLK, pKO, pOK, pLDK, pKLO, c2b5 |
| r7 / r0 | 10 | c2H, t0O, hKLD, hLKD, hKOL, hOLD, t0_KOLDRSWE, x03_hOKld |
| None / r9 | 7 | c2T8, c2T8L, t8O, t8L, t8RSWE, t8KOL, t8LDK |
| r3 / r0 | 5 | x08_qLkD, x09_qlkdo, x10_qLKd, r6a_KLDoR, r10a_KLDoR |
| r3 / r1 | 2 | t5O, t5L |
| r2 / r0 | 2 | hOKLDr, x11_hOKLDr |
| r3 / r7 | 1 | gRSWE |
| r0 / r2 | 1 | t0_LKDORSWE |

109 spellings captured (lamports-first pcva forms, c2 + neighbours, and every neighbour literal order); the original's r6 / r0 appears in none.

Library check (`tools/scane8.py`, 10,463 cached captures): the accounts+232 load is in r6 in 40 captures, all on old
bases, forced-RA builds (w16a04 `Ln1ra`, `Ln1pohra`, `Lpora`, w16a08 `F2p2__ra`) or far-off code (best unforced M 2,227
at 27,344 B, w15a35 `pd_b5x11`).

## 7. Notes for other lanes

- macOS filesystems are case-insensitive: capture names that differ only in case (`hOKLD`/`hOKld`, `pKDOL`/`pKdOL`)
  share `rx/` and `ir/` paths and corrupt each other (a worker crashed on a deleted `ir/*.ll`). This lane's rows
  `hOKLD hOKld hokLD pKDOL pKdOL pKDoL gKOld gkoLD qLkD qlkd qLKd qlKD` are superseded by `x01`-`x13`.
- The TCF-local literal levers are exactly additive: the captures of J_qKLD_t4O, J_qKLD_t10L, J_t10L_t4O and
  J_gOKLD_qKLD equal their splice/additive predictions (2,248, 2,248, 2,247, 2,247).

## Tools (`tools/`, experiment only)

- `prof.py <fn.bin|so|orig>`: abort-jump profile (41 jumps); `abortjs.py`: ja-target clusters.
- `census.py <sbs.txt>`: per-clone census from `w16-strategy/skeleton/tools/sbs.py main 2600 3c40`.
- `mk.py`: M, profile, per-segment delta vs main and the c2 marker (skeleton-aligned registers at orig 0x3078/0x3370).
- `scanprof.py`, `tcfsplice.py`, `scane8.py`: library scans.
- `genes_tp.py`: literal genes (above). `scr.py`/`capraw.py`/`rx.py`/`splice.py`/`jdiff.py`/`drift.py`: w16a02's oracle,
  re-pointed (ledger approach `tcfprofile`).
- `tab.py`, `mktable.py`, `beam.py` (joint search), `joint.py` (exact splice subsets), `dp.py` (brute force; superseded
  by beam.py).
