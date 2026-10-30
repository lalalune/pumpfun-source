# w14a10-cto-and1outline: one `and 1` holder + `and 1` 306 tag reproduces the original validate outline

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 769f331fe (0.63241, 3,288 slots). Continues w14a02-cto-validatecr (#3209) next ideas 2 and 3.
Ledger keys: `0x22a10-w14-769f331-and1outline-*`.

## Oracles

- Raw-IR capture + `opt -O3` + extracted `llc` (w14a02 `capvar.sh`/`rx.py`; reproduces main exactly, `eq_main: true`).
- New post-opt oracle `tools/llcm.py` + `tools/pc.sh`: edit the slimmed post-opt module, run only `llc`, score, chunk
  table and error-tail order (0.3 s per trial). `e/post_gen2.py` has the post-opt genes.
- `tools/pbk.py`: matched orig instructions per 0x800 region with jump offsets masked; `tools/shift.py`: median
  (cand - orig) offset per 0x400 region (where the size difference sits).
- rm = registers, frame offsets and jump targets masked; rmV = rm-matched orig instructions in 0x0-0x1800 (score.py-style
  global alignment); L = local validate-window alignment (w14a02 `chunk.py`).

## Step 1: the outline is reachable (post-opt IR oracle on main 769f331)

Post-opt edits: `a1` = the holder test value `and i8 %holder, -3` (what `hopt==Some(true)` folds to) rewritten as the
original's `and i8 %holder, 1` (one representation feeds every holder test); `t306` = the 306 new-tag test
`icmp eq i8 %tag, 0` rewritten as `(tag & 1) == 0`; `t298` the same on the holder-arm 298 tag test.

| trial | bytes | plain | rm | rmV | rmT | L | chunks rm (0x200, 0x0-0x1800) | error tail |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | --- |
| original | | | | | | | | 289 298 306 296 326 312 307 330 338 334 410 |
| main | 27,400 | 0.63241 | 0.84691 | 432 | 2,827 | 484 | 37 38 31 25 28 56 34 20 38 51 39 35 | 298 289 296 326 306 312 307 330 338 410 334 |
| a1 | 27,336 | 0.61908 | 0.85603 | 451 | 2,854 | 509 | 37 38 33 46 59 53 1 20 45 45 39 35 | 289 298 296 306 326 312 307 ... |
| t306 | 27,416 | 0.62384 | 0.83827 | 404 | 2,799 | 456 | 37 38 31 25 28 56 3 21 46 45 39 35 | 298 289 296 306 326 ... |
| **a1+t306** | 27,344 | 0.63218 | **0.86610** | **486** | **2,888** | **544** | 37 38 33 48 59 53 34 28 37 45 39 35 | **289 298 306 296 326 312 307 330 338** 410 334 |
| a1+t298 | 27,336 | 0.61908 | 0.84973 | 432 | 2,833 | 490 | | 289 298 326 296 306 ... |
| a1+t306+t298 | 27,344 | 0.61988 | 0.85590 | 454 | 2,854 | 512 | | 289 298 306 326 296 ... |
| v2 (nested 289) + a1 | 26,920 | 0.49864 | 0.79359 | 333 | 2,626 | 367 | | 312 289 298 296 ... |
| hm + a1 | 27,312 | 0.47802 | 0.79370 | 381 | 2,645 | 436 | | 289 298 306 312 307 296 ... |

So the original's error-tail order through 338 needs exactly two things, both single-bit masks that BPI's zero heuristic
ignores (50/50): one `and 1` holder value for all holder tests, and the 306 tag test as `tag & 1`. The 298 tag test
must stay a plain `icmp eq tag, 0`. The nested-289 threading (v2) is not needed and hurts. a1+t306 is +54 rm in
0x0-0x1800, +61 rm in total and +60 L over main; the plain ratio at -56 B is already 0.63218.

## Step 3: source spellings (raw-IR capture on main 769f331)

Holder (all with the main 306 test):

| gene | source | bytes | plain | rmV | rmT | tail |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| hx | `matches!(hopt,Some(true))` everywhere | 26,760 | 0.52501 | 399 | 2,689 | 298 296 326 284 ... |
| ux | `hopt.unwrap_or(false)` everywhere | 26,768 | 0.51826 | 387 | 2,677 | 284 289 306 ... |
| hxe/uxe | execute's holder only (matches!/unwrap_or) | 27,144 | 0.56231 | 424 | 2,816 | = main |
| e1 / e2 | entry `hb=holder.unwrap_or(false)` / matches!, validate keeps `hopt` | 26,848 / 26,840 | 0.475 / 0.482 | 391 / 407 | | |
| **e3** | entry `let hb=holder.unwrap_or(false);`, **validate takes `hopt:bool`** (= hb), 289 is `!hopt` | 27,320 | 0.60486 | **451** | 2,849 | = a1 oracle |
| e4 | entry `(holder==Some(true)) as u8&1!=0` | 27,328 | 0.61407 | 435 | 2,831 | = main |

`matches!`/`unwrap_or` in execute become a phi of constants (the match is lowered as control flow in execute's
CFG), not an `and 1`. Passing the bool into validate (e3) is the only spelling that gives the single `and 1` holder;
it reproduces the a1 oracle (rmV 451, L 503).

306 tag on top of e3:

| gene | source | bytes | plain | rmV | rmT | L | tail |
| --- | --- | ---: | ---: | ---: | ---: | ---: | --- |
| thb | w14a07 HB without `cold()`: `has=args.0.is_some()`, `if has{new.unwrap_or_default()}` | 27,192 | 0.57504 | 488 | 2,875 | 543 | orig through 338 |
| **tu8** | `if unsafe{*(&new as *const Option<Pubkey> as *const u8)}&1!=0{unsafe{new.unwrap_unchecked()}}else{306}` | 27,328 | 0.61377 | **487** | **2,884** | **539** | **orig through 338** |
| tu8d | same test, `new.unwrap_or_default()` | 27,328 | 0.61377 | 487 | | | = tu8 |
| tun | `if new.is_some(){unsafe{new.unwrap_unchecked()}}` | 27,320 | 0.60486 | 451 | | | = e3 |

**e3+tu8 equals the a1+t306 oracle** (rmV 487 against 486): the original validate block outline and error-tail order
through 338 are source-reachable on current main. What it still loses in plain ratio (0.61377 at 27,328 B) is:

- size: -72 B. `shift.py`: main sits at -56 (prologue) through the body and ~0 at the tail; e3+tu8 sits ~45 B further
  behind from orig 0x1c00 on and ~70 B behind at the tail, so every long jump from validate into the shared tails
  carries a different offset;
- registers in the fee-check chunk (orig 0x1000-0x1400 fm 37/43 -> 15/12) and the sharing/sweep region
  (orig 0x4000-0x4800: 95/175 -> 59/155 plain-matched).

## Step 3b: on main cef0574 (0.63421, M 2117): where the and-1 value is defined decides the register map

`M` = scorer-exact matched orig units (`tools/preg.py`; ratio = 2M/(3339+n)). At the pinned size a neutral fill gives
ratio ~ M/3339, so a landing needs M > 2117.

| trial | bytes | plain | M | rmV | tail | note |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| main cef0574 | 27,400 | 0.63421 | 2,117 | 432 | 298 289 296 326 306 ... | |
| e3+tu8 (hb at execute entry) | 27,328 | 0.61407 | 2,047 | 487 | orig through 338 | orig 0x4000-0x4800 clone run 79 -> 20 (RA) |
| p0/p1 (hb after `let a` / `mint`) | 27,328 | 0.61407 | 2,047 | | same | = e3 |
| **p2 / p1b / p2b / p2c** (hb after the shared test or the holder PDA call; `unwrap_or` or `matches!`) | 27,360 | **0.63289** | 2,111 | 487 | orig through 338 | clone run restored (81) |
| p3 (hb just before the state block) | 27,344 | 0.63278 | 2,110 | | same | |
| e3b/e3d (hb inside the state block) | 27,192 | 0.57323 | | 413 | | |
| p2d (`holder==Some(true)` bool) | 27,416 | 0.60677 | | | 298 289 ... | and -3 form: outline lost |
| **vu8 / vraw** (validate takes `hopt:u8`, tests `hopt&1`; vraw passes the raw `Option<bool>` byte) | 27,368 | **0.63309** | 2,112 | | orig through 338 | best form |
| vref (`&bool`) | 26,936 | 0.54804 | 1,814 | | | |

`p2` source: `holder_key=hk.0;let hb=holder.unwrap_or(false);` in execute, `let hopt=hb;let holder=hb;` in the state block,
`fn validate(st:&CtoState,hopt:bool,...)` with `let holder=hopt;` and the 289 test `st.holder_reward&&!hopt`, plus tu8 at 306.
The p2 holder store matches the original's shape (orig 0x4b58-0x4b78: `ldxdw [curve+0x38]; stxb [+0xa5]` per flag; main
spends 40 B on a bool re-materialisation there), which is where most of the -40 B comes from: the original is short there too.

Size repay (sizeknobs-cto.json, all applicable knobs as genes `K<name>`): every size-adding knob loses on p2/e3
(Kwltsclockvar +16 0.63180, Kgfeeunwrap +8 0.62860, Kevmintkey +16 0.62461, Kwevcreatorfirst +64 0.57793; all +40
combinations at 27,400 B: 0.594-0.620). Zero-size knobs: Kcureplace byte-identical, the rest -0.0003..-0.004.
Other composites on e3+tu8 / p2+tu8: pda 0.566 (rmV 519, RA collapse), rar 0.610, ov 0.538, kv 0.549, anew 0.523,
t296/smap/sw/q338 no change, tg/tg3 (tag byte read in execute) 0.535-0.582, q289 (289 test as `ho==Some(true)`) 0.557.

## llc weight bound on p2 (`tools/wscan.py`, `tools/wmulti.py`)

All 146 conditional branches x {20:12, 12:20, 1:1000, 1000:1} on p2+tu8's post-opt IR. Best singles: sweep gate
(`!skip`) 20:12 0.63778 @ 27,352; fee range test (338) 1000:1 0.63778; 289 holder test 12:20 0.63668 @ 27,344.
Combinations reach 0.63808 (M 2,128, +11 over main). None changes the error-tail order: they are register/frame
reassignments. No source spelling for them was found (q289 relayouts the function).

## Step 3c: on main b174038 (0.63571, M 2122) the register map moves again

After #3241 (quote_locked inline) and #3250 the p2 position lands in the clone-run collapse (orig 0x4000-0x4800 79 -> 20),
and only an `hb` defined after `quote_locked` (just before the state block) keeps it:

| trial | bytes | plain | M | note |
| --- | ---: | ---: | ---: | --- |
| main b174038 | 27,400 | 0.63571 | 2,122 | |
| e3 / p0 / p1 / p1b / p2 / p2c / vu8 / vraw + tu8 | 27,336-27,344 | 0.6142 | 2,048 | clone-run collapse |
| p3n + tu8 (`let hb=holder.unwrap_or(false);` after quote_locked, validate `hopt:bool`) | 27,336 | 0.63227 | 2,108 | |
| **p3u + tu8** (same, validate `hopt:u8`, tests `hopt&1`) | 27,344 | **0.63248** | **2,109** | full `measure.sh`: = oracle, normalized 1034 (0 losses), calls 154+3, differential 363/363 |

On main 1b0ae70 (0.63661, M 2,125): p3u+tu8 0.63317 @ 27,336 (M 2,111), p3n 0.63297 (2,110), p2 / vu8 / e3 0.6314
(2,104); all keep the original error-tail order through 338.

So the and-1 outline form tracks main at -13 M / -56 B, and which `hb` position works depends on the rest of the
function's register pressure: it is not a stable lever.

LLC weight bound on p3u (`tools/wscan2.py`, scorer M per trial, validate branches 0-31 x 4 weights): only the 338
fee-range test (`icmp ult f-1, max`) helps: OK-likely 20:12 gives M 2,128 (+6 over main, 0.63808 @ 27,352), 1000:1 M
2,127. fee_configurable (330) at 1:1000 gives 2,123 and moves 334 ahead of 338. Combinations stay <= 2,128. The
338 test has no BPI heuristic in our IR (instcombine merges `f==0||f>max` into one unsigned compare); the split
spelling (`v_fee_split`) costs +200 B.

## Next

- The and-1 outline form is the right validate skeleton (+55 rm in 0x0-0x1800, original error-tail order through 338)
  but on b174038 it is 13 M short of main at -56 B (p3u+tu8). A landing needs those M back from register/frame
  assignment in validate (orig 0x1000-0x1400 fm 37/43 -> 15/12) and the clone run, plus a fill that is not a catalog knob.
- Compose p3u+tu8 (or whichever `hb` position avoids the clone-run collapse on the then-current main; screen p0..p3)
  with any clone-run / frame RA fix (w14a01/w14a05/w14a06 leads) before the size repay.
- Look for a spelling that gives the 338 fee-range test an OK-likely weight without splitting the error site.
- Fill candidates that are faithful: the original's entry copy of `new` and the holder_key copy (orig 0x4d8-0x5d0).
