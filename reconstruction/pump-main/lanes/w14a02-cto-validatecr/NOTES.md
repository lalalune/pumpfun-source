# w14a02-cto-validatecr: whole-region composites of validate + shared/holder join (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 53abf28b1 (0.62672) and 23322b07c (0.62882, #3200, merged during the lane).
Angle: compose the continuation lanes' validate forms into one body that follows the original's block outline of
orig 0x0000-0x1a88, and score it per 0x200 chunk before any frame or size repay.
Ledger keys: `0x22a10-w14-{53abf28,23322b0}-validatecr-<genes>-v1` (46 rows).

**Result: no zero-loss gain, no source change.** The only composition step that clears the brief's bar (skeleton
+30 instructions in orig 0x0-0x1800) is holder_key PDA before `shared` (`pda`). It reaches +35 rm there and +30 rm
over the whole function. Its plain-ratio loss is pure register assignment in the clone-run / sweep-CPI region
(orig 0x3000-0x3800). Every validate-body step (nested 289, OV, take306, `and 1` holder, holder phi) reorders the
error/arm blocks against the original and loses rm in 0x0-0x1800 on its own and in every composite tried.

## Oracles

Every number is the raw-IR capture + `opt -O3` + extracted `llc` oracle (w13a23/w13a38 `capvar.sh` + `rx.py`). It
reproduces both mains exactly (`eq_main: true`; 0.62672 and 0.62882 at 27,400 B). New tools (`tools/`):

- `chunk.py <m.o|so>`: w13a38 `abs.py` fm/rm, plus the brief's per-0x200 chunk table of rm-matched orig instructions
  (global difflib alignment, as score.py aligns) over 0x0-0x1800 (`rmV`) and the whole window (`rmT`), plus a local
  validate-window alignment `L` (orig [0,0x1a88) against the candidate up to the prepare_bonding_curve tag test).
- `aln.py <m.o> lo hi [L]`: each orig instruction with its aligned candidate instruction (or `--`).
- `bucket.py n1 n2..` (`G=1` for global alignment): per-0x100 matched counts side by side.
- `lseq.py`: layout order of the `error!` line immediates (the error tail order).
- `outl.py orig|<m.o> lo hi`: condensed block outline (labels, branches with resolved targets, calls, error/line stores).
- `e/gen.py` + `tools/batch.sh name_name..`: composable genes; a trial name is its genes joined by `_`.
- `coal.py` (w13a40): Err-payload class / accounts-pointer split diagnosis with the debug llc.

## The original's validate outline (orig 0x5d8-0x1a88)

```
5e0 mayhem -> tail 0x5680
628 hr?  (hr = st.holder_reward)       hr false -> 710
640   holder (r8 = hopt & 1)? -> 900    else 648: 289 msg (fallthrough), tail 818
710 holder? no -> 730, yes -> 8f8
730   new tag & 1 == 0 -> 750: 306 msg (fallthrough)   Some -> c08
8f8 holder_enabled? no -> f40 (296)     falls into 900
900 holder arm: new.is_some -> 298 (908, tail 9d8)
ab8   target = holder_key (-0x518 -> -0x530); fee None -> 10e8; quote_locked -> b40 (326 msg); else -> 1638 (skips 330)
c08 non-holder: t pieces; memcmp default -> 1328 (307); memcmp sharing / holder_key -> 1258 (312)
d78   cashback flag (-0x958); shared? no -> 1490
dc8   shared: target = st.creator; fee None -> e38 -> 1850 (shared, non-holder exit)
1490  not shared: target = t; fee None -> 18f8 (collect_old)
1510 fee checks (shared by both non-holder exits; holder enters at 1638): 326, 330, 334, 338
1800 fee ok: shared? -> 1830 (holder? 1138 : 1850) else 18b0 -> collect_old memcmp 18f8 -> join 1990
```

Error tail order: orig `289 298 306 296 326 312 307 330 338 334 410`, main `298 289 296 326 306 312 307 330 338 410 334`.

## Composition table (main 23322b0, 0.62882)

rm = registers + frame offsets + jump targets masked; columns are rm-matched orig instructions per 0x200 orig chunk.

| trial | bytes | plain | fm | rm | rm 0x0-0x1800 | rm total | L rm | chunks |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| **main** | 27,400 | **0.62882** | 0.72049 | 0.84781 | 432 | 2,830 | 484 | 37 38 31 25 28 56 34 20 38 51 39 35 |
| **pda** | 27,384 | 0.56758 | 0.66197 | **0.85706** | **467** | **2,860** | **519** | **59 51** 31 25 28 56 34 20 38 51 39 35 |
| h2 | 27,200 | 0.60051 | 0.72079 | 0.85220 | 434 | 2,834 | 491 | 36 38 32 29 25 56 34 20 38 51 41 34 |
| take | 27,424 | 0.61985 | 0.71298 | 0.84054 | 409 | 2,807 | 461 | 37 38 34 25 28 56 3 21 47 46 39 35 |
| hm+ov | 27,192 | 0.50195 | 0.68722 | 0.83759 | 407 | 2,785 | 462 | 36 38 33 21 59 54 2 52 42 15 21 34 |
| hm+ov+take | 27,216 | 0.52548 | 0.69172 | 0.84112 | 419 | 2,798 | 474 | 36 38 33 46 57 51 2 52 37 4 29 34 |
| v2+anew | 26,792 | 0.53923 | 0.67343 | 0.83611 | 372 | 2,760 | 428 | 37 38 33 24 30 22 2 19 43 52 38 34 |
| pda+v2+anew | 26,992 | 0.54987 | 0.64977 | 0.83567 | 407 | 2,769 | 464 | 59 51 33 24 30 22 2 19 43 52 38 34 |
| pda+take | 27,432 | 0.54611 | 0.65269 | 0.85150 | 448 | 2,844 | 500 | 59 51 35 25 28 56 3 21 47 46 42 35 |
| pda+hm | 27,448 | 0.4765 | 0.60401 | 0.82909 | 417 | 2,770 | 453 | 58 51 34 21 58 55 2 51 31 3 21 32 |
| pda+hm+ov | 27,304 | 0.35444 | 0.62695 | 0.79952 | 391 | 2,664 | 443 | 57 47 33 21 56 38 0 45 42 13 10 29 |
| pda+kv | 27,424 | 0.47492 | 0.60189 | 0.79443 | 382 | 2,653 | 437 | 58 51 35 28 25 15 0 26 46 19 47 32 |
| pda+h2+anew | 27,488 | 0.47286 | 0.54314 | 0.64364 | 468 | 2,152 | 528 | 59 50 32 23 30 57 34 20 38 51 40 34 |
| take+v2 | 26,976 | 0.52377 | 0.65872 | 0.80060 | 351 | 2,652 | 385 | 35 38 31 25 29 15 0 27 33 49 36 33 |

The same ladder on 53abf28 (32 trials, `table_53abf28.md`) gives the same ranking: pda +35 rm in 0x0-0x1800,
h2 +2/+7 (L), all others negative. Genes (`e/gen.py`): v2 = nested 289 (w13a43 T289N, the holder-threading form);
d289/g289 = 289 spellings; hm/hu = `matches!(hopt,Some(true))` / `hopt.unwrap_or(false)` (the original's `and 1`
holder); t296 = `!(hr||en)`; take = w13a17 TAKE306 (`new.take()`, the 1:2 Some:None form); ov = shared override in
the non-holder arm (w13a04 OVMK); lv3n = w13a45 out-param fee-None threading; h2 = w13a38 holder out-param phi;
kv = validate takes holder_key and the sharing key by value (w13a41 t8 / w13a33 v1); anew = sharing arm reads
`Some(new)` (no `args` copy); smap = w13a31 token `.map`; pda = holder_key PDA before `shared` (original call order).

## Which composition step loses, and why

1. **pda (orig 0x100-0x260) is the only skeleton win, and it loses only on registers.** Per 0x800 region, pda's rm
   equals main's everywhere except region 0 (+35). fm drops 193 -> 51 and 205 -> 140 in orig 0x3000-0x3800 (the
   AccountInfo clone runs before the sharing/transfer CPIs): 148 instructions there lose their register match
   (`ldxdw rX,[r8+..]` becomes `[r6+..]` / `[r3+..]`). `coal.py`: the Err-payload class moves from r8 (main) to r6
   (pda); the original uses r9. The post-opt IR of pda differs from main only in the entry order plus one PRE'd
   curve-pointer phi at the shared join. Removing that phi (IR oracle `e/l_nophi.py`) is worse (0.53307), so the RA
   shift comes from the call order itself. Size is -16 B. This is the w13a13 R2 loss, now much larger (-0.061
   against -0.005 on 9eb6c00), because later landings tuned the clone-run RA to main's shared-first order.
2. **The validate-body forms reorder blocks against the original.** The original lays out 289 msg, 306 msg,
   289 tail, 296 test, holder arm, 326 msg, *then* the non-holder memcmps. v2/d289 (nested 289) gets the original
   to_string outline set but puts the 312 tail first and moves the memcmp chunk (orig 0xa00-0xe00 falls from 90 to
   15-24 rm). hm (`and 1` holder) gives the original's first three tails (289 298 306) and +30 rm at orig 0x800 and
   +23 at 0xe00, but its holder is tested in two representations (`and 1` and the icmp), so the non-holder memcmp
   arm is laid out before the holder arm and orig 0xc00-0xe00 and 0x1100-0x1400 lose 85. OV and lv3n lose 0xc00 and
   0x1200 the same way. take puts 306 before 326 (orig order) but loses the 0xc00 memcmp chunk (34 -> 3).
3. **h2 (holder phi) is skeleton-neutral (+2 rm, +7 L) at -200 B.** Composed with ov or pda it collapses the tail
   (pda+h2+anew: orig 0x4000-0x5000 rm 0, a sweep/pool-region relayout), as w13a38 and w13a49 saw for g1+n5hp.
4. **kv (by-value keys) is negative with every partner on current main** (pda+kv: 382 rm in 0x0-0x1800 against 467 for pda alone).
5. No composite reached the step-4 threshold except pda alone, so no size knobs or faithful partners were applied
   beyond the kv/anew pairings above. All trials keep 154+3 calls.

## Next ideas

- pda + a register-class fix for the clone run: the Err-payload class must get r9 (original) instead of r6 after the
  PDA-first reorder. w13a40/w13a44/w13a36 have the mechanism (swept joins the payload class first). A pda trial on
  top of any landed clone-run RA fix is the first thing to screen. The +35 skeleton is there to collect.
- The validate block order needs one holder representation (`and 1`) **and** the nested 289 threading at the same
  time; `v2+hm` relayouts the whole function (mayhem inline, AnchorError temp moves -0x2b8 -> -0x2d0). An IR
  oracle that applies hm's `and 1` to the three holder tests of v2's post-opt IR would show whether the outline
  itself is reachable before searching for a source spelling.
