# w14a46-cto-walletcsr: the extra callee-saved occupant across wallet() (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 6db95a764 (0.65458, 3,280 slots). Re-checked on main 0fbf8daa1 (0.65578): the occupancy map is identical
(r9 = %1731 <- %60 over [21296,33488)), and the key bounds stay below main: k1 0.56043, sg 0.49813, sg+start 4:1
0.64118 @27,344, w1 0.63429, cpm 0.65339, g1 0.65408, k1+w1+cpm 0.55389. Angle: w14a37-cto-collectsib (#3312) next idea 1, plus the w14a35-cto-walletr8
(#3320) queue. Ledger: approach `walletcsr`, keys `0x22a10-w14-6db95a7-walletcsr-*`.

**No source change is proposed.** The occupant is named and every removal is priced. None beats main. This PR adds the
per-register occupancy map, the correction below, the IR bounds, the source screens and five small tools.

## 1. The r9 occupant over the wallet is the sweep gate flag, not the sharing_update tag

`tools/csrmap.py` reads the debug-greedy log (`llc -debug-only=regalloc` on the rx.py post-opt module). For every final
vreg assigned to r6-r9 whose interval overlaps the wallet slot range, it prints the overlap, the vreg's split root and
the root's definition. Here the range is [21296, 33488), from `bb.72.bb33` (the wallet entry) to the end of the coin CPI.
Full output: `csrmap-6db95a7.txt`.

| reg | ours (main 6db95a7), by overlap | original, same region (orig 0x5b40-0x6b08) |
| --- | --- | --- |
| r6 | `do_collect` (%1581), accounts pointer split pieces (%0), one clone buffer | `do_collect` |
| r7 | Result payload class word 0 (%1652, 65 uses, function-wide), clone buffers `_130.i` / `_106.i`, the memcmp result | accounts pointer, reloaded per use from `[r10-0x8d8]` |
| r8 | Result payload class word 1 (%1651), `authority_info` buffer, accounts pointer split | **`do_coin`** |
| r9 | **%1731 <- %60 for all 11,456 slots**: `MOV_ri 0/1/0/0` at bb.58/59/60/64, one use, `JNE_ri %60, 0` in `bb.71.bb35` | memcmp result (`collection_native`), clone buffer `-0x450`, payload |

`%60` is the IR phi `%_540.sroa.0.0.off0 = phi i1 [false,%bb21],[false,%bb22],[false,%bb23],[true,%bb19]`: the `!skip` sweep
gate from the tuple at line 339 (`(!skip).then(||sweep(..))` at line 647). It is defined at the bb26 join and used only at
`bb35`, the post-wallet join. Because `bb35` follows the wallet in the CFG, the flag is live through every wallet block, and
greedy's region split gives it r9 over the whole wallet. The tag is `%59` (`MOV_ri 2` defs, `JNE_ri .., 2` at the event),
and it is spilled over the wallet.

**Correction to #3320 / #3251:** w14a35's `%60 "tag split"` is this same flag. Its own `mi_base.txt` on 06967d3 shows
`%60 = MOV_ri 0/1/0/0` and one `JNE_ri %60, 0` at bb35. The "tag" chain in #3320 section 1 is the sweep-gate chain.

Original vs ours at the post-wallet join:

| | original | ours |
| --- | --- | --- |
| bb26 join (flag def) | `mov r3,1` (skip polarity: 1 on the shared&&!holder and !shared paths), `stxdw [r10-0x8e0], r3` (spilled at its def) | `mov r9,0` in each pred (`!skip`), kept in r9 |
| bb35 join (flag use) | `0x1d38 ldxdw r1,[r10-0x8e0]; jne r1,0,+0x3e4` -> post-sweep (sweep falls through) | `0x1d30 jne r9,0,+1` -> sweep; `ja +0x3dd` -> post-sweep |

The original's gate is the skip polarity (`br skip, post, sweep`, as w13a49 found), and its flag is spilled from its
definition.

## 2. Removal bounds (post-opt IR edit + llc; `edits/ir/`)

`F`/`Fw` come from `tools/wf2.py`, the w14a35 `wf.py` with frame addresses also masked (`add64 rX,-0x..` after `mov rX,r10`).
F is whole-function frame-masked, register-kept. Fw is the matched tokens in orig [0x5c40,0x6b08) (468 tokens). Main:
F 0.74745, Fw 408. The alloca-based edits shift the frame, so read their plain ratio as a lower bound and F/Fw as the bound.

| oracle | removes from the wallet CSRs | bytes | ratio | F | Fw | what takes r9 over the wallet |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| main | | 27,400 | 0.65458 | 0.74745 | 408 | flag %60 |
| k1 | flag through an i8 slot (store at bb26, load at bb35) | 27,408 | 0.56133 | 0.69223 | 405 | `coin_present` raw (%715, `data_is_empty` r0) |
| sg | skip-polarity gate (phi 1/1/1/0, `br skip, bb89, bb84`; = source `if skip{Ok(0)}else{sweep(..)}?`) | 27,424 | 0.49828 | 0.56296 | 403 | `coin_present` + tag piece; flag spilled at def like the original; layout collapses (sweep token chunk after post-sweep) |
| sg reordered to main's chain order (`tools/reorder.py`) | sg's code under main's layout | 27,424 | 0.57703 | 0.73484 | 403 | |
| sg + `start` 4:1 | | 27,344 | 0.64238 | 0.72395 | 406 | flag again (layout restored, flag back in r9) |
| w1 | tag through a slot across wallet only | 27,360 | 0.6212 | 0.73152 | 390 | the `&a.current_creator` GEP (%72 = accounts+168; the original spills it to -0x910) |
| cpm | `coin_present` raw through a slot | 27,424 | 0.65219 | 0.74652 | 406 | flag |
| k1 + w1 + cpm | flag, tag and coin_present | 27,432 | 0.55479 | 0.68293 | 390 | **`do_coin`** (%1586); do_collect r8, accounts r7, clone buffers r6 |
| k1 + w1 + cpm + GEP remat | all four long-lived values | 27,464 | 0.55326 | 0.67534 | 369 | |
| r1 | GEP %186 rematerialised at each call | 27,400 | 0.65368 | 0.74176 | 392 | flag |
| g1 | coin gate on `do_coin` only | 27,368 | 0.65288 | 0.74640 | 404 | flag |

Whack-a-mole: each removal hands r9 to the next long-lived, low-weight value (flag -> coin_present / tag -> the
current_creator GEP). In the original all of them are spilled. Removing all four gives a rotation of the original's
assignment (do_coin r9 / do_collect r8 / clone r6, against r8 / r6 / r9), not the original. Every bound loses
0.01-0.07 F, mostly in the sweep (0x2800-0x3400, 0x4000) where the freed registers re-shuffle.

The flag's register is frequency-driven. `sgh` (`edits/ir/sgh.py`, `sgh-6db95a7.txt`) sweeps 24 head weights (start, bb1 and bb6 x {20:12, 12:20, 16:1, 1:16,
4:1, 1:4, 2:1, 1:2}) on top of sg:
- Only `start`/`bb1` 4:1 restores the layout (0.64238), and that puts the flag back in r9.
- 16:1 restores most of the layout (F 0.723) and keeps the flag spilled, but it breaks the wallet (Fw 332).
- Every other weight gives sg's bytes.

No weight gives both the original layout and the original flag spill.

`tools/wsweep.py` extends this to every conditional `br` of execute (146 branches x {20:12, 12:20, 16:1, 1:16} = 584 llc
runs on top of sg, `wsweep-sg-6db95a7.jsonl`). The best F is 0.73993 (0.58242 @27,424): the with_pubkeys `to_string`
branch `%336` at 12:20 or 1:16, the MBP divergence point found with `-debug-only=block-placement` (below). Main's F is
0.74745. No single weight on the skip-polarity gate reaches main's frame-masked match. The plain ratio stays near 0.58
because the spilled flag adds a spill slot and shifts the frame.

MBP detail (debug llc, `-debug-only=block-placement`). BPF conditional branches are unanalyzable, so under sg `bb35`
is pre-merged with `bb84` (the sweep falls through, as in the original). Later, at the with_pubkeys Err block
`to_string...exit.i`, `bb57.i` (the sweep Result join, pre-merged with `bb89`, the post-sweep) becomes a legal "CFG break"
successor. It is a "non-cold CFG conflict" on main. So the whole post-sweep chain is placed inside the sweep, and the
token/native chunk goes after it.

Note: on this main the rx oracle of an unmodified capture differs from the baseline build in 57 tokens, a one-spill
schedule swap at 0x2680 (`ldxdw r4,[r2+0x18]; stxdw [r10-0x950],r4` placement). The ratio is equal (0.65458) and the
slots are 3,279 against 3,280. Lanes that need `eq_main: true` on 6db95a7 should expect `false` from the unedited capture. On 0fbf8da the unedited capture
is `eq_main: true` again.

## 3. Source forms (raw-IR capture + rx oracle; `edits/src/`; line counts kept)

| key | form | bytes | ratio |
| --- | --- | ---: | ---: |
| s1 | `if do_coin{` (w14a35 queue g1/s1) | 27,400 | 0.65279 |
| n1 | `if coin_present&&do_coin{` | 27,400 | 0.65428 |
| n2 | `if do_coin&coin_present{` | 27,400 | = main |
| n3 | `let do_coin=if coin_present{!token_frozen(..)?}else{false};` | 27,400 | = main |
| g9 | `swept=if skip{Ok(0)}else{sweep(&ctx,&holder_key)}?;` (original skip polarity) | 27,424 | 0.49828 (= sg) |
| g3 | `swept=if skip{0}else{sweep(&ctx,&holder_key)?};` | 27,416 | 0.53249 |
| ta / tc | gate re-derived from the tag after wallet: `matches!(sharing_update,Some(None))` / `if let Some(None)=sharing_update` (tuple `skip` unused) | 9,056 | 0.12438 (sweep outlined) |
| td | `(sharing_update==Some(None))` gate | 27,376 | 0.37614 |
| tb / te | `(holder&&sharing_update.is_some())` / `(sharing_update.is_some()&&holder)` gate | 27,440 | 0.50861 |
| r1-r4 | `skip` carried through the `Ok::<_,Error>((..))?` re-wrap at line 339, in four positions | 27,400 | = main (fold) |
| x1-x4 (on 0fbf8da) | gate made implied by `collect_old` (the wallet path never sweeps): `if collect_old{0}else{..}`, `!skip&&!collect_old`, `!collect_old&&!skip`, `!(skip\|\|collect_old)` | 27,208-27,216 | 0.37367-0.37372 |

Ending the flag's life before the wallet in source either re-derives it from values that are also live, which costs
instructions and re-lays the sweep, or folds back to main's tokens. The faithful form (skip polarity) moves the flag to
the original's spill, but MBP then collapses the layout (the w13a49 / w14a11 whole-function near-tie, still present on
6db95a7).

## 4. Next ideas

1. The wallet RA cannot be reached by removing occupants, because the original spills all four long-lived values.
   The lever is the frequency picture. The original has the skip-polarity gate **and** the main-like layout **and** the
   flag spilled; none of the 24 head weights in ours gives all three. Look for an IR difference upstream of bb26 that
   changes block frequencies the way `start` 16:1 does, without the wallet damage 16:1 causes. Screen candidates with
   the `sgh` oracle for flag_r9=0 and F >= 0.747.
2. `tools/reorder.py` reorders a candidate's chains into a reference layout, so it prices "this RA under that layout".
   Use it to separate RA effects from MBP effects in any candidate that re-lays the function.

## Tools (`tools/`; experiment only; run next to the w14a35/w14a03 `rx.py`, `dll.sh`, `dis.sh`, `ra.sh` in the lane scratch dir)

- `csrmap.py <ra.log> <lo> <hi> [regs]`: callee-saved occupancy over a slot range, with each piece's split root and its def.
- `lineage.py <ra.log> <vreg>..`: split-parent chain of a vreg and its root's defs and uses in the pre-RA MIR.
- `wf2.py <m.ll|dis>`: frame-masked (including frame-address `add64`), register-kept match F and wallet Fw.
- `chunk.py <a> <b> [chunk]`: per-orig-chunk wf2 matched-token deltas. `hunk.py <a.dis> <b.dis>`: masked diff hunks.
- `reorder.py <cand.s> <ref.s> <out.s>`: placement-only oracle that sorts cand's fallthrough chains into ref's layout.
  Blocks are keyed by (IR block name, occurrence). Score the result with w14a36 `asmscore.py`.
