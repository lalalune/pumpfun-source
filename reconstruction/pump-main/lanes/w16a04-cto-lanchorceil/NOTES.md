# w16a04-cto-lanchorceil: joint RA+frame ceiling matrix of L-anchored composites (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `9bd38c7d5` (`admin_cto.rs` unchanged since 9120883a9): 0.67376, 3,124 slots, M 2,249, 1034/1034.
Angle: build the joint RA + frame ceiling matrix of composites anchored on the L basin
(L = `mv_5_1+t1n+m_crl2+devol`: cashback before creator in the CtoState literal, `if new.is_none()` in the shared arm,
`let cr=` creator binding, both read_volatile placeholders removed), then hand off the decisive forces.
w15a32-cto-lbasinweight owns L's spill-weight lever; this lane does not repeat its source screens.
Ledger: approach `lanchorceil`, keys `0x22a10-w16-9bd38c7-lac-*-v1`.

**Status: in progress (first table below).**

## 1. Oracle (all experiment-only, no build slot except the captures)

- Captures: w15a16 `scr.py` (w15a03 capraw identity build with `--emit=llvm-ir -C no-prepopulate-passes`, SDK `opt -O3`,
  slim, SDK `llc`), genes from `tools/genes_lac.py` (= w15a32 `genes_lbw` + c2, s1, tf_g1a, n1, po).
  `m0` reproduces main (`eq_main: true`), and its slim module equals w15a28's `m0` capture except for one declaration hash,
  so main's pass-1/pass-2 rows are w15a28's (#3746). **L reproduces 0.66926 / 3,075 slots at 27,400 B exactly.**
- `tools/lpipe.sh <rx> [N K R P BASEFORCE]` (w15a28 `pipe.sh` generalised): w14a84 `colmap.py` vote under the sticky
  RAPRIO llc (w15a24 `llc-patch`), sticky single screen of the top 80 colour misses, greedy sticky climb over the top 30
  (ratio objective, free size, 12 rounds), forced build, joint `permhc` (forces + best spill-offset permutation + vote swap
  climb), true LCS vs main (`evall.py`), window-rotation check. Pass 2 = the same with the pass-1 forces as base.
- `tools/winrot.py`: for the 13 spill offsets `-2264..-2360`, the original offset each slot's aligned accesses vote for;
  `rot` = slots whose vote differs from main's. main 0, L 11.
- `tools/brjoint.sh`: w14a87 `B` validate block order (Bspec963 names, w14a98 `sub.border2` content resolution against
  main's asm), with (`Br`) and without condition reversal, applied to the sticky-forced asm, then joint `permhc`.
- `tools/loo.py`: leave-one-out joint value of each force in a set.

## 2. Joint-ceiling matrix (first rows; main = w15a28 #3746 pass 1 / pass 2)

| composite | pass | bytes | M | Mperm | Mhc | forces | climb ratio @ bytes | forced M | forced Mperm | joint | d joint vs main p2 | true LCS ---/rfj vs main | window rot (unforced/forced) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| main | p1 | 27400 | 2249 | 2293 | 2300 | 7 | 0.68245 @ 27376 | 2277 | 2321 | **2328** | -10 | 28/3 | 0/0 |
| main | p2 | 27400 | 2249 | 2293 | 2300 | 9 | 0.68395 @ 27376 | 2282 | 2338 | **2338** | +0 | 35/2 | 0/0 |
| L + c2 | p1 | 27392 | 2205 | 2300 | 2309 | 6 | 0.67536 @ 27392 | 2254 | 2346 | **2350** | +12 | 4/12 | 11/11 |
| L = mv_5_1+t1n+m_crl2+devol | p2 | 27400 | 2234 | 2307 | 2316 | 8 | 0.67775 @ 27416 | 2263 | 2345 | **2350** | +12 | 13/10 | 11/11 |
| L + s_tai2 | p2 | 27400 | 2228 | 2312 | 2321 | 7 | 0.67536 @ 27392 | 2254 | 2349 | **2349** | +11 | 9/11 | 11/11 |
| L + s_tai2 | p1 | 27400 | 2228 | 2312 | 2321 | 5 | 0.67386 @ 27392 | 2249 | 2332 | **2341** | +3 | 2/12 | 11/11 |
| L = mv_5_1+t1n+m_crl2+devol | p1 | 27400 | 2234 | 2307 | 2316 | 6 | 0.67615 @ 27400 | 2257 | 2337 | **2341** | +3 | 7/8 | 11/11 |
| L + sh_iflet+rP_back | p1 | 27400 | 2234 | 2307 | 2316 | 6 | 0.67615 @ 27400 | 2257 | 2337 | **2341** | +3 | 7/8 | 11/11 |
| L + s1 | p1 | 27376 | 2139 | 2215 | 2255 | 12 | 0.66247 @ 27320 | 2208 | 2315 | **2332** | -6 | 3/34 | 12/12 |

- L + c2 p1: `2172=r0,1686=r6,1673=r7,1618=r3,1708=r4,1704=r3`
- L = mv_5_1+t1n+m_crl2+devol p2: `1687=r6,1674=r7,1619=r3,1709=r4,2173=r0,1705=r3,1908=r6,2199=r3`
- L + s_tai2 p2: `1687=r6,1674=r7,1619=r3,1709=r4,1705=r3,1908=r6,2128=r0`
- L + s_tai2 p1: `1687=r6,1674=r7,1619=r3,1709=r4,1705=r3`
- L = mv_5_1+t1n+m_crl2+devol p1: `1687=r6,1674=r7,1619=r3,1709=r4,2173=r0,1705=r3`
- L + sh_iflet+rP_back p1: `1692=r6,1679=r7,1626=r3,1714=r4,2178=r0,1710=r3`
- L + s1 p1: `1640=r3,334=r2,355=r2,1684=r6,1671=r7,352=r7,1616=r3,1647=r5,346=r4,2143=r7,1701=r3,1705=r4`

Early findings (more rows and the hand-off follow):
- Every L composite keeps the 11-slot window rotation (`rot` 11-12, forced and unforced). The RA forces are main's own
  families with vreg numbers shifted by +1..+3 (1687=r6 = main 1684=r6, 1674=r7 = 1671=r7, 1619=r3 = 1617=r3, 1709=r4 =
  1706=r4, 1705=r3 = 1702=r3, 1908=r6 = 1906=r6, 2128=r0 = 2127=r0); main's head forces 2145=r9 and 467=r2 have no
  colour miss left in L. So L's joint lead over main (+11/+12 at pass 2) is all spill-slot permutation: L's forced M is
  lower (2,263 vs 2,282) and its forced Mperm higher (2,345 vs 2,338).
- The payload phi force (main `1657=r9`, w15a33) is `%1659` in L (same weight, size and votes). On L it is a collapse:
  `1659=r9` gives 0.56022 @27,400 (L2 0.749), sticky or not; on main `1657=r9` gives 0.66867 @27,280 (L2 0.798).
- B / Br (the original's validate block order) is worth +28 M on main but only +12 on L. With forces, joint:
  main+Br+7f 2,356, main+Br+9f 2,366; L+Br+6f 2,353, L+Br+8f 2,365, L_tai2+Br+5f 2,357, Lc2+Br+6f 2,363. Under the
  original's validate order the L lead disappears (ties or loses by 1-3).
