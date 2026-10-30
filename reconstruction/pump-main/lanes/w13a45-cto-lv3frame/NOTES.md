# w13a45-cto-lv3frame: why the lv3 family trails main (frame cascade, holder-register shift)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
This lane continues w13a31-cto-lv3relayout (#3073) and w13a18-cto-feephi (#2979). Nothing here is landable: it is
an IR-oracle bound with the blockers named.

All numbers come from the raw-IR opt oracle (w13a01 `rx.py` via `capvar.sh` / `runq.sh`). Its tokens equal the
baseline build on both mains (`eq_main: true`). fm is the frame-masked ratio and sk the skeleton ratio (frame and
registers masked), both from w13a18 `absratio.py`. "Frame edits" are `frsweep.py` specs (w13a31) on the post-opt
module. They are oracles only: none of them is a source form.

## 1. lv3 + s_map ported to main 52c0b087c (0.62103)

| trial | change | bytes | ratio | fm | sk | errseq |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| main 52c0b08 | | 27,400 | 0.62103 | 0.71210 | 0.85440 | 298 289 296 326 306 312 307 330 338 410 334 .. |
| lv3 | w13a18 out-param form | 27,400 | 0.26064 | 0.59017 | 0.73367 | 289 298 296 326 306 312 307 330 338 334 410 .. |
| **s_map** | lv3 + token arm `.map(\|()\|amount)` (w13a31) | 27,384 | 0.31705 | 0.69044 | **0.85766** | = lv3 |
| okw | s_map without the `Ok::<_,Error>((target,..))?` wrapper | 27,384 | 0.30716 | 0.69014 | | = lv3 |
| resout | `out:&mut Result<Pubkey>` to get main's 7/9 B Result pieces | 9,064 | 0.12884 | | | validate no longer inlined |
| L9m / okw_L9 | + holder_key PDA before `shared` (L9) | 27,400 | 0.25075 / 0.23936 | 0.53385 | | = lv3; sweep chunk relayout |
| tgtfirst / skinline | `target` declared before `sk`, or `sk` inlined as the arg | 27,336 | 0.33173 | 0.69196 | 0.85573 | = lv3 |
| in296 | 296 check moved into the `hb` arm (IN296) | 27,312 | 0.34029 | 0.70338 | 0.85881 | reverts to main's (threading lost) |
| el296 | EL296 nesting | 27,384 | 0.31705 | | | byte-identical to s_map |
| vA | arm split on validate's own `holder` instead of `hb` | 27,240 | 0.34135 | 0.70042 | 0.85667 | reverts to main's |
| vB | no `shared` param, override back in the tree | 27,256 | 0.33313 | 0.66717 | 0.85761 | = lv3 (shared is not needed for the errseq) |
| h296m/l, h296u/s | line 296 spelled `matches!` / `if let Some(true)` / `unwrap_or(false)` / `is_some_and` | 26,568-26,960 | 0.235-0.286 | 0.555-0.658 | 0.71-0.72 | large relayouts |
| nh, nh2-nh4 | negated `nh=hopt!=Some(true)` for line 296/314 | 27,368 / 27,384 | 0.33064 / 0.31705 | 0.69484 / 0.69044 | | nh: 306 after 296 |

`bficall.py` (w13a05) on the raw IR gives validate 1.0, wallet 0.04688 and sweep 0.03516 of entry for both main and
lv3+s_map, so both stay inlined (154+3 calls).

## 2. Frame: a StackColoring cascade started by the 32 B out-param

Stack-coloring groups come from `tools/frsc.sh` (debug llc `-debug-only=stack-coloring`, w13a17 `scg.py`). Frame
deltas come from w13a31 `fdelta.py`. In main the 0x10-0x470 band is exact. In s_map it sits at +0x10, and only 157 of
1,237 aligned frame refs are exact. The cascade:

1. lv3's `target` (out-param, `[32 x i8]`, only whole memcpys, so SROA cannot split it) has a higher MIR local
   index than `sk`. It therefore comes earlier in the alloca list and wins the 32 B tie for the `authority_info.i`
   group. (In main this group hosts `sk`.)
2. `sk` falls to `_112.i`. Because `sk` is live through validate, `_112.i` can no longer take validate's 307/312
   `to_string` bufs. (In lv3 these are inlined at execute level, as `buf.i277`/`buf.i269`.)
3. Those bufs open a new 24 B group, `buf.i277`, at the frame top. That puts +0x10 on every slot from orig 0x10 to 0x470.
4. `_11.i275` (the 0 B `unwrap_failed` arg) merges into `event_signers.i`. In main, `target.i.sroa.0` occupies that
   group, so main's `_11` stays alone at the frame top.
5. `_116.i` (1 B) loses its host `target.sroa.0` and becomes its own slot at 0x461 (+8 for the band below it).
6. `_27.sroa.5` (32 B entry copy of `new`'s payload) stays unmerged above `hk` (+0x20). In main it is forwarded to
   `new` directly, but in lv3 the sharing payload copy reads from it.

Frame-only IR bound on s_map (fm stays 0.69044 throughout):

| spec | ratio |
| --- | ---: |
| none | 0.31705 |
| t1 `mv:target:END,mv:_27.sroa.5:END` | 0.35031 |
| t2 t1 + `nolt:target` | 0.35781 |
| t3 t2 + `nolt:_11.i275` (top band exact) | 0.43512 |
| **t5** t3 + `mv:_116.i:hk` | **0.51483** |
| greedy on t5 (`frgreedy.py`, top-50 single items) | 0.51513 (`mv:holder_key:END`) |

A single-item sweep over all 141 allocas (415 runs) peaks at 0.34342. tgtfirst/skinline reproduce t1 in source:
`sk` gets its group back, but `target` then lands in `_112.i` and still blocks the bufs.

Since fm is fixed, frame edits alone cannot reach main. At main's plain/fm efficiency (0.872), a frame-perfect lv3+s_map
would land near 0.60.

## 3. Registers: execute's `holder` read in validate shifts the tag web from r7 to r6

The tag==2 tests on the Result tags use r7 at 21 of 26 sites in the original and at 18 of 25 sites in main. In
lv3+s_map those same 18 sites use r6, and none uses r7. Every region where lv3 trails main on fm outside validate
(orig 0x2e00-0x3300, 0x5e00-0x6900) is this shift. `tools/ralong.py` on the debug-llc regalloc logs shows the whole
pair moving down one register: tag web r7 -> r6, partner web r8 -> r7. Main's long split product of the accounts
pointer (r6) has no counterpart in lv3.

Cause (IR oracle `tools/hbremat.py`): in lv3, validate's arm split `*out=if hb{..}` reads execute's `holder` i1, the
same SSA value the tree and the curve store read. That value is needed for the threading. Main's validate tests its
own `icmp eq` copy instead. Giving only the two arm-split branches their own `trunc i8 %holder to i1` after opt
(`hbremat.py m.ll out.ll br`):

| oracle (post-opt edit on s_map) | bytes | ratio | fm | sk | tag regs |
| --- | ---: | ---: | ---: | ---: | --- |
| s_map | 27,384 | 0.31705 | 0.69044 | 0.85766 | 18 r6 |
| remat line-296 `and` use only | 27,240 | 0.33383 | 0.69832 | 0.86238 | 19 r7 |
| **remat the 2 arm-split branches** | 27,224 | 0.33123 | **0.71025** | **0.87556** | 19 r7 |
| remat all 3 | 27,208 | 0.33133 | 0.71046 | 0.87583 | 19 r7 |
| remat all 3 + t5 frame edits | 27,208 | **0.52886** | 0.71046 | 0.87583 | 19 r7 |
| remat the late uses (tree / curve store) | 27,304-27,328 | 0.317 | 0.691-0.692 | | 18 r6 |

With the register fix, lv3+s_map's skeleton is 0.876 against main's 0.854, and its fm is 0.710 against 0.712. The
threading structure is the better one. What remains is the frame (section 2), plus a chunk-order swap at orig
0x2900-0x2a00 / 0x3200-0x3300 (two AccountInfo-clone runs, -44/-35 frame-masked matches; `bincov.py`).

**Source blocker.** Opt needs the arm split and the tree to read one SSA holder value: that is what lets
JumpThreading/LVI do the three-way fee-None threading (w13a18). llc needs the arm split's value as a separate, short
vreg. Every source spelling that separates them before opt was tried: vA, h296*, nh*. Each one either loses the
threading (errseq reverts to main's) or relays out the function. Rematerialization would have to happen after
JumpThreading, and no source form found here does that.

## 4. Main moved to 6ff770f (0.62403) during the lane

On 6ff770f (#3155: entry copy of `new` after the CtoState stores; tree tuple reordered), the same lv3+s_map port
(`trials/lv3n.py`, `trials/s_mapn.py`) relays out again: 27,312 B, 0.31478, fm 0.63946, sk 0.82461. 410 moves to
after 326 (`289 298 296 326 410 306 ..`). The arm-split remat no longer helps there either (0.29042 / fm 0.6321). So
lv3 again sits near an MBP threshold, as w13a31 found for L9.

## 5. Wave-14 continuation: main 53abf28 (0.62672, after #3168 stitch9)

The raw-IR oracle reproduces main 53abf28 exactly (`eq_main: true`; 0.62672, fm 0.72588, sk 0.85410). The same
`trials/lv3n.py` + `trials/s_mapn.py` edits still apply cleanly:

| oracle | bytes | ratio | fm | sk | errseq |
| --- | ---: | ---: | ---: | ---: | --- |
| main 53abf28 | 27,400 | 0.62672 | 0.72588 | 0.85410 | 298 289 296 326 306 312 307 330 338 410 334 .. |
| lv3+s_map port | 27,328 | 0.31588 | 0.64017 | 0.82436 | 289 298 296 326 410 306 312 307 330 338 334 .. |
| + holder arm-split remat (`hbremat.py br`) | 27,264 | 0.32227 | 0.57156 | 0.82565 | |

The 410-after-326 relayout seen on 6ff770f persists. The lv3 skeleton (0.824) is now below main's (0.854): the
skeleton lead it had on 52c0b08 (0.876 with the remat oracle) did not survive #3155/#3168. On 52c0b08 even all three
IR fixes together gave 0.529, below main. **The lv3 threading family is a dead end on current main.** Ledger:
`0x22a10-w13-53abf28-lv3frame-smapn-port-v1`. New tool: `tools/llcm.py <m.ll> <name>` (llc a post-opt module and
score it with rx.py's metric).

## Conclusion

On 52c0b08 the lv3 threading family has the best skeleton seen so far (0.876 with the holder remat oracle). It has
three blockers, each named with its IR proof:
1. **holder vreg** (section 3, worth +0.02 fm). Source-blocked: one SSA is needed for JumpThreading, two vregs for RA.
2. **frame cascade** from the 32 B out-param `target` and the `_27.sroa.5` entry copy (section 2). Five IR edits take
   plain from 0.317 to 0.515 (0.529 with item 1). The source would need `target` to leave validate in main's 7/9 B
   Result pieces while the fee join stays a single memcpy. `resout` (a `Result` out-param) stops validate from inlining.
3. **306 placement** (orig `289 298 306 296`), unchanged from w13a31.

Even all three IR fixes together leave lv3+s_map at 0.529, below main's 0.621/0.624. That is the bound this lane sets.

## Tools (`tools/`; experiment only)

- `hbremat.py <m.ll> <out.ll> [and|br|all]`: holder-vreg remat oracle on post-opt IR.
- `frsc.sh <m.ll> <spec> <tag>`: frsweep spec + llc + StackColoring group table (debug llc).
- `bincov.py A.dis B.dis [bin]`: per-orig-bin frame-masked match counts of two candidates.
- `sbs.py <m.dis> lo hi`: side-by-side frame-masked opcode diff for an orig range.
- `ralong.py <regalloc.log>`: longest vregs with final physreg (from `llc -debug-only=regalloc`).
- `fnraw.py <raw.ll> <regex>`: grep inside execute in a raw module.
- `capvar.sh`, `runq.sh`, `frgreedy.py`: w13a01/w13a18/w13a31 tools with this lane's paths. capvar accepts callable
  EDITS, runq keeps the raw IR, and frgreedy takes a `FRBASE` start spec and `FRJ` threads.
- `trials/*.py`: source EDITS (main 52c0b08; `lv3n`/`s_mapn` for 6ff770f).

Ledger keys: `0x22a10-w13-52c0b08-lv3frame-*`.
