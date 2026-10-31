# w14a74-cto-s1tagjoin: pricing the sharing-tag / swept live ranges on the s1 base (main 39eb377)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a60-cto-s1rescan (#3371) and w14a47-cto-sharestruct (#3351). Base: main 39eb377aa (#3386), admin_cto
0.66477 / 3,230 slots. Ledger approach `s1tagjoin`, keys `0x22a10-w14-39eb377-s1tagjoin-*-v1` (12 rows).

**No source change is proposed.** No tag or swept live-range change rescues s1. The s1 deficit is not at the sweep join.

## 1. s1 on 39eb377, and where it loses

s1 means all 7 sharing `AccountInfo`s written as plain `to_account_info()`. `edits/gen.py` regenerates it from the
current source. The rx oracle's `m0` run reproduces main (`eq_main: true`).

| form | ratio | bytes | L1 (frame masked) | L2 (frame + regs masked) | cls 0x3c38-0x4a78 miss/fm/rm/jm/sk |
| --- | ---: | ---: | ---: | ---: | --- |
| main 39eb377 | 0.66477 | 27,400 | 0.70102 | 0.78370 | 231/60/0/2/169 |
| s1 | 0.63638 | 27,344 | 0.69186 | 0.81302 | 327/123/123/15/66 |

Split the s1 loss of -0.0284 by mask level (`tools/fmr.py`):
- structure gains +0.029 (L2);
- registers cost -0.038 (L1 minus L2, relative to main);
- frame offsets cost -0.019 (plain minus L1, relative to main).

Matched tokens per 0x800 chunk differ from main only in three chunks: 0x3800 -9, 0x4000 -60, 0x4800 -27. All three
lie inside the sharing CPI, and most of the loss is in the clone run (0x4000-0x46c0). At L1 the 0x4800 chunk is
equal to main, so its -27 is frame-only. The sweep join, where swept and the tag live (orig 0x3c40-0x3d20), accounts
for at most the 9 tokens in chunk 0x3800.

`tools/regmap.py` gives s1's register mismatches per 0x100 of the region: 0x4500: 34, 0x4600: 26, 0x4200: 19,
0x3e00: 16. These are a global permutation of the clone run. The original reloads the accounts pointer
`[r10-0x8d8]` before each clone; ours holds it in r7. In the original r6 is the flag scratch register and r9 holds
swept. `tools/sbs.py` prints the L2-aligned side-by-side listing.

## 2. Tag and swept live-range pricing (post-opt IR + llc, `tools/px.py`, `edits/post/`)

| probe | s1 | main |
| --- | --- | --- |
| a1: event `sharing_config_reset` recomputed from the tag SSA (icmp at the event) | byte-identical | byte-identical |
| empty-asm use of swept at the join | identical | identical |
| swept use at arm entry / before / after the CPI | 0.63568 @27,352 | 0.66347 / 0.66467 @27,408 |
| tag use at arm entry | identical | identical |
| tag use before / after the CPI | 0.63718 @27,352 (+0.0008) | 0.66467 @27,408 |
| swept + tag uses (5 combinations) | 0.63439-0.63718 | 0.66347-0.66467 |
| register pins via inline asm (`={r9}` swept, `={r6}` tag) | 0.477-0.590 | 0.496-0.607 |
| accounts pointer reloaded per clone (volatile alloca) | L1 0.670-0.692 | n/a |

- a1 is a no-op. Ours already re-tests the tag from its slot at the event (`and 0xff; mov r2,1; jne 2; mov r2,0`),
  as the original does at 0x4f18. The tag's data flow is already the original's; only its register differs. This
  matches w14a12-cto-tagreg (#3251), whose bound for the tag register is +0.0027.
- An extra use only adds a reload. swept stays spilled at `[r10-0x968]`, and the tag is still reloaded from
  `[r10-0x8e8]`.
- The inline-asm pins are not usable bounds. Any asm call in the join block changes block placement and moves the
  whole sharing arm (chunks 0x4000-0x4800 drop to 0 matched).

Source forms on s1 (raw-IR capture builds):

| form | s1 | main |
| --- | --- | --- |
| `let reset=sharing_update.is_some()` before the sweep, event uses `reset` | byte-identical (GVN folds it) | |
| `if let Some(val)=sharing_update.as_ref()`, `*val` at the CPI | 0.53367 | |
| `reset` bool + `if reset{let val=sharing_update.unwrap();` | 0.63718 @27,352 | 0.66467 @27,408 |

## 3. New lever found: block frequency reorders s1's spill slots (`bwsweep.py`, `bwgreedy.py`)

The sharing-gate branch weight changes only frame offsets. With 8:1 (arm hot), s1 rises to **0.64657** at 27,344 B
(+0.0102). Its L1 and L2 are identical to s1's, and the region's fm falls from 123 to 90. StackSlotColoring orders
spill slots by block-frequency-weighted use, so a hotter sharing arm moves the clone-run spill slots toward the
original's. On main the same weight costs -0.012, and 1:8 costs -0.001, so main's 50/50 is already its optimum.

Single-weight sweep: 146 conditional branches × {1:2000, 2000:1, 1:8, 8:1}, on s1 and main:

| base | best single | greedy combination |
| --- | --- | --- |
| s1 | gate 8:1 0.64657; Rc `inc_strong` trap br 124 1:8 0.64390; other traps +0.003 | gate 8:1 + trap 125 1:8 + trap 79 1:2000 = **0.65037** @27,352 |
| main | Rc traps 79/80 1:2000 0.66657 (+0.0018) | (not run) |

Even the weight-optimal s1 is 0.0144 below main. The Rc trap weights are not source-expressible (w13a26-cto-bfreq).
The sharing gate is `icmp ne tag,2`, which no BPI heuristic biases. A 5:3 zero-heuristic form would need a compare
with 0 that InstCombine keeps.

## Re-check on main 0d04cf4 (#3393, sharing `match` form)

Main 0.66507. s1 is 0.63589 at 27,360 B (L1 0.69135, L2 0.81247; main 0.70132 / 0.78310). With the gate at 8:1 s1
reaches 0.64608, at 2:1 0.64578 and at 1:8 0.60249. The tag use before the CPI gives 0.63549, and a1 is identical.
On main the gate at 8:1 gives 0.65309, the tag use 0.66437 @27,408, and a1 is identical. The picture is the same as
on 39eb377.

## Verdict

No tag or swept live-range change rescues s1. Tag edits are byte-identical or lose, swept edits lose, and the best
weight bound reaches 0.65037, still below 0.66477. s1's deficit is in the clone run: registers -0.038 and frame
-0.019 against a structural gain of +0.029. The join is not where it loses.

s1 is still the better structural base: its L2 is +0.029 above main. w14a18-cto-slotpin's interval-level original-slot
pin of s1 (ledger `0x22a10-w14-cef0574-slotpin-c_s1-none-v1`) reached 0.67866 when main was 0.63421. A lane that can
move frame slot order through source-expressible block frequency or spill weight could revisit s1. The first such
lever is the sharing gate (+0.010 at 8:1).

## Tools (experiment only; paths point at this lane's worktree and scratch)

- `tools/px.py <name> <m.ll> [edits.py] [--dbg]`: post-opt IR oracle. It applies EDITS (pairs or callables) to an rx
  slimmed module, then runs llc and scores the result. With `--dbg` it also writes the greedy regalloc log. It
  reproduces main and s1 byte for byte.
- `tools/fmr.py fn.bin...`: plain, L1 and L2 ratio, plus L1-matched tokens per 0x800 chunk.
- `tools/fdelta.py fn.bin lo hi`: frame-offset pairs (orig to cand) for L2-aligned instructions.
- `tools/regmap.py fn.bin lo hi`: register-pair mismatch histogram and per-0x100 counts.
- `tools/sbs.py fn.bin dis.txt lo hi`: L2-aligned side-by-side listing (orig against cand asm).
- `tools/bwsweep.py m.ll tag w...` and `tools/bwgreedy.py m.ll tag`: branch-weight sweep and greedy combination.
- `edits/post/`: IR probes (`common.py`, `pin.py`, `prof.py`, `vr.py`); `edits/s1*.py` and `t5.py`: source forms.
- w14a60's capvar.sh, batch.sh, rx.py, cls.py and csrmap.py, repointed to this lane.
