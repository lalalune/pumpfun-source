# w16a12-cto-allfaith: faithful head forms H x faithful tail union T (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `1f4e396b5` / `599891304` (admin_cto.rs identical; #3859's sweep tuple had just landed):
0.67436, 3,141 slots, M 2,251, Mperm 2,295, Mhc 2,302, true LCS 2,257 / rfj 3,006, restored joint p1 2,329 (7 forces).
Angle: price faithful head forms crossed with the faithful tail union. Hypothesis: each side loses alone because the other
side of the function is tuned to main.
Ledger: approach `allfaith`, keys `0x22a10-w16-5998913-allfaith-<cell>-v1` (one row per capture, written by `scr.py`), plus
the summary rows `0x22a10-w16-5998913-allfaith-{e1x,ftcxT,ftcT-jointp2,table,loo}-v1`.

**Result: notes only, no landing; main is still the best zero-loss measurement (0.67436 / 3,141 slots / 27,400 B).
The kill test does NOT hold, so the hypothesis stays open, narrowed to one pair.**

| kill-test condition | verdict |
| --- | --- |
| no H x T restored joint within 40 M of 2,338 | **fails**: `ftcT` (frame-faithful fee-tag phi x T) p2 joint **2,342** > main p2 2,339 (same pipeline, converged climbs); h1T (running) |
| no realisable cell beats 2,302 | holds: best H x T pin+ri9 is h1T 2,195 (main 2,305); best H x T as built h1T M 2,075 (main 2,251) |
| LOO: every form loses inside the basin | **fails**: in the artifact-free metric ft/ftc (+145 / +130), the holder form h1 (+30 / +81), rev_ff (+58), n1 (+21) and c2 (+18 / +11) help inside the basin while losing alone; per-arm cashback, s1 and po lose in both |

What is confirmed (details in sections 3-5):
- **The tail union T is tuned against main's fee handling.** It costs -83 stacked on main's head but gains +56 on `ftc`'s
  head (the fee re-made in validate's arms, the fee argument dying in validate as in the original): I = +139 stacked,
  +141 Mhc. For the other heads I is about 0 (h1, e1, S1) or shared layout or frame damage (h2, h2p, S2, hc, ft).
- **ftcT's ceiling passes main only through RA forces.** It has 17 sticky forces, the decisive ones being 236=r5, 325=r4
  and 2140=r7 in the TCF and sharing-CPI clone runs. Its fee carrier `ftc` is an oracle: two semantically no-op stores. No
  ordinary spelling that keeps validate's `Result<Pubkey>` layout was found. Returning the fee (`ft`) or a holder flag
  (`S1`/`S2`) moves the Pubkey off Result offset 1, drops main's 7 B `target.sroa.0` piece and shifts every spill slot.
- None of the three original facts (swept in r9 across both CPIs, tag in r6 at the pool gate, the 0x54e0 trampoline)
  appears in any cell without forces.

## 1. Oracle (experiment only; one build slot per capture, everything else llc/MIR)

- **Captures.** w16a09's `scr.py` pipeline: w15a03 `capraw.py` identity build with pre-opt IR, SDK `opt -O3`, slim, SDK `llc`.
  Genes come from `tools/genes_af.py` on top of the swarm library (`genes_fu` -> `genes_lac` -> `genes_lbw` -> ...). Main's
  row is lanchorceil's `n_m` capture on 1f4e396 (`eq_main: true`, M 2,251); its post-opt module is reused as `m0`.
- **Per cell.**
  - M, Mperm, Mhc (`mp.py`); true LCS `---`/`rfj` and the dotmap (`fuev.py`); per-0x800 rfj deltas (`evall.py`).
  - `6 KB swap`: SWAP when 3 or more dotmap chunks sit 0x800+ away from the median shift; `k outlier` = k such chunks (no swap).
  - `restored stacked` (`stk.sh`): main's block layout restored (`blkrestore.py`), allocas rebased to main's frame objects
    (`fnorm.py`), then the spill-slot permutation climb. It removes layout flips and frame artifacts, not register naming.
  - w15a06's exact cells (`t6/cells.sh`): legal tail pin, then pin + regideal r9 (the realisable swept-only cell) and
    pin + regideal all, over orig 0x3c00-0x5040.
  - Restored joint ceilings: `lpipe.sh` (w15a28 pipe, sticky RAPRIO climb, pass 1; pass 2 on the closest cells), then
    `stk.sh` with those forces.
  - Callee-saved occupancy at the tail program points (`tools/livecs.py`, new) and the 0x54e0 trampoline (`tools/tramp.py`).
- **IR-only cells.** `e1`/`hc` are w14a142's post-opt edits (`hphi`+`hcs`, plus `hev` for e1), applied by `tools/e1x.py` to
  `m0` and to T's capture.

## 2. Forms

Head forms (on main 1f4e396 text):
- `h1` = t_v_h1 (w14a111/w14a142): `curve.is_holder_reward=_holder`, the block's holder bool instead of `holder.unwrap_or(false)`.
- `h1b` = h1 + per-arm holder flag (`true`/`false` constants in the shared arms, `holder` in the non-shared arm).
- `h2p` = per-arm cashback only (w15a32 pa1 on main's `if holder` arms: `false` / `st.cashback` / `!holder&&st.cashback`).
- `h2` = h1b + h2p (per-arm holder flag and cashback).
- `h2f` = h2 with the non-shared arm split on holder: four arms, like the original's four flag-spill writers at
  0xdb8/0x1138/0x1850/0x18b8.
- `ft` = the fee-tag phi as source (w15a29's IR probe). Validate re-makes the fee
  (`let fee=match fee{Some(f)=>{..checks..;Some(f)}None=>None}`) and returns `Result<(Pubkey,Option<u64>)>`. Execute uses
  the validated fee for the curve store and the admin_cto_pool tag, so the fee argument dies in validate. `h3` = h2 + ft.
- `ftc` = the same phi through a `&mut Option<u64>` out-param, so validate keeps `Result<Pubkey>`. It is an oracle only and
  not landable, because its two stores are semantic no-ops (the RULE's dummy writes). `h3c` = h2 + ftc.
- `S1`/`S2` = w16a08 basinbound's ordinary-source form of w14a142's per-arm flag: validate returns
  `Result<(Pubkey,bool)>`. S1 also reads the event's is_holder_reward from the holder argument.
- `h4` = faithunion's best local union `G51+GPF`; nothing was pushed by w16a09.

Tail `T` = `s1+s_tai2+c2+n1+po+rev_ff`: w14a85 s1, w15a17 s_tai2, w15a24 c2, w15a04 n1+po and w14a50 raw-first.
plaintail's P0 was not pushed. Its local P0 (`pS+pT+pC+pN+pR+pP`) is a different, plainer union (M 2,028 @27,360).

## 3. Cross-product table


`M` is the masked difflib match count as built (main 2,251). `restored stacked` = layout restored + frame rebased + spill
perm, unforced. `pin+ri9` = w15a06's realisable swept-only cell (main 2,305); `pin+ria` = every register ideal over
0x3c00-0x5040 (main 2,353). `joint` = restored joint ceiling with the lpipe forces (main p1 2,329). An empty cell was not run.


| cell | genes | bytes | M | dM | Mperm | Mhc | L--- | Lrfj | 6 KB swap | restored stacked | pin | pin+ri9 | pin+ria | joint p1 (forces) | joint p2 (forces) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| m0 | - (main 1f4e396/5998913) | 27400 | 2251 | +0 | 2295 | 2302 | 2257 | 3006 | no | 2302 | 2294 | 2305 | 2353 | 2329 (7) | 2339 (9) |
| T | s1+s_tai2+c2+n1+po+rev_ff | 27352 | 2094 | -157 | 2182 | 2219 | 2169 | 3038 | 1 outlier | 2219 | 2199 | 2250 | 2371 | 2321 (9) |  |
| h1 | h1 | 27416 | 2207 | -44 | 2277 | 2284 | 2213 | 3007 | no | 2284 | 2247 | 2258 | 2323 |  |  |
| h1T | h1+s1+s_tai2+c2+n1+po+rev_ff | 27360 | 2075 | -176 | 2187 | 2207 | 2137 | 3040 | no | 2207 | 2168 | 2195 | 2319 | 2291 (10) |  |
| h1b | h1b | 27416 | 2207 | -44 | 2277 | 2284 | 2213 | 3007 | no | 2284 |  |  |  |  |  |
| h1bT | h1b+s1+s_tai2+c2+n1+po+rev_ff | 27360 | 2075 | -176 | 2187 | 2207 | 2137 | 3040 | no | 2207 |  |  |  |  |  |
| h2p | h2p | 27400 | 1596 | -655 | 1695 | 1696 | 1623 | 2473 | SWAP | 1975 |  |  |  |  |  |
| h2pT | h2p+s1+s_tai2+c2+n1+po+rev_ff | 27328 | 1533 | -718 | 1670 | 1671 | 1590 | 2488 | SWAP | 1934 |  |  |  |  |  |
| h2 | h2 | 27496 | 1889 | -362 | 2016 | 2019 | 1960 | 2996 | 1 outlier | 2019 |  |  |  |  |  |
| h2T | h2+s1+s_tai2+c2+n1+po+rev_ff | 27480 | 1815 | -436 | 2012 | 2014 | 1908 | 3036 | no | 2014 | 1923 | 1958 | 2080 | 2213 (10) |  |
| h2f | h2f | 27496 | 1823 | -428 | 2049 | 2110 | 1992 | 2954 | 1 outlier | 2109 |  |  |  |  |  |
| h2fT | h2f+s1+s_tai2+c2+n1+po+rev_ff | 27464 | 1768 | -483 | 2063 | 2078 | 1994 | 3021 | 1 outlier | 2076 | 1751 | 1796 | 1897 |  |  |
| ft | ft | 27072 | 1113 | -1138 | 1281 | 1312 | 1437 | 2942 | 1 outlier | 2207 |  |  |  |  |  |
| ftT | ft+s1+s_tai2+c2+n1+po+rev_ff | 27024 | 1107 | -1144 | 1286 | 1305 | 1420 | 2974 | 2 outlier | 2173 |  |  |  |  |  |
| h3 | h2+ft | 27176 | 1236 | -1015 | 1353 | 1383 | 1442 | 2997 | no | 2203 | 1206 | 1212 | 1225 |  |  |
| h3T | h2+ft+s1+s_tai2+c2+n1+po+rev_ff | 27264 | 1150 | -1101 | 1290 | 1385 | 1406 | 3045 | no | 2159 | 1149 | 1159 | 1282 |  |  |
| ftc | ftc | 27240 | 2050 | -201 | 2165 | 2181 | 2082 | 2943 | 2 outlier | 2181 |  |  |  |  |  |
| ftcT | ftc+s1+s_tai2+c2+n1+po+rev_ff | 27304 | 1863 | -388 | 2229 | 2239 | 2092 | 3033 | 1 outlier | 2237 |  |  |  | 2286 (5) | 2342 (17) |
| h3c | h2+ftc | 27408 | 1873 | -378 | 2142 | 2185 | 2014 | 2996 | 1 outlier | 2184 | 1950 | 1957 | 2012 |  |  |
| h3cT | h2+ftc+s1+s_tai2+c2+n1+po+rev_ff | 27344 | 1886 | -365 | 2125 | 2147 | 2036 | 3027 | 1 outlier | 2144 | 1952 | 1965 | 2139 | 2265 (12) |  |
| S1 | S1 | 27416 | 1354 | -897 | 1487 | 1497 | 1579 | 3009 | no | 2293 |  |  |  |  |  |
| S1T | S1+s1+s_tai2+c2+n1+po+rev_ff | 27368 | 1312 | -939 | 1462 | 1462 | 1520 | 3041 | 1 outlier | 2214 | 1320 | 1401 | 1507 |  |  |
| S2 | S2 | 27528 | 1027 | -1224 | 1067 | 1068 | 1158 | 2480 | SWAP | 2180 |  |  |  |  |  |
| S2T | S2+s1+s_tai2+c2+n1+po+rev_ff | 27480 | 1009 | -1242 | 1053 | 1057 | 1136 | 2490 | SWAP | 2155 |  |  |  |  |  |
| e1 | IR e1=hphi+hcs+hev (w14a142) on m0 | 27432 | 1992 | -259 | 2291 | 2298 | 2123 | 3009 | no | 2298 | 2091 | 2102 | 2151 |  |  |
| e1T | IR e1 on T | 27384 | 1964 | -287 | 2182 | 2218 | 2092 | 3041 | 1 outlier | 2218 | 2065 | 2116 | 2237 |  |  |
| hc | IR hc=hphi+hcs on m0 | 27528 | 1714 | -537 | 1714 | 1748 | 1719 | 2481 | SWAP | 2194 |  |  |  |  |  |
| hcT | IR hc on T | 27480 | 1644 | -607 | 1644 | 1690 | 1685 | 2491 | SWAP | 2161 |  |  |  |  |  |
| h4 | G51+GPF | 27344 | 1956 | -295 | 2170 | 2180 | 2053 | 3025 | 1 outlier | 2180 |  |  |  |  |  |
| h4T | G51+GPF+s1+s_tai2+c2+n1+po+rev_ff | 27312 | 1917 | -334 | 2145 | 2151 | 2007 | 3065 | no | 2149 | 2002 | 2019 | 2118 |  |  |
| t_s1 | s1 | 27376 | 2146 | -105 | 2203 | 2240 | 2207 | 3028 | 1 outlier | 2240 |  |  |  |  |  |
| t_tai | s_tai2 | 27400 | 2245 | -6 | 2300 | 2307 | 2254 | 3009 | no | 2307 |  |  |  |  |  |
| t_c2 | c2 | 27392 | 2218 | -33 | 2285 | 2292 | 2235 | 3010 | no | 2292 |  |  |  |  |  |
| t_n1 | n1 | 27376 | 2239 | -12 | 2283 | 2290 | 2245 | 3005 | no | 2290 |  |  |  |  |  |
| t_po | po | 27440 | 2121 | -130 | 2164 | 2171 | 2127 | 2907 | no | 2175 |  |  |  |  |  |
| t_ff | rev_ff | 27376 | 2244 | -7 | 2287 | 2294 | 2250 | 3007 | no | 2294 |  |  |  |  |  |
| To | o_rs+s1+s_tai2+c2+n1+po+rev_ff | 27232 | 1923 | -328 | 2088 | 2099 | 2033 | 3024 | 1 outlier | 2099 |  |  |  |  |  |
| h2po | h2p+o_rs | 27248 | 1961 | -290 | 2120 | 2125 | 2048 | 2975 | no | 2125 |  |  |  |  |  |
| S2o | S2+o_rs | 27200 | 1287 | -964 | 1465 | 1469 | 1489 | 2987 | 1 outlier | 2163 |  |  |  |  |  |
| S2c2 | S2+c2 | 27520 | 1027 | -1224 | 1067 | 1072 | 1158 | 2478 | SWAP | 2183 |  |  |  |  |  |
| S1c2 | S1+c2 | 27408 | 1333 | -918 | 1484 | 1493 | 1568 | 3013 | no | 2289 |  |  |  |  |  |
| h1c2 | h1+c2 | 27408 | 2180 | -71 | 2272 | 2279 | 2196 | 3011 | no | 2279 |  |  |  |  |  |
| ftm | ftm | 28128 | 1397 | -854 | 1487 | 1490 | 1490 | 2494 | SWAP | 1747 |  |  |  |  |  |
| ftmT | ftm+s1+s_tai2+c2+n1+po+rev_ff | 28008 | 1395 | -856 | 1494 | 1504 | 1495 | 2508 | SWAP | 1768 |  |  |  |  |  |


### Interaction terms `I = d(HxT) - d(H) - d(T)` (d = metric minus main's)

| H | metric | d(H) | d(T) | d(HxT) | I |
| --- | --- | ---: | ---: | ---: | ---: |
| h1 | M | -44 | -157 | -176 | **+25** |
| h1 | Mhc | -18 | -83 | -95 | **+6** |
| h1 | Lrfj | +1 | +32 | +34 | **+1** |
| h1 | stacked | -18 | -83 | -95 | **+6** |
| h1b | M | -44 | -157 | -176 | **+25** |
| h1b | Mhc | -18 | -83 | -95 | **+6** |
| h1b | Lrfj | +1 | +32 | +34 | **+1** |
| h1b | stacked | -18 | -83 | -95 | **+6** |
| h2p | M | -655 | -157 | -718 | **+94** |
| h2p | Mhc | -606 | -83 | -631 | **+58** |
| h2p | Lrfj | -533 | +32 | -518 | **-17** |
| h2p | stacked | -327 | -83 | -368 | **+42** |
| h2 | M | -362 | -157 | -436 | **+83** |
| h2 | Mhc | -283 | -83 | -288 | **+78** |
| h2 | Lrfj | -10 | +32 | +30 | **+8** |
| h2 | stacked | -283 | -83 | -288 | **+78** |
| h2f | M | -428 | -157 | -483 | **+102** |
| h2f | Mhc | -192 | -83 | -224 | **+51** |
| h2f | Lrfj | -52 | +32 | +15 | **+35** |
| h2f | stacked | -193 | -83 | -226 | **+50** |
| h3 | M | -1015 | -157 | -1101 | **+71** |
| h3 | Mhc | -919 | -83 | -917 | **+85** |
| h3 | Lrfj | -9 | +32 | +39 | **+16** |
| h3 | stacked | -99 | -83 | -143 | **+39** |
| ft | M | -1138 | -157 | -1144 | **+151** |
| ft | Mhc | -990 | -83 | -997 | **+76** |
| ft | Lrfj | -64 | +32 | -32 | **+0** |
| ft | stacked | -95 | -83 | -129 | **+49** |
| h4 | M | -295 | -157 | -334 | **+118** |
| h4 | Mhc | -122 | -83 | -151 | **+54** |
| h4 | Lrfj | +19 | +32 | +59 | **+8** |
| h4 | stacked | -122 | -83 | -153 | **+52** |
| h3c | M | -378 | -157 | -365 | **+170** |
| h3c | Mhc | -117 | -83 | -155 | **+45** |
| h3c | Lrfj | -10 | +32 | +21 | **-1** |
| h3c | stacked | -118 | -83 | -158 | **+43** |
| ftc | M | -201 | -157 | -388 | **-30** |
| ftc | Mhc | -121 | -83 | -63 | **+141** |
| ftc | Lrfj | -63 | +32 | +27 | **+58** |
| ftc | stacked | -121 | -83 | -65 | **+139** |
| S1 | M | -897 | -157 | -939 | **+115** |
| S1 | Mhc | -805 | -83 | -840 | **+48** |
| S1 | Lrfj | +3 | +32 | +35 | **+0** |
| S1 | stacked | -9 | -83 | -88 | **+4** |
| S2 | M | -1224 | -157 | -1242 | **+139** |
| S2 | Mhc | -1234 | -83 | -1245 | **+72** |
| S2 | Lrfj | -526 | +32 | -516 | **-22** |
| S2 | stacked | -122 | -83 | -147 | **+58** |
| e1 | M | -259 | -157 | -287 | **+129** |
| e1 | Mhc | -4 | -83 | -84 | **+3** |
| e1 | Lrfj | +3 | +32 | +35 | **+0** |
| e1 | stacked | -4 | -83 | -84 | **+3** |
| hc | M | -537 | -157 | -607 | **+87** |
| hc | Mhc | -554 | -83 | -612 | **+25** |
| hc | Lrfj | -525 | +32 | -515 | **-22** |
| hc | stacked | -108 | -83 | -141 | **+50** |


## 4. Leave-one-out inside the basin vs alone on main


`in basin` = metric(full cell) - metric(full cell without the form); `alone on main` = metric(main + form) - metric(main).
The `stacked` row (layout restored, frame rebased, perm) is the artifact-free one; `M` in the h3T basin is dominated by ft's
16 B frame shift. Classes: *needs partner* = loses alone, helps in the basin; *wrong* = loses in both.


### Basin h3T (h2 + ft + T, frame-shifted)

Full cell h3T: M 1150, Mhc 1385, Lrfj 3045, stacked 2159

| form | metric | in basin (h3T - (h3T-X)) | alone on main (main+X - main) | class |
| --- | --- | ---: | ---: | --- |
| holder (h1: curve store from the block bool; h1b folds into it) | M | -55 | -44 | wrong (loses in both) |
| holder (h1: curve store from the block bool; h1b folds into it) | Mhc | -20 | -18 | wrong (loses in both) |
| holder (h1: curve store from the block bool; h1b folds into it) | Lrfj | +12 | +1 | helps on main |
| holder (h1: curve store from the block bool; h1b folds into it) | stacked | +30 | -18 | needs partner |
| per-arm cashback (h2p) | M | -58 | -655 | wrong (loses in both) |
| per-arm cashback (h2p) | Mhc | -7 | -606 | wrong (loses in both) |
| per-arm cashback (h2p) | Lrfj | +70 | -533 | needs partner |
| per-arm cashback (h2p) | stacked | -29 | -327 | wrong (loses in both) |
| fee-tag phi (ft) | M | -665 | -1138 | wrong (loses in both) |
| fee-tag phi (ft) | Mhc | -629 | -990 | wrong (loses in both) |
| fee-tag phi (ft) | Lrfj | +9 | -64 | needs partner |
| fee-tag phi (ft) | stacked | +145 | -95 | needs partner |
| s1 (sharing CPI to_account_info) | M | -42 | -105 | wrong (loses in both) |
| s1 (sharing CPI to_account_info) | Mhc | -12 | -62 | wrong (loses in both) |
| s1 (sharing CPI to_account_info) | Lrfj | +22 | +22 | helps on main |
| s1 (sharing CPI to_account_info) | stacked | -17 | -62 | wrong (loses in both) |
| s_tai2 (TCF program to_account_info) | M | +1 | -6 | needs partner |
| s_tai2 (TCF program to_account_info) | Mhc | +1 | +5 | helps on main |
| s_tai2 (TCF program to_account_info) | Lrfj | +3 | +3 | helps on main |
| s_tai2 (TCF program to_account_info) | stacked | +4 | +5 | helps on main |
| c2 (TCF pcva clone order) | M | -1 | -33 | wrong (loses in both) |
| c2 (TCF pcva clone order) | Mhc | +17 | -10 | needs partner |
| c2 (TCF pcva clone order) | Lrfj | +4 | +4 | helps on main |
| c2 (TCF pcva clone order) | stacked | +18 | -10 | needs partner |
| n1 (event reads curve fee) | M | -39 | -12 | wrong (loses in both) |
| n1 (event reads curve fee) | Mhc | +3 | -12 | needs partner |
| n1 (event reads curve fee) | Lrfj | +18 | -1 | needs partner |
| n1 (event reads curve fee) | stacked | +21 | -12 | needs partner |
| po (owner-first pool gate) | M | +0 | -130 | wrong (loses in both) |
| po (owner-first pool gate) | Mhc | +38 | -131 | needs partner |
| po (owner-first pool gate) | Lrfj | +4 | -99 | needs partner |
| po (owner-first pool gate) | stacked | +0 | -127 | wrong (loses in both) |
| rev_ff (raw amount first) | M | +42 | -7 | needs partner |
| rev_ff (raw amount first) | Mhc | +43 | -8 | needs partner |
| rev_ff (raw amount first) | Lrfj | +101 | +1 | helps on main |
| rev_ff (raw amount first) | stacked | +58 | -8 | needs partner |


### Basin h3cT (h2 + ftc + T, frame-faithful oracle)

Full cell h3cT: M 1886, Mhc 2147, Lrfj 3027, stacked 2144

| form | metric | in basin (h3cT - (h3cT-X)) | alone on main (main+X - main) | class |
| --- | --- | ---: | ---: | --- |
| holder (h1: curve store from the block bool; h1b folds into it) | M | +331 | -44 | needs partner |
| holder (h1: curve store from the block bool; h1b folds into it) | Mhc | +471 | -18 | needs partner |
| holder (h1: curve store from the block bool; h1b folds into it) | Lrfj | +527 | +1 | helps on main |
| holder (h1: curve store from the block bool; h1b folds into it) | stacked | +81 | -18 | needs partner |
| per-arm cashback (h2p) | M | +67 | -655 | needs partner |
| per-arm cashback (h2p) | Mhc | -80 | -606 | wrong (loses in both) |
| per-arm cashback (h2p) | Lrfj | -6 | -533 | wrong (loses in both) |
| per-arm cashback (h2p) | stacked | -81 | -327 | wrong (loses in both) |
| fee-tag phi (ftc, out-param oracle) | M | +71 | -201 | needs partner |
| fee-tag phi (ftc, out-param oracle) | Mhc | +133 | -121 | needs partner |
| fee-tag phi (ftc, out-param oracle) | Lrfj | -9 | -63 | wrong (loses in both) |
| fee-tag phi (ftc, out-param oracle) | stacked | +130 | -121 | needs partner |
| s1 (sharing CPI to_account_info) | M | +11 | -105 | needs partner |
| s1 (sharing CPI to_account_info) | Mhc | -3 | -62 | wrong (loses in both) |
| s1 (sharing CPI to_account_info) | Lrfj | +21 | +22 | helps on main |
| s1 (sharing CPI to_account_info) | stacked | -5 | -62 | wrong (loses in both) |
| s_tai2 (TCF program to_account_info) | M | +2 | -6 | needs partner |
| s_tai2 (TCF program to_account_info) | Mhc | +6 | +5 | helps on main |
| s_tai2 (TCF program to_account_info) | Lrfj | +3 | +3 | helps on main |
| s_tai2 (TCF program to_account_info) | stacked | +6 | +5 | helps on main |
| c2 (TCF pcva clone order) | M | +3 | -33 | needs partner |
| c2 (TCF pcva clone order) | Mhc | +11 | -10 | needs partner |
| c2 (TCF pcva clone order) | Lrfj | +4 | +4 | helps on main |
| c2 (TCF pcva clone order) | stacked | +11 | -10 | needs partner |
| n1 (event reads curve fee) | M | +1 | -12 | needs partner |
| n1 (event reads curve fee) | Mhc | -1 | -12 | wrong (loses in both) |
| n1 (event reads curve fee) | Lrfj | +1 | -1 | needs partner |
| n1 (event reads curve fee) | stacked | -1 | -12 | wrong (loses in both) |
| po (owner-first pool gate) | M | +0 | -130 | wrong (loses in both) |
| po (owner-first pool gate) | Mhc | -2 | -131 | wrong (loses in both) |
| po (owner-first pool gate) | Lrfj | +4 | -99 | needs partner |
| po (owner-first pool gate) | stacked | +0 | -127 | wrong (loses in both) |
| rev_ff (raw amount first) | M | -5 | -7 | wrong (loses in both) |
| rev_ff (raw amount first) | Mhc | -30 | -8 | wrong (loses in both) |
| rev_ff (raw amount first) | Lrfj | -2 | +1 | helps on main |
| rev_ff (raw amount first) | stacked | -29 | -8 | wrong (loses in both) |


### Basin ftcT (ftc + T, the cell whose joint passes main)

Full cell ftcT: M 1863, Mhc 2239, Lrfj 3033, stacked 2237

| form | metric | in basin (ftcT - (ftcT-X)) | alone on main (main+X - main) | class |
| --- | --- | ---: | ---: | --- |
| fee-tag phi (ftc, out-param oracle) | M | -231 | -201 | wrong (loses in both) |
| fee-tag phi (ftc, out-param oracle) | Mhc | +20 | -121 | needs partner |
| fee-tag phi (ftc, out-param oracle) | Lrfj | -5 | -63 | wrong (loses in both) |
| fee-tag phi (ftc, out-param oracle) | stacked | +18 | -121 | needs partner |
| s1 (sharing CPI to_account_info) | M | -43 | -105 | wrong (loses in both) |
| s1 (sharing CPI to_account_info) | Mhc | +3 | -62 | needs partner |
| s1 (sharing CPI to_account_info) | Lrfj | +24 | +22 | helps on main |
| s1 (sharing CPI to_account_info) | stacked | +2 | -62 | needs partner |
| s_tai2 (TCF program to_account_info) | M | -6 | -6 | wrong (loses in both) |
| s_tai2 (TCF program to_account_info) | Mhc | +5 | +5 | helps on main |
| s_tai2 (TCF program to_account_info) | Lrfj | +3 | +3 | helps on main |
| s_tai2 (TCF program to_account_info) | stacked | +5 | +5 | helps on main |
| c2 (TCF pcva clone order) | M | -128 | -33 | wrong (loses in both) |
| c2 (TCF pcva clone order) | Mhc | +67 | -10 | needs partner |
| c2 (TCF pcva clone order) | Lrfj | +60 | +4 | helps on main |
| c2 (TCF pcva clone order) | stacked | +65 | -10 | needs partner |
| n1 (event reads curve fee) | M | -2 | -12 | wrong (loses in both) |
| n1 (event reads curve fee) | Mhc | -2 | -12 | wrong (loses in both) |
| n1 (event reads curve fee) | Lrfj | -1 | -1 | wrong (loses in both) |
| n1 (event reads curve fee) | stacked | -2 | -12 | wrong (loses in both) |
| po (owner-first pool gate) | M | -1 | -130 | wrong (loses in both) |
| po (owner-first pool gate) | Mhc | -1 | -131 | wrong (loses in both) |
| po (owner-first pool gate) | Lrfj | +3 | -99 | needs partner |
| po (owner-first pool gate) | stacked | -1 | -127 | wrong (loses in both) |
| rev_ff (raw amount first) | M | +102 | -7 | needs partner |
| rev_ff (raw amount first) | Mhc | +102 | -8 | needs partner |
| rev_ff (raw amount first) | Lrfj | +104 | +1 | helps on main |
| rev_ff (raw amount first) | stacked | +61 | -8 | needs partner |


### ftcT pass-2 force leave-one-out (`t2/loo.py`; joint = permhc Mhc of the forced build)

Vreg ids are ftcT's. Main's own families are `1679=r7` (main 1672=r7, post-event tail accounts piece), `1684=r6` (main
1685=r6, event accounts piece), `469=r2` (main 468=r2, head piece) and `1704=r4`/`1690=r3` (main 1707=r4/1703=r3).
The ftcT-specific forces carry most of the joint:
- `236=r5`: orig 0x3340-0x39e0, the TCF clone run and the sweep CPI;
- `325=r4` and `352=r7`/`355=r2`: 0x4180-0x4660, the sharing-CPI clone run;
- `2140=r7`: 0x3de8-0x3e18;
- `2173=r6`: 0x3078-0x30c8, the TCF pcva clone temps, i.e. c2's tax site. Without it, M collapses to 2,043 and the spill
  perm recovers the joint.

All are register-naming choices inside clone runs. Earlier lanes found no source lever for this class (w15a24 #3736,
w15a33 #3829, w16a04 #3855).

| force left out | joint | d joint | forced M | bytes |
| --- | ---: | ---: | ---: | ---: |
| (none: all 17) | 2342 | | 2259 | 27304 |
| `236=r5` | 2316 | -26 | 2233 | 27304 |
| `325=r4` | 2325 | -17 | 2234 | 27304 |
| `2140=r7` | 2325 | -17 | 2230 | 27280 |
| `1679=r7` | 2331 | -11 | 2248 | 27304 |
| `1684=r6` | 2333 | -9 | 2249 | 27304 |
| `352=r7` | 2334 | -8 | 2250 | 27304 |
| `469=r2` | 2335 | -7 | 2252 | 27328 |
| `248=r6` | 2335 | -7 | 2252 | 27312 |
| `1675=r7` | 2335 | -7 | 2252 | 27304 |
| `355=r2` | 2336 | -6 | 2253 | 27304 |
| `2173=r6` | 2338 | -4 | 2043 | 27280 |
| `1673=r8` | 2338 | -4 | 2255 | 27304 |
| `1651=r3` | 2338 | -4 | 2255 | 27304 |
| `1083=r3` | 2340 | -2 | 2256 | 27304 |
| `1704=r4` | 2340 | -2 | 2257 | 27304 |
| `1690=r3` | 2340 | -2 | 2257 | 27304 |
| `2188=r4` | 2342 | +0 | 2251 | 27288 |


## 5. Findings and mechanisms

1. **No H x T cell beats main** on any measure: as built, perm-bounded, frame-normalised, in w15a06's realisable cell or in
   the restored joint ceiling.

   | cell | M | stacked | pin+ri9 | joint |
   | --- | ---: | ---: | ---: | --- |
   | main | 2,251 | 2,302 | 2,305 | p1 2,329 / p2 2,339 |
   | T on main's head (plaintail's cell, the closest to main) | | | | p1 2,321 / p2 (running) |
   | `h1T` | 2,075 | | 2,195 | p1 2,291 / p2 (running) |
   | `ftcT` (oracle) | 1,863 | 2,237 | | p1 2,286 (5 forces) / p2 **2,342** (17 forces) |
   | `h3cT` (oracle) | 1,886 | 2,144 | | p1 2,265 |
   | `e1T` (IR) | 1,964 | 2,218 | 2,116 | (running) |
2. **The head x tail hypothesis holds for one pair only: the fee-tag phi (frame-faithful `ftc`) with the tail union.**
   - Raw M: every head form interacts positively with T (`I = d(HxT) - d(H) - d(T)`): h1 +25, h2 +83, h2f +102,
     h2p +94, h3 +71, ft +151, h3c +170, S1 +115, S2 +139, e1 +129, hc +87.
   - The artifact-free metric (restored stacked: layout restored, frame rebased, spill perm) separates three groups:
     - **Near-main heads, I about 0:** h1 +6 (h1 stacked -18), e1 +3 (-4), S1 +4 (-9). T costs about -80 on each of them,
       as it does on main (-83).
     - **Heads that damage layout or frame themselves, I +39 to +78:** h2, h2p, h2f, S2, hc, ft, h3, h3c. Two
       perturbations of the same colouring or block order do not add, so this is shared damage.
     - **ftc, I +139 stacked / +141 Mhc.** On the ftc head T is a **gain** of +56 stacked and +58 Mhc
       (ftc 2,181 -> ftcT 2,237), where it is -83 on main.
   - The tail union is tuned against main's fee handling: the fee argument kept live to the pool CPI. It pays once the fee
     tag is a phi at validate's exit and the argument dies there, as in the original (w15a29).
   - ftc alone is -121 stacked (-201 M at -160 B), so ftcT is still -65 stacked and -388 M as built. As built, its loss is
     spill colouring: Mperm +366.
3. **Leave-one-out (section 4) confirms which faithful forms need a partner.** The values below are in the artifact-free
   stacked metric, given as the marginal inside the h3T / h3cT / ftcT basins against the form alone on main; values under
   10 are noise.

   | form | h3T | h3cT | ftcT | alone on main | verdict |
   | --- | ---: | ---: | ---: | ---: | --- |
   | fee-tag phi (ft / ftc) | +145 | +130 | +18 | -95 / -121 | **needs partner** in every basin |
   | holder form h1 | +30 | +81 | | -18 | **needs partner** |
   | c2 | +18 | +11 | +65 | -10 | **needs partner** in every basin |
   | rev_ff | +58 | -29 | +61 | -8 | needs partner in the ft/ftc basins |
   | n1 | +21 | -1 | -2 | -12 | partner only in h3T |
   | per-arm cashback h2p | -29 | -81 | | -327 | **wrong** |
   | s1 | -17 | -5 | +2 | -62 | **wrong** |
   | po | 0 | 0 | -1 | -127 | wrong alone, inert in a basin |
   | s_tai2 | +4 | +6 | +5 | +5 | inert |

   The angle's first two faithful head forms (the holder flag and per-arm cashback) split: the holder form h1 is confirmed
   and the per-arm cashback is wrong. The fee-tag phi is confirmed. On the tail, c2 and rev_ff are confirmed with the
   fee-tag phi, and s1 is wrong in every basin. s1 is the form w15a06 built its +63 regideal ceiling on.
   In raw M, c2 is -128 in the ftcT basin: its clone-temp tax, the force 2173=r6 / lanchorceil's 2172=r0, is paid there.
4. **h1b == h1 byte for byte.** Per-arm holder constants (`true`/`false`/`holder` in the three arms) fold back into `holder`.
   The original's four flag-spill writers need a carrier that LLVM cannot fold: w14a142's IR `hphi`, or S1/S2's
   validate-returned flag.
5. **The real 6 KB tail swap is a post-RA layout flip keyed to the holder argument's last use.**
   - Shape: dotmap 0x2400-0x3800 at +0x1900 and 0x4400-0x5000 at -0x1800, Lrfj about -520.
   - It appears with `h2p` (per-arm cashback with main's `holder.unwrap_or(false)` curve store), `hc` (w14a142's collapsed
     IR flag) and S2, with or without T, and in the h3cT basin without the holder form (c_hf).
   - `h1` cancels it (h2 = h1 + h2p: Lrfj -10). `hev`, the event reading the holder argument, cancels it for hc (e1) and S2
     (S1).
   - `stk.sh`'s block restore recovers most of it (h2p 1,596 -> 1,975; S2 1,027 -> 2,180).
   - fuev's `swap` flag on T, h2, h2f, e1T, ft, ftc and h3c marks one or two outlier chunks, not a tail swap. The outliers
     fall at 0x4000/0x4800, in the sharing-CPI clone run, whose 5-grams repeat.
   - The ordinary carrier `sharing_config_reset:shared` (o_rs) cancels the real swap: h2p 1,596 -> 1,961 (Lrfj 2,473 ->
     2,975) and S2 1,027 -> 1,287 (2,480 -> 2,987). It costs T -171 (2,094 -> 1,923), so it is a swap fix, not a gain.
6. **ft's collapse is a frame artifact; ftc removes it.**
   - ft returns `Result<(Pubkey,Option<u64>)>` and S1/S2 return `Result<(Pubkey,bool)>`. Both move the Pubkey off Result
     offset 1.
   - Main's 7 B `target.sroa.0` piece then disappears; it is the trace of the original's 8/24 target split. Every spill slot
     moves by 16 B (8 B for S1/S2): ft 1,113, h3 1,236, h3T 1,150.
   - The `&mut Option<u64>` out-param ftc keeps `Result<Pubkey>` and `target.sroa.0`: 107 spill slots against main's 108.
   - ftc is oracle-only, because its two stores are semantic no-ops. The closure idiom
     `*fee=fee.map(|f|..Ok(f)).transpose()?` (`ftm`) is not ftc's code: +728 B, the real tail swap and M 1,397.
7. **None of the three original facts holds in any cell without forces** (`livecs.py`, `tramp.py`, `data/livecs.txt`).
   - No callee-saved register is live across the TCF or sharing CPI in any cell, so swept is spilled. The original keeps it
     in r9 across both CPIs.
   - At the pool gate, r6 or r8 holds the accounts-pointer reload and r9 the pool owner. In the original, the sharing tag
     holds r6 there.
   - No cell has the original's `call; ldxdw r1; ldxdw r7; mov64 r9,r1; ja` trampoline (orig 0x54e0).
   - Through the wallet, main and the h1/h2/S1/e1/T cells keep the sweep-gate phi of constants (`skip`, `MOV_ri 0/1/0` in
     the post-validate arms) in r9. The ft, ftc, h2p, h2f and h4 heads free r9 there.


## 6. Next ideas (for later lanes)

1. **A frame-preserving carrier for the validated fee.** ftc proves that the fee-tag phi with main's `Result<Pubkey>`
   layout is +71 M / +133 Mhc on h2T and makes T a gain (+13 M on h3c). Both ordinary spellings tried here break the
   layout: ft returns `Result<(Pubkey,Option<u64>)>`, and S1/S2 return `Result<(Pubkey,bool)>`, where bool's niche or the
   align-8 tuple moves the Pubkey off Result offset 1. The original's 8/24 target split says its validate returned a value
   with the Pubkey at offset 1. Look for a source shape in which the fee tag is *reloaded from memory* after validate's
   switches, so that GVN load-PRE builds the phi (w15a29). One example would be validate taking an args struct that holds
   `fee` by reference, if that struct is not SROA'd before GVN.
2. **Price h3c (h2 + ftc) jointly with the tail swap fix and T's c2 tax force.** It is the faithful head on which the tail
   union stops costing M. Its gap is in exact tokens (true LCS `---` -243), while its skeleton is close (rfj -10).
3. The 6 KB tail swap is a post-RA layout flip that follows the holder argument's last use. Any lane that changes where
   `holder` (`%0`) dies must check dotmap chunks 0x2400-0x5000 (`aftab2.py`'s `6 KB swap` column). It must not trust
   fuev's single `swap` flag, which also fires on one-chunk outliers in the sharing-CPI clone run.
4. Per-arm constant flags written in source fold back (h1b == h1 byte for byte). Only a carrier that crosses a non-inlined
   or memory boundary keeps them as phis.

## 7. Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `genes_af.py`: the head and tail genes above (exact single-occurrence replacements, line count kept). `bbS1.py` and
  `bbS2.py` are basinbound's S1/S2 edit lists. Note that `e/S1.py` and `e/s1.py` collide on macOS (case-insensitive APFS),
  so copies must be renamed.
- `aftab2.py`: the cross-product table, the `6 KB swap` test and the interaction terms. `loo_af.py <h3T|h3cT>`: the
  leave-one-out table.
- `e1x.py <src> <dst> [hc|e1]`: w14a142's per-arm flag IR edits on any capture's post-opt module (anchors found by pattern,
  not by value number).
- `livecs.py <pei.mir>`: r6-r9 liveness and reaching defs at the wallet (token_frozen, create_idempotent, collect), sweep,
  TCF, sharing CPI, pool gate and pool CPI, with a head/tail tag on each def (head = before prepare_bonding_curve).
- `tramp.py <fn.bin|orig>`: the original's CPI-result trampoline shape (`mov64 r9,r1` at orig 0x54e0).
- Data: `data/res-5998913.jsonl` (every capture and IR cell), `data/cells.jsonl` (w15a06 cells), `data/stk-p0.jsonl`
  (restored stacked), `data/stkra.jsonl` (restored joints), `data/livecs.txt` (occupancy summary).
