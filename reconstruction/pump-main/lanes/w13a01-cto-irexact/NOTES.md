# w13a01-cto-irexact: exact-IR target recipe for 0x22a10 `admin_cto::execute`

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: edit admin_cto's IR until `llc` reproduces the original bytes as closely as possible, record the
cumulative ratio after each feature, and publish the ordered IR delta from main as a recipe for the
source lanes. Everything in this directory is an experiment on IR; nothing here is a source proposal.

Base: main 4394685 (#2892, w13a11-cto-stitch-2): admin_cto **0.49071**, slots_diff 3,313, 27,400 B.

## Oracles (tools/, no build slot after one capture)

| tool | what it does |
| --- | --- |
| `capraw.py <crate> <work> <out>` | identity build (slot-locked through fastbuild) with `--emit=link,llvm-ir -C no-prepopulate-passes`: writes the **pre-opt** module `out/raw.ll` (35 MB). The link of the unoptimized object fails (frame overflow); only the `.ll` is used. ~22 s. |
| `rx.py <name> [edits.py] [--base raw.ll] [--keep]` | raw-IR opt oracle: applies `EDITS` (exact `(old,new)` replacements or callables) to the pre-opt module, runs the SDK rustlib `opt -O3`, slims to execute, `llc` exactly like fastbuild, scores with target_metric tokens. ~10-15 s. |
| `sbdiff.py <m.o> [--frame] [--from 0x.. --to 0x..]` | original vs candidate instruction diff (jump offsets relative, calls and lddw imms masked; `--frame` masks every r10 offset). |
| `dis.sh <m.o>` | execute's disassembly from an oracle object, offsets relative to the function. |
| `regmap.py <cand.dis> [seg]` | skeleton alignment (registers, frame and jump offsets masked): skeleton ratio and the dominant orig->ours register renames per region. |
| `skelscan.py <mod.ll> <dir> <basespec> <items>` | iredit items scored by plain ratio, bytes and skeleton ratio. |
| `scgroups.py <sc.log> [names]` | stack-coloring merge groups from `llc -debug-only=stack-coloring` (debug llc). |

`sbdiff.py`, `regmap.py` and `skelscan.py` read the original's disassembly from `$RX_OUT/orig.dis`
(`python3 reconstruction/harness/win.py orig 0x22a10 > $RX_OUT/orig.dis`).

Validation: `rx.py` on main's unedited pre-opt IR gives tokens **equal to the landed baseline build** on
3912c47 (0.48772), 085e5df (0.48922) and 4394685 (0.49071). So `opt -O3` on rustc's pre-opt module is the
whole post-MIR pipeline of the identity recipe; a raw-IR edit is measured exactly as if rustc had emitted it.
The post-opt `llc` oracle and `iredit.py` / `features.py` / `greedy.py` are w12a02-cto-iroracle's
(`origin/swarm/w12a02-cto-iroracle-3`), run here on main's post-opt IR (`opt -O3` output slimmed).

## Recipe (ordered IR delta from main 4394685, cumulative, all at 27,400 B unless noted)

| step | IR edit (post-opt names on 4394685) | what it is in the original | ratio | gain |
| ---: | --- | --- | ---: | ---: |
| 0 | main | | 0.49071 | |
| 1 | `mv:_114.i:_179` | F1: the wallet emit_cpi signer slice (16 B) shares the 24 B slot above holder_key with the final emit_cpi slice (orig T 0x680) instead of its own slot | 0.51917 | +0.02846 |
| 2 | `nolt:buf.i32.i` | an unmerged 24 B slot in the validate region (any one 24 B validate/wallet buffer ties): the original's 24 B target[8..32) host / +80 B of unmerged pieces | 0.53865 | +0.01948 |
| 3 | `mv:val5:_179` | sharing-config CPI `val` (33 B Option<Pubkey>) late in the frame (orig `val7` below old_creator) | 0.54614 | +0.00749 |
| 4 | `bw:start:1:2000` (the first `shared` memcmp: mismatch hot) | block frequency only, no source construct | 0.54853 | +0.00239 |
| 5 | `bw:bb7.i:2000:1` | block frequency only | 0.54883 | +0.0003 |

Steps 4-5 are the size-pinned greedy over 583 single edits (branch weights 2000:1 / 1:2000, successor swaps,
lifetime drops, alloca moves) on top of step 3; it stops paying (< 0.0003 per round) after two rounds, and
no successor swap (the only source-expressible kind) gains at 27,400 B. Bound with a perfect frame on step 3
(`framebound.py`): **0.62013**.

### Where the rest of the gap is: registers and frame, not code shape

`tools/regmap.py` aligns the two instruction streams with registers, frame offsets and jump offsets masked
(the *skeleton*). Skeleton ratio: main 0.8286, step 3 0.8487. So about 85 % of the original's instruction
stream already has the same shape; the remaining distance to an exact window is mostly register assignment
and frame offsets. Example: the 215-instruction "insert" that difflib reports at orig 0x2bc8 (sweep CPI
AccountInfo clones) is the same code with the accounts pointer in r6 instead of r8 (`o8->c6`), and per
0x800-byte region the dominant renames are different (orig r9->ours r5 and r8->r6 in 0x2800, r2->r1 in
0x4000, ...): there is no single permutation, so the register gap is allocation order, not a naming slip.
`tools/skelscan.py` scores IR edits by skeleton ratio: the best successor swaps for code shape are
`inv:bb11.i` (validate's holder test in the !holder_reward arm, non-holder arm first, as the original's DFS
order) 0.8541 and `inv:bb5.i` (holder_reward test) 0.8541, both lowering the plain ratio by 0.005.

### F1 and the 24 B step are stack-coloring positions, not new merges

`llc -debug-only=stack-coloring` (debug llc in `~/.cache/pumpfun-reconstruction/llvm-dbg`) on main and on
F1 gives identical merge groups: the wallet signer slice `_114.i` (16 B) leads the group {`_114.i`,
`target.i.sroa.0` (validate's 7 B target piece)} in both. F1 only changes the group's frame index (its slot
moves next to holder_key, the original's T 0x680). So the source fix must give that group an execute-level
leader allocated near holder_key (the original's 24 B target[8..32) host, w12a01's H24), not a new merge.
`nolt:buf.i32.i` takes one 24 B buffer out of the `_91.i`/old.i/t.i/... group and gives it its own slot.
`tools/scgroups.py <sc.log> <names>` prints the groups.

The anchor `_179` is the final emit_cpi `invoke_signed` sret (24 B, no lifetime) on 4394685 (`_182` on
085e5df/3912c47). Names drift with every main; `features.py` re-detects steps 1-3 by IR shape.

### Frame steps are position-graded (085e5df scan, on top of steps 1+2)

`mv:val6:X` for every execute-level alloca X: 0.53685 (in place) -> 0.53925 for any X from old_creator up to
`authority_info` (val below old_creator: the original's order) -> 0.54134 at ix_data/inner_data -> 0.54344
at `_174`/ix/`_167` -> **0.54434** at any X from `_186` upward (the final emit_cpi temporaries). Moving
`old_creator` down to just above `target1` instead of moving `val` gives the same +0.0024 as the first plateau.

## Structural raw-IR features (on 3912c47, then frame steps on top)

| raw-IR edit | bytes | ratio | + steps 1-3 |
| --- | ---: | ---: | ---: |
| none (main 3912c47) | 27,400 | 0.48772 | 0.52666 |
| `to_string` noinline at 307 and 312 (the original's outlined set; w12a10 `noinl.py`) | 26,960 | 0.43304 | 0.46867 (best 24 B nolt: `inner_data.i`) |

| holder as `trunc(load holder arg)` instead of `Option::eq` (orig `and64 r8,1`) | 27,152 | 0.44364 | 0.52430 (skeleton 0.811) |
| `new` copied into a local 33 B alloca at the **entry block start**, all uses read the local | 27,728 | 0.39720 | 0.42608 (F1 only) |
| same copy at the start of bb7 (after `shared`, before `global_quote`) | 27,536 | 0.47751 | |
| same copy after global_quote / after the CtoState stores (orig position) / before validate's arg copy | 27,648 / 27,744 / 27,624 | 0.47592 / 0.48400 / 0.47971 | 0.54115 (after CtoState) |

**Entry copy of `new`:** the entry-block copy reproduces the original's piece loads instruction for instruction
(`ldxb [+0]`, `ldxw [+4]`, `ldxw [+1]`, `ldxdw [+8]`, `ldxdw [+0x10]`, `ldxb [+0x20]`, `ldxdw [+0x18]`, the 7 B
piece written as two overlapping words) and adds exactly the original's frame objects: `new.sroa.3.sroa.0/5`
(7/9 B, w12a01's F7/G9) plus the sharing payload pieces `_395.sroa.6.sroa.0/8` and
`sharing_update.sroa.3.sroa.0/4` (A7/B9, C7/D9). But the loads land at the function entry (the original
loads them at 0x4d8, after CtoState) and the function grows 328 B. Placed at bb7's start the pattern
survives (with +0x10 loaded before +8); placed after `global_quote` or later, the copy is forwarded and the
pieces vanish. The SROA'd local must exist before the code that follows it is simplified; a source spelling
needs a copy that MemCpyOpt cannot forward (w13a03-cto-entrycopy's `mut new` + `take()` direction).

The outlined `to_string` set costs 440 B that the original fills with data flow (see w12a09-cto-cleanroom).

## Source trials (main 085e5df, measure.sh)

| trial | change | result |
| --- | --- | --- |
| oc1-oc4 | declare `old_creator` (deferred init / destructuring assignment) before the sharing CPI match, to emulate the val-below-old_creator frame step | **byte-identical** to main (sha 4fc952ce): declaration position does not move that alloca |

Ledger keys: `0x22a10-w13-*-irexact-*`.
