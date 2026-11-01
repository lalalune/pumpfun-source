# w16a09-cto-faithunion: unions of three or more validate/head classes, priced as one basin (notes)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Experimental base: main `9bd38c7d5` (admin_cto.rs as on 9120883a9): 0.67376, 3,124 slots, M 2,249, Mperm 2,293, Mhc 2,300,
true LCS `---` 2,255 / `rfj` 3,007, head rfj 631, joint RA ceiling (w15a28 pass 2) 2,338.
Main moved to `1f4e396b5` (#3859, sweep AMM guard tuple, 0.67436) and `599891304` (#3870, buy_v3) during the lane. Those
changes are in the sweep tail, the event literal and buy_v3, not in validate or the head. Every row below is captured from
a pinned copy of the 9bd38c7 crate, so all rows share one base.
Angle: w15a11's cause table splits validate's 183 original-only tokens into classes A-J. Every class alone collapses or
loses. This lane prices unions of at least three classes as one basin and stacks the bounds: restore the layout,
normalise the frame, then take the RA ceiling.
Ledger: approach `faithunion`. Captures are `0x22a10-w16-9bd38c7-fu-<union>-v1` (36 rows, written by `tools/scr.py`;
E1 and E2 were keyed `0x22a10-w16-5998913-fu-*` by mistake, see `-fu-keyfix-E1E2-v1`). Stacked bounds are
`0x22a10-w16-9bd38c7-fu-stk-<union>[_p1|_p2|_p3]-v1`. The verdict is `0x22a10-w16-9bd38c7-fu-killtest-v1`.

**Result: notes only, no source change. Main is still the best zero-loss measurement.**
- Unions do cancel cascades. A+B+E's unforced stacked bound (2,216) is 497 M above the sum of its three single-class
  costs. They also give the most original-like skeleton measured so far: Lrfj 3,057 (+50) and opcode LCS 3,094 (+45)
  for Gorig+GPF+Fa+V2+qli+hkt(+v01), and head rfj up to +53.
- No union reaches main's stacked RA ceiling. Here is the same pass-1/2/3 climb on every row:
  - main: 2,338 at pass 2, 2,344 at pass 3;
  - the best union, A+B+G (byte-identical to GPF): 2,306 at pass 2, 2,313 at pass 3;
  - A+B+E: 2,289 at pass 2, 2,290 at pass 3;
  - the single class B (F0): 2,322 at pass 2.

  Each class added to B lowers the ceiling. The step-4 gate (stacked ceiling >= 2,338) is not met, so no union was
  realised.
- The angle's kill test does not fire as written, because both of its conditions fail:
  - A+B-based unions beat head rfj 631 by 30-53;
  - A+B+G sits 32 M below 2,338, inside the 40 M margin.

  The table therefore closes the angle through the gate, not through the kill test. Unions of the head/validate classes
  improve the skeleton but not the ceiling. Register naming is the binding residual.

## 1. Oracles (experiment only; `tools/`)

- Captures: w16a04's `scr.py` (capraw identity build with pre-opt IR, SDK `opt -O3`, slim, SDK `llc`), with genes from
  `tools/genes_fu.py` and `SRCBASE` pinned to a 9bd38c7 crate copy. `m0` reproduces main (`eq_main: true`,
  0.67376 @27,400).
- `genes_fu.py` writes the classes so that they compose; a class is a callable wherever two classes touch the same text:
  - `p289n` (C/D, T289n);
  - `vmt` / `emt` (H, v14 / U4);
  - `b01`, `v01`;
  - `Fa` (E: validate reads the `args` copy);
  - `ov1a` (F);
  - `G51` (= mv_5_1) and `Gorig` (the original's store order as the literal order) (G);
  - `GPF` / `PDA` / `F0` / `GF` (A/B);
  - `V2`, `qli`, `hkt` (w15a10's faithful entry forms).
- `fuev.py` reports:
  - true LCS `---` / `rfj` (w14a128 masks) and opcode LCS;
  - order-free `bag4` (multiset overlap of rfj 4-grams);
  - head rfj (orig 0x0-0x1c00 against the best variant cut, as w16-strategy `headcmp.py`);
  - a dotmap swap flag.
- `fnorm.py` (new) normalises the frame:
  - every r10 access and every r10 lea that falls inside a variant non-spill frame object is rebased to main's object
    of the same IR name, and unnamed objects are paired by size in offset order;
  - objects main does not have keep their offset;
  - then the spill slots take the best colour permutation plus the vote swap climb (relab, as Mperm/Mhc).

  It is the identity on main (2,249 / 2,293 / 2,300). It generalises w15a19's `shperm.py` (one band shift) to any
  alloca layout change.
- `blkrestore.py` (new) restores the layout at MIR level:
  - run `llc -stop-after=block-placement`;
  - re-sort the execute blocks into main's layout, segment-wise, keyed by unique IR block names and otherwise by unique
    call/global signatures;
  - add a `JMP` where a fall-through breaks, then resume with `-start-after=block-placement`.

  The identity round trip on main is byte-exact. It repairs the w15a20 A/B chunk swap: E3 Lrfj 2,513 -> 3,033,
  AE 2,507 -> 3,030, E 2,486 -> 3,006, ACD 2,481 -> 2,806. Where validate's blocks were renamed (the C/D/H family) it can
  scramble the order, so the stack always takes the better of the plain and restored layouts.
- `binrestore.py` (new) restores placement at binary level toward the original's order (placenorm segments, with jumps
  re-linked). It is lossy on main (2,249 -> 2,107) and is kept only as a probe.
- `stk.sh <rx> [forces] [tag]` computes the stacked bound:
  1. optional sticky RAPRIO forces (w15a24 llc);
  2. layout: the better of plain and `blkrestore`;
  3. `fnorm` plus the spill permutation.

  With w15a28's pass-2 forces it gives main's joint exactly (2,338), and GPF's (2,306).
- RA passes: `raq.sh` runs pass 1 (w16a04 `lpipe.sh`: colmap vote, sticky single screen, greedy sticky climb), `raq2.sh`
  runs pass 2 and `raq3.sh` pass 3 (`pass2.sh` on top of the previous force set). Each pass then reruns `stk.sh` with
  its force set.
- `chunkmask.py`: true-LCS totals under `---`, `-f-`, `r--`, `rf-` and `rfj`, to split a residual into registers and
  frame/content.

## 2. Single classes (reference)

Archived single-class captures, measured with the same `fuev.py`. The w15a10 rows are on 90300f9, one literal order
earlier:

| capture | bytes | L--- | Lrfj | op | head rfj |
| --- | ---: | ---: | ---: | ---: | ---: |
| C/D (T289n, w15a25) | 27008 | 1535 | 2452 | 2559 | 608 |
| C/D+H (U1, w15a25) | 27048 | 1249 | 2823 | 2867 | 526 |
| H (v14, w15a11) | 27416 | 1515 | 2433 | 2547 | 577 |
| b01 (w15a11) | 27480 | 2003 | 3010 | 3050 | 631 |
| F (ov1a, w15a11) | 27448 | 1543 | 2473 | 2584 | 628 |
| B (F0, w15a28) | 27352 | 2149 | 3008 | 3049 | 641 |
| A+B (GPF, w15a28) | 27344 | 2055 | 3026 | 3068 | 665 |
| A (X_pdaf, w15a35) | 27400 | 1976 | 3019 | 3062 | 653 |
| G (mv_5_1, w15a16) | 27392 | 2226 | 3013 | 3056 | 637 |
| main 90300f9 (w15a10 m0) | 27400 | 2253 | 3007 | 3046 | 631 |
| E (Fa, w15a10) | 27688 | 1555 | 2493 | 2596 | 638 |
| E+B+hkc (Fa_f_h, w15a10) | 27760 | 1941 | 3034 | 3070 | 662 |
| E+V2+qli+hkt (w15a10) | 27712 | 2060 | 3032 | 3065 | 665 |
| E+A+B+hkc (w15a10) | 28016 | 1636 | 2523 | 2630 | 677 |
| A (pda, w15a10) | 27400 | 1974 | 3019 | 3059 | 653 |
| B (fl, w15a10) | 27352 | 2148 | 3007 | 3048 | 640 |
| b01 (hkc, w15a10) | 27480 | 2003 | 3010 | 3050 | 631 |
| E+V2+B+hkt (w15a10) | 27760 | 2049 | 3032 | 3069 | 665 |
| E+hkc+qli (w15a10) | 27712 | 1970 | 3032 | 3065 | 660 |

Head rfj is close to additive over the head classes (this lane's 9bd38c7 captures): A +22, B +10, E +9, G +6, A+B +34,
A+B+E +36, A+B+E+b01 +47.
C/D (T289n) costs -23 and H (v14) -54. F is neutral (-3).

## 3. Union table (9bd38c7 base; M = scorer-style masked matches; main M 2,249)

Column notes:
- `Mfn` is `fnorm` without the spill permutation, on the plain layout.
- `stacked` is the unforced stacked bound.
- The RA columns repeat the stack on the pass-1/2/3 force sets; the number of forces is in brackets.
- The B pass-1/2 force sets and GPF's pass-2 set are w15a28's, re-applied to these captures. They reproduce w15a28's
  joints (2,322 and 2,306).

| union | genes | classes | bytes | M | Mperm | Mhc | L--- | Lrfj | op | bag4 | head rfj | Mfn | stacked | RA p1 / p2 / p3 (forces) |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| m0 | - | main | 27400 | 2249 | 2293 | 2300 | 2255 | 3007 | 3049 | 2632 | 631 | 2249 | 2300 | 2328 (7) / 2338 (9) / 2344 (10) |
| U3 | p289n+vmt | C/D, H | 27048 | 1077 | 1105 | 1190 | 1276 | 2859 | 2903 | 2021 | 565 | 1800 | 1961 |  |
| ABG | G51+GPF | A+B, G | 27344 | 1958 | 2173 | 2183 | 2055 | 3026 | 3068 | 2619 | 665 | 1958 | 2183 | 2224 (3) / 2306 (14) / 2313 (16) |
| ABb | GPF+b01 | A+B, b01 | 27424 | 1881 | 2017 | 2023 | 2016 | 3030 | 3076 | 2487 | 661 | 1987 | 2129 | 2216 (8) / - / - |
| ABH | GPF+vmt | A+B, H | 27416 | 1607 | 1882 | 1886 | 1875 | 2931 | 2973 | 2485 | 611 | 1753 | 2030 |  |
| UAB | GPF+p289n+vmt | A+B, C/D, H | 27008 | 1063 | 1063 | 1199 | 1270 | 2888 | 2932 | 2015 | 589 | 1777 | 1990 |  |
| UG | p289n+vmt+G51 | C/D, G, H | 27080 | 858 | 858 | 892 | 978 | 2418 | 2533 | 1994 | 563 | 1441 | 1853 |  |
| Ub01 | p289n+vmt+b01 | C/D, H, b01 | 27072 | 211 | 847 | 936 | 1190 | 2869 | 2911 | 2007 | 572 | 1603 | 1806 |  |
| UE | p289n+vmt+Fa | C/D, E, H | 27136 | 1538 | 1698 | 1710 | 1840 | 2880 | 2916 | 2467 | 611 | 1759 | 1982 | 2041 (10) / - / - |
| UF | p289n+vmt+ov1a | C/D, F, H | 27200 | 1108 | 1125 | 1205 | 1267 | 2869 | 2913 | 2032 | 569 | 1755 | 1990 |  |
| ABGb | G51+GPF+b01+v01 | A+B, G, b01, v01 | 27424 | 1886 | 2022 | 2028 | 2018 | 3030 | 3076 | 2487 | 663 | 1992 | 2134 |  |
| ABE | GPF+Fa | A+B, E | 27664 | 1856 | 2096 | 2110 | 1982 | 3047 | 3085 | 2492 | 667 | 1999 | 2216 | 2257 (8) / 2289 (13) / 2290 (15) |
| ALL | G51+GPF+p289n+vmt+b01+Fa+ov1a | A+B, C/D, E, F, G, H, b01 | 27496 | 847 | 945 | 965 | 1091 | 2543 | 2579 | 2034 | 610 | 1461 | 1889 |  |
| U4 | p289n+vmt+emt | C/D, H | 27016 | 1081 | 1130 | 1222 | 1295 | 2858 | 2902 | 2031 | 563 | 1908 | 2010 |  |
| E1 | GPF+Fa+b01 | A+B, E, b01 | 27976 | 1379 | 1498 | 1556 | 1900 | 2953 | 2992 | 2650 | 678 | 1379 | 1678 |  |
| E2 | GPF+Fa+V2+qli+hkt | A+B, E, b01+b03, hkt, qli | 27952 | 1758 | 1940 | 2008 | 1882 | 3055 | 3091 | 2555 | 668 | 1863 | 2109 | 2168 (6) / 2190 (13) / - |
| E3 | Fa+V2+qli+hkt | E, b01+b03, hkt, qli | 27864 | 1604 | 1696 | 1696 | 1663 | 2513 | 2610 | 2644 | 667 | 1604 | 2185 |  |
| E4 | F0+Fa+b01 | B, E, b01 | 27720 | 1688 | 1977 | 2012 | 1954 | 3032 | 3068 | 2514 | 659 | 1714 | 2037 |  |
| AGo | Gorig+GPF | A+B, G | 27344 | 1961 | 2176 | 2186 | 2058 | 3026 | 3069 | 2619 | 665 | 1961 | 2186 |  |
| ACD | GPF+p289n | A+B, C/D | 27072 | 1438 | 1490 | 1502 | 1554 | 2481 | 2589 | 2464 | 639 | 1539 | 1886 |  |
| E2G | Gorig+GPF+Fa+V2+qli+hkt | A+B, E, G, b01+b03, hkt, qli | 27864 | 1840 | 2003 | 2010 | 1955 | 3057 | 3094 | 2541 | 673 | 1945 | 2114 |  |
| E2v | Gorig+GPF+Fa+V2+qli+hkt+v01 | A+B, E, G, b01+b03, hkt, qli, v01 | 27864 | 1847 | 2010 | 2017 | 1956 | 3057 | 3094 | 2541 | 674 | 1952 | 2121 | 2179 (11) / 2206 (20) / - |
| E2F | GPF+Fa+V2+qli+hkt+ov1a | A+B, E, F, b01+b03, hkt, qli | 27848 | 1631 | 1731 | 1733 | 1677 | 2532 | 2634 | 2647 | 684 | 1631 | 2146 |  |
| E2U | GPF+Fa+V2+qli+hkt+p289n+vmt | A+B, C/D, E, H, b01+b03, hkt, qli | 27528 | 1530 | 1547 | 1582 | 1605 | 2447 | 2542 | 2595 | 656 | 1530 | 1932 |  |
| AE | PDA+Fa | A, E | 27744 | 1453 | 1586 | 1587 | 1518 | 2507 | 2610 | 2467 | 654 | 1550 | 1962 |  |
| BE | GF+Fa | B, E | 27720 | 1670 | 1872 | 1901 | 1808 | 2928 | 2962 | 2501 | 654 | 1734 | 1966 |  |
| E | Fa | E | 27584 | 1471 | 1496 | 1501 | 1557 | 2486 | 2590 | 2456 | 640 | 1571 | 2089 |  |
| A | PDA | A | 27400 | 1939 | 2024 | 2024 | 1976 | 3019 | 3062 | 2599 | 653 | 1939 | 2024 |  |
| B | F0 | B | 27352 | 2117 | 2197 | 2205 | 2149 | 3008 | 3049 | 2620 | 641 | 2117 | 2205 | 2294 (9) / 2322 (16) / - |
| Bg | GF | B | 27384 | 2103 | 2198 | 2206 | 2134 | 3007 | 3050 | 2621 | 641 | 2103 | 2206 |  |
| ABEv | GPF+Fa+v01 | A+B, E, v01 | 27664 | 1849 | 2089 | 2103 | 1981 | 3047 | 3085 | 2492 | 666 | 1992 | 2209 |  |
| ABEG | Gorig+GPF+Fa | A+B, E, G | 27680 | 1853 | 2093 | 2107 | 1979 | 3043 | 3081 | 2489 | 664 | 1996 | 2213 |  |
| UEA | GPF+p289n+vmt+Fa | A+B, C/D, E, H | 27312 | 1522 | 1757 | 1800 | 1877 | 2897 | 2932 | 2427 | 634 | 1693 | 2027 |  |
| UEF0 | F0+p289n+vmt+Fa | B, C/D, E, H | 27160 | 1566 | 1738 | 1784 | 1843 | 2882 | 2917 | 2469 | 613 | 1794 | 2014 |  |
| UEV | p289n+vmt+Fa+V2+qli+hkt | C/D, E, H, b01+b03, hkt, qli | 27512 | 1443 | 1515 | 1559 | 1556 | 2434 | 2534 | 2613 | 633 | 1443 | 1859 |  |
| UEb | p289n+vmt+Fa+b01 | C/D, E, H, b01 | 27208 | 972 | 1027 | 1103 | 1238 | 2892 | 2925 | 2051 | 586 | 1715 | 1977 |  |
| UEG | Gorig+p289n+vmt+Fa | C/D, E, G, H | 27272 | 1264 | 1410 | 1423 | 1515 | 2429 | 2532 | 2420 | 608 | 1488 | 1857 |  |
| UEm | p289n+vmt+emt+Fa | C/D, E, H | 27152 | 1525 | 1697 | 1712 | 1857 | 2877 | 2911 | 2474 | 609 | 1805 | 1983 |  |

## 4. What the stacked bound shows

- **The C/D/H family is closed: T289n + v14, and every union built on them.**
  - M is 211-1,566.
  - The frame is a large part of the collapse. `fnorm` alone recovers 400-1,400 M (U3 1,077 -> 1,800; Ub01
    211 -> 1,603). With the spill permutation the unforced stack is 1,806-2,027, and pass-1 RA adds about 60 (UE 1,982
    -> 2,041 with 10 forces).
  - The order-free content shows why no layout or frame oracle can rescue them. bag4 is 2,000-2,470 against main's
    2,632. The loss sits at orig 0x800 (-25 rfj) and 0x4800-0x6000 (-42, -29, -35 rfj: event, pool CPI, curve).
  - T289n's V-time threading changes the instruction content of the whole function, through spills and moves from the
    RA reassignment (w15a25), not just its order.
  - E cancels part of the collapse (UE: M +461 over U3, bag4 +446), but all of it is frame: after `fnorm`, UE and U3
    differ by 21 M.
  - Adding A/B to the family (UAB, UEA, ACD) does not help.
- **The A+B family is the only base that keeps the body.**
  - GPF (A+B) has Lrfj 3,026 (+19) and head 665.
  - G is a no-op on it: G51+GPF is byte-identical to GPF, and Gorig adds +3 M.
  - E on A+B gives ABE, the best unforced stack of any union (2,216, +33 over GPF), with Lrfj 3,047 (+40), op 3,085 (+36)
    and head 667.
  - V2 + qli + hkt (E2), then G + v01 (E2v), lift the skeleton further, to Lrfj 3,057 (+50) and op 3,094 (+45). That is
    the most original-like skeleton measured so far (w14a128's census maximum was 3,038). Each of these pieces costs M,
    though: E2v's stack is 2,121.
  - b01 (E1) and F (E2F) push the head to 678 / 684 but collapse the body (Lrfj 2,953 / 2,532).
- **RA is the binding constraint.** The same climb was run on every row:

| basin | p0 | p1 | p2 | p3 | forced bytes |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 2,300 | 2,328 (7) | 2,338 (9) | **2,344** (10) | 27,376 |
| B (F0) | 2,205 | 2,294 (9) | **2,322** (16) | | 27,296 |
| A+B (GPF; = A+B+G51) | 2,183 | 2,224 (3) | 2,306 (14) | **2,313** (16) | 27,336 |
| A+B+E (ABE) | 2,216 | 2,257 (8) | 2,289 (13) | **2,290** (15) | 27,696 |
| A+B+E+G+b01/b03+qli+hkt+v01 (E2v) | 2,121 | 2,179 (11) | 2,206 (20) | | 27,840 |
| A+B+E+b01/b03+qli+hkt (E2) | 2,109 | 2,168 (6) | 2,190 (13) | | 27,928 |
| A+B+b01 (ABb) | 2,129 | 2,216 (8) | | | 27,472 |
| C/D+E+H (UE) | 1,982 | 2,041 (10) | | | 27,296 |

  The true-LCS split of the pass-2 stacked builds against main's pass-2 stacked build names the residual:

| pass-2 stack vs main pass 2 | `---` | `-f-` (registers) | `r--` (frame + content) | `rf-` | `rfj` |
| --- | ---: | ---: | ---: | ---: | ---: |
| B (F0) | -14 | +1 | -23 | -12 | -5 |
| A+B (GPF) | -22 | +3 | -9 | +21 | +28 |
| A+B+E (ABE) | -49 | -21 | +28 | +25 | +33 |

  Along B -> A+B -> A+B+E the skeleton (`rf-` -12 -> +21 -> +25) and the frame-normalised content (`r--` -23 -> -9 ->
  +28) both get closer to the original. The registers do not: `-f-` stays at main's level for B and A+B and drops to -21
  for A+B+E. Up to 16 greedy forces do not undo it.
  - A+B's residual is the compound of small register and frame misses (`---` -22 where each mask alone is within 9).
  - A+B+E's residual is register naming in the clone runs, not GPF's accounts pointer. GPF's decisive head force is
    `%249=r8`, `COPY %0; ADD 72` in wallet's bb94.i (w15a28). ABE's low-numbered forces are different values:
    `%241` (final R9, forced r5) and `%242` (final R7, forced r8) are `LDD %238,8` / `LDD %238,16`, the Rc pointer
    pieces of an early AccountInfo clone (`clone.exit186.i`, `Rc inc_strong.exit198`). Named with w15a35 `vname.py`.

## 5. Ablation: the A/B/E lattice (unforced stacked bound; main 2,300)

| state | stacked | cost vs main | additive prediction | interaction | Lrfj (restored) | head rfj |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main | 2,300 | 0 | | | 3,007 | 631 |
| A (PDA) | 2,024 | -276 | | | 3,019 | 653 |
| B (F0) | 2,205 | -95 | | | 3,008 | 641 |
| B (GF, with `g`) | 2,206 | -94 | | | 3,007 | 641 |
| E (Fa) | 2,089 | -211 | | | 3,006 | 640 |
| A+B (GPF) | 2,183 | -117 | 1,930 | **+253** | 3,026 | 665 |
| A+E | 1,962 | -338 | 1,813 | +149 | 3,030 | 654 |
| B+E (GF+Fa) | 1,966 | -334 | 1,995 | -29 | 2,924 | 654 |
| **A+B+E** | **2,216** | -84 | 1,719 | **+497** | 3,047 | 667 |

- A and B cancel each other's cascades (+253). E's collapse (the A/B chunk swap) is cancelled only when both A and B
  are present. E costs 211 alone, 62 on A and 240 on B, but it adds +33 on A+B. That is the faithunion
  hypothesis, measured: the original's classes are jointly cheaper than one at a time.
- The cancellation stops at the RA ceiling. At pass 2, B alone (2,322) beats A+B (2,306), which beats A+B+E (2,289).
  The unforced gains come from frame and placement, which the stack normalises anyway. What the stack cannot normalise,
  register naming, gets worse with each added head class.
- Removing one class from A+B+E: -E -> 2,183 (-33), -B -> 1,962 (-254), -A -> 1,966 (-250). A and B are the load-bearing
  pair. G (ABEG 2,213) and v01 (ABEv 2,209) cost 3-7 on top.

## 6. Kill test and verdict

- Head rfj: every A+B-based union beats main's 631 by 30 or more (ABb +30, ABGb +32, A+B+G +34, ABE +36, E2 +37, E2v +43,
  E1 +47, E2F +53). The first kill condition does not hold.
- Stacked ceiling: A+B+G (byte-identical to GPF) reaches 2,306 at pass 2 and 2,313 at pass 3, within 40 M of main's 2,338.
  The second kill condition does not hold either, so the lane ran steps 2-4.
- Step 4's gate is **not met**: no union's stacked ceiling reaches main's joint 2,338. The best union is 25-32 M below main
  at every matched pass depth (p2 2,306 against 2,338; p3 2,313 against 2,344). ABE converges at 2,290. The single class
  B (2,322) beats every union.
- So there is no union to realise, and no source change, size repay or differential run was attempted.
- Measured closure of head/validate-structure unions:
  - they move the skeleton toward the original (Lrfj up to +50, opcode up to +45, head up to +53);
  - they cancel each other's frame and placement cascades (A+B+E +497 over additive);
  - under the same RA climb, register naming keeps every union below main;
  - the C/D/H family is closed by content (bag4), not by layout or frame.

## 7. Next ideas (untried)

1. The best skeleton (E2v: Lrfj 3,057, op 3,094) loses on registers (`-f-` -126 unforced). A register-only oracle on E2v,
   for example w15a32's exact spill-colour oracle or w15a18's priority/cascade greedy (rather than vreg->physreg pins),
   would show whether its register gap is the same head-accounts-pointer family as GPF's `%249`.
2. A+B+E is +28 in `r--` and +25 in `rf-` over main at pass 2. Its register residual sits in clone-run Rc pieces
   (`%241`, `%242`), not in GPF's accounts pointer. A source lever for those clone-piece colourings (the w15a24/w15a34
   clone-order families) would be worth more on A+B+E than on main. Any lane that finds one should re-price ABE and
   E2v with `stk.sh`.
3. `fnorm.py` and `blkrestore.py` are general. A lane with a swap-collapsed candidate can price it at main's frame and
   layout in about a minute (`tools/stk.sh`).

## 8. Data (`data/`)

- `union_table.md`: the full union table of section 3.
- `res-9bd38c7.jsonl`: per-capture scr rows (bytes, M, Mperm, Mhc, LCS, head, dotmap).
- `stkra.jsonl`: stacked bounds with forces, per pass.
- `stk.jsonl`: unforced stacked bounds.
- `fuev.jsonl` and `singles_fuev.jsonl`: fuev rows for the unions and for the archived singles.
