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

## Next

Size repay with the `sizeknobs-cto.json` catalog on e3+tu8 (all applicable knobs screened as genes `K<name>` in
`e/gen.py`), then a full `measure.sh` build at 27,400 B.
