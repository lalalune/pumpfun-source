# w14a42-cto-levy1port: le_vy1 validate closure re-ported onto mains 6db95a7 and 6330811

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a21-cto-helperbound (#3273). Bases: main 6db95a7 (0.65458, M 2,185), then 6330811 (0.65698, M 2,193).
Ledger: approach `levy1port`, keys `0x22a10-w14-6db95a7-levy1port-*-v1` and `0x22a10-w14-6330811-levy1port-*-v1`.

Oracle: w14a21's raw-IR capture + `opt -O3` + `llc` (`capvar.sh`/`rx.py`/`q.py`), repointed at this lane. `m` reproduces
main on both bases (`eq_main: true`). New tools here: `tools/mr.py` (ratio, bytes, M = exact matched original
instructions, jM = jump-masked matches, for jsonl results or names), `tools/gen.py` (writes base+gene edit lists for every
hb/genes47/size-knob/knob8 gene that applies, deduped by resulting text), and `tools/hb_levy1port_genes.py` (the genes
below, as additions to w14a21's `e/hb.py`).

Genes (all on top of w14a21's `v7c` closure): `ny` = `let new=new;` at the start of the non-holder arm,
`le` = line 306 `let Some(t)=new else{..}`, `sh_iflet` = sharing CPI `if let Some(val)=sharing_update{..}` (knob8 / nativejoin -8 B knob).

## Result 1: on 6db95a7 le_vy1 lost its tail, and the cause is one `and` instruction

| name | spec | bytes | ratio | M | jM |
| --- | --- | ---: | ---: | ---: | ---: |
| m | main 6db95a7 | 27,400 | 0.65458 | 2,185 | 2,223 |
| le_v7c | v7c+le | 27,424 | 0.64770 | 2,163 | 2,285 |
| le_vy1 | v7c+ny+le | 27,392 | 0.63191 | 2,109 | 2,153 |
| vy1 | v7c+ny | 27,392 | 0.63071 | 2,105 | 2,228 |
| a_sh_iflet | v7c+le+sh_iflet | 27,416 | 0.64750 | 2,162 | 2,286 |
| b_sh_iflet | v7c+ny+le+sh_iflet | 27,392 | 0.64210 | 2,143 | 2,183 |

- The post-opt IR of le_vy1 and le_v7c differs in exactly one instruction: `and i8 %new.tag, 1` before the non-holder arm's
  tag test (the original's and-1 306 test, w14a10). Every copy spelling (`let new=new` in the arm, at 306, `{new}`, `*&new`,
  `.clone()`, `as_ref()` + `&t`, double copy) gives the same object; `match` and `ok_or_else` forms are worse.
- That one `and` changes register allocation. On 6db95a7 it made the sweep's Err exit block `bb88` (sweep `?` -> return)
  empty after RA (`$r8 = COPY $r2` disappears), so branch-folder deleted it, the curve-update block `bb38` became the ISel
  fallthrough of `bb89` (`if let Some(val)=sharing_update` test), and MachineBlockPlacement pre-merged it there. The
  ~400 B curve block moved up (orig 0x4800 -26, 0x5c00 -43). Debug llc `-debug-only=block-placement` shows
  `Pre-merging due to unanalyzable fallthrough: bb89 -> bb38` only in le_vy1.
- `sh_iflet` removes the `None=>{}` arm, so the sharing test no longer falls through into `bb38`: the layout comes back
  (b_sh_iflet 0x4800 +0), and the copy family is no longer broken by placement. On 6db95a7 the remaining loss was sweep-region
  RA (0x5c00 -43). 62 knob8 genes and 44 size-knob genes on top of b_sh_iflet did not restore it (all 2,143 or lower).

## Result 2: on 6330811 (after the TCF/sweep-token landings) the copy family is within 6 M of main

| name | spec | bytes | ratio | M | jM |
| --- | --- | ---: | ---: | ---: | ---: |
| n_m | main 6330811 | 27,400 | **0.65698** | **2,193** | 2,225 |
| n_b2 | v7c+ny+le+sh_iflet | 27,432 | 0.65479 | 2,187 | 2,231 |
| n_a2 | v7c+le+sh_iflet | 27,424 | 0.65130 | 2,175 | 2,289 |
| n_le_v7c | v7c+le | 27,432 | 0.65030 | 2,172 | 2,288 |
| n_le_vy1 | v7c+ny+le | 27,432 | 0.64581 | 2,157 | 2,200 |
| n_vy1 / n_v7c | | 27,432 | 0.6446 / 0.6440 | 2,153 / 2,151 | |

Exact matched original instructions per 0x400 region, n_b2 minus main: 0x400 +4, 0x800 +10, 0xc00 +3, 0x1000 -5, 0x1400 -1,
0x1c00 -1, 0x2400 -2, 0x2800 -2, 0x2c00 +1, 0x3800 -2, 0x3c00 -4, 0x5400 -1, 0x5800 -3, 0x5c00 -1, 0x6800 -2 (total -6).
The validate gain (+17 in 0x400-0x1000) is real; the losses are spread spill-slot colours (`[r10-0x968]` / `[r10-0x8e8]`
traffic) in the sharing CPI and sweep regions.

Offsets against the original (`vsorig.py`, STEP 0x200): n_b2 puts orig 0x1c00-0x3e00 at -16..+24 B (main -24..-64) and
0x4c00-0x5a00 at -16..0 (main -48..-56), but the tail from 0x5c00 at +8..+32 (main -24..0). The bytes that stand between
n_b2 and the pinned size are the validate closure's (+40 B against main before 0x1c00) minus what the original-shaped
layout saves; the place where the original is shorter than n_b2 is the sweep native arm Err edge (orig 0x5b18-0x5b28):
ours tail-duplicates the sweep join test (`stxdw [r10-0x968]; mov r7,r1; ldxdw r8,[r10-0x968]; jne r7,2; ja`) where the
original jumps to the join (`ldxdw r9; mov r7,r1; ja -0x3db`). The original's join block at 0x3c50 holds two spill reloads
before `jne r7,2,+0x380`, so it is too big to tail-duplicate; ours has only the `jne`, so the post-RA tail duplicator copies it.
That is a register-allocation outcome, not a source size knob.

## Result 3: size repay on n_b2

See the table in SUMMARY.json (`repay_6330811`). n_b2 needs -32 B with no M loss and +7 M to beat main at 27,400 B.
