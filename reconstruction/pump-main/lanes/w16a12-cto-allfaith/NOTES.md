# w16a12-cto-allfaith: faithful head forms H x faithful tail union T (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `1f4e396b5` / `599891304` (admin_cto.rs identical; #3859 sweep tuple landed during the lane start):
0.67436, 3,141 slots, M 2,251, Mperm 2,295, Mhc 2,302, true LCS 2,257 / rfj 3,006, pass-1 joint 2,329 (7 forces).
Angle: price faithful head forms crossed with the faithful tail union. Hypothesis: each side loses alone because the other
side of the function is tuned to main.
Ledger: approach `allfaith`, keys `0x22a10-w16-5998913-allfaith-<cell>-v1` (one row per capture, written by `tools/scr.py`).

**Status: first table pushed while the leave-one-out, S1/S2 and RA-joint rows run (updated at the end of the lane).**

## 1. Oracle (experiment only; one build slot per capture, everything else llc/MIR)

- Captures: w16a09's `scr.py` pipeline (w15a03 `capraw.py` identity build with pre-opt IR, SDK `opt -O3`, slim, SDK `llc`),
  genes from `tools/genes_af.py` on top of the swarm library (`genes_fu` -> `genes_lac` -> `genes_lbw` -> ...). Main's row is
  lanchorceil's `n_m` capture on 1f4e396 (`eq_main: true`, M 2,251); its post-opt module is reused as `m0`.
- Per cell: M, Mperm, Mhc (`mp.py`), true LCS `---`/`rfj` and the dotmap tail-swap flag (`fuev.py`), per-0x800 rfj deltas
  (`evall.py`), the stacked bound with main's block layout restored and the frame rebased to main's frame objects
  (`stk.sh`, w15a20/w16a08 restore + w15a19 fnorm + spill perm), w15a06's exact cells (`t6/cells.sh`: legal pin, pin +
  regideal r9 / all over 0x3c00-0x5040), the pass-1 RA joint (`lpipe.sh` sticky climb, then `stk.sh` with the forces =
  restored joint ceiling), and callee-saved occupancy at the tail program points (`tools/livecs.py`, new).

## 2. Forms

Head (main 1f4e396 text):
- `h1` = t_v_h1 (w14a111/w14a142): `curve.is_holder_reward=_holder` (the block's holder bool instead of `holder.unwrap_or(false)`).
- `h1b` = h1 + per-arm holder flag (`true`/`false` constants in the shared arms, `holder` in the non-shared arm).
- `h2p` = per-arm cashback only (w15a32 pa1 on main's `if holder` arms: `false` / `st.cashback` / `!holder&&st.cashback`).
- `h2` = h1b + h2p (per-arm holder flag and cashback). `h2f` = h2 with the non-shared arm split on holder (four arms, as the
  original's four flag-spill writers at 0xdb8/0x1138/0x1850/0x18b8).
- `ft` = the fee-tag phi as source (w15a29's IR probe): validate re-makes the fee (`let fee=match fee{Some(f)=>{..checks..;
  Some(f)}None=>None}`) and returns `Result<(Pubkey,Option<u64>)>`; execute uses the validated fee for the curve store and the
  admin_cto_pool tag, so the fee argument dies in validate. `h3` = h2 + ft.
- `ftc` (oracle only, not landable: two semantically no-op stores): the same phi through a `&mut Option<u64>` out-param, so
  validate keeps its `Result<Pubkey>` layout.
- `h4` = faithunion's best pushed union `G51+GPF` (CtoState order mv_5_1 + PDA-first/quote-locked/bool/global-field entry).

Tail `T` = `s1+s_tai2+c2+n1+po+rev_ff` (w14a85 s1, w15a17 s_tai2, w15a24 c2, w15a04 n1+po, w14a50 raw-first). plaintail's P0
was not pushed; its local P0 (`pS+pT+pC+pN+pR+pP`) is a different, plainer union (M 2,028 @27,360).

## 3. Cross-product table (first rows)

`restored stacked` = stk.sh unforced (main layout, frame rebased, spill perm). `pin+ri9` is w15a06's realisable swept-only cell
(legal tail pin + ideal r9 over 0x3c00-0x5040); `pin+ria` = all registers ideal there. `joint p1` = lpipe pass-1 forces, then
stk.sh (restored joint ceiling).

| cell | genes | bytes | M | dM | Mperm | Mhc | L--- | Lrfj | swap | restored stacked | pin | pin+ri9 | pin+ria | joint p1 (forces) |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | ---: | ---: |
| T | s1+s_tai2+c2+n1+po+rev_ff | 27352 | 2094 | -157 | 2182 | 2219 | 2169 | 3038 | True | 2219 | 2199 | 2250 | 2371 |  |
| h1T | h1+s1+s_tai2+c2+n1+po+rev_ff | 27360 | 2075 | -176 | 2187 | 2207 | 2137 | 3040 | False | 2207 | 2168 | 2195 | 2319 | 2291 (10) |
| h1 | h1 | 27416 | 2207 | -44 | 2277 | 2284 | 2213 | 3007 | False | 2284 | 2247 | 2258 | 2323 |  |
| h2T | h2+s1+s_tai2+c2+n1+po+rev_ff | 27480 | 1815 | -436 | 2012 | 2014 | 1908 | 3036 | False | 2014 | 1923 | 1958 | 2080 |  |
| h2 | h2 | 27496 | 1889 | -362 | 2016 | 2019 | 1960 | 2996 | True | 2019 |  |  |  |  |
| h2fT | h2f+s1+s_tai2+c2+n1+po+rev_ff | 27464 | 1768 | -483 | 2063 | 2078 | 1994 | 3021 | False | 2076 | 1751 | 1796 | 1897 |  |
| h2f | h2f | 27496 | 1823 | -428 | 2049 | 2110 | 1992 | 2954 | True | 2109 |  |  |  |  |
| h2pT | h2p+s1+s_tai2+c2+n1+po+rev_ff | 27328 | 1533 | -718 | 1670 | 1671 | 1590 | 2488 | True | 1934 |  |  |  |  |
| h2p | h2p | 27400 | 1596 | -655 | 1695 | 1696 | 1623 | 2473 | True | 1975 |  |  |  |  |
| h3T | h2+ft+s1+s_tai2+c2+n1+po+rev_ff | 27264 | 1150 | -1101 | 1290 | 1385 | 1406 | 3045 | False | 2159 | 1149 | 1159 | 1282 |  |
| h3 | h2+ft | 27176 | 1236 | -1015 | 1353 | 1383 | 1442 | 2997 | False | 2203 | 1206 | 1212 | 1225 |  |
| h4T | G51+GPF+s1+s_tai2+c2+n1+po+rev_ff | 27312 | 1917 | -334 | 2145 | 2151 | 2007 | 3065 | False | 2149 | 2002 | 2019 | 2118 |  |
| e1 | IR e1=hphi+hcs+hev (w14a142) on m0 | 27432 | 1992 | -259 | 2291 | 2298 | 2123 | 3009 | False |  |  |  |  |  |
| m0 | - (main 1f4e396/5998913) | 27400 | 2251 | +0 | 2295 | 2302 | 2257 | 3006 | False | 2302 | 2294 | 2305 | 2353 | 2329 (7) |

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


## 4. Findings so far

- No cell beats main as built, perm-bounded, restored or realisable. Best H x T: h1T (M 2,075, joint 2,291 vs main 2,329 p1).
- Interactions are positive for every head form (I = +25..+102 M, +6..+85 Mhc): the tail union loses less on a faithful head
  (T costs -157 on main, -132 on h1, -74 on h2, -86 on h3), but no head form turns T positive.
- `h1b` (per-arm holder constants) is byte-identical to `h1`: LLVM folds the constants back into `holder`.
- `h2p` (per-arm cashback alone) makes the real 6 KB tail swap (dotmap 0x2400-0x3800 at +0x1900, 0x4400-0x5000 at -0x1800;
  Lrfj -533). `h1` cancels it (h2 = h1 + h2p: Lrfj -10). The dotmap `swap` flag on T, h2 and h2f is a single-chunk outlier
  (0x4000 or 0x4800) in the sharing-CPI clone run, not a tail swap.
- `ft` (fee re-made in validate) collapses M through a frame artifact: `Result<(Pubkey,Option<u64>)>` puts the Pubkey at an
  8-aligned offset, so main's 7 B `target.sroa.0` piece (Pubkey at Result offset 1, the original's 8/24 target split) and one
  8 B band vanish and every spill slot moves 16 B. Frame-normalised, ft is worth +184 over h2 on main's tail (h3 2,203 vs h2
  2,019) and +145 on T (h3T 2,159 vs h2T 2,014).


## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `genes_af.py`: the head and tail genes above (exact single-occurrence replacements, line count kept).
- `aftable.py`, `aftab2.py`: the cross-product table and the interaction terms `I = d(HxT) - d(H) - d(T)`.
- `livecs.py <pei.mir>`: r6-r9 liveness and reaching defs at the wallet (token_frozen, create_idempotent, collect), sweep,
  TCF, sharing CPI, pool gate and pool CPI, with head/tail classification of each def (head = before prepare_bonding_curve).
- `tramp.py <fn.bin|orig>`: the original's CPI-result trampoline shape (`mov64 r9,r1` at orig 0x54e0).
