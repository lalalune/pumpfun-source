# w15a31-cto-mbp660chain: the MBP decision behind the skip-polarity collapse, and its bound (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 9120883 (`$BASE`, not rebuilt). 1cc4879 and 3034223 have the same admin_cto (0.67376, 3,124 slots, M 2,249,
Mperm 2,292). Continues w15a13-cto-jointraceback (#3728, next idea 2). Ledger: approach `mbp660`, keys
`0x22a10-w15-9120883-mbp660-*-v1` (7 rows).

**Result: no landable change.** The MBP decision is named below, with its inequality. Fixing it does not help:
basin A at main's block layout is bounded at Mperm 2,243, below main's M 2,249. A threaded sweep exit, with or without
the skip polarity, is bounded at Mperm 2,202 / 2,155. The skip-polarity lead is closed on main's structure.

Naming fix: the block w15a13 called "the 660 error block `to_string.exit.i` (`%bb.84`)" is the **648**
`error!(ConstraintSeeds).with_pubkeys(..)` tail (orig 0x2490-0x24b0, ours `call` with r1=-2000). Its predecessor is the
sweep head `bb35` (memcmp of holder_creator_vault against `dest`). The 660 block (CtoSharedVaultFrozen, r1=-2016) comes
after it. The 648 path gets 62.5% of the sweep's frequency (`memcmp != 0` heuristic): 0.0021915 of 0.0035064.

## 1. The decision (debug llc `-debug-only=block-placement,branch-folder`, `data/mbp-decisions.txt`)

BPF `analyzeBranch` cannot analyse conditional branches, so `bb56.i` (sweep.exit, `jne r7,2,err`) is pre-merged with its
IR-next block, the post join. That chain is placed by the **second** MBP pass, which runs after the post-placement
BranchFolder tail merge.

At the 648 tail, `hasBetterLayoutPredecessor(BB=648 tail, Succ=bb56.i)` decides. It finds a conflict when some other
predecessor P of `bb56.i` is the tail of its own chain and satisfies

    freq(P) * p(P->bb56.i) * 0.8  >=  freq(648 tail) * p(648->bb56.i) * 0.2
    i.e. freq(P) >= 0.25 * 0.0021915 = 0.000548        (HotProb = StaticLikelyProb 80%, no profile)

- **Main.** P is `bb60.i117`, the merged sweep `?`-Err reload block (`ldxdw r3,[r10-0x2c8]; ja join`). The tail merge
  folds four identical blocks into it: `bb60.i` 0.000329, `bb62.i` 0.000103, `bb93.i` 0.000195 and `bb95.i` 0.0000975.
  That is 0.000724 >= 0.000548, so there is a conflict. `bb56.i` is not taken at the 648 tail. It becomes a `CFG break`
  candidate only at its last predecessor, `bb84.i139`, and the post chain stays after the sweep, as in the original.
- **Basin A** (q1mv1: skip-polarity gate plus `bb87` moved after `bb38`).
  - The sharing tag (the `Option<Option<Pubkey>>` tag, `and r9,255; jne r9,2` in the post chain) is live into `bb56.i`
    in r9.
  - On the two amm_frozen `?` Err edges (`bb34.i->bb93.i` from token_frozen, `bb94.i->bb95.i126` from
    token_raw_amount), greedy has the tag in r6. It inserts `$r9 = MOV_rr $r6` into `bb93.i` and `bb95.i126`.
  - Those two blocks no longer share a tail with the others, so BranchFolder merges only `bb62` into `bb60`.
    0.000431 < 0.000548, so there is no conflict.
  - `bb56.i` is then a `CFG break` at the 648 tail. The post chain lands at 0x2490 and the function grows to 27,448 B
    (M 1,711).
  - Pass 1 places these blocks identically in both builds (same pre-MBP CFG for them, same `ord1` positions). Only the
    merge differs.
- This is the w14a142 "bb56.i join split" family, with a different value. In w14a142 it was the accounts pointer in r5;
  here it is the sharing tag in r9. In both, RA copies in some `bb56.i` preds break the tail merge.

Gate weights cannot fix this (w15a13, `gatew.py`). An Err-edge weight that lifts `bb60.i` above the threshold
(`succ:120:0.2,0.8`) flips the pass-1 fallthrough of `bb9.i112` and relays the sweep (M 1,412). An explicit `JMP` after
main's `bb56.i` (`t_m0jmp`) gives main's bytes: pass 1 places `bb56.i` after the 648 tail, the JMP folds, and pass 2
pre-merges again.

## 2. Bounds (M = scorer difflib matched tokens; Mperm = w15a08 `relab.bestperm`, best spill-slot relabel)

| oracle | what | bytes | ratio | M | Mperm | true-LCS `---`/`--j`/`-fj`/`rfj` |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| main (`t_m0base`) | | 27,400 | 0.67376 | 2,249 | 2,292 | 2255 / 2367 / 2599 / 3007 |
| q1mv1 (`t_q1base`) | basin A | 27,448 | 0.51212 | 1,711 | 1,752 | 1720 / 1820 / 2008 / 2483 |
| **t_q1nomov** | basin A with the two r6->r9 copies deleted in pre-MBP MIR, so the merge re-forms and MBP keeps main's placement (post chain at 0x3c68 = orig, 648/660 at 0x2370/0x2590) | 27,400 | 0.58778 | 1,962 | **2,243** | 2141 / 2265 / 2585 / 3005 |
| d1 | raw IR: drop `lifetime.end(dest)` in sweep `bb56` (w13a27 on current main), so the sweep `?` Err edges are threaded | 27,440 | 0.50022 | 1,671 | | 1844 / 1955 / 2216 / 2616 |
| **d1asm1** | d1 plus an asm move of chunk X back to main's place (placement only) | 27,440 | 0.63164 | 2,110 | **2,202** | 2165 / 2284 / 2559 / **3014** |
| q1d1 / q1d1mv | skip polarity + d1 / + `bb87` after `bb38` | 27,472 | 0.47779 / 0.42094 | 1,597 / 1,407 | | 1626 / 1727 / 1991 / 2491; 1755 / 1874 / 2217 / 2618 |
| **q1d1asm1** | q1d1mv plus the chunk-X asm move | 27,472 | 0.56006 | 1,872 | **2,155** | 2072 / 2202 / 2551 / 3011 |

- Basin A at main's layout is equal to main in skeleton (`rfj` -2) and -14 in registers. The rest is frame: the sweep
  body's spill slots differ (the r8 pointer spill is at [0x948]; the original and main use [0x928]). RA and PEI run
  before MBP, so no placement decision can recover it. Even the best spill relabel (Mperm 2,243) stays below main's
  plain M.
- The threaded sweep exit (d1) gives the original's tail shape:
  - the 648/660 tails get their own `jne r7,2,exit; ja post` (ours 0x2490 and 0x25f8, orig 0x24a8 and 0x2610);
  - the `?` Err edges go to `bb87` through `sweep.exit.thread`.
  - It collapses for a different MBP reason. The native-path tag-test instance `bb48.i133` (preds `bb85.i`, `bb89.i142`,
    `bb91.i`, `bb43.i134`, `bb37.i130`) is an unanalyzable fallthrough into the post join `bb88`. The post chain is
    therefore "Mid chain!" for every other pred. It is placed only after the whole native path: chunk X
    (`bb5.i..bb53.i87`, 452 asm lines) sits between the sweep and the post chain, which lands at 0x49b0 (orig 0x3c68).
  - Moved back (d1asm1), it is the only form here with a better skeleton than main (`rfj` +7). It still loses 40
    register tokens and more in frame (Mperm 2,202).
- The original has the skip polarity and the threaded exit together. Even that joint form (q1d1asm1) is bounded at
  Mperm 2,155.

## 3. What the original's layout needs (for any lane that re-opens this)

In the original, the sweep-exit tag test is laid out like this:
- one instance at 0x3c50 (`ldxdw r1,[0x950]; ldxdw r6,[0x8f8]; jne r7,2,5868`) falls into the post chain at 0x3c68;
- its fallthrough predecessor is the native-path `Rent::get` Err `From` block (0x3c18, `call 0x2eaad`);
- 0x3ba8, 0x62e8, 0x6380 and 0x63a8 jump to it;
- the 648 and 660 tails carry copies (`jne r7,2,5868; ja 3c68`), which matches early tail-dup into the
  unconditional-branch preds;
- the sweep `?` Err edges are threaded straight to `ldxdw r9,[0x2c8]; ja 5868` (0x6360);
- the token Ok path is threaded straight to the post chain (0x60d8-0x60f0 `ja 3c68`, with the r6/r1 reloads).

Our IR has none of these at once:
- main has one shared `bb56.i`, pre-merged with the post join;
- d1 has the copies and the threading, but its surviving pre-merged instance is the native-path one;
- w14a48 (`tailerr`) reached the same tag-test skeleton with block moves, also below main.

The register and frame consequences of every such CFG change cost more than the skeleton gains (+4 to +7 `rfj`).

## Tools (`tools/`, experiment only; they import `oracle.py`, `xled.py`, `fact.py` and `dis.py` from w14a128 / w15a13)

- `mirx.py <src> <out> [succ:BB:a,b] [sub:BB:old=>new]` edits the pre-MBP MIR (`rx/<src>/pre.mir`, from
  `llc -stop-before=block-placement`). It can set successor probabilities or make an exact text substitution inside one
  block. It then runs the debug `llc -start-before=block-placement` and prints ratio, bytes and M. Set `BP=1` to also
  write the MBP debug log. On m0mv0 and q1mv1 it reproduces main and basin A byte for byte.
  - Gotcha: under zsh, pass llc flags as an array. `A="-O3 -relocation-model=pic ..."` is not word-split, so llc silently
    builds a different (28,704 B) function.
- `mirg.py <mir> <bb-number|name-regex>...` prints a block's successors (with probabilities) and its predecessors.
- `bpsplit.py <bp.txt>` splits a debug MBP log into the pass-1 decisions and order and the pass-2 decisions and order
  (`dec1`/`ord1`/`dec2`/`ord2`). Pass-2 numbers are the post-BranchFolder renumbering, the same as in
  `-stop-after=block-placement` MIR.
- `asmmv.py in.s out.s START END BEFORE` cuts asm labels [START,END) and pastes them before BEFORE. It fixes
  fallthroughs with `ja` and drops a `ja` to the next label. `asmsc.py <file.s> <dir>` assembles the result
  (`cc1as`, sbf, +store-imm,+jmp-ext) and scores it. Together they give a placement-only bound with registers and frame
  fixed.
- `mperm.py <fn.bin|so>...` wraps w15a08's `relab.py` (with w15a08's `rx.py`) and prints M and Mperm.
- `e_d1_dest_ltend.py` (raw-IR EDIT for `rx.py`: drop `lifetime.end(dest)` in the sweep Err join) and `e_q1_skip.py`
  (the skip-polarity source spelling used for q1).

## Next ideas (none of them is in this lane's angle)

1. Every CFG change in the sweep exit moves greedy's spill colouring in the sweep body (0x2800-0x3c00). That holds for
   basin A, for d1 and for w14a142. A lane that wants the original's tail shape should start from a frame model of the
   sweep body (which value the original spills where), not from layout.
2. d1asm1 is the only skeleton-positive form in this region (`rfj` +7, with the tag-test copies as in the original).
   If a source form for "no `dest` lifetime at the Err join" exists (for example, `dest` dying before the `?` Err joins),
   it still needs a native-path instance that does not pre-merge with the post join. Its register cost (-40 `-fj`) has
   to be bought back elsewhere.
