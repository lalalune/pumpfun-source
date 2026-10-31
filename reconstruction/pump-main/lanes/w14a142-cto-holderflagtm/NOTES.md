# w14a142-cto-holderflagtm: the per-arm holder flag's tail-merge break, its RA cause and its restored-layout price (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Bases: main ebe5387 (0.67316, 3,123 slots, M 2,247), then
main e88f9d5 (#3621, 0.67346, 3,124 slots, M 2,248). Continues w14a132-cto-holderslot950 (#3604) and w14a121-cto-delwin
(#3524); this lane carries out the first next idea of each. Ledger: approach `holderflagtm`, keys
`0x22a10-w14-{ebe5387,e88f9d5}-holderflagtm-*`.

**Result: notes only, no source change.** The tail pair is named, and so is its RA cause. Restoring main's layout under the
per-arm flag gives **M 2,047 against main's 2,248**, so the bound is below main. As the angle requires, step 3 (source tuple
plus joint re-tune) was not taken past a pricing screen. The source tuple form hits the same layout break and also shifts
the frame by 8 B.

## 1. Which tail merge changes (debug llc, `-debug-only=branch-folder`, MIR dumps)

The variant is w14a132's `hphi`+`hcs`: `%hph` is a phi of constants at validate's exits (bb54.i/bb75), consumed at the
curve `+0xa5` store. On ebe5387 it scores M 1,726, 0.5163 at 27,480 B.

- Before branch folding, the MBB numbering of main and the variant is identical (361 blocks), so the `TryTailMergeBlocks`
  logs can be compared directly.
- The pair is in the predecessors of **`bb56.i`**, the post-sweep `Result` join (`JNE_ri $r7, 2`; it is bb.268 before
  branch folding). Its 6 direct predecessors are bb128 to_string.exit.i, bb60.i116, bb62.i119, bb16.i120, bb82.i152 and
  bb52.i127. bb52.i127 is fed by 7 more: bb93.i, bb95.i128, bb39.i130, bb106.i, bb108.i, bb84.i138 and bb88.i.
  - In main, the live-ins are `$r3, $r7` only. The predecessors end in plain `r3`/`r7` loads, and bb56.i stays one 12-predecessor block.
  - In the variant, the live-ins are `$r3, $r5, $r7`. **`r5` is the accounts pointer** (`%0 = LDD ctx+8`; greedy piece
    `%1689`, R5, 36 blocks, carried over bb56.i → bb88 → bb37). Nine predecessors set it with `$r5 = LDD [r10-2264]`, and
    three (bb16.i120, bb82.i152, bb93.i) with `$r5 = COPY killed $r6`.
  - The first divergent merge is in the first BranchFolder pass, on the merge set `%bb.128, %bb.132, %bb.242, %bb.243,
    %bb.239, %bb.257 with successor %bb.268`:
    - Main has `Common tail length of %bb.242 and %bb.132 is 1` (`$r3 = LDD [r10-712]`) and merges nothing.
    - The variant has `… is 2` (the extra `$r5 = LDD [r10-2264]`), and `Using common tail in %bb.132 for %bb.242` follows.
    - The `bb52.i127` group also gains 1-instruction common tails, the r5 reloads, which main lacks.
  - After branch folding (pre-placement MIR), bb56.i is two blocks:
    - a reload block, `$r5 = LDD [r10-2264]`, with 5 predecessors;
    - the `jne r7,2` block, with 6 predecessors, three of which deliver r5 by `COPY r6`.
  - The to_string.exit.i error predecessor (bb.258) falls into the new 5-predecessor block. In main, bb56.i has 12
    predecessors, so placement does not let bb.258 fall into it.
  - MachineBlockPlacement then puts **chunk B** (bb56.i, bb88, bb35, …, bb37 curve store; 88 blocks) at 0x2460, in front of
    **chunk A** (bb9.i114 …; 118 blocks, main 0x2460–0x3bd0, ~6 KB). This is the 6 KB move w14a132 saw.
- Under `-enable-tail-merge=false` this split does not occur, which is why the two builds had equal layouts there.

## 2. Restored-layout price (MIR oracle)

`tools/restore.sh`: the variant stops before branch-folder (`-stop-before`), the three `COPY r6` defs become the `[r10-2264]`
reload, and llc resumes with `-start-before=branch-folder`. With no edit, the round trip is `cmp`-identical to llc.

| variant | base | M | ratio | bytes | layout vs main |
| --- | --- | ---: | ---: | ---: | --- |
| main | ebe5387 / e88f9d5 | 2,247 / 2,248 | 0.67316 / 0.67346 | 27,400 | = |
| hphi+hcs (default llc) | ebe5387 / e88f9d5 | 1,726 / 1,728 | 0.5163 / 0.5169 | 27,480 | chunk A/B swapped |
| **+ restore 3 preds** | ebe5387 / e88f9d5 | **2,045 / 2,047** | 0.61218 / 0.61278 | 27,440 | **equal** |
| + restore 2 preds (bb16.i120, bb82.i152) | ebe5387 | 1,730 | 0.51765 | 27,464 | swapped |

- The −201 M at the restored layout sits in the sweep body: orig bins 0x2800 −27, 0x2c00 −32, 0x3000 −40, 0x3400 −80,
  0x3800 −25. It is not a placement loss. The instruction diff against main starts at the entry: `mov64 r9,r5` becomes
  `mov64 r8,r5`, and the accounts pointer is spilled to `[r10-2264]` at entry instead of staying in r8. The greedy queue
  already diverges at dequeue 4, because the 4 `MOV_ri` phi defs change slot-index distances, hence interval sizes and
  priorities. The recolouring is therefore global.
- Role swap (w14a121, `sb.py`): the original has 3 store-back pairs, all on the holder `[0x950]`. Main has 4, on the
  `sharing_update` tag (`[r10-2272]`). The variant has **0**. Its tag `%61` is spilled whole (`S`, as the original's tag
  `[0x8f8]` is), not region-split into main's 9 pieces for r9. Its holder `%50` is split into `%1728`, spilled, and `%1729`,
  R2. The flag therefore takes the tag's spill role, but not its region split, and the sweep colouring that main's r9 tag
  split carried is lost.
- RAPRIO llc (w14a84 patch) does not restore it. Forcing the holder to a spill, the accounts piece to a spill or to r6, or
  moving the holder's or the tag's queue priority gives M 1,583–1,727 with 0 store-backs.

## 3. Source pricing (raw-IR capture + rx opt/llc, about 8 s each)

| variant | M | ratio | bytes | notes |
| --- | ---: | ---: | ---: | --- |
| `curve.is_holder_reward=_holder` (t_v_h1) on e88f9d5 | 2,205 | 0.66038 | 27,416 | Layout equal to main. −17 at orig 0x4800: `_holder` is re-derived from the spilled `!holder` (`and 255; mov 1; jne; mov 0`), where the original reads `[0x950]` directly |
| tv1: `validate -> Result<(Pubkey,bool)>`, `(*holder_key,true)` / `(t,false)` per arm, tuple → curve store | 1,038 | 0.3105 | 27,480 | same bb56.i split (COPY r6 in bb82.i, bb16.i, bb93.i) **and** frame −8 (entry spill −1704 → −1696) |
| tv1 + MIR restore of the join | 1,314 | 0.39335 | 27,440 | the frame shift remains |
| tv3 / tv4 / tv6: return type change only (flag unused or dead; `u8` instead of `bool`) | 1,260 | 0.37747 | 27,400 | `Result<(Pubkey,_)>` alone shifts the frame by 8 |
| per-arm cashback phi (original `[0x958]`), alone / with the holder phi (IR) | 1,872 / 1,609 | | 27,136 / 27,424 | |
| pool-CPI phi / i8 alloca (w14a132 hpa / halpa) on e88f9d5 | 1,855 / 2,114 | | 27,448 / 27,472 | another move: the post-sweep error group bb5.i/bb3.i/bb2.i (main 0x54e0, 8 blocks) is placed at 0x3bf8 |

## 3b. Keeping the holder arg live, and the frame-masked value

The variant that keeps the layout without the MIR restore is `e1`. It is the per-arm phi at the curve store, with the event's
`is_holder_reward` from `and %0,1`, so `%0` stays live past the store. With `%0` live, greedy no longer carries the accounts
pointer across bb56.i (no `COPY r6` predecessors), and default llc gives main's block layout. Validate (0x0–0x2400) is
almost byte-equal to main, but the plain score is still M 1,993.

`tools/fm.py` compares decoded instructions (call, lddw and jump immediates masked) against the original:

| build | bytes | M plain | M, frame offsets masked | M, frame + registers masked |
| --- | ---: | ---: | ---: | ---: |
| main e88f9d5 | 27,400 | 2,274 | 2,510 | 2,787 |
| e1 (phi + `%0` kept live) | 27,424 | 2,018 | 2,508 | 2,790 |
| hc2A (phi, MIR-restored join) | 27,440 | 2,097 | 2,376 | 2,780 |
| h1 (`_holder`) | 27,416 | 2,235 | 2,490 | 2,784 |
| e0 (event from `%0` only) | 27,408 | 2,274 | 2,508 | 2,786 |
| tv1 (source tuple) / restored | 27,480 / 27,440 | 1,146 / 1,438 | 1,628 / 2,205 | 1,973 / 2,599 |

- e1's whole loss is spill-slot numbering. Its holder gets the spill slot `-2304`, and every spill slot created after it
  moves by 8. One example: main's clone run `-2496/-2504/…` matches the original's, and in e1 it becomes `-2504/-2512/…`.
- Main uses the original's holder slot `[r10-2384]` (`0x950`) for a different value, `stxdw [r10-2384], r5` in the sweep
  clone run at 0x2710.
- **With the frame masked, the per-arm flag ties main (−2 / +3) at +24 B.** So even with a perfect frame it carries no
  code-shape value. The original's flag only pays if the spill-slot assignment follows the original, which is a frame
  problem, not a holder problem.

## 4. Reading for other lanes

- Many variants show a ~6 KB "chunk A/B swap" around 0x2460/0x3bd0, or lose 300–500 M with the curve store moving up. Those
  variants should check `tools/jp.py` on their `-stop-before=branch-folder` MIR first. If bb56.i has an extra register
  live-in, set by some predecessors through `COPY` and by others through a reload, the move is this tail merge.
  `tools/restore.sh` then prices the variant at main's layout.
- The bb56.i split follows from greedy carrying the accounts pointer across the join. That happens whenever a variant frees
  a callee-saved register in the post-sweep region, for example by dropping main's `%0` holder piece over the curve-store
  block.
- Changing validate's return type to a tuple shifts the frame by 8 B, so any `(target, flag)` form needs a frame
  compensator before it can be priced.

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `l.sh`: the debug or RAPRIO llc with fastbuild flags.
- `sb.sh` / `rt.sh`: stop before or start before a pass (`STOP=`, default `branch-folder`) as MIR. The round trip is exact.
- `mired.py`: edits one line inside the listed MIR blocks.
- `restore.sh`: the join-restore oracle.
- `jp.py`: bb56.i predecessors with their `r5` defs and live-ins.
- `lay.py` / `laydiff.py`: block order and approximate offsets from `-print-after=block-placement`, aligned by normalized
  IR block name.
- `bins.py`: per-orig-bin matched tokens for two candidates.
- `var.sh`: post-opt IR edits on main's capture, with a layout diff.
- `fnx.py`: extracts the function from an object file.
- `fm.py`: plain, frame-masked and frame+register-masked M; `idiff.py`: instruction diff between two builds; `scr.sh`: IR screen with join check.
- `pe.sh`, `wr.py`, `rx.py`, `capvar.sh` and `capraw.py` come from w14a132 and w14a84, with this lane's paths.
- `edits/`: the IR edits (`hphi`, `hcs`, `hpa`, `hal*` from w14a132, plus `cbphi`) and the source edit `src_h1.py`.
