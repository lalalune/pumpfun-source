# w16a06-cto-bonoutline: the original validate order B on outline bases (price table, notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9bd38c7d5 (admin_cto unchanged since 9120883a9): 0.67376, 3,124 slots, M 2,249, jM 2,275, fM 2,380,
Mperm 2,293, true LCS 2,255 (rfj 3,007). Ledger approach `bonoutline`, keys `0x22a10-w16-9bd38c7-bonoutline-*-v1`.

**Result: no landable change (kill test met for every source-reachable cell).** Main is still the best zero-loss
measurement (0.67376 / 3,124 slots / 27,400 B).

- At fixed RA, B is worth about **three times as much on an outline base as on main**: +81 to +86 M, against main's +28.
  The angle's premise holds. Once validate has the original's size, B's jump gain turns into real M.
- Real llc does not deliver it. IR-order realisations lose (main -130, O -72, T -30). The only real-llc lever that pays
  on an outline base is the **306 Some/None branch weight (`bb23.i`)**. At 2:1 (error edge hot) it gives the original
  tail order `306 296 326 312 307` on O and O312: +32/+33 M at the same RA.
- Every cell that passes the ideal-repay bound sits on an IR-forced outline base (O or O312), or needs a branch
  probability that ordinary source cannot produce. The source triggers T, Tb and Tv01 stay below main + repay.
  Under true LCS (unmasked and rfj), even the passing cells are below main and below their own base (section 5).

## 0. Oracle (tools/, experiment only; paths point at this lane's `$OUT`)

- Captures: `cap1.sh <name> <genes> <slot>` (one identity build with `--emit=llvm-ir`, then `rx.py`: `opt -O3`, slim, llc).
  The genes are in `gx.py`, with w15a09/w15a21's `tg.py` as fallback. The `m0` capture reproduces main
  (`eq_main: true`).
- IR-forced outline bases: w15a09/w15a21 `ni.py` (noinline on the 307/312 `to_string` call sites; `NI=19` gives 312
  only) on the raw `m0` / `tf_g3` captures. These are w15a25's `none_O`, `none_O312`, `tf_g3_O` and `tf_g3_O312`, and they
  reproduce w15a25's bytes and ratios.
- Fixed-RA B:
  - `bprice.py <name>` applies w14a87's relayout (`relayn.py`, Br = condition reversal allowed) with w14a98's
    content-mapped spec. `data/Bspec_cur.txt` is the spec renamed for this main (`bb3.i291`, `exit292`).
    `data/Bspec_O.txt` drops `bb3.i51.i`, which has no counterpart once 312 is outlined (it mis-maps to the 410 block).
  - `arel.py <m.s> <order>` relays an explicit asm-label order. T's CFG differs (the `invalid_creator` splice), so it
    gets its own order, `data/TB_T.txt`.
  - `uo.py` and `ux.py` give per-unit alone / LOO / greedy prices.
- Real-llc realisations:
  - `irB.py` and `iru.py` reorder the post-opt IR in B order, either the full order or unit by unit (a unit's IR blocks
    go after its B predecessor).
  - `ux.py <name> <order> ir` does the same for an explicit order.
  - `wg.py` is a parallel greedy over every validate conditional branch x 8 `!prof` weights.
  - `and1.py` gives the IR and-1 holder/tag forms (w14a78). `phix.py` gives w15a29's fee-tag phi.
  - `vw.py` puts V-time (pre-opt) weights on validate's 306 `switch`.
- Measures: `sc.py` (M, jM, fM, skM), w15a16 `mp.py` (Mperm, true LCS), w14a128 `lcschunk.py` (true LCS per
  0x800 chunk), and `tp2.py`, which is skeleton/transplant2.py on any fn.bin (per-region perfect-transplant headroom).
  `eoff.py` gives the error-site offsets against the original, `blays.py` the block layout.

## 1. Where validate ends: the outline bases are short, not long

Error-site offsets (`eoff.py`, the `stw [r10-0x2b8], <line>` stores):

| build | 289 | 298 | 306 | 296 | 326 | 312 | 307 | 330 | 338 | 334 | 410 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| orig | 0x8a0 | 0xa60 | 0xee8 | 0x1090 | 0x1200 | 0x12c8 | 0x1398 | 0x15d8 | 0x16d0 | 0x17a0 | **0x1c20** |
| main | 0x9f8 | 0x850 | 0x1098 | 0xe40 | 0xef0 | 0x1178 | 0x1320 | 0x1520 | 0x1628 | 0x16f8 | **0x1c20** |
| tf_g3_O | 0xa20 | 0x878 | 0x10c8 | 0xe70 | 0xf20 | 0xd88 | 0x1190 | 0x13a0 | 0x14a8 | 0x1578 | 0x1aa8 (-376) |
| none_O312 | 0x9f8 | 0x850 | 0x10a0 | 0xe48 | 0xef8 | 0xd60 | 0x1248 | 0x1448 | 0x1550 | 0x1620 | 0x1b48 (-216) |

Main's entry+validate region already ends exactly where the original's does (410 at 0x1c20). Main inlines two extra
`to_string`s (+376 B), so it lacks 376 B of something else before 0x1c20. The outline bases free those 376 B (O) or
216 B (O312) *inside* validate, so the repay has to come from the entry/validate region too: the class-E entry copy of
`new`, the OV duplication, and the `Result<Pubkey>` pieces at 0x538-0x580 (w15a11, w14a89, w12).

## 2. Fixed-RA B on every base (`bprice.py`, `arel.py`)

| base | bytes | M | jM | fM | + B/Br (bytes) | M | dM | jM | fM | errseq after |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| main | 27,400 | 2,249 | 2,275 | 2,380 | Br 27,408 | 2,277 | **+28** | 2,389 | 2,472 | original |
| tf_g3_O (Otf_g3_O) | 27,024 | 2,199 | 2,267 | 2,356 | Br 27,032 | 2,285 | **+86** | 2,397 | 2,482 | original |
| none_O (O, collapsed) | 26,992 | 1,955 | 2,031 | 2,199 | Br 27,000 | 2,040 | +85 | 2,161 | 2,327 | original |
| none_O312 (O312) | 27,184 | 2,196 | 2,264 | 2,379 | Br 27,192 | 2,281 | **+85** | 2,393 | 2,478 | original |
| tf_g3_O312 | 27,240 | 2,196 | 2,264 | 2,379 | Br 27,248 | 2,281 | +85 | 2,393 | 2,476 | original |
| T (w14a141 trigger) | 27,184 | 2,200 | 2,228 | 2,326 | TB 27,192 | 2,281 | **+81** | 2,394 | 2,478 | original |
| Tb (T+dv1+le306) | 27,176 | 2,203 | 2,228 | 2,326 | TB 27,184 | 2,285 | +82 | 2,276 | 2,478 | original |
| Tv01 (T, helper compares holder_key first) | 27,184 | 2,194 | 2,228 | 2,319 | TB 27,192 | 2,274 | +80 | 2,393 | 2,471 | original |
| h289 (one holder test = w15a25 T289n, collapsed) | 27,008 | 1,410 | | | Br 27,016 | 1,499 | +89 | 1,547 | 1,616 | original |
| main + fee-tag phi (w15a29) | 27,224 | 2,063 | 2,103 | 2,313 | Br 27,232 | 2,094 | +31 | | | original |
| tf_g3_O + fee-tag phi | 26,832 | 2,007 | 2,103 | 2,253 | Br 26,840 | 2,098 | +91 | | | original |

True LCS (unmasked, `lcschunk.py`) agrees. Main 2,255 -> main+Br 2,287 (+32). tf_g3_O 2,248 -> +Br 2,295 (+40 over
main). T 2,215 -> T+TB 2,291. The gain sits in orig chunks 0x800 (+32) and 0x1000 (+4 to +8).

Unit prices at fixed RA:
- tf_g3_O (`uo.py`):
  - the 312 error block after the 326 exit: **alone +41, LOO -76**;
  - the Err306 exit after the compares: alone +15;
  - the head exits need each other (LOO exit289 -58, exit298 -25, exit296 -23, bb17.i -20, bb10.i -19);
  - the compares: LOO -27.
- T (`ux.py`):
  - the 312+307 groups after 326: +23;
  - Err306 after the compares: +12;
  - the success chain (330) after 307: +12.

## 3. Real-llc realisations

IR order (post-opt block reorder, real llc; MBP re-places every cold block, so errseq rarely follows):

| base | full B in IR | best single unit | note |
| --- | --- | --- | --- |
| main | 2,119 (-130) | | reproduces w14a98's -129 |
| tf_g3_O | 2,127 (-72) | 2,204 (+5): 312 err block / compares / Err306 units | 330/338 come forward (`298 289 330 296 326 338 306 312 307`), as on T |
| T | 2,170 (-30) | none above 2,200 | |
| tf_g3_O + bb23.i 2:1 | | none above 2,232 | bb17.i/bb16.i -9, bb22.i -61 |

Branch weights (post-opt `!prof`, real llc). `bb23.i` is the 306 tag test `icmp eq i8 tag,0`: None, i.e. Err306, versus
Some. BPI's zero heuristic gives the None edge 37.5 % today.

| base | none (today) | bb23.i 1:1 (= IR and-1 tag) | bb23.i 20:12 (reversed zero heuristic) | **bb23.i 2:1** | 2:1 errseq |
| --- | ---: | ---: | ---: | ---: | --- |
| main | 2,249 | 2,221 | 2,204 | 2,218 @27,400 | 298 289 **306 296 326 312 307** 330 338 334 |
| tf_g3_O | 2,199 | 2,217 | 2,212 | **2,232** @27,032 | 298 289 **306 296 326 312 307** 330 338 334 |
| none_O312 | 2,196 | 2,213 | 2,209 | **2,228** @27,192 | same |
| tf_g3_O312 | 2,196 | 2,213 | 2,208 | 2,228 @27,248 | same |
| T + r2 (312 err block IR-glued after cmp2, w15a02's r2) | 2,196 | 2,213 | 2,209 | **2,228** @27,192 | same |
| T / Tb / Tv01 | 2,200 / 2,203 / 2,194 | 2,185 / 2,183 / 2,180 | 2,163 / 2,183 / 2,163 | 2,180 / 2,182 / 2,180 | 330/338 still inside |
| none_O | 1,955 | 1,973 | 2,029 | 2,049 | |

- On an outline base the 306 weight is the realisation lever of B's tail. It puts the original's
  `306 296 326 312 307 330 338 334` in place at real RA. Only the 289/298 head stays swapped. On main the same weight
  costs 31.
- Fixed-RA Br on top of tf_g3_O + bb23.i 2:1 gives 2,287 at 27,040 B. The 3 head flips are all that is left (+55),
  and they are not realisable: every head IR move loses (bb22.i -61), and holder weights or holder and-1 collapse
  (below).
- `wg.py` greedy (22 validate branches x 7 weights):
  - tf_g3_O stops at `{bb23.i 2:1}`, 2,232; no second weight helps.
  - T reaches `{bb28.i 20:12, bb33.i 12:20}`, 2,225 @27,192. bb28.i is the 307 zero-pubkey memcmp; 20:12 needs its
    error edge more likely than BPI's libcall heuristic allows for `memcmp==0`, a polarity no source spelling gives.
- and-1 union (bb7/bb14/bb23 1:1): main 2,199, tf_g3_O 2,057, T 2,163, Tb 2,170.
- IR and-1 holder (w14a78 H1) collapses everywhere: main 2,056, tf_g3_O 1,729, T 2,013. The and-1 tag equals bb23.i 1:1.
- w15a29's fee-tag phi (feeds line 757 and the pool CPI tag): main 2,063 (-186 @ -176 B, reproduces #3830),
  tf_g3_O 2,007, T and Tb 1,955.

Mperm (`mp.py`) of the key cells:

| cell | bytes | M | Mperm | Mhc | lcs | lcs_f |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main | 27,400 | 2,249 | 2,293 | 2,300 | 2,255 | 2,488 |
| tf_g3_O | 27,024 | 2,199 | 2,243 | 2,253 | 2,248 | 2,463 |
| tf_g3_O + bb23.i 2:1 | 27,032 | 2,232 | 2,275 | 2,282 | 2,244 | 2,456 |
| none_O312 | 27,184 | 2,196 | 2,240 | 2,247 | 2,244 | 2,464 |
| T | 27,184 | 2,200 | 2,243 | 2,250 | 2,215 | 2,445 |
| Tb | 27,176 | 2,203 | 2,246 | 2,253 | 2,215 | 2,445 |

## 4. Kill test: real-llc M plus an ideal repay (one matched token per 8 B up to 27,400 B)

| cell (real llc) | bytes | M | M + ideal repay | source-reachable? |
| --- | ---: | ---: | ---: | --- |
| tf_g3_O + bb23.i 2:1 | 27,032 | 2,232 | **2,278** | no: O has no non-collapsing source trigger (w15a25), and BPI cannot give 2:1 |
| tf_g3_O + bb23.i 1:1 / 20:12 | 27,032 | 2,217 / 2,212 | 2,263 / 2,258 | no: O as above |
| tf_g3_O + IR unit (312 err block) | 27,024 | 2,204 | 2,251 | no |
| none_O312 or T+r2 + bb23.i 2:1 | 27,192 | 2,228 | **2,254** | no: 2:1 not BPI-reachable; r2 glue has no spelling (w15a02: every 312-helper spelling is byte-identical to T) |
| none_O312 or T+r2 + bb23.i 1:1 / 20:12 | 27,192 | 2,213 / 2,209 | 2,239 / 2,235 | fails the bound |
| T + {bb28.i 20:12, bb33.i 12:20, bb38.i 1:1} (greedy end) | 27,192 | 2,226 | 2,252 | no: inverted memcmp polarity |
| tf_g3 + V-time 306 Some:None 1:2 (= tf_g3_O + bb23.i 2:1) | 27,032 | 2,232 | 2,278 | no: needs a None-hot 306 test; screen in section 7 |
| Tb (best source-real outline base) | 27,176 | 2,203 | 2,231 | fails |
| T / Tv01 / h289 / phi cells | | <= 2,200 | <= 2,227 | fail |

The ideal repay is generous. w15a02 showed that a perfect 216 B fill on T reaches only 2,226, and w15a25/w15a21 found no
faithful repay of O's 376 B. True LCS also disagrees with the difflib gains:
- tf_g3_O + bb23.i 2:1 has unmasked LCS 2,244, below tf_g3_O's 2,248 and main's 2,255;
- rfj LCS is 2,972 against O's 2,983 and main's 3,007.

The +33 is therefore a difflib alignment effect of the tail order, not a closer skeleton.

## 5. Hand-off (to w15a25-cto-o2tfg3repay and any later outline lane)

1. **The B order to use on any outline base is `data/OB_asm.txt`** (asm labels, valid for tf_g3_O, none_O312,
   tf_g3_O312 and h289, whose validate labels coincide). For T-family bases use `data/TB_T.txt`. Both give the original
   errseq. At fixed RA they are worth +80 to +89 M.
2. **The one real-llc lever is the 306 tag frequency.** With 306's None edge at 2:1, MBP lays out the original tail
   `306 296 326 312 307 330 338 334` on O/O312 at unchanged RA (+32/+33 M).
   - Applied from validate's inliner visit on, the same bias is also the outline trigger (section 6).
   - `tf_g3` with a V-time 306 Some:None of 1:2 is byte-identical to `tf_g3_O` + bb23.i 2:1: 27,032 B, M 2,232,
     lddw 86, no collapse.
   - This settles w15a25's next idea 1 ("lower 306's Some test") at the IR level. Its source form is the open part.
3. A 312-only trigger also needs the r2 glue: the 312 error block IR-adjacent to the last compare, as main has it.
   With T's spliced helper, 330/338 come forward and no weight helps (T row of the table).
   - T's weight greedy ends at `{bb28.i 20:12, bb33.i 12:20, bb38.i 1:1}` = 2,226 @27,192.
   - That is +26, but it needs the 307 memcmp error edge to be likely, which no spelling of `t==Pubkey::default()` gives.
4. Even with a source form for the None-hot 306 test, O sits at 27,032 B. Its 368 B repay must come from the entry and
   validate region (section 1), and w15a25/w15a21 found no faithful piece for it.

## 6. V-time 306 weights: one lever for both the outline trigger and the layout

`vw.py` puts a `!prof` on validate's raw 306 `switch` (the pre-opt IR). The full `opt -O3` and llc follow. lddw 86 is the
original's count (307 and 312 outlined); main has 88.

| base (raw capture) | V weight Some:None | to_string calls / lddw | bytes | M | errseq |
| --- | --- | --- | ---: | ---: | --- |
| m0 (main, `eq_main`) | none | 16 / 88 | 27,400 | 2,249 | 298 289 296 326 306 312 307 330 338 334 |
| m0 | 1:2 | 16 / **86** | 26,976 | 2,049 | 298 289 **306 296 326 312 307 330 338 334** |
| m0 | 1:4 | 16 / 86 | 26,992 | 2,046 | same |
| **tf_g3** (w15a21 creator binding) | none | 16 / 88 | 27,456 | 2,248 | 298 289 296 326 306 312 307 330 338 334 |
| **tf_g3** | **1:2** | 16 / **86** | **27,032** | **2,232** | 298 289 **306 296 326 312 307 330 338 334** |
| tf_g3 | 1:4 | 16 / 86 | 27,088 | 2,231 | same |
| T | 1:2 / 3:5 | 16 / 87 (307 stays inlined) | 27,192 | 2,180 / 2,163 | 330/338 still inside |

- **`tf_g3` + V 1:2 is byte-identical to `tf_g3_O` + post-opt `bb23.i` 2:1.** One fact, a None-hot 306 test from
  validate's inliner visit onward, does two things on the stabilised base:
  - it outlines 307 and 312 exactly as the original does, with no V-threading collapse (unlike w15a25's T289n family);
  - it lays out the original's tail order.
- On main's own form (m0) the same lever gives w15a25's collapsed `none_O` class (2,049 = `none_O` + bb23.i 2:1). The
  creator binding (tf_g3) is still needed.
- Arithmetic at V: 307 = N x P(Some) x 0.375 with N = 0.1509, so P(Some) <= 1/3 gives 0.0189 < 0.02 (cold, threshold 45).
- **No ordinary spelling makes None hot.**
  - At V, `if let Some` is the range form (50/50, w15a25).
  - After opt, every form canonicalises to `icmp eq i8 tag,0`, and BPI's zero heuristic makes None 37.5 %. The pointer
    heuristic (`Option<&Pubkey>`, null) points the same way.
  - Only `!prof` (the banned `likely`/`unlikely` family) or a cold call on the Some path would do it. A cold call there is
    a codegen-forcing construct under the RULE.
  - Section 7 screens the 306 spellings the angle named.

## 7. Source screen of the 306 test on tf_g3 (`gx.py` genes, `cap1.sh`, w15a25 `reduce.py` + `vbfi.py` for V-time BFI)

| gene on tf_g3 | line 306 | result |
| --- | --- | --- |
| `s306mi` | `let t=match new.is_some() as i32{1=>new.unwrap_or_default(),_=>return Err(..)};` (the sweep_fees.rs:145 idiom) | byte-identical to tf_g3 |
| `s306mz` | `let t=match new.is_none() as i32{0=>new.unwrap_or_default(),_=>return Err(..)};` | byte-identical to tf_g3 |
| `s306in` | `let t=if new.is_none(){return Err(..);}else{new.unwrap_or_default()};` | byte-identical to tf_g3 |
| `s306mu` | `let t=match new.map(\|t\|t.to_bytes()){Some(b)=>Pubkey::new_from_array(b),None=>return Err(..)};` | byte-identical to tf_g3 |

- All four have tf_g3's V-time BFI: 306 0.0754, and 307 0.0283 / 312 0.0287, which stay inlined.
- w14a98 already showed that the `match` Some/None-first, `if let None`, `&new`, `is_none()`/`is_some()` and let-else
  forms are identical on main or cost RA.
- The tag reaches validate as a `!range [0,2)` i8, so every spelling canonicalises before V.
- A None-hot or `and 1` (non-canonical) 306 test needs `new`'s tag to arrive in another representation. The original
  loads it as an i64 piece and tests `and 1`, which is consistent with w15a11's class-E entry copy. That representation
  gives 50/50, not None-hot. So in the original, 307/312 were cold for another reason, most likely the extra non-holder
  split of the OV duplication (w14a89), and its tail order came from the and-1 tag plus that CFG. On tf_g3_O the and-1
  tag alone is bb23.i 1:1 = 2,217 (+18).

## 8. Re-check on main 7e5ba44a7 (#3859, w16a07 sweep tuple: 0.67436, M 2,251)

The new captures (`m1` is `eq_main: true`; `tfg3n` is tf_g3 on the merged source) carry every delta over. The #3859
sweep change adds +2 M on each base and does not touch validate.

| cell | bytes | M | + fixed-RA Br | bb23.i 2:1 | 1:1 | 20:12 |
| --- | ---: | ---: | --- | --- | --- | --- |
| main (m1) | 27,400 | 2,251 | 2,279 @27,408 (+28) | 2,218 | 2,223 | 2,206 |
| tf_g3_O (tfg3n_O) | 27,024 | 2,201 | 2,287 @27,032 (+86) | **2,234** (+33) | 2,219 | 2,214 |
| O312 (m1_O312) | 27,184 | 2,198 | 2,283 @27,192 (+85) | **2,230** (+32) | 2,215 | 2,211 |
| tf_g3 + V-time 306 Some:None 1:2 | 27,032 | 2,234 (lddw 86, = tfg3n_O + 2:1) | | | | |

Kill test against 2,251 with the ideal repay:
- tfg3n_O + 2:1: 2,280. Unreachable, as for O.
- m1_O312 + 2:1: 2,256 (+5). Unreachable: 2:1 is not BPI-producible.
- m1_O312 + 1:1 / 20:12: 2,241 / 2,237. These fail.
- The conclusions of sections 4-7 stand.

## Verdict

Kill test met: no source-reachable cell reaches main's M (2,249 on 9bd38c7d5, 2,251 on 7e5ba44a7) even with an ideal
repay. The price table, the B orders
for outline bases and the 306-lever mechanism are the hand-off. Next ideas are in `SUMMARY.json`.
