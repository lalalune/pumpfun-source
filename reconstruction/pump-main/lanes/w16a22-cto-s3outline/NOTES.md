# w16a22-cto-s3outline: the 307/312 outline on S3's per-arm holder flag (notes)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (origin/main 1647da0f2 has the same `programs/pump/src`): 0.67436, 3,141 slots, M 2,251,
Mperm 2,295, Mhc 2,302, rfj 3,006. Wave-16 lane, continued in wave 17 after the 02:30 UTC restart.
Ledger: approach `s3outline`, keys `0x22a10-w16-5998913-s3outline-<cell>-v1`.

**Result: notes only. Main stays the best zero-loss measurement (0.67436 / 3,141 slots / 27,400 B). Kill test met.**

- The angle was to put the faithful 307/312 outline validate on w16a08's S3, so that the outline's entry pieces stop
  evicting the accounts pointer from r8. **The hypothesis is refuted for every carrier that reads the copy.** On S3, tA,
  tB1 and trw collapse further than on main. The 660 chain moves after the sweep (0x3db8-0x3e70), and `bb56.i` gets
  the extra live-ins r5 (the accounts pointer) and r9/r4/r8. S3 does not stop the accounts pointer being carried
  across `bb56.i` once the copy's entry pieces are live.
- **Shim cells (owner decision 2026-11-01).** The empty `#[cold] fn cold(){}` marker at the head of the 306 Some arm
  (w14a07 c1, w17a02 `c306`) outlines exactly the original set with no carrier copy. It keeps 660 in place and adds no
  `bb56.i` live-in.
  - On S3 alone (`S3C1`) the accounts pointer moves to r6 in the sweep CPI clone chunk.
  - With w15a21's tf_g3 creator binding (`S3tfC1`) it stays in r8, at 11 of 13 uses, the same as S3 alone.
  - But S3 costs the outline base what it costs main: M 2,201 → 1,921 and Mperm 2,245 → 2,220 (tfC1 → S3tfC1).
- Stacked bounds (w16a08 `full.sh`: placement restore, permhc, restore-aware sticky RA climb): see section 3. No
  S3+outline cell reaches S3n's 2,347.

## 1. Method

- `tools/cap.sh <cell> <genes> <slot>` copies the worktree crate, applies `tools/s3g.py` genes in order (exact
  single-occurrence edits, line count kept), and does one identity raw-IR capture (w15a25 `capraw.py`). It then runs
  the fast V oracle (w15a25 `reduce.py` + `vbfi.py` + `thr.py`) and `opt -O3` + SDK `llc` (w16a06 `rx.py`). `tools/ev.sh`
  adds:
  - w16a06 `sc.py` (M, skM);
  - w15a16 `mp.py` (Mperm, Mhc);
  - w16a13 `eo.py` (error order, lddw);
  - `tools/accreg.py` (chunk M and the candidate base register of each original `[r8+..]` use in orig 0x3000-0x3800);
  - w16a08 `ar.sh`/`ares.py` (`bb56.i` live-ins, placement restore);
  - w14a128 `lcschunk.py --mask rfj` (true LCS with regs, frame and jumps masked).
  `tools/q2.sh` queues cells.
- `tools/s3g.py` imports w16a13's `sg.py` (copied here) and adds:
  - `S3`: w16a08 `e/S3n.py` as edits;
  - `h289`;
  - `tf`: the w15a21 tf_g3 creator binding;
  - the shim genes `C1` (`cold()` at the 306 Some arm) and `C2` (`cold()` inside the 307 and 312 error branches).
  Every shim edit carries a same-line `/*shim: ...*/` marker.
- Stacked bounds come from w16a08 `tools/full.sh` (stack.sh, `rpipe.sh` pass 1, `rpass2.sh` pass 2; w15a24's sticky
  RAPRIO llc). They run against main capture `m0` (`eq_main: true`).
- RA tracing: `llc -debug-only=regalloc` (patched llc) on each cell's post-opt IR. `tools/cov.py` lists the physreg of
  every live piece at a slot. `tools/dbgocc.py` (w15a33) names the occupants at a piece's `selectOrSplit`.

## 2. Cell table (oracle on 5998913; `data/cells.tsv`)

| cell | genes | bytes | M | Mperm | Mhc | skM | rfj | lddw | error order (validate) | 660 | extra `bb56.i` live-ins | chunk 0x3000 M | accounts-ptr base regs |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | --- | ---: | --- |
| m0 | main | 27400 | 2251 | 2295 | 2302 | 2808 | 3006 | 88 | 298 289 296 326 306 312 307 330 338 334 | 2578 | - | 158 | r8:13 |
| S3 | S3 | 27416 | 1990 | 2289 | 2296 | 2813 | 3009 | 88 | = main | 2590 | - | 71 | r8:11 |
| S3tf | tf+S3 | 27448 | 1970 | 2269 | 2270 | 2807 | 3009 | 88 | = main | 25b0 | - | 71 | r8:11 |
| tA3 | tA+S3 | 27144 | 1479 | 1540 | 1545 | 2161 | 2443 | 86 | 298 289 306 296 326 312 307 330 338 334 | **3dd0** | r5, r9 | 0 | unaligned |
| tB13 | tB1+S3 | 27504 | 1389 | 1476 | 1476 | 2134 | 2453 | 86 | = tA3 | **3e70** | r4, r5, r8 | 0 | unaligned |
| trw3 | trw+S3 | 27208 | 1428 | 1518 | 1524 | 2172 | 2449 | 86 | = tA3 | **3db8** | r4, r5, r9 | 0 | unaligned |
| tA3h | tA+S3+h289 | 27144 | 1465 | 1526 | 1531 | 2185 | 2425 | 86 | = tA3 | 3dd0 | r5, r9 | 0 | unaligned |
| tB13h | tB1+S3+h289 | 27504 | 1373 | 1460 | 1460 | 2154 | 2434 | 86 | = tA3 | 3e70 | r4, r5, r8 | 0 | unaligned |
| tAn23 (ref) | tAn2+S3 | 27032 | 1939 | 2238 | 2238 | 2760 | 2963 | 86 | 298 289 296 312 306 326 307 330 338 334 | 2410 | - | 71 | r8:11 r1:1 |
| m0C1 (shim) | C1 | 26992 | 1954 | 2111 | 2111 | 2792 | 2975 | 86 | 298 289 312 296 326 306 307 330 338 334 | 23b8 | - | 52 | r8:9 r6:3 |
| m0C2 (shim) | C2 | 27040 | 1953 | 2110 | 2110 | 2792 | 2980 | 86 | = m0C1 | 23e8 | - | 52 | r8:8 r6:3 |
| m0C1h (shim) | C1+h289 | 26992 | 1940 | 2097 | 2097 | 2792 | 2957 | 86 | = m0C1 | 23b8 | - | 52 | r8:9 r6:3 |
| S3C1 (shim) | C1+S3 | 27000 | 1841 | 2125 | 2125 | 2797 | 2977 | 86 | = m0C1 | 23d0 | - | 33 | r8:8 r6:3 |
| S3C2 (shim) | S3+C2 | 27048 | 1840 | 2124 | 2124 | 2797 | 2982 | 86 | = m0C1 (326 warm: V 0.0322, inlined) | 2400 | - | 33 | r8:7 r6:3 |
| S3C1h (shim) | C1+S3+h289 | 27000 | 1827 | 2111 | 2111 | 2797 | 2959 | 86 | = m0C1 | 23d0 | - | 33 | r8:8 r6:3 |
| tfC1 (shim ref) | tf+C1 | 27024 | 2201 | 2245 | 2255 | 2791 | 2982 | 86 | = m0C1 | 2400 | - | 158 | r8:13 |
| **S3tfC1 (shim)** | tf+C1+S3 | 27016 | 1921 | 2220 | 2221 | 2790 | 2983 | 86 | = m0C1 | 2400 | - | 71 | r8:11 r1:1 |
| tfC1b (repay) | tf+C1+b01 | 26960 | 1760 | 2013 | 2027 | 2845 | 2980 | 86 | = m0C1 | 23f0 | - | 42 | r9:7 r8:3 r1:1 |
| tfC1v (repay) | tf+C1+v01 | 27024 | 2194 | 2238 | 2248 | 2791 | 2982 | 86 | = m0C1 | 2400 | - | 158 | r8:13 |
| tfC1bv (repay) | tf+C1+b01+v01 | 26960 | 1765 | 2018 | 2032 | 2845 | 2980 | 86 | = m0C1 | 23f0 | - | 42 | r9:7 r8:3 r1:1 |
| **tfC1Fa (repay)** | tf+C1+Fa | 27264 | 1393 | 1491 | 1497 | 2195 | 2471 | 86 | = m0C1 | **3df0** | r4, r5, r9 | 1 | unaligned |

The original's validate order is 289 298 306 296 326 312 307 330 338 334. The 660 column gives the offset of the 660
error site; it sits at about 0x23b8-0x2590 when the sweep tail is in place. `tfC1` reproduces w17a02's `tfc306`
exactly (0.66385 @ 27,024 B).

## 3. Stacked bounds (w16a08 pipeline; S3n on 5998913 = 2,347, main = 2,339)

| cell | bytes | M raw | RA pass 1 (forces) | joint Mperm / Mhc | pass 2 | note |
| --- | ---: | ---: | --- | --- | --- | --- |
| S3C1 | 27000 | 1841 | 0.62402 @26872 (272=r8, 1285=r2, 1087=r5) | 2127 / 2131 | 0.63822 @26848 at round 5 (stopped) | far below |
| tB13 | 27504 (restored 27368) | 1389 (restored 1641) | 12 forces | 2032 / 2042 | - | far below |
| S3tfC1 | 27016 | 1921 | PENDING | | | |
| tfC1 | 27024 | 2201 | PENDING | | | |

## 4. Findings

1. **S3 does not shield the accounts pointer from the copy's entry pieces.** All three copy-reading carriers (tA, tB1,
   su-first) collapse further on S3 than on main. tA on main keeps 660 in place (M 1,789, w16a13); on S3 the 660 chain
   moves after the sweep and M is 1,479.
   - The extra `bb56.i` live-in is r5 (accounts pointer, slot -2264) in every one, as w16a08 found for the collapsed
     basins. After the restore, tA3 recovers to 1,908 (restored Mhc 2,008), still far below S3's 2,296.
   - h289 does not change the 298/289 order in any cell, and costs 14-16 M everywhere.
2. **The carrier copy causes the collapse, not the outline.** The `cold()` shim outlines the same set (307, 312, 326,
   330, 338, 334; lddw 86) with no copy. It keeps 660 in place and adds no `bb56.i` live-in on main and on S3.
3. **Without tf_g3, the outline itself moves the accounts pointer out of r8.** This happens on main (m0C1) and on S3
   (S3C1).
   - From 0x1d78 on, `r8 = accounts + 264` (`mov64 r8,r6; add64 r8,264`) and the accounts pointer is r6 through the
     sweep CPI clone chunk (orig 0x3000: `ldxdw r4,[r6+0xd8]` vs the original's `[r8+0xd8]`).
   - At the `selectOrSplit` of the piece that covers the `+0xd8` load (S3C1 `%2093`, from `%132`), r8 is held by `%2090`
     (from `%131`, live [43192..46280], w 2.6e-7 < 4.9e-7) and r6 is free. Greedy takes the free r6, so no eviction is
     tried.
   - The whole-function region split of `%0` is the same in m0, S3, m0C1 and S3C1: r5 wins, and r8's static cost is 7.5
     against r5's 3.46. The r8 placement in chunk 0x3000 is decided by these later pieces, not by `%0`'s first split.
4. **tf_g3 restores r8.** With the w15a21 creator binding, the outline base keeps r8 at main's 13/13 (tfC1, chunk M 158).
   With S3 on top it keeps r8 at S3's 11/13 (S3tfC1, chunk M 71). That is the angle's question answered positively, but
   only for the shim carrier on tf_g3. S3 still costs the outline base about what it costs main: -280 raw M (spill-slot
   numbering, w14a142) and -25 Mperm.
5. **Clean A/B on the shim base: reading the copy is the collapse, not the outline.** tfC1Fa differs from tfC1 only by
   Fa (validate reads `args.0`, the entry copy of `new`, whose pieces are the original's 0x4d8-0x538 loads, Ghidra
   w17a01 finding 3). It collapses exactly like tA/tB1/trw: 660 moves to 0x3df0, and `bb56.i` gains r4, r5 (accounts
   pointer, -2296) and r9. M drops from 2,201 to 1,393.
   - After the join restore (`ares`), tfC1Fa is at **rfj 2,997 (main 3,006 - 9), a better skeleton than tfC1's 2,982**.
     The chunk deltas are entry +11, validate -37, 0x1000 +20. That is the faithful entry copy matching the original.
   - But the restore only reaches M 1,671 / Mhc 1,946 at 27,120 B. The register naming collapses well beyond the
     `bb56.i` carry (RA pass 1 in section 3).
   - The other repay-grid pieces do not repay on tfC1. b01 shrinks it to 26,960 B and moves the accounts pointer to r9
     (M 1,760). v01 costs 7 everywhere at the same size.
6. **Error order.** Every copy-reading carrier gives the original's order after the 298/289 head (306 296 326 312 307).
   Every `cold()` cell gives 312 296 326 306 307, because the cold call's BPI weight is gone by llc (w17a02 section 1).
   Only an llc-time weight (w17a02's `llvm.expect` extern) can move 306 ahead of 296 there (w14a07: None:Some >= 2:1).

## 5. Kill test

- No copy-reading carrier on S3 keeps the accounts pointer in r8 over chunk 0x3000: tA, tB1 and trw move 660, and
  chunk 0x3000 is unaligned. **Met.**
- No S3+outline cell stacks above S3n's 2,347 (section 3). **Met.**
- 17 cells (3 references). The mechanism closes the remaining carrier spellings: any carrier that reads the copy makes
  its entry pieces live, so `bb56.i` carries the accounts pointer.

## 6. Next ideas (for the shim lanes)

- tfC1 is the best outline base (M 2,201 / Mhc 2,255 at 27,024 B; 376 B of room). S3 does not help it raw. Price
  tfC1+S3 at the joint level only after an RA lever exists for S3's spill-slot shift (w16a19 / w16a20).
- The remaining outline gap on tf_g3 is the llc-time 306 weight (306 before 296) plus the 376 B repay. w17a02 owns the
  weight. The w15a25 O-repay grid (b01, v01, g1 SSA pieces, inline-L339) is the faithful repay catalog to try on tfC1.
