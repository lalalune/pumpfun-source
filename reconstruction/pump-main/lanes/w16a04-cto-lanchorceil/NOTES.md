# w16a04-cto-lanchorceil: joint RA+frame ceiling matrix of L-anchored composites (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `9bd38c7d5` (`admin_cto.rs` unchanged since 9120883a9): 0.67376, 3,124 slots, M 2,249, 1034/1034. Re-checked on
main `1f4e396` (w16a07 sweeptuple, 0.67436 / 3,141) in section 5; the branch merges it.
Angle: build the joint RA + frame ceiling matrix of composites anchored on the L basin
(L = `mv_5_1+t1n+m_crl2+devol`: cashback before creator in the CtoState literal, `if new.is_none()` in the shared arm,
`let cr=` creator binding, both read_volatile placeholders removed), then hand off the decisive forces.
w15a32-cto-lbasinweight owns L's spill-weight lever; this lane did not repeat its source screens.
Ledger: approach `lanchorceil`, keys `0x22a10-w16-9bd38c7-lac-*-v1`.

**Result: notes only, no landing (clean kill of the force hand-off).** Several L composites have joint ceilings above
main's 2,338: L_tai2+c2 2,359 (pass 1), L+c2 2,358 (pass 2), L 2,350 (pass 2). The c2 part carries most of it (main+c2
2,354 at pass 2). Every decisive force is a register-naming choice
with no source lever: main's own force families (event accounts piece, post-event tail piece, TCF clone run), the c2
clone-temp tax, and one new L-specific pair (the holder piece). The best zero-loss measurement stays main
(0.67376 / 3,124 / 27,400 B).

New for other lanes:
1. **The holder-piece force pair** `1702=r5,2094=r6` (vreg ids on L) turns L's frame potential into real matches:
   L 0.66926 -> **0.67775 @27,392** (+28 M, window rotation 11 -> 6 slots), with two forces and no other change. It is
   the RA-level form of w15a32's two-fact cell (holder arg reloaded once; cashback byte spilled on the freq-1 path).
   Mechanism and failed levers in section 4.
2. **c2 is a joint lead on main itself** (main+c2 pass-1 joint 2,346 vs main 2,328), but only through its tax force
   (`2178=r0`, the TCF `pump_creator_vault_ata` clone temp in r0; LOO -26). Without it c2 is 2,320.
3. **The B / Br relayout must use positional block resolution on L.** w14a98's content resolver mis-maps two blocks on L
   and makes B look worthless there (+12 instead of +28). Corrected, B is worth +28 on both main and L, and the L lead
   survives the original's validate order (section 3).
4. The payload-phi force (`1657=r9` on main, w15a33) is a collapse on L (`1659=r9`: 0.56022).

## 1. Oracle (experiment-only; only the captures take a build slot)

- Captures: w15a16 `scr.py` (w15a03 capraw identity build with `--emit=llvm-ir -C no-prepopulate-passes`, SDK `opt -O3`,
  slim, SDK `llc`), genes from `tools/genes_lac.py` (= w15a32 `genes_lbw` + c2, s1, tf_g1a, n1, po, mfh_*).
  `m0` reproduces main (`eq_main: true`). Its slim module equals w15a28's `m0` capture except one declaration hash, so
  main's pass-1/pass-2 rows are w15a28's (#3746). **L reproduces 0.66926 / 3,075 slots at 27,400 B exactly.**
- `tools/lpipe.sh <rx> [N K R P BASEFORCE]` (w15a28 `pipe.sh` generalised): w14a84 `colmap.py` vote under the sticky
  RAPRIO llc (w15a24 `llc-patch`), sticky single screen of the top 80 colour misses, greedy sticky climb over the top 30
  (ratio objective, free size, up to 12 rounds), forced build, joint `permhc` (forces + best spill-offset permutation +
  vote swap climb), true LCS vs main (`evall.py`), window-rotation check. Pass 2 = the same with the pass-1 forces as
  base (`TAGSFX=p2`).
- `tools/winrot.py`: for the 13 spill offsets `-2264..-2360`, the original offset that each slot's aligned accesses
  vote for. `rot` counts the slots whose vote differs from main's: main 0, L 11.
- `tools/brjoint.sh` with `BRPOS=1`: w14a87's `B` validate block order (Bspec963 names) applied to the sticky-forced asm,
  with (`Br`, condition reversal) and without (`B`) flips, then joint `permhc`. `BRPOS=1` maps the 26 spec blocks by
  main's block index (the span 14..39 has the same block count in every L variant). w14a98's content resolver
  (`sub.border2`) maps `bb95.i` to block 78 and `bb23.i` to block 48 on L. That pulls 38 blocks of the 0x2000 region
  into the span and costs about 16 M; the first pushed table used it.
- `tools/loo.py`: leave-one-out joint value of each force in a set. `tools/table.py` renders the matrix.

## 2. Joint-ceiling matrix (sorted by joint; main rows are w15a28 #3746)

`joint` = Mhc of the forced build (RA forces + any legal spill-offset permutation). `d` is against main's pass-2 2,338.

| composite | pass | bytes | M | Mperm | Mhc | forces | climb ratio @ bytes | forced M | forced Mperm | joint | d joint vs main p2 | true LCS ---/rfj vs main | window rot (unforced/forced) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | --- | --- |
| main | p1 | 27400 | 2249 | 2293 | 2300 | 7 | 0.68245 @ 27376 | 2277 | 2321 | **2328** | -10 | 28/3 | 0/0 |
| main | p2 | 27400 | 2249 | 2293 | 2300 | 9 | 0.68395 @ 27376 | 2282 | 2338 | **2338** | +0 | 35/2 | 0/0 |
| L_tai2 + c2 | p1 | 27392 | 2199 | 2305 | 2314 | 9 | 0.67984 @ 27416 | 2270 | 2354 | **2359** | +21 | 22/16 | 11/11 |
| L + c2 | h [1701=r5,2093=r6,2172=r0 (holder pair + c2 tax)] | 27392 | 2205 | 2300 | 2309 | 10 | 0.68385 @ 27384 | 2282 | 2352 | **2359** | +21 | 32/6 | 11/6 |
| L + c2 | p2 | 27392 | 2205 | 2300 | 2309 | 9 | 0.67775 @ 27392 | 2262 | 2353 | **2358** | +20 | 12/9 | 11/11 |
| main + c2 | p2 | 27392 | 2218 | 2285 | 2292 | 10 | 0.68245 @ 27376 | 2277 | 2349 | **2354** | +16 | 28/3 | 0/3 |
| L + n1 + po | h [358=r7 (pool ptr)] | 27416 | 2105 | 2176 | 2185 | 9 | 0.67975 @ 27400 | 2269 | 2349 | **2353** | +15 | 17/13 | 12/10 |
| L + c2 | p1 | 27392 | 2205 | 2300 | 2309 | 6 | 0.67536 @ 27392 | 2254 | 2346 | **2350** | +12 | 4/12 | 11/11 |
| L = mv_5_1+t1n+m_crl2+devol | p2 | 27400 | 2234 | 2307 | 2316 | 8 | 0.67775 @ 27416 | 2263 | 2345 | **2350** | +12 | 13/10 | 11/11 |
| L + s_tai2 | p2 | 27400 | 2228 | 2312 | 2321 | 7 | 0.67536 @ 27392 | 2254 | 2349 | **2349** | +11 | 9/11 | 11/11 |
| L + n1 | p1 | 27376 | 2224 | 2297 | 2306 | 8 | 0.67855 @ 27400 | 2265 | 2345 | **2349** | +11 | 15/9 | 12/10 |
| main + c2 | p1 | 27392 | 2218 | 2285 | 2292 | 8 | 0.68035 @ 27376 | 2270 | 2342 | **2346** | +8 | 21/6 | 0/3 |
| L_tai2 + po | h [358=r7 (pool ptr)] | 27440 | 2097 | 2179 | 2188 | 6 | 0.67506 @ 27392 | 2253 | 2336 | **2345** | +7 | 4/16 | 11/11 |
| L + po | h [359=r7 (pool ptr)] | 27440 | 2103 | 2174 | 2183 | 7 | 0.67735 @ 27400 | 2261 | 2341 | **2345** | +7 | 9/12 | 11/11 |
| L + s_tai2 | p1 | 27400 | 2228 | 2312 | 2321 | 5 | 0.67386 @ 27392 | 2249 | 2332 | **2341** | +3 | 2/12 | 11/11 |
| L = mv_5_1+t1n+m_crl2+devol | p1 | 27400 | 2234 | 2307 | 2316 | 6 | 0.67615 @ 27400 | 2257 | 2337 | **2341** | +3 | 7/8 | 11/11 |
| L + sh_iflet+rP_back | p1 | 27400 | 2234 | 2307 | 2316 | 6 | 0.67615 @ 27400 | 2257 | 2337 | **2341** | +3 | 7/8 | 11/11 |
| L = mv_5_1+t1n+m_crl2+devol | h [1702=r5,2094=r6 (holder pair)] | 27400 | 2234 | 2307 | 2316 | 8 | 0.68255 @ 27392 | 2278 | 2336 | **2340** | +2 | 30/4 | 11/6 |
| L + tf_g1a | p1 | 27456 | 2224 | 2296 | 2303 | 8 | 0.67604 @ 27456 | 2259 | 2334 | **2338** | +0 | 9/10 | 11/11 |
| L + s1 | p1 | 27376 | 2139 | 2215 | 2255 | 12 | 0.66247 @ 27320 | 2208 | 2315 | **2332** | -6 | 3/34 | 12/12 |

- L_tai2 + c2 p1: `2183=r0,1686=r6,1673=r7,1882=r6,1618=r3,1076=r3,2191=r0,1708=r4,1704=r3`
- L + c2 h: `1701=r5,2093=r6,2172=r0,1673=r7,1907=r6,2181=r5,1618=r3,1708=r4,1704=r3,2125=r0`
- L + c2 p2: `2172=r0,1686=r6,1673=r7,1618=r3,1708=r4,1704=r3,1907=r6,2181=r5,2265=r2`
- main + c2 p2: `2178=r0,1683=r6,1670=r7,1616=r3,467=r2,2144=r9,1705=r4,1701=r3,1905=r6,2187=r5`
- L + n1 + po h: `358=r7,1684=r6,1672=r7,1617=r3,1706=r4,2168=r0,2174=r6,2254=r2,1702=r3`
- L + c2 p1: `2172=r0,1686=r6,1673=r7,1618=r3,1708=r4,1704=r3`
- L = mv_5_1+t1n+m_crl2+devol p2: `1687=r6,1674=r7,1619=r3,1709=r4,2173=r0,1705=r3,1908=r6,2199=r3`
- L + s_tai2 p2: `1687=r6,1674=r7,1619=r3,1709=r4,1705=r3,1908=r6,2128=r0`
- L + n1 p1: `1685=r6,1673=r7,1618=r3,1707=r4,2169=r0,2175=r6,2255=r2,1703=r3`
- main + c2 p1: `2178=r0,1683=r6,1670=r7,1616=r3,467=r2,2144=r9,1705=r4,1701=r3`
- L_tai2 + po h: `358=r7,1686=r6,1673=r7,1618=r3,1708=r4,1704=r3`
- L + po h: `359=r7,1686=r6,1673=r7,1618=r3,1708=r4,2172=r0,1704=r3`
- L + s_tai2 p1: `1687=r6,1674=r7,1619=r3,1709=r4,1705=r3`
- L = mv_5_1+t1n+m_crl2+devol p1: `1687=r6,1674=r7,1619=r3,1709=r4,2173=r0,1705=r3`
- L + sh_iflet+rP_back p1: `1692=r6,1679=r7,1626=r3,1714=r4,2178=r0,1710=r3`
- L = mv_5_1+t1n+m_crl2+devol h: `1702=r5,2094=r6,1674=r7,1619=r3,1709=r4,2173=r0,1705=r3,2126=r0`
- L + tf_g1a p1: `1688=r6,472=r2,1675=r7,2182=r0,1620=r3,1710=r4,1285=r2,1706=r3`
- L + s1 p1: `1640=r3,334=r2,355=r2,1684=r6,1671=r7,352=r7,1616=r3,1647=r5,346=r4,2143=r7,1701=r3,1705=r4`

Unforced rows that were not piped: L+mfh_st 2,110 @27,392, L+mfh_q 1,957 @27,256, L+mfh_a 1,950 @27,448 (section 4);
L+1659=r9 0.56022 @27,400.

Readings:
- Every L composite keeps the 11-slot window rotation unforced. The RA forces are main's own families, with vreg ids
  shifted by +1..+3: 1687=r6 = main 1684=r6 (event accounts piece), 1674=r7 = 1671=r7 (post-event tail accounts piece),
  1619=r3 = 1617=r3 (TCF pcva Rc overflow flag), 1709=r4 = 1706=r4, 1705=r3 = 1702=r3, 1908=r6 = 1906=r6,
  2128=r0 = 2127=r0. Main's head forces 2145=r9 and 467=r2 have no colour miss left in L: L's head already has them.
- L's joint lead over main (+12 at pass 2) is all spill permutation. L's forced M is lower than main's (2,263 vs 2,282) and
  its forced Mperm higher (2,345 vs 2,338).
- c2 carries most of the composite gain: main+c2 2,346 and L 2,341 at pass 1, against L+c2 2,350. The gains are
  sub-additive.
- sh_iflet+rP_back is neutral on L (a different binary with identical M, Mperm, Mhc and forces). s1, tf_g1a and po are
  below main.

## 3. B / Br (the original's validate block order, w14a87) on top, positional resolution

| build | base M @ bytes | +Br M @ bytes | joint (+Br) |
| --- | --- | --- | ---: |
| main | 2,249 @27,400 | 2,277 @27,408 | 2,328 |
| main + 7 p1 forces | 2,277 @27,376 | 2,305 @27,384 | 2,356 |
| main + 9 p2 forces | 2,282 @27,376 | 2,310 @27,384 | 2,366 |
| L | 2,234 @27,400 | 2,262 @27,408 | 2,344 |
| L + holder pair | 2,262 @27,392 | **2,290 @27,400** (0.68604) | 2,341 |
| L + pair + 6 forces (pass h) | 2,278 @27,392 | **2,308 @27,400** (0.69143) | 2,369 |
| L + 6 p1 forces | 2,257 @27,400 | 2,286 @27,408 | 2,369 |
| L + 8 p2 forces | 2,263 @27,416 | 2,295 @27,424 | 2,381 |
| L_tai2 + 7 p2 forces | 2,254 @27,392 | 2,282 @27,400 | 2,376 |
| L+c2 + 9 p2 forces | 2,262 @27,392 | 2,290 @27,400 | **2,385** |

Br adds +28 to +32 M on every base, so B and the L basin are additive. Under the original's validate order the L
lead holds (+13 to +19 joint). B itself is still not source-reachable (w14a98).

## 4. Force hand-off (composites whose joint beats 2,338 by 10 or more)

Leave-one-out joint values (`data/loo-*.out`):

| composite (joint) | force | LOO d joint | value / region (orig offsets) | lever? |
| --- | --- | ---: | --- | --- |
| L+c2 p2 (2,358) | `2172=r0` | -23 | c2 tax: TCF `pump_creator_vault_ata` clone temps (is_writable/is_signer/executable/rent/owner copies) in r0, orig 0x3370-0x33b8 | no: TCF clone naming cascade; the force evicts `%209` from r0 (orig keeps that value in r6). w15a24 c2climb, w14a17 729 placements, w14 sweepr0 |
| | `1686=r6` | -7 | event accounts piece (split of `%0`), 0x4e80-0x50e8 | no: w15a33 chain ends at the payload phi in r8 (needs r9 free at wallet sites); w15a04 n1 |
| | `1673=r7` / `1907=r6` | -7 / -7 | post-event tail accounts piece 0x5cc0-0x5d78 / sharing CPI program clone temp | no: w15a12 wallet chain; w15a24 1906 chain (`%465` piece) |
| L p2 (2,350) | `1687=r6` | -24 | event accounts piece | no (as above) |
| | `2173=r0` | -17 | TCF pcva clone temps in r0 (the c2 tax site; on main the same force is -0.0019) | no (as above) |
| | `1674=r7` / `1908=r6` | -7 / -7 | post-event tail piece / sharing program clone temp | no |
| main+c2 p1 (2,346) | `2178=r0` | -26 | c2 tax | no |
| | `467=r2` | -9 | head piece (main's own force) | no |

None of these has an ordinary spelling in the ledger. Main's own copies are traced by w15a24 (#3736), w15a33 (#3829),
w15a12 (#3686) and w15a04 (#3700).

### The holder-piece pair (new, L-specific)

- Vregs on L: the holder arg `%384` (r3) is split into 1701 (spilled, SS#184), **1702** (local piece over bb8..validate
  head) and 1703. In main the matching piece is 1699 (size 600, weight 2.40e-3) and keeps r5 to the validate head
  (`mov64 r8,r5; and64 r8,-3`).
- In L the list-ilp schedule of IR block bb11 puts the max_fee load (`ldxdw [global+1072]`, `%10`) after the cashback
  select diamonds, in the last machine block (bb12). The max_fee piece **2094** (size 420, weight 2.93e-3) then evicts
  the holder piece 1702 (size 712, weight 2.16e-3) from r5, because 1702 is lighter than the `new` pointer piece 1952 in
  r6 (2.38e-3). 1702 is re-split, the second piece is spilled to SS#184, and the holder arg is reloaded twice (bb8 and
  validate bb6.i): w15a32's weight 2.3789 that rotates the window.
- Forcing `1702=r5` (sticky) plus `2094=r6` sends max_fee to r6, which evicts the `new` piece. The final spills move
  exactly as in w15a32's best SSC cell (holder arg loses a spill piece, the cashback byte SS#317 gains one):

| forces on L | ratio @ bytes | window rot |
| --- | --- | ---: |
| none | 0.66926 @27,400 | 11 |
| `1702=r5` | 0.67026 @27,392 | |
| `1702=r5,2094=r6` | **0.67775 @27,392** | 6 |
| `1702=r5,2094=r0` / `r1` / `r2` | 0.67745 @27,416 / 0.67705 @27,424 / 0.67525 @27,424 | 6 / 6 / 5 |
| `1702=r5,2094=r3` / `r9` | 0.67196 @27,400 / 0.67136 @27,400 | 11 / 10 |
| pair + climb (pass h: +1674=r7, 1619=r3, 1709=r4, 2173=r0, 1705=r3, 2126=r0) | 0.68255 @27,392, joint 2,340 | 6 |
| L+c2 with its pair `1701=r5,2093=r6` | 0.66886 @27,384 (from 0.66067); + `2172=r0` 0.67745 @27,392 | 6 |

  The pair does not raise the joint (Mhc 2,314 against L's 2,316). It realises the matches that the free spill permutation
  already counts, and it conflicts with `1687=r6` (pair + 1687=r6: 0.67156).
- Levers tried (raw-IR captures, all fail): max_fee read into a local before the literal (`mfh_st`, 2,110 @27,392 = w15a32's
  E3), before `quote_locked` (`mfh_q`, 1,957 @27,256), at the head (`mfh_a`, 1,950 @27,448). Every CtoState literal order
  with cashback first or second is w15a16 spec8 (17 tie L, the rest worse, e.g. max_fee before creator 2,110).
  RAPRIO_WEIGHT cannot test the weight story directly (1702 is a split product created after the weight hook).
- What a lever must do: keep the max_fee load in the bb8 segment (main's r6 position) without moving the cashback load,
  or shorten the holder piece by about 70 slot units (5 instructions) so it outweighs the `new` piece. With such a lever L
  would sit at about 0.6778 with 8 B to repay.
- Single forces do not reproduce the pair: `2094=r6/r7/r9/r4`, `1952=r9/r7`, `2093=r5`, `2092=r6` give 0.6667-0.6701.
  The holder piece must also keep r5.

### Size-pinned RA ceilings (sticky climb with `--size 27400`, no spill permutation)

| base | forces | ratio @27,400 |
| --- | --- | ---: |
| main (w15a24 #3736) | 1684=r6, 1671=r7, 1906=r6, 1617=r3, 1706=r4, 1384=r5, 1314=r7, 2251=r2 | 0.68244 |
| main, 3 forces (w15a28 climb) | 1684=r6, 1671=r7, 1617=r3 | 0.67945 |
| L | 1687=r6, 1674=r7, 1619=r3, 1709=r4 (then no improvement) | 0.67525 |
| L + holder pair | pair + 2173=r0 | 0.67825 |
| L + holder pair | pair + 2173=r0, 1674=r7, 1619=r3, 1709=r4, 2126=r0 (then no improvement) | 0.68214 |
| L + po (pool ptr `359=r7`) | 359=r7, 1686=r6, 1673=r7, 1618=r3, 1708=r4, 2172=r0, 1704=r3 | 0.67735 |
| L + n1 + po (`358=r7`) | 9 forces (`data/joint.jsonl`) | 0.67975 |

At the pinned size the L basin is not a better RA base: even with the holder pair for free its ceiling (0.68214) stays
just below main's (0.68244). Its joint lead exists only with a free spill permutation.

### Owner-first pool gate (po) on L

The pool-pointer force keeps its id on L (`359=r7`: L+po 0.62955 @27,440 -> 0.67046 @27,400, +4 M over L, as on main).
On L_tai2+po and L+n1+po it is `358=r7` (0.66866 @27,400 and 0.66777 @27,376). The colmap screen does not list it, so the
plain pass-1 pipes on the po composites missed it (L+po p1 joint 2,241); the table uses pipes with the pool force as base.

## 5. Re-check on main 1f4e396 (w16a07 sweeptuple #3859, admin_cto 0.67436)

Main moved while this lane ran (sweep AMM guard as a tuple match, event `is_holder_reward` first). All genes still apply.

| capture on 1f4e396 | bytes | M | Mperm | Mhc | rot |
| --- | ---: | ---: | ---: | ---: | ---: |
| main (`eq_main: true`) | 27,400 | 2,251 | 2,295 | 2,302 | 0 |
| L | 27,400 | 2,236 | 2,309 | 2,318 | 11 |
| L + c2 | 27,392 | 2,205 | 2,300 | 2,309 | |
| main + c2 | 27,392 | 2,218 | 2,285 | 2,292 | |

- The sweeptuple gain (+2 M) carries onto L unchanged and does not reach the c2 rows.
- The holder pair carries over with new ids (the holder arg is `%385` now): `1703=r5,2095=r6` gives L 0.67835 @27,392
  (rot 6); adding `2174=r0` (the TCF clone temp) gives **0.67855 @27,400** (main 0.67436).
- Joint pipes (pass 1) on 1f4e396: main 7 forces 0.68275 @27,376, forced M 2,278, **joint 2,329** (old main 2,328);
  L 6 forces 0.67615 @27,400, **joint 2,341** (+12); L+c2 6 forces 0.67566 @27,392, **joint 2,351** (+22). The forces are the
  same families with ids +1 (`1688=r6,1675=r7,1620=r3,1710=r4,1706=r3,2174=r0` on L). The matrix above holds on the new
  main to within 1-2 M.

## 6. Ledger rows

`0x22a10-w16-9bd38c7-lac-{m0,L,L_tai2,Lc2,Ls1,Lsh,Ltf,Ln1,Lpo,Ln1po,Ltpo,Mc2,Ltc2,Lmfst,Lmfq,Lmfa}-v1` (captures),
`...-lac-jointmatrix-v1`, `...-lac-holderpair-v1`, `...-lac-payload1659-v1`, `...-lac-brpos-v1`, `...-lac-loo-v1`,
`...-lac-mfhoist-v1`, `...-lac-poforce-v1`; on 1f4e396 `0x22a10-w16-1f4e396-lac-{n_m,n_L,n_Lc2,n_Mc2,recheck}-v1`.

## Files

- `tools/`: `lpipe.sh`, `rowsum.py`, `winrot.py`, `brjoint.sh`, `loo.py`, `table.py`, `genes_lac.py`.
- `data/joint.jsonl` (matrix rows with forces), `data/loo-*.out`, `data/brjoint_pos*.out` (positional B rows; `brjoint*.out`
  are the mis-resolved first runs), `data/hold_L.scr`, `hold1_L.scr`, `hold_Lc2.scr`, `hold_nL.scr` (holder pair grids),
  `data/po_L.scr`, `po_scan.jsonl` (pool-pointer force), `data/climb-size27400.jsonl` (size-pinned climbs),
  `data/payload_nonsticky.jsonl`.
- Experiment tools are not standalone: they expect this lane's `$OUT` layout (copies of w15a28's `t2/` and `t84/`, the
  w15a24 sticky llc at `$OUT/llvmb/bin/llc`, w14a98's relayout tools in `$OUT/t98`). The slim captures `rx/*/m.ll` stay in
  `$OUT` for reuse.
