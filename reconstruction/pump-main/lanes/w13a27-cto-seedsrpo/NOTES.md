# w13a27-cto-seedsrpo: admin_cto region 2 (648 seeds check RPO, sweep `?` exits)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: continues w13a14-cto-region2of3 (#2955) next ideas 1-2: move the 648 ConstraintSeeds error block later
in RPO so the region-2 sret-demotion slots reach the original's ranks, and look for a sweep body whose `?` exits
feed the sweep-exit tag test directly.
Bases: main bf9a05d (0.55872 / 3,323 slots) and 6ac6f9b (#3011, 0.56291 / 3,315 slots).
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w13a27-cto-seedsrpo/` (not in git).
Ledger keys: `0x22a10-w13-bf9a05d-seedsrpo-*`, `0x22a10-w13-6ac6f9b-seedsrpo-*`.

No source change is proposed. This PR holds notes and tools.

## 1. The angle's premise is already resolved on main

`tools/sret.py <fn.bin>` pairs the 33 sret-demotion slots (`mov r1,r10; add r1,-X; .. call`, X in 0x6a0..0x8e0) by
call layout position and prints each slot's rank in the original and in the candidate.

- **bf9a05d**: from layout position 13 on, every slot has the original's rank. That covers all of region 2 and
  region 3 (`648:7c8`, `660:7e8`, `719:808`, ...). The w13a14 "+3 ranks" (measured on 74b3171) is gone.
  Only the +8 B base remained (orig 0x6d0 + 16·rank, ours 0x6d8 + 16·rank). Shifting every candidate r10 offset in
  [0x6c1, 0x8e8] by -8 (`tools/shiftbound.py`) bounded that part at +0.011 (0.55872 -> 0.5698).
- **6ac6f9b** (#3011, `hk` kept alive): the sret block now sits at the original's offsets. Every slot from layout
  position 13 on matches in both rank and offset.
- The only rank differences left are in region 1, at layout positions 0-12 (validate's sites, where 330 comes
  after 338/334 and 306/296 are laid out elsewhere). Fixing their ranks while keeping our layout is worth 0.0
  (remap bound). The sites are laid out in a different order, so ranks alone cannot align them.

Still true on main d81d0f5 (0.571): `slots.py` (w13a06) shows every error-site slot at the original's offset except
330/338/334 (orig `330:710 338:720 334:730`, ours `338:710 334:720 330:730`).

Region 2 therefore needs no further RPO change. The 648 block's RPO position is not a lever any more.

## 2. Where region 2's distance is now (`tools/seg.py`, main 6ac6f9b)

Matched tokens per 0x800 bin of the original (plain / regs masked / frame masked / both):

| orig bin | tokens | plain | regs | frame | both |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0x2800 | 256 | 133 | 198 | 121 | 173 |
| 0x3000 | 256 | 89 | 166 | 162 | 227 |
| 0x3800 | 255 | 127 | 148 | 205 | 241 |
| 0x4000 | 256 | 65 | 163 | 120 | 171 |

Region 2's remaining distance is register assignment and spill-slot choice in the two CPI clone runs:
- In the original, the accounts pointer is r8 and is reloaded from `[r10-0x8d8]` before each sharing-CPI clone.
  Ours keeps it in r5/r6.
- Callee-saved r6-r9 are permuted between the original and ours.
- Some spill slots are 8 B off. The spill-slot count is equal on bf9a05d: 114 distinct offsets at or below 0x8e0
  in both.

The 0x3c40-0x3d80 sharing payload copy is the P2 7/8/8/8/1 piece residual, which belongs to the payload/frame
lanes.

## 3. Sweep `?` threading: why the layout flips (new mechanism detail)

IR oracle (raw-IR capture + `opt -O3` + llc, w13a23's `rx.py`). The edit drops `lifetime.end` calls in the inlined
sweep's Err merge chain (`tools/swedit.py`, `edits/lt*.py`):

| edit (main) | bytes | ratio |
| --- | ---: | ---: |
| bf9a05d: drop `dest` end in bb58 (`lt58`) | 27,488 | 0.43308 |
| bf9a05d: drop ends in bb54+bb58 (`lt54`) | 27,432 | 0.22605 |
| bf9a05d: drop ends in bb50+bb54+bb58 (`lt54b`) | 27,304 | 0.21248 |
| 6ac6f9b: `lt58` | 27,488 | 0.43009 |
| 6ac6f9b source `v3` = block-scoped 648 `dest` | 27,488 | 0.43667 |

`lt58` is the IR form of the destscope source (`v3`).
- JumpThreading builds `sweep.exit.thread` from the pre-seed `?` sites (the coin-ATA token_frozen and
  token_raw_amount, and the transfer CPI). It sends them straight to the Err return, exactly like the original.
- The From sites get their own tail-duplicated `jne r7,2` test, also like the original.

Why the layout still collapses (debug llc `-debug-only=block-placement`, `mbp_*.log` in scratch):
- BPF's `analyzeBranch` cannot analyze conditional branches. MachineBlockPlacement therefore **pre-merges every
  block that ends in a conditional branch with its MBB-order successor** ("Pre-merging due to unanalyzable
  fallthrough").
- On main, the MBB just before `bb82` (post-sweep) is `bb58.i86`, the end of the Err merge chain, which carries
  the tail-duplicated tag test. Its chain is Rent From -> bb54 -> bb58 -> bb82, so post-sweep follows the Rent
  error site, as in the original.
- With threading, `bb58` disappears. The MBB before `bb82` becomes `bb50.i`, the sweep Ok join with the test copy.
  `bb50.i`'s chain is the token-arm path (`bb104.i -> bb50.i`), so post-sweep is glued there. That is the flip every
  destscope / vsigner / skip-tree trial since w12a07 hit.
- To get the original's layout, threading needs a merge block that is MBB-adjacent to `bb82` and reached from
  the Rent From site, while the pre-seed sites still thread past it.

IR block-order scan on `lt58`. The scan tried 135 `blk:` moves of `bb50.i`, `bb54.i`, `bb40.i`, `bb89.i` and `bb86.i`
within the sweep block range (on a copy run through `opt -passes=instnamer` first, so moved blocks keep legal value
numbering).
- Exactly one move restores the layout: `blk:bb54.i98:sweep.exit`. It moves the post-seed Err StorageDead chain
  (old/bump/vaultseeds/vsigner ends) to just before the exit block.
- Result: 0.43009 -> **0.52986**, abs ratio 0.499 -> 0.669, 27,440 B. That is still below main (0.56291, abs 0.686).
- So the threading mechanism is understood end to end. On the current main it is a net loss even with the
  original's layout, and it is not worth pursuing until the rest of the function has moved further.

Weights do not rescue it. On `lt58`, every 1:2000 / 2000:1 weight on its 147 conditional branches stays at or below
0.528 (best: `bb25.i` 2000:1, the seeds block's native test). On `bb77` (the dest check) the weights 1:1, 1:2, 2:1,
1:16 and 16:1 give 0.29-0.43.

## 4. Other measurements

| trial | form | bytes | ratio |
| --- | --- | ---: | ---: |
| v1 (6ac6f9b) | `if key!=dest{Err::<(),_>(error!(..).with_pubkeys(..))?;}` | 27,400 | identical to main |
| v2 | `(key==dest).then_some(()).ok_or_else(\|\|error!(..).with_pubkeys(..))?;` | 27,528 | 0.20681 |
| v4 | `let chk:Result<()>=if key!=dest{Err(..)}else{Ok(())};chk?;` | 27,400 | identical to main |
| bw/inv scan (bf9a05d, 441 items) | every condbr 1:2000, 2000:1, inverted | 27,400 | best 0.56351 (`bw:bb82:2000:1`, abs ratio unchanged) |
| nolt scan (6ac6f9b, 137 items) | drop each lifetime alloca's markers | 27,400 | none above main |
| llc `-tail-dup-size=3` (6ac6f9b) | knob only, not source-expressible | 27,416 | 0.56634 (gains in regions 1 and 3) |

## Tools (this directory)

They import `oracle.py` from w13a23-cto-irexact2's tools (`capraw.py`, `capvar.sh`, `rx.py`, `iredit.py`). Copy
those next to these files and set the lane paths.

- `tools/sret.py <fn.bin>`: sret-demotion slot rank table (orig vs candidate, by call layout position).
- `tools/seg.py <fn.bin> [bin]`: matched tokens per original bin: plain, regs masked, frame masked, both.
- `tools/shiftbound.py <fn.bin> lo hi d`: ratio after shifting candidate r10 offsets in [lo,hi] by d.
- `tools/swedit.py`: raw-IR edit helpers scoped to the un-inlined `admin_cto::execute::sweep` function.
- `tools/sbs.py <cand.dis> lo hi delta`: side-by-side original/candidate disassembly window.
- `tools/runlist.sh <list> <slot>`: sequential capvar runner (stdin-safe).
