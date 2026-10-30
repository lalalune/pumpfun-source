# Lane w10r1-admincto-region2of6 (wave 10, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`).
Angle: region split, region 2 of 6. The original window (27,400 B, 3,425 slots) is cut into six equal
byte ranges; region 2 is original `0x23be6..0x24dbd` (537 slots).
Base: origin/main 917ee615f (1032 / 347), admin_cto 27,344 B, ratio 0.37637; re-measured on 5a057949 (#2524: 27,400 B, 1033 / 1033) and 319a7d10f (#2622: 27,400 B, ratio 0.36129, 3,297 differing slots).
Builds: `~/.cache/pumpfun-reconstruction/lanes/w10r1-admincto-region2of6/`.

## What region 2 holds in the original

Mapped with the error-site coordinates (`coords.py window 0x22a10`) and call targets:

| original offset | contents |
| --- | --- |
| 0x23be8 | tail of the 326 `CreatorFeeNotConfigurableForQuote` error (inlined to_string, then the error) |
| 0x23c68 | 312 `InvalidCreator` and 307 `CreatorShouldNotBeZero` (+ with_pubkeys): to_string is OUTLINED here (two calls) |
| 0x23ea0 | Ok(target) merge, fee tag test, 330 check (`[r10-0x8e8]` = !holder&&cashback) |
| 0x24048 | 334 check (`fee_configurable`), 338 range check (`f-1 < max`), then the 338 error block and the 334 error block back to back |
| 0x24210 | phi merges of sharing_update tag (2 = None), collect_old, skip-sweep flag; `creator != default` memcmp |
| 0x24460 | `prepare_bonding_curve` call, `?`, 410 `CreatorFeesNotSwept` |
| 0x24688 | wallet gate (`collect_old`), executable / owner checks, shared msg call |
| 0x24740 | sweep gate on a precomputed bool `[r10-0x8e0]`, sweep entry: bump read, native-mint memcmp, creator-vault PDA, 648 check, amm token_frozen |

Main's layout differs in region 2 mainly in: 312/307 inline to_string (known, PRs #2370/#2416); 330 is
placed in region 1; the 334 error block is chained after the wallet's executable check instead of after 338;
the sweep gate recomputes `holder & shared`.

Metric used for this region: `regm.py` (lane scratch) aligns the whole function with win.py's tokens and counts
how many of region 2's 537 original slots fall in matching blocks (`frac`).

## Result (current main 319a7d10f): notes only

Since #2524 put admin_cto at exactly 27,400 B, any size change shifts every later window and costs 686 raw
matches. None of this lane's region-2 mechanisms keeps 27,400 B while lowering the 3,297 differing slots, so the
branch carries no source change. What it carries for a stitcher:

| set (on 319a7d10f) | bytes | ratio | slots_diff | region-2 frac | raw |
| --- | ---: | ---: | ---: | ---: | ---: |
| main | 27,400 | 0.36129 | 3,297 | 0.4618 | 1033 |
| `oldbump` only | 27,400 | 0.36159 | 3,305 | 0.4637 | 1033 |
| C = `tree` + `feematch` + `oldbump` + by-value validate keys (`region2-c.patch`) | 27,416 | 0.38904 | n/a | 0.5214 | 347 |
| Cp3 = C with tuple order `(skip, collect_old, sharing_update)` (`region2-cp3.patch`) | 27,424 | **0.39467** | n/a | 0.5028 | 347 |

The four region-2 mechanisms (`mutations.py`; `variants.py` holds every spelling tried):

1. `tree`: `sharing_update`, `collect_old`, the `shared && !holder` target override and a `skip` flag come from one
   `if shared { if holder {..} else {..} } else {..}` tree of per-arm constants, and the sweep is gated on `if !skip`.
   The original gates the sweep on a precomputed bool (`mov r7,0; ldxdw r1,[r10-0x8e0]; jne r1,0`); with `tree`
   ours emits the same three instructions on the same slot. Alone it lowers the ratio (register churn); it pays off
   together with `feematch`.
2. `feematch`: `match fee { None => {}, Some(f) => {..} }` for the 326-338 checks. The original tests the fee tag with
   `jeq tag,0` (None first); this also moves the 330 check into region 2 as in the original. It is the main ratio
   driver (+0.022 alone) but costs +160 B alone.
3. `oldbump`: sweep binds `old` (key copy) before `bump`; the original stores the bump byte after the key copy.
4. `vsigner`: `&[vaultseeds]` bound once (the original stores the `{ptr,3}` element at seeds time). -32..-80 B.

Size map of the sets on 5a057949 (27,400 B main): t 27,520; f 27,560; o 27,400; v 27,368; tf 27,512; tfv 27,432;
tfo+rref 27,408; tfv+rref 27,376; tfv+rref+oldbump 27,376 (0.38663); +rcpi 27,416. Byte quantum is 8, and no
semantically neutral knob tried (14 more: tuple orders, arm order, `if`-forms, 648/312/330 operand order, array
vs typed vsigner, inline bump, CPI field orders) moved C by exactly -16 B. CPI `system_program`-first reorders of
the wallet / sweep `Create` and `AdminCtoPool` literals change clone inlining (158 calls).

To use: compose `region2-cp3.patch` with another region's change that shrinks the function by 24 B without
touching these statements, or with the region-1 entry-order work (#2550 was +88 B on old main).

Scratch collision: this lane's scratchpad was shared with other admin_cto lanes (w9r2-admincto-asm-tail,
w10r1-admincto-stitch), whose `trial.sh` overwrote this lane's; tools were moved to the lane's cache directory.

## Earlier trials on 917ee615f (before #2524; PR #2515, closed after main moved)


| trial | mechanism | bytes | ratio | region-2 frac | result |
| --- | --- | ---: | ---: | ---: | --- |
| base | origin/main 917ee615f | 27,344 | 0.37637 | 0.4637 | |
| t1 | fee checks 326-338 as `require!` | 27,344 | 0.37637 | 0.4637 | byte-identical |
| t2 | sharing_update / collect_old / target override in one `if shared {..} else {..}` tree | 27,440 | 0.37599 | 0.4674 | size nearer (40), ratio lower |
| t3 | t2 + explicit `do_sweep` flag from the tree used as sweep gate | 27,632 | 0.30157 | 0.4544 | rejected |
| **t6** | tree with explicit holder arms: `if shared { if holder {(Some(None),false)} else {target=creator;(Some(new),false)} } else {(None, !hr && creator != default)}` | **27,368** | **0.37680** | 0.4674 | **kept** |
| t8 | t6 with the `!holder` arm first | 27,368 | 0.37680 | 0.4674 | byte-identical to t6 |
| t10 | t6 with tuple order swapped | 27,368 | 0.37680 | 0.4674 | same metrics |

| t11 | t12 + `let vsigner:&[&[&[u8]];1]=&[vaultseeds]` once (original stores the {ptr,3} element at seeds time) | 27,320 | 0.37744 | 0.4693 | size away (80 B) |
| **t12** | t6 + sweep `let old=..key(); let bump=[..];` (original stores the bump byte after the old-key copy) | **27,368** | **0.37710** | 0.4693 | **kept** |
| t13 | t12 + vaultseeds as a named array | 27,368 | 0.37710 | | byte-identical |
| t14 | t12 + sweep gate `matches!(sharing_update,Some(None))` | 20,280 | 0.14696 | | inliner flips, loss 0xbc108 |
| t15 | t12 + validate takes the precomputed `cashback` (original's 330 tests one flag) | 27,816 | 0.35642 | 0.4544 | rejected |
| t16 | t12 + `match fee {None=>{}, Some(f)=>{..}}` (original tests `jeq tag,0`) | 27,448 | 0.37474 | **0.5158** | region 2 aligns much better (local 0.395 -> 0.484, 330 moves into region 2), regions 4/5 lose; size away |
| t17 | `cashback=if holder{false}else{..}` | | | | byte-identical |
| t18 | t16 + cashback param | 27,808 | **0.37996** | 0.5102 | best ratio, size 408 away |
| t19 | `let Some(f)=fee else{return Ok(target)}` | 27,480 | 0.36135 | 0.4507 | rejected |
| t20, t23, t24 | 338 as `contains`, 330 / 312 operand order | | | | byte-identical or same metrics |
| t25 | 312 as two ifs | 27,360 | 0.34848 | | 157 calls |

| t26 | `let sweep_holder=shared&&holder` before validate as the sweep gate | 27,448 | 0.30290 | 0.4469 | rejected |
| t27 | t12 tree also yields `skip` (= !(shared&&holder)) as per-arm constants; gate `if !skip` | 27,440 | 0.36072 | 0.4637 | gate now has the original's form and slot (`mov r7,0; ldxdw r1,[r10-0x8e0]; jne r1,0`) |
| t28 | t27 + `match fee {None=>{}, Some(f)=>..}` | 27,448 | **0.38641** | 0.5214 | composes: ratio jumps |
| t29 | t27 + cashback param | 27,520 | 0.37453 | 0.4488 | rejected |
| **t30** | t28 + `let vsigner:&[&[&[u8]];1]=&[vaultseeds]` bound once | **27,416** | **0.38634** | 0.5196 | **kept**: 16 B from the original size |
| t31 | t28 with bump bound before the old key | 27,448 | 0.38491 | 0.5121 | rejected |

t30 (current branch head) is 16 B from the original size (main: 56 B), ratio 0.37637 -> 0.38634, 0 gains / 0 losses.

Earlier head t12 was 32 B from the original size (main: 56 B) and has a higher ratio, with 0 gains / 0 losses (1032 / 347).
For a stitcher: t16 (`match fee` with the `None` arm first) is the strongest region-2 alignment found so far
(region-2 slots in matching blocks 252 -> 277 of 537), at a whole-function cost in regions 4/5.
