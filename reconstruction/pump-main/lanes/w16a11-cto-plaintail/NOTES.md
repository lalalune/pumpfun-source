# w16a11-cto-plaintail: the faithful tail priced as one union (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `1f4e396b5` (w16a07 sweeptuple #3859 landed after the angle was written; `admin_cto.rs` is unchanged on
`599891304`): admin_cto 0.67436, 3,141 slots, M 2,251, Mperm 2,295, Mhc 2,302, 1034/1035.
Angle: price the faithful tail forms as one union instead of one form at a time, and test whether one missing register
fact (sharing tag in r6, swept in r9) blocks all of them.
Ledger: approach `plaintail`, keys `0x22a10-w16-<sha7>-plaintail-<cell>-v1` (22 capture rows + 7 analysis rows).

**Result: notes only, no source change. The kill test holds on all three counts.**
1. No union, leave-one-out or pair, on main or on L, has a realisable cell above main's. The best `+pin+regideal r9` cell
   is RS (raw-first + s1) at 2,296 (orig 0x3c00-0x5040) against main's 2,305. The best P0-family cell is P0_T at 2,249.
2. No joint ceiling exceeds main's. With the sticky RAPRIO climb plus a spill permutation, P0 reaches 2,306, P0_T 2,304,
   LP0 2,281 and LP0-S 2,329 (a tie). w16a04 measures main at 2,329 (p1) on this base.
3. The tag and swept pins close at most 28% of P0's register-only mismatches, and they cost 154-450 M.

The angle's premise is also only half right: in the original the sharing tag is **not** held in r6 over the sharing clone
run (section 4). Only `swept` in r9 is a held, whole-tail fact.

## 1. Oracle (experiment only; one build slot per capture, at most 2 at a time)

- Captures: w15a16 `scr.py` (w15a03 `capraw.py` identity build with `--emit=llvm-ir -C no-prepopulate-passes`, SDK
  `opt -O3`, slim, SDK `llc`) with the genes in `tools/genes_pt.py` (on top of w16a04 `genes_lac`). main is w16a04's
  `n_m` capture of 1f4e396 (`eq_main: true`).
- Genes (all exact single-line edits, line count held, every error line kept):
  - `pS` s1: all seven sharing AccountInfos as plain `to_account_info()`.
  - `pT` tai: the TCF program, both as the `CpiContext::new` program and as the `program:` field, as `a.pump_amm.to_account_info()`.
  - `pC` c2 family: the TCF ATAs (`coin_creator_vault_ata`, `pump_creator_vault_ata`) as `to_account_info()`.
    This is the derive clone order, lamports right after key.
  - `pN` n1po: no `nf` local, plus the owner-first pool gate.
  - `pR` raw-first: `token_raw_amount` before `token_frozen` in the sweep token arm (w14a50 `rev_ff`).
  - `pP` p2: pool CPI args inline, no `pargs` tuple.
  - `Lv`: L_vol = `mv_5_1+t1n+m_crl2+vol334_back`. This uses no `devol`; one read_volatile is left, as on main.
  - P0 = `pS+pT+pC+pN+pR+pP`. It replaces every AccountInfo struct literal in the file.
- Metrics:
  - M, Mperm and Mhc come from scr.py and `mp.py`.
  - True LCS `---`/rfj, per 0x800 chunk, comes from w14a128 `lcschunk.py` (`lcschunk-x.txt`, `lcschunk-rfj.txt`).
  - The dotmap swap flag comes from w16a09 `fuev.py`, which uses the w16-strategy ceilings `dotmap` logic.
  - L1/L2 per chunk come from `tools/lv.py`.
  - The exact cells come from w15a06 (`tools/cells.sh`): `mkdbg.sh`, then the `mirperm.py` legal pin, then w14a85
    `regideal.py` with `RF=9` (swept-only) or over all registers, for orig 0x3c00-0x5040 and 0x2800-0x5040.
- Fix for other lanes: `mirperm.py` (w14a139/w15a06) hard-coded the CPI account-infos slot name (`_55.i9\d`). On this base
  the slot is `_41.i`, so the legal pin silently failed. `tools/mirperm.py` now picks the most common LDD->ST target
  slot (or `SLOT=`). With the fix, main + legal pin = 2,294.

## 2. The table (`table.md`; main as built = 2,251)

| variant | genes | bytes | M | Mperm | Mhc | LCS --- | rfj | free | +pin | +pin+ri9 3c00 | +pin+ria 3c00 | +pin+ri9 2800 | +pin+ria 2800 | joint p1 |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| **main** | - | 27400 | 2251 | 2295 | 2302 | 2257 | 3006 | 2251 | 2294 | **2305** | 2353 | **2315** | 2463 | **2329** (w16a04) |
| **P0** | S+T+C+N+R+P | 27360 | 2028 | 2151 | 2184 | 2125 | 3038 | 2028 | 2133 | 2184 | 2309 | 2184 | 2449 | 2306 |
| P0-S | T+C+N+R+P | 27384 | 2128 | 2233 | 2242 | 2170 | 3016 | 2128 | 2171 | 2183 | 2247 | 2183 | 2387 | |
| P0-T | S+C+N+R+P | 27344 | 2093 | 2170 | 2207 | 2165 | 3036 | 2093 | 2198 | 2249 | 2374 | 2260 | 2496 | 2304 |
| P0-C | S+T+N+R+P | 27368 | 2026 | 2145 | 2178 | 2122 | 3033 | 2026 | 2131 | 2182 | 2307 | 2180 | 2443 | |
| P0-N | S+T+C+R+P | 27384 | 2026 | 2149 | 2182 | 2123 | 3036 | 2026 | 2131 | 2181 | 2305 | 2181 | 2445 | |
| P0-R | S+T+C+N+P | 27392 | 1927 | 2052 | 2085 | 2024 | 2935 | 1927 | 2032 | 2083 | 2207 | 2083 | 2347 | |
| P0-P | S+T+C+N+R | 27368 | 2035 | 2158 | 2191 | 2132 | 3038 | 2035 | 2140 | 2191 | 2312 | 2191 | 2452 | |
| **LP0** | Lv+P0 | 27360 | 2024 | 2165 | 2198 | 2110 | 3045 | 2024 | 2018* | 2042* | 2160* | 2042* | 2299* | 2281 |
| Lv | Lv | 27400 | 2236 | 2309 | 2318 | 2241 | 3013 | 2236 | 2176* | 2183* | 2176* | 2193* | 2286* | 2341 (w16a04 n_L, devol form, same M) |
| R | R | 27376 | 2244 | 2287 | 2294 | 2250 | 3007 | 2244 | 2287 | 2298 | 2346 | 2308 | 2456 | |
| RN | R+N | 27384 | 2225 | 2266 | 2273 | 2231 | 3009 | 2225 | 2268 | 2280 | 2337 | 2290 | 2447 | |
| RP | R+P | 27400 | 2223 | 2264 | 2271 | 2229 | 3007 | 2223 | 2266 | 2277 | 2337 | 2287 | 2447 | |
| NRP | N+R+P | 27376 | 2223 | 2264 | 2271 | 2229 | 3009 | 2223 | 2266 | 2278 | 2339 | 2288 | 2449 | |
| RC | R+C | 27368 | 2217 | 2283 | 2290 | 2234 | 3012 | 2217 | 2260 | 2271 | 2322 | 2282 | 2444 | |
| CNRP | C+N+R+P | 27368 | 2193 | 2257 | 2264 | 2210 | 3014 | 2193 | 2236 | 2248 | 2312 | 2259 | 2434 | |
| RT | R+T | 27392 | 2149 | 2252 | 2262 | 2190 | 3009 | 2149 | 2192 | 2203 | 2254 | 2201 | 2390 | |
| RS | R+S | 27352 | 2141 | 2197 | 2234 | 2202 | 3029 | 2141 | 2246 | **2296** | **2409** | **2306** | **2519** | |
| S1 | S | 27376 | 2146 | 2203 | 2240 | 2207 | 3028 | 2146 | 2251 | 2301 | **2414** | 2311 | **2524** | |
| SC | S+C | 27368 | 2118 | 2198 | 2235 | 2190 | 3033 | 2118 | 2223 | 2273 | 2385 | 2284 | 2507 | |
| ST | S+T | 27392 | 2050 | 2172 | 2205 | 2146 | 3030 | 2050 | 2155 | 2205 | 2317 | 2203 | 2453 | |
| SN | S+N | 27392 | 2019 | 2075 | 2112 | 2080 | 2928 | 2019 | 2124 | 2175 | 2295 | 2185 | 2405 | |
| SP | S+P | 27408 | 2014 | 2070 | 2107 | 2075 | 2926 | 2014 | 2119 | 2169 | 2292 | 2179 | 2402 | |

`*` On L heads the legal pin is not legal: the 11-slot window rotation (w16a04 `winrot`) makes `mirperm` move the wrong
colours, so pin < free there. Use L's free and regideal-only cells (Lv: ri9 2,253, ria 2,344 over 0x2800).

Leave-one-out on L (`spec4.txt`). The comparable cells on L are regideal without the pin; main's are ri9 2,258 / 2,268
and ria 2,252 / 2,362 (0x3c00 / 0x2800).

| variant | bytes | M | Mperm | Mhc | LCS --- | rfj | ri9 3c00 | ria 3c00 | ri9 2800 | ria 2800 | joint p1 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| LP0 | 27360 | 2024 | 2165 | 2198 | 2110 | 3045 | 2043 | 2162 | 2043 | 2301 | 2281 |
| LP0-S | 27384 | 2114 | 2247 | 2258 | 2154 | 3023 | 2122 | 2126 | 2122 | 2265 | 2,329 (ties main p1) |
| LP0-T | 27344 | 2091 | 2186 | 2223 | 2152 | 3043 | 2110 | 2229 | 2121 | 2350 | |
| LP0-P | 27368 | 2030 | 2171 | 2204 | 2116 | 3045 | 2049 | 2164 | 2049 | 2303 | |
| LP0-N | 27384 | 2022 | 2163 | 2198 | 2108 | 3043 | 2040 | 2158 | 2040 | 2297 | |
| LP0-C | 27368 | 2021 | 2158 | 2191 | 2106 | 3040 | 2040 | 2159 | 2038 | 2294 | |
| LP0-R | 27392 | 1924 | 2066 | 2099 | 2010 | 2942 | 1943 | 2061 | 1943 | 2200 | |

On L the pattern repeats: S and T are the as-built losers, raw-first is worth about +100 inside the union (the same
wallet-block flip, -61 at 0x5000 and -55 at 0x5800), and no cell reaches main's.
The L+one-lead rows (s1, s_tai2, c2) are w16a04's (#3855) and are not recomputed here.

What the table says:
- **Every union loses as built.** The order is main 2,251 > R 2,244 > RN 2,225 > RP/NRP 2,223 > RC 2,217 > CNRP 2,193 >
  ... > P0 2,028 > SN 2,019 > SP 2,014 > P0-R 1,927.
- **Per-form costs** (true LCS `---` by orig chunk; they are additive when there is no layout flip):
  - T: -22/-24 at 0x2800/0x3000 (the TCF clone run).
  - S: -31 at 0x4000, -10 at 0x4800, -5 at 0x3800.
  - C: -8 at 0x3000, -6 at 0x3800.
  - N: -6 at 0x4800, -11 at 0x5800.
  - P: -13 at 0x4800, -11 at 0x5800.
  - R: -7, spread thinly.
- **Ceilings.** Only the s1 family beats main in the ideal-register cell (`+pin+ria`): S1 2,414, RS 2,409, SC 2,385 and
  P0-T 2,374, against main's 2,353. That is the w15a06 s1 result (2,416 on 90300f9) reproduced on this base. T costs
  65-97 M in every cell (P0 vs P0-T, S1 vs ST, R vs RT), so no tai form keeps that ceiling. The realisable part
  (`+pin+ri9`, swept only) is 4 below main for S1 and 9 below for RS; the other s1 rows are further below.
- **Code shape.** The union has the original's skeleton but not its colours.
  - L2 (frame and registers masked) is 0.8215 for P0 against 0.7852 for main: M2 2,740 against 2,621.
  - All of the +119 is in the 0x4000-0x4800 chunk (215 against 96 L2 matches), and it comes from s1 alone (P0-S: 96).
  - True LCS rfj is +32 (3,038 against 3,006), while `---` is -132.
  - In that chunk the s1 sharing clone run is instruction-for-instruction the original's. Only registers and frame
    offsets differ (`sbs2.py` view, section 4).
- **Plain versus partial TCF forms.** w16a12's tail union `T` = `s1+s_tai2+c2+n1+po+rev_ff` (#3878) is M 2,094 @27,352,
  with cells 2,199 / 2,250 / 2,371. That is 59 above P0-P, which is the same union except for the plain conversions.
  - P0-P converts the TCF `CpiContext::new` program literal and the `coin_creator_vault_ata` literal to
    `to_account_info()` as well. `T` converts only the `program:` field (s_tai2) and only reorders
    `pump_creator_vault_ata` (c2).
  - Those two remaining literals are main-side compensators worth about 59 M as built.
- **The dotmap swap flags are artifacts.** Every flagged row shows one chunk, orig 0x4000, with a median shift of about
  -0xf88, and its neighbours are not shifted. With T (or S), the sharing program clone and the TCF program clone are the
  same rfj sequence, so the original's unique 5-grams at 0x4000 hit our TCF clone. True LCS rfj is up in those rows, not
  down. The real region moves are the +0x378 shifts in section 3.

## 3. New mechanism: frozen-first + S + (N or P) flips a 110-insn wallet cold block into the tail

- Inside the full union, raw-first is worth **+101 M** (P0 2,028 against P0-R 1,927). Alone on main it is -7 M at -24 B.
- With main's frozen-first order:
  - S+N (SN) and S+P (SP) flip a block, and so do S+T+C+N+P (P0-R). They cost an extra 95-110 M against the additive
    estimate.
  - S, S+C and S+T do not flip it.
- The block is the original's 0x55b8-0x5968 (about 110 insns). It is entered from 0x2628 `jeq r1,0,55b8`, and its Ok edge
  returns to the wallet/sweep-gate join at 0x1d28 after `ldxdw r9,[r10-0x7a8]` (the payload in r9 again).
  - The original and P0 keep it in the cold tail (P0 0x5558).
  - In the flipped builds MachineBlockPlacement puts it right after the sweep-exit join (P0-R 0x3c50).
  - That shifts orig 0x4400-0x5400 by +0x378 and costs 60 M at 0x5000 and 41-52 M at 0x5800 (L2 0x5000 chunk 232 -> 177).
- Raw-first keeps the block cold in every combination tried (P0, P0-N, RN, RP, RS). So any faithful-tail lane that adopts
  s1 together with n1po or p2 **must also take raw-first**, or it loses about 100 M to layout.
- Why raw-first differs locally (main vs R vs orig at 0x20b0-0x2140):
  - The original's raw-first does `add64 r8,72; ldxdw r6,[r10-0x2c8]` (account ref in r8, amount in r6).
  - Ours does `mov64 r6,r8; add64 r6,72; ldxdw r8,[r10-0x2c8]`. The registers are swapped because ours still needs the
    accounts base in r8.
  - Main's frozen-first gets `add64 r8,72` right by accident of RA, and that is the whole of its 7 M edge.

## 4. The register facts the faithful tail lacks (orig trace vs P0, `regfacts` row)

Original, orig 0x3c40-0x5100:
- **swept = r9** from `ldxdw r9,[r10-0x828]` at 0x3c40, untouched, until `stxdw [r10-0x218],r9` at 0x5030. This is the
  only callee-saved value held through both CPIs.
- **The sharing tag is in r6 only for the match**, 0x3c58-0x3d20. r6 is then a clone temp in the sharing run (0x3e70-0x4648).
  The tag is spilled at [r10-0x8f8] and reloaded into r6 twice:
  - at 0x4a90, held across the pool gate to 0x4c50. Here the pool pointer takes r7, the n1po blocker of w15a04;
  - at 0x4d48-0x4f28, for the event `is_some`.
- The accounts pointer is reloaded from [r10-0x8d8] before every sharing clone.

P0 (and main) at the same places:
- swept is loaded into r3 and spilled at once to [r10-0x968].
- The tag is reloaded and re-spilled to [r10-0x8e0], a greedy split artifact.
- The accounts piece `%1676` is held in r7 over the whole sharing run.
- A piece of the `!holder` family (`%2089`, root `%465`) is reloaded into r8 at the run start and never read before r8 is
  overwritten.
- The pool pointer `%357` takes r6 at the gate; the original's is r7.

Register-only mismatched pairs (regideal) in 0x3c00-0x5040:

| base | total | orig reg r9 | orig r6 | orig r0 / r1 / r2 | ours r9 | ours r6 / r7 / r8 |
| --- | ---: | ---: | ---: | --- | ---: | --- |
| main | 104 | 2 | 17 | 21 / 27 / 31 | 13 | 15 / 4 / 9 |
| P0 (= P0-T) | 196 | 2 | 41 | 43 / 56 / 56 | 50 | 25 / 26 / 18 |
| RS | | 2 | 33 | 42 / 51 / 47 | 49 | 25 / 11 / 18 |

So swept-in-r9 is worth about 2 direct pairs. Its value is indirect: r9 is never free for temps in the original, and P0
uses r9 as a temp in 50 mismatched pairs. The larger mismatch families are the r0/r1/r2 temps of the clone run.

### Pins (`tools/tpin.sh`; pre-coalescer physreg pins at the sweep-exit join `bb.269.bb88`, w15a06 swr9 method)

| base | round trip | swept -> r9 | tag -> r6 | both |
| --- | --- | --- | --- | --- |
| main | 2,251 (104 pairs, ria 2,252) | 1,525 @27,464 (alignment lost) | 1,991 @27,224 (118 pairs, ria 2,043) | 1,811 (114 pairs) |
| P0 | 2,028 (196 pairs, ria 2,177) | 1,578 (1 pair left: alignment lost) | 1,874 @27,192 (142 pairs, ria 1,973) | 1,758 @27,344 (153 pairs, ria 1,859) |

- The tag pin removes 54 of P0's 196 register-only pairs (28%), or 50 of its 149-M regideal gap. It costs 154 M.
- The swept pin destroys the alignment on both bases. The sticky RA force on the swept piece, `1720=r9`, gives 0.48943.
  That piece is the sweep-exit phi, and it spans every sweep exit from 0x1d28 to 0x3bb8, not just the tail. No
  RA-faithful pin covers only the post-sweep part, because the coalescer merges the join copy into the phi.
- So neither fact closes half of the gap. The fact the original needs is a function-wide one: the Result payload phi and
  swept in r9 (w15a33 `1657=r9`). It cannot be imposed locally.

### The decisive vregs (`dbgocc.py` replay of `llc -debug-only=regalloc` on P0, `dbgocc-P0` row)

| at the selectOrSplit of | r6 | r7 | r8 | r9 |
| --- | --- | --- | --- | --- |
| `%56`, the sharing tag | small pieces only | `%4` (1648..19808) | **`%0` accounts, whole function** | **`%465` holder flag, 3216..64416** |
| `%1619`, the sweep payload phi (swept) | small pieces | `%1180` | **`%0` accounts** | **`%465` holder flag** |
| `%1720`, swept's split piece | small pieces | `%1652` Result tag phi (4960..71648) | `%246` | **`%1702`, a piece of the `%465` family (17992..56112)** |

- The tail values lose r9 and r8 to the same two head-to-tail values that block main: the holder flag `%465`, which is live
  from the entry to the curve update, and the accounts pointer `%0` (w15a14, w15a33).
- In the original, both are memory-resident in the tail: accounts is reloaded from [r10-0x8d8] at every use, and the holder
  flag is spilled per arm. That is how swept gets r9.
- So **the faithful tail's register fact is a head fact.** The union cannot get it on a main-like head.
- Sticky prices on P0:
  - `465=spill`: 2,020 (-8; L1 +0.012, L2 -0.007).
  - `465=spill` + `1720=r9`: 1,585 (L2 0.604).
- Spilling the accounts pointer for the whole function (`0=spill`) costs 250-515 M and adds 550-700 B on every base:
  main 1,736 @28,096, R 1,807, P0 1,779, RS 1,779 (`spillforces` row).
  - The original keeps accounts in a register in the head and reloads it only in the tail.
  - So the needed fact is a tail-only split of `%0`, which no force reproduces.
- Raw-first's own -7 M is the same fact. The original's `add64 r8,72` consumes the accounts base in place. Ours copies it
  (`mov64 r6,r8; add64 r6,72`), because `%0` stays live in r8.

## 5. Sticky RAPRIO joint ceilings (w16a04 `lpipe.sh` = w15a28 pipe.sh; sticky colmap screen of 80, 12-round climb, permhc)

| base | as built | climb (forces) | forced M | forced Mperm | joint | true LCS vs main (---/rfj) |
| --- | --- | --- | ---: | ---: | ---: | --- |
| main (w16a04 n_m) | 2,251 | 0.68275 @27,376 (7) | 2,278 | 2,322 | **2,329** | +27/+3 |
| P0 | 2,028 | 0.64956 @27,296 (12) | 2,164 | 2,306 | 2,306 | -27/+40 |
| P0-T | 2,093 | 0.66236 @27,184 (9) | 2,202 | 2,283 | 2,304 | +1/+27 |
| LP0 | 2,024 | 0.65037 @27,328 (11) | 2,168 | 2,261 | 2,281 | -62/+32 |
| LP0-S | 2,114 | 0.66767 @27,360 (12) | 2,227 | 2,319 | 2,329 | -15/+18 |

- P0's climb forces are main's own families with new numbers: 1675=r6/1677=r6 (accounts pieces, main 1684=r6) and
  332=r2, 323=r4, 350=r7, 1665=r7, 467=r2, 2145=r7, 216=r9, 2179=r5.
- Its first force is `1958=r7`, the TCF program lamports Rc. This is w15a26's marker, and it fails on P0: the Rc lands in
  r5 without forces, exactly as on tai alone.
- P0-T's climb starts with `1651=r9`, the payload phi (-152 B).
- Neither tag nor swept appears in any climb.

## 6. Verdict and hand-off

- Kill test: realisable max 2,296 (RS) < 2,305; joint max 2,329 (LP0-S, a tie with main p1; P0 2,306) <= 2,329 < 2,338;
  pins close at most 28% < 50%. The faithful tail is closed on main-like heads. The allfaith lane (w16a12) picks it up
  with heads.
- What the faithful tail is worth, and what it needs:
  - It is worth +119 L2 (the sharing CPI's code shape) and +61 M in the ideal-register cell, all of it s1's.
  - It needs the original's register naming of the clone-run temps and swept in r9 from the sweep exit to the event.
  - Both need r8 and r9 free in the tail, which means the head's holder flag `%465` and the accounts pointer `%0` must
    not be register-resident there (section 4).
  - Neither is reachable by a pin or a sticky force without losing more elsewhere.
- For the allfaith lane:
  - Take raw-first whenever s1 is combined with n1po or p2 (section 3).
  - Drop tai unless a head change lands the TCF lamports Rc in r7.
  - c2/n1po/p2 are cost-neutral inside P0 (+-7), but each costs 19-27 M on top of raw-first alone (RN, RC, RP).

## Tools (`tools/`, experiment only)

- `genes_pt.py`: the union genes (P0 parts, Lv).
- `cells.sh <name> <m.ll>`: the w15a06 exact cells over two orig ranges.
- `tpin.sh <name> <m.ll>`: tag->r6 / swept->r9 pre-coalescer pins, with auto-detection of bb88, swept and tag.
- `lv.py`: L1/L2 and per-chunk L2.
- `sbs2.py <fn.bin> lo hi`: L2-aligned side-by-side against the original, with `R`/`f` marks for register and frame mismatches.
- `mirperm.py`: the w14a139/w15a06 legal-pin tool with slot auto-detection.
- `dbgocc.py` (w15a33, copied): occupancy replay of `-debug-only=regalloc`.
- `evalall.sh`, `table.py`, `rec.py`: the evaluation loop, table and ledger rows.
- `spec*.txt`: capture specs.
- Data: `captures.jsonl` (scr rows), `cells.jsonl`, `fuev.jsonl`, `joint.jsonl`, `lcschunk-x.txt`, `lcschunk-rfj.txt`, `table.md`.
