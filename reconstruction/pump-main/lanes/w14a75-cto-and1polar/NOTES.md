# w14a75-cto-and1polar: and-1 branch polarity bound on main 0d04cf4 (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a10-cto-and1outline (#3224) and w14a39-cto-and1pscan-2 (#3352). Base: main 0d04cf4 (#3393), admin_cto
0.66507 / 3,228 slots, M 2,220 (M = scorer-exact matched original instructions, `tools/jm.py` of w14a39).
Ledger keys: `0x22a10-w14-0d04cf4-and1polar-*-v1`.

**Result: notes only, no landing.** The and-1 basin is alive again after #3386: with w14a39's RVJ (per-arm native join)
it reproduces the original error-site order through 556 and is 19 M short of main at -48 B. The gap is one
fallthrough: the 296 holder_enabled test. On BPF the IR block order fixes it, and no source spelling found so far moves
that IR block.

## Oracles

- Raw-IR capture + SDK `opt -O3` + `llc` (w14a66 `capvar.sh`/`rx.py`/`px.py`, repointed): `eq_main: true` on 0d04cf4.
- Placement-only chain scan + greedy (w14a71 `blkscan.py --chains`, `greedy.py`; greedy patched so a size change does not
  crash the sort).
- New `tools/irorder.py`: a post-opt IR block-ORDER oracle. It moves a named IR block before another one, then runs `px.py`.
- New `tools/fscan.py`: an IR fallthrough-flip scan. For every conditional `br` block, it moves the non-fallthrough
  successor right after the block.
- New `tools/side.py` (orig vs candidate side by side, jump-masked alignment), `tools/jd2.py` (mismatched jumps with
  orig/cand src and dst), `tools/shift2.py` (size-shift profile per orig region).
- Genes: `gen/genes.py` (w14a39 library + this lane's). `B` = p3u + tu8.

## 1. The and-1 basin on 0d04cf4 (the #3386 fee-Some edge block is in place)

| variant | bytes | ratio | M | jM | fm | sk | error-site order |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| original | 27,400 | | | | | | 289 298 306 296 326 312 307 330 338 334 410 719 648 660 284 556 |
| main 0d04cf4 | 27,400 | 0.66507 | 2,220 | 2,249 | 0.71061 | 0.79509 | **298 289** 296 326 306 312 ... (rest = orig) |
| tu8 alone | 27,416 | 0.65618 | | | 0.70979 | 0.79515 | 298 289 296 306 326 ... |
| p3u alone | 27,368 | 0.58064 | | | 0.67446 | 0.80066 | 289 298 296 306 326 ... |
| p3u+tu8 | 27,344 | 0.65077 | 2,170 | 2,291 | 0.71795 | 0.80342 | = original |
| **p3u+tu8+RVJ** (= q2u/q4u) | 27,352 | **0.65997** | **2,201** | **2,317** | **0.72864** | **0.81919** | **= original through 556** |
| p3n+tu8+RVJ | 27,344 | 0.65977 | | | 0.72845 | 0.81721 | = original |
| p2+tu8+RVJ / q5u+tu8+RVJ | 27,328 / 27,336 | 0.65397 / 0.65387 | | | | | = original |

The basin has come back: on 6e011ea it was -92 M (w14a39), and now it is -19 M. Per 0x200 chunk against main it gains +14
at orig 0x600-0xc00. It loses -9 at 0xe00-0x1200 (the 296 region), -8 at 0x4a00 (curve-store register shape) and about
-1 in each of many later chunks. Per region (0x1c00 steps): validate +7, the rest -26. RVJ's native-join spellings J3,
J4 and J5 are token-identical to RVJ. J2 and J6 (`?;Ok(amount)`) collapse.

Fill bound (`fillg.py`, greedy junk slots): +48 B of pure fill gives at most **+2 M**.

## 2. Where the 19 M are: one fallthrough at the 296 test

The placement-only chain scan of the basin (`cs_basin.jsonl`, 116 chains) has one large lever:
**`bb13.i` (the `holder_enabled` 296 test plus the 296 prelude) moved before the 296 tail: +0.0057**. Greedy reaches
0.66687 @ 27,352 in 4 moves. That is above main's 0.66507, at -48 B.

Mechanism, from the original's validate:

- Original 0x8f8: `jeq r1,0,+0xc8` jumps to the 296 prelude at 0xf40, which sits after the 306 tail. The block falls through
  to 0x900, the holder-arm 298 new-tag test. The 289-pass edge (0x640 `jne r8,0,+0x57`) also lands on 0x900.
- Ours, in the basin: `bb13.i: mov r1,r8; jne r1,0,bb19.i`. It falls through into the 296 prelude `bb14.i`.
- BPF `analyzeBranch` cannot analyze conditional branches. MachineBlockPlacement therefore keeps ISel's fallthrough, and
  ISel falls through to the next IR block whenever that block is a successor. **The post-opt IR block order fixes the
  polarity of every conditional-branch block.** Post-opt, `bb14.i` follows `bb13.i` in the IR.
- Branch weights cannot fix it. `brw.py` on bb5.i, bb6.i, bb11.i and bb13.i at 1:2000 .. 2000:1 reruns register
  allocation every time (0.459 .. 0.656), and `bb14.i` stays after `bb13.i`. The post-opt `and 1` / `icmp ne` rewrites of
  the holder_reward/holder_enabled tests are neutral or lose.

| oracle | bytes | ratio | M | jM |
| --- | ---: | ---: | ---: | ---: |
| basin p3u+tu8+RVJ | 27,352 | 0.65997 | 2,201 | 2,317 |
| asm: invert bb13.i (`jeq r1,0,<296 prelude>`) and move only the prelude chain before its tail | 27,352 | **0.66687** | **2,224** | 2,339 |
| asm: same, plus placement greedy | 27,352 | 0.66867 | | |
| **IR order: `bb19.i` moved right after `bb13.i`** (`irorder.py ... bb19.i bb14.i`) | 27,344 | **0.66577** | **2,220** | **2,337** |
| IR order + placement greedy | 27,344 | 0.66757 | | |
| IR order + `fscan.py` (78 conditional blocks, one flip each) | | no further gain | | |
| main + the same IR move | 27,400 | 0.65129 | | |

The IR move gives `bb13.i: jeq r1,0,LBB<296 prelude>` with a fallthrough into `bb19.i`, the original's shape, and ties
main's M at -56 B. The asm inversion is +4 M over main at -48 B. With the +2 M fill bound, the polarity basin's ceiling
at 27,400 B is about M 2,222-2,226 (ratio about 0.666-0.667) **if** a source spelling put `bb19.i` after `bb13.i`.

## 3. Why the source does not reach that IR order (rejected spellings, all on B+RVJ)

rustc appends LLVM blocks when they are first referenced. In validate's pre-opt IR the order is bb11, bb6, **bb18**
(join, `br holder,bb19,bb20`), bb12, bb13, **bb14**, bb71, bb7, bb92, bb20, **bb19**. bb14, the 296 error, is appended as
soon as bb13 is codegened. bb19 is appended only when the bb18 join is codegened, after all of its predecessors.
JumpThreading then removes bb18 and leaves `bb19.i` at bb19's place.

| genes | bytes | ratio | note |
| --- | ---: | ---: | --- |
| s1/s3 (`!(hr\|\|he)`, `he` before `hr`), p1/p2/p5 (`if !(c){}else{err}`, `!h\|\|hr\|\|he`, `else{}`) | 27,352 | 0.65997 | token-identical |
| s2 (`!hr&&h&&!he`) | 27,344 | 0.64717 | |
| s4/s9 (`!he&&!hr&&h`, `!hr&&!he&&h`) | 27,336 | 0.5021 | |
| s5/s6/p4 (nested `if`, `he==false`, `(c)==false`) | 26,832-26,856 | 0.524-0.530 | 312 moves before 306 |
| s8 (`&` non-short-circuit) | 26,528 | 0.45205 | |
| t1/t2/t4/m2/m4 (`match holder{true=>..}`, `holder==true`, `if let true`, `match holder as u8{1=>..}`, `match hopt&1!=0`) | 27,352 | 0.65997 | token-identical |
| m1/m3 (`match hopt&1{1=>..}`, `match hopt{1=>..}`) | 26,680-26,840 | 0.498 | |
| g1-g4 (298 test hoisted before `let target`) | 27,344 | 0.65917 | bb19.i now precedes the non-holder arm, still after bb14.i/bb7.i (M 2,198) |
| i1/i2/i4 (296 inside the holder arm) | 26,856 | 0.53797 | the known to_string-outline collapse (-544 B) |
| C1/C2/C3 (validate returns `(Pubkey,bool)` cashback) | 27,192 | 0.33774 | |
| sw (holder store before cashback), cbif (`if holder{false}else{st.cashback}` in execute) | 27,352 | 0.65997 | token-identical |

## 4. Size repay on the basin (`sizeknobs-cto.json`, every applicable knob, B+RVJ base)

All 46 applicable knobs were screened (`rk.jsonl`). None reaches main. The best is `ev_hr_curve` (event `is_holder_reward`
read from the curve) at 0.66057 @ 27,352 (M 2,203, +2, size-neutral). Every size-adding knob loses (`w_ev_creator_first`
+88 B 0.6526, `ev_cb_local` +16 B 0.65947, `ev_mint_key` +16 B 0.65198, `ev_newfee_unwrap` +24 B 0.65278, `p_ev_ts_last` /
`w_create_rev` +256 B 0.50). The full list is in the ledger.

## Polarity bound (main 0d04cf4)

- Source-reachable now: the and-1 basin (p3u+tu8+RVJ) is 0.65997 @ 27,352, M 2,201, **19 M below main**. With the +2 fill
  bound and the best knob (+2), it is still about 15 M short at 27,400 B. **Not landable.**
- If the 296 test's fallthrough could be reached (bb19.i right after bb13.i): M 2,220-2,224 at -48/-56 B, about +2..+6 over
  main after fill. That is a ceiling of about +0.001..+0.002 ratio. The chainscan2 E298/E289 jump-masked +0.016..+0.021
  is real structure (jM +88), but at fixed size it is worth only a few M.
- The lever that remains is an IR-order one: get `bb19.i` (the holder-arm 298 test) appended before `bb14.i` (the 296
  error). Neither weights nor condition spellings reach it. Moving 296 into the holder arm does, but costs the
  to_string outline (-544 B).

## Next ideas

- A source structure where the 296 error block is created after the 298 test block, for example the 296 error reached
  through a shared error edge that is codegened late, without the in296 outline cost.
- The in296 form (i1) reproduces the original's block nesting. A lane with the to_string outline repay (w13 tostring296)
  could combine it with p3u+tu8+RVJ.
- Under zsh, `$L` is not word-split: use `${=L}` or `$(cat file)` when passing name lists to `batch.sh`.
