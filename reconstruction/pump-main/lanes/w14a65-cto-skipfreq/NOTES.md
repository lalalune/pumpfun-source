# w14a65-cto-skipfreq: two-weight frequency screen for the skip-polarity sweep gate (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 2e1379de9 (0.65728, 3,192 slots), re-run on main 304b03a82 and spot-checked on 0d04cf460 (section 5) (0.65788, 3,223 slots; post-opt IR F 0.74805, Fw 409, the same as 2e1379d).
Angle: w14a46-cto-walletcsr (#3355) next idea 1 and w13a49-cto-colderr (#3156) next idea 1. Find a block-frequency picture in which the
original's skip-polarity gate (`br skip, post, sweep`) keeps main's layout and leaves the `!skip` flag spilled, then find source for it.
Ledger: approach `skipfreq`, keys `0x22a10-w14-{2e1379d,304b03a}-skipfreq-*`.

**Result: no source change. The skip-polarity family is retired.** The screen covers 4,101 IR pictures on 304b03a and about 2,600 on 2e1379d.
The picture the angle asked for exists: one weight on the shared-arm holder test (`bb19` 16:1) gives main's layout and a spilled flag.
But none of those pictures reaches main's frame-masked match (best F 0.74130 against main's 0.74805), and none beats main's plain ratio
(best 0.64824 against 0.65788). Once the flag is spilled, r9 over the wallet goes to `coin_present` (the `data_is_empty` r0 result) in
every picture, and the wallet match falls (Fw ≤ 402 against main's 409).

## Oracle (`tools/pair.py`)

`pair.py <m.ll> <out.jsonl> --pre edits/ir/sg3.py --heads <blocks> --hw <weights> --ws <weights> [--single|--only-heads]` works on the post-opt
module from `rx.py --keep`. It applies the sg gate, adds a `!prof` weight to the head branch and to each other conditional `br` of execute,
runs llc to asm and assembles it with cc1as. For each picture it records:
- `ratio`/`bytes`: the rx metric.
- `F`/`Fw`: w14a46 `wf2.py`, frame-masked with registers kept, and its wallet tokens (orig 0x5c40-0x6b08).
- `moved`: w14a46 `reorder.py`, the number of chains out of main's chain order. 0 means main's layout.
- `flag`: for F ≥ FMIN, read from the debug-greedy log (`csrmap.py`). The flag is the vreg tested by `J*_ri %N, 0` in `bb35`. The value is the
  callee-saved register that holds it over the wallet range [bb33, bb82), or `spill`.

Run it next to the w14a03 `rx.py`/`capraw.py`/`capvar.sh`/`dis.sh`, w14a46 `wf2.py`/`reorder.py`/`csrmap.py`, w14a36 `asmscore.py` and w14a35
`dll.sh`/`ra.sh` in `$OUT/tools`, with `or.dis` in `$OUT`. A non-deep job takes about 1 s, so 580 pairs take about 8 min at -j 5.
`tools/table.py` builds the tables below. `tools/jm.py` scores with jump offsets masked and frame offsets kept. It shows whether a plain-ratio
loss comes from size or from the frame.

Checks: an unedited capture gives `eq_main: true` on both mains. The sg gate on this main (`edits/ir/sg3.py`, `%_555`, `bb82`/`bb87`) gives exactly
the g9 source bytes (0.48362 @27,456 on 304b03a, 0.48332 @27,456 on 2e1379d), so the IR oracle prices the source form.

## 1. Single weights on sg (304b03a; `table_304b03a.md`, rows "head" and "single")

| weight on sg | bytes | ratio | F | Fw | moved | flag over wallet |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| main (no sg) | 27,400 | 0.65788 | 0.74805 | 409 | 0 | r9 |
| sg alone (= g9 source) | 27,456 | 0.48362 | 0.56262 | 399 | 55 | spill |
| `start` (= `bb1`) 3:1-4:1 | 27,384 | 0.60953 | 0.71022 | 405 | 0 | r9 |
| `start` ≥ 5:1 | 27,256 | 0.64824 | 0.73536 | 376 | 9 | r6 (head RA cascade, same bytes as main + start 16:1) |
| `bb12` 2:1 / 3:2 | 27,320 | 0.6157 | 0.7105 | 364 | 0 | r9 |
| **`bb19` (shared-arm `if holder`) 4:1 or 16:1** | 27,312 | 0.58245 | 0.73548 | 400 | **0** | **spill** |
| `bb74` (`if shared`) 12:20 / 1:16 | 27,304 | 0.5819 | 0.73499 | 400 | 2 / 8 | spill |
| `bb26` 12:20 | 27,312 | 0.60795 | 0.69347 | 406 | 2 | spill |
| sweep-exit `?` test 1:k, k ≥ 4 (Err-likely) | 27,320 | 0.61026 | **0.74977** | 409 | 0 | r9 |
| every other branch x {20:12, 12:20, 16:1, 1:16} | | ≤ 0.6104 | | | | |

- The flag is spilled whenever the shared/holder tree (`bb74`/`bb19`) leans toward `shared && holder`, the sweep path. This happens with or
  without sg: on main, `bb19` 16:1 alone gives 0.58211 @27,288, F 0.73612, flag spilled. The gate polarity is not what spills the flag.
  The frequency of the `!skip` region is.
- `start` 4:1 → 5:1 is the threshold where the head RA cascade (-144 B, `moved` 9) moves the flag from r9 to r6. It never spills the flag
  together with main's layout.
- The sweep-exit 1:k result is the only picture whose F is above main's. Its jump-masked ratio (`jm.py`) is 0.62286 against main's
  0.66747, so the loss is spill-slot assignment, not size. It also needs the `?` Err edge to be likely, which no source can express.

## 2. Pairs on sg (304b03a: 3,480 pairs; 2e1379d: 1,756 pairs plus 585 singles; `table_*.md`, `top-rows-304b03a.jsonl`)

The head is one of `bb19` 16:1, `bb74` 12:20, `start` 4:1 and the sweep exit at 1:16, 12:20 and 1:3. On 2e1379d the heads were `start` 4:1/16:1 and `bb12`
2:1/1:4 (partial). The second weight goes on each of the other 145 conditional branches, at 20:12, 12:20, 16:1 and 1:16 (on 2e1379d also 4:1 and 1:4).

| head (304b03a) | pairs | moved 0 | moved 0 + spilled | max F | max F, moved 0 + spilled | max Fw, spilled | max ratio |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `bb19` 16:1 | 580 | 296 | 210 | 0.74531 | 0.74130 | 402 | 0.64824 @27,256 |
| `bb74` 12:20 | 580 | 0 | 0 | 0.74482 | - | 402 | 0.64774 @27,248 |
| `start` 4:1 | 580 | 291 | 0 | 0.74440 | - | - | 0.64824 @27,256 |
| sweep exit 1:16 | 580 | 185 | 0 | 0.75619 (r9, moved 3) | - | 401 | 0.64684 @27,248 |
| sweep exit 12:20 | 580 | 2 | 0 | 0.74902 | - | - | 0.64824 @27,256 |
| sweep exit 1:3 | 580 | 4 | 0 | 0.74977 | - | - | 0.64714 @27,248 |

- No pair meets all three criteria (layout = main, flag not in r9, F ≥ main). On 304b03a no row has a plain ratio above main. The best is 0.64824
  @27,256, the `start` ≥ 5:1 cascade.
- The only row that is spilled with F ≥ main is sweep exit 1:16 + `bb23.i` 16:1: F 0.74865, but moved 5, Fw 401 and ratio 0.59898.
- Across all 287 spilled rows on 304b03a's `bb19`/`bb74` heads, r9 over the wallet holds `%721`/`%722` (`coin_present`, the `data_is_empty` r0
  copy) plus a `%62` accounts-pointer copy. This repeats w14a46's k1 whack-a-mole. Freeing r9 by frequency does not produce the original's wallet
  assignment, because the original spills `coin_present` as well.
- The sweep-exit pictures beat main's F only because they mark the whole post-sweep tail cold. That changes RA and spill slots in the tail
  (plain ratio about 0.61). The original's `?` test is not Err-likely.

## 3. Source spellings (raw-IR capture + rx = identity build; `edits/src/`, `src_screen.jsonl`)

On 304b03a the `bb19`/`bb74` tests are `i1` branches, which have no BranchProbabilityInfo heuristic (50:50, or 37.5/62.5 from the
`hopt==Some(true)` inline). A 16:1 weight needs a cold call in the `!holder` arm, which adds a call (154+3 must stay). So these spellings
can only change structure, not frequency:

| key | line-339 tuple spelling | alone | + g9 gate |
| --- | --- | --- | --- |
| v1 | `if !shared{..}else if holder{..}else{..}` | 0.65788 (= main score) | 0.48362 @27,456 (= sg) |
| v2 | `match (shared,holder){(true,true)=>..,(true,false)=>..,_=>..}` | = main | = sg |
| v3 | `if shared&&holder{..}else if shared{..}else{..}` | 0.57554 @27,368 | 0.57554 @27,368 |
| v4 | `if shared{if !holder{..}else{..}}else{..}` | = main | = sg |
| v6 | `if shared{(false,if holder{Some(None)}else{..},!holder)}` | 0.4634 @27,544 | 0.64755 @27,288 (F 0.73431, Fw 376, moved 35) |

The head (`shared` chain) spellings were screened by w14a11 (#3227) and fold back to main or change instruction selection.
The `if skip{0}else{sweep()?}` and gate-from-tag forms were screened by w14a46 (#3355).

## 5. Re-check on main 0d04cf460 (0.66507, 3,228 slots; post-opt F 0.75524, Fw 409; `edits/ir/sg4.py`, `%_549`, `bb84`/`bb89`)

| picture | bytes | ratio | F | Fw | moved | flag |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| main | 27,400 | 0.66507 | 0.75524 | 409 | 0 | r9 |
| sg | 27,456 | 0.4908 | 0.56891 | 399 | 57 | spill |
| main + `bb19` 16:1 (no sg) | 27,328 | 0.58917 | 0.74276 | 400 | 0 | spill |
| sg + `bb19` 4:1 / 16:1 | 27,312 | 0.58905 | 0.74269 | 400 | 0 | spill |
| sg + `start` 4:1 | 27,376 | 0.62221 | 0.7322 | 405 | 0 | r9 |
| sg + `start` 16:1 | 27,256 | 0.65515 | 0.74257 | 376 | 9 | r6 |
| sg + sweep exit 1:4 | 27,320 | 0.61746 | 0.75698 | 409 | 0 | r9 |

The picture is unchanged: layout + spilled flag costs about 0.013 F, and the only F gain needs an Err-likely `?` and keeps the flag in r9.

## 4. Conclusion and next ideas

- The skip-polarity gate is a dead lever. The frequency picture that spills the flag with main's layout exists (`bb19` 16:1), but it costs
  F 0.007-0.013, it has no source spelling, and it hands r9 to `coin_present`. No two-weight picture repairs this.
- The wallet's r9 residual is not a frequency effect. It is the set of long-lived values (flag, `coin_present`, tag, the current_creator GEP)
  that the original spills. Next, look at what makes the original spill `coin_present`. In the original it is reloaded from `[r10-..]` per use.
  w14a46's k1+w1+cpm bound (all spilled) is a rotation of the original assignment, so the remaining difference is the order of the
  long-lived values' spill weights. The order to compare is `do_coin` / `do_collect` / clone buffers.
- `pair.py` applies to any two-weight question. Pass `--pre` with any post-opt IR edit and `--single` for one-weight sweeps.
