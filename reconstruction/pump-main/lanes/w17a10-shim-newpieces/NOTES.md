# w17a10-shim-newpieces: the original's `new` piece flow (E3 + J1 + C1) as unsafe shims

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Wave 17 shim track. Ledger approach `shim-newpieces`, keys `0x22a10-w17-<main7>-newpieces-<item>-v<n>`.

Bases measured: main 442ae70ca (M 2,257, 0.67615) and main af6ca66a2 (M 2,264, 0.67825). Main has since moved to
fd78179b8 (0.67855). The lane's work dir copy of `programs/pump` and every IR file stay under `$OUT`; nothing in this
lane changes source, so there is no build and no landing.

**Result: no gain. Every shim form of the original's `new` piece flow collapses the function to M 1,445-1,767 (main
2,264), and the cause is the same placement cliff in all of them (section 3).** The forms do reproduce the original's
instruction shapes in E3, J1 and C1 (section 2), so the direction is structurally right, but it cannot be landed
piecewise on main's register-allocation basin.

## 1. Oracle

The exact slim pre-opt oracle from w17a06 (`preslim.py` + `fx.py`), on a fresh capture of each main:

- capture with `irbeam/tools/capraw.py <crate copy> <work> <cap>` (60 s, one build slot);
- **trap:** when a work dir is reused, `capraw.py` copies `target*/*/release/deps/pump_recovered*.ll` and can pick up
  the *previous* build's `pump_recovered.ll`. The new module is the `pump_recovered.pump_recovered.<hash>-cgu.0.rcgu.ll`
  next to it. Delete the old `.ll` files before each capture (w17a06's `capv.py` does), or check the score: the stale
  file reproduced 442ae70 instead of af6ca66;
- `SURV=surv-1647da0.txt preslim.py raw.ll slim.ll keep`, then `fx.py slim.ll <name>`: M 2,264 / 0.67825 / 27,400 B on
  af6ca66, equal to the baseline `cto.json`;
- edits are text replacements on the slim pre-opt module (`tools/ired.py ex/<set>.py [names]`), 1-3 s each.
- The debug llc in `$C/llvm-dbg/build/bin` produces byte-identical objects to the SDK llc and runs `-debug-only=block-placement`
  and `-print-before=block-placement` on a slim `m.ll` in 0.1 s. That is how section 3 was found.

## 2. What the shim forms reproduce

The original loads every SROA piece of `new` right after the CtoState stores (orig +0x4d8..+0x538: tag, u32@4/u32@1
overlapping = a 7-byte copy into an alloca at -0x658, u64@8 -> spill, u64@16 -> r9, u8@32 + u64@24 = a 9-byte copy into
an alloca at -0x668). The sharing payload then travels as 7/8/8/9 pieces (two allocas plus two SSA words) through J1
(-0x538/-0x548) and the post-join copy (-0x550/-0x560) into the CPI argument at [-0x651, -0x630).

| form | IR edit (pre-opt) | what appears | M @ bytes (af6ca66 unless noted) |
| --- | --- | --- | --- |
| `c1a` | C1: `val8` built piecewise from `sharing_update16` (tag; 7 B memcpy; i64 @8, @16; 9 B memcpy) | SROA splits the payload back through `_71`, the arms and the args copy: **`ldxdw r9,[new+0x10]; ldxdw r7,[new+8]; ldxb r4,[new+0]` at +0x540..0x550, right before the sk copy and the mayhem `jne`** (orig +0x4d8/+0x508/+0x518, even r9), spills to -0x958/-0x950/-0x940; the 7 B / 9 B parts stay lazy (new+1, new+0x18 kept live) | 1,458 @27,696 |
| `c1a` variants | order (16,8), `ptr` middle words, tag last, volatile loads (`c1v`) | same | 1,458 / 1,472 |
| `e79v` | `c1a` + the 7 B and 9 B copied at the CtoState site into two new allocas with **volatile** memcpy (so MemCpyOpt cannot forward them), shared arm copies from them | the full original E3 piece set: new+0x10, new+8, tag (spilled), `ldxb [new+0x20]; ldxdw [new+0x18]` (the 9 B exactly as the original), the 7 B as b/h/w (a volatile memcpy cannot use overlapping loads). E3 frame/reg/jump-masked match 50 -> 56 of 90 | 1,445 @27,456 |
| `e79n` | same with plain memcpy | forwarded, = `c1a` | 1,458 |
| `e79p_*` | `e79v` with the two allocas at 10 positions of the alloca list | | 1,445-1,449 |
| `x3a`-`g` (442ae70) | volatile i64 loads of new+8/new+16 at the CtoState site feeding the CPI argument's middle words | GVN forwards the volatile values into validate's `target.i.sroa.7/8` loads (they live from entry) | 1,599-1,603 @27,704 |
| `j1v`, `j1n`, `j1v45` | the shared arm builds `sharing_update` from pieces (middle words read at the arm) | live J1 -> C1 only | 1,520-1,565 |
| `esc_*`, `fa_*` | `asm sideeffect "" "r,~{memory}"(new)` after the args copy (= `black_box(&new)`), validate reads `args.0` (Fa) | | 1,453-1,518 |
| `x3j` | tag store + 32 B memcpy (the main shape, re-spelled) | | 2,264, byte-identical |

## 3. Why every form collapses: one placement cliff in the sweep join

All of them move the whole sharing-config CPI region (about 800 instructions, orig C1 0x3c50-0x4aa8) from after the
TCF CPI (0x3c30 in main, as in the original) to right after the 660 error exit at about 0x2478. `tools/mdiff.py`
shows it as one ~805-instruction insert at 0x2478 plus deletes at 0x3c48/0x3d08/0x4220.

Mechanism (debug llc, `-debug-only=block-placement`, main vs `e79v`):

- the sweep's result join `bb58.i` (the `jne r7,2` after sweep, then `bb90` = C1 head, then `bb35` = the CPI) has 12
  predecessors in main and is one machine block. When MachineBlockPlacement's second pass (after BranchFolder) reaches the
  660 `to_string` exit, it reports `Not a candidate: bb58.i -> 100% (non-cold CFG conflict)`, so `bb58.i` waits and is
  later laid out after `bb87.i` (TCF Ok). That is the original's layout;
- in every newpieces form, greedy RA keeps one more value across the join (the accounts pointer, reloaded from its
  spill slot into r5) for 5 of the 12 predecessors, so `bb58.i` splits into a reload block plus the test block. The
  reload block's predecessor set has no hot chain-tail predecessor, so the conflict check passes, the 660 `to_string` exit
  takes it as fallthrough, and `bb58.i -> bb90 -> bb35` follow the error path;
- the same flip happened earlier (442ae70) through `bb34` (the `skip` test): main tail-merges the three wallet `msg!`
  `sol_log_` tails into one block in front of `bb34` (live-in r9 only). Any extra live value gives `bb34` reloads,
  tail duplication copies it, and the chains change.

How fragile the site is (`ex/dead.py`, all af6ca66):

| probe right after the args copy at the CtoState site | M @ bytes |
| --- | --- |
| dead `load volatile i8, ptr %new` | 1,631 @27,536 |
| dead volatile i64 @8 / i8 @32 of `new` | 1,644 / 1,647 |
| dead volatile byte of the args copy `_45` | 2,100 @27,368 |
| empty `asm sideeffect "" "~{memory}"` (`black_box(())`) | 1,986 @27,344 |
| dead volatile 9 B copy / 7 B + 9 B copies | 1,467 / 1,479 |

For the dead byte load, the normalized post-opt IR of `execute` differs from main by that one line. So the -633 M is
llc alone: one extra dead `ldxb` renumbers slot indexes, and the greedy RA cascades into the flip.

Attempts to pin the placement, all on the collapsed bases:
- `llvm.expect.i1` true/false on every `br i1` of the pre-opt sweep (11) and execute (13) bodies on `c1a`: best 1,470
  (`ex/bs_c1a_*.jsonl`);
- the 660 `amount==0` weight (`pin660`): costs 114 M on main and does not restore `c1a`/`x3`;
- w17a06's single-edit generator (`gen.py`: vl, rr, bw, sw, bf, noalias, vs:fld; 906 edits) on `e79v`: best
  `vl:validate:28014` 1,767 @27,392 and `vl:execute:28969` 1,761. The best one **does** restore main's block layout:
  the frame/reg/jump-masked diff to main is only the intended E3/J1/C1 changes, 3,209 of 3,337 tokens. The exact loss
  is then register names and the frame shift from the two new allocas. 141 edits on `c1a`: best 1,574;
- pairs of the 24 best singles on `e79v` (276 runs, `ex/scr_e79v_pairs.jsonl`): none beats 1,767;
- `vl:validate:28014` is a volatile read of the `st.quote_locked` byte at 326, `read_volatile(&st.quote_locked)`. It is
  not a general pin (`ex/qpin.py`): main alone falls to 1,876, `c1a` reaches 1,511, `x3h` 1,887, the dead `new` probe 1,897
  and `j1v` 1,804. It is one more chaotic perturbation, which happens to put `e79v` back on main's layout;
- `mp.py` on `e79v` + `vl:validate:28014` against main: Mperm 2,012 vs 2,308, frame-masked LCS 2,377 vs 2,494. The
  remaining gap is register naming, not frame: a frame pass alone cannot recover it;
- `-tail-dup-placement=false` / `-enable-tail-merge=false` on both sides: no information (main itself loses 640 M
  without tail merge).

## 4. Conclusions for later lanes

- The original's E3/J1/C1 piece flow is reachable with marked constructs. `c1a` is a 5-line IR change that a C1-only
  shim (raw-pointer piecewise construction of the CPI argument) produces, and `e79v` adds the two volatile entry copies.
  But it is not separable from the rest of the function: main's RA basin and its layout of the sweep join are tuned
  for the lazy loads, and even a dead instruction at the CtoState site flips the layout.
- To use it you must re-tune the basin around it, as waves 13-17 did for main. A single nudge (`vl:validate:28014`)
  already restores the layout on `e79v`, so the starting point would be `e79v` + that nudge (M 1,767). Its
  frame-masked gap to main is still 117 tokens (Mperm 2,012 vs 2,308), so the work is mostly an RA-nudge search
  (weighted traps, volatile reloads), with a frame pass second (place e7/e9 where the original has them, at
  -0x658/-0x668, where main keeps target pieces). That is a multi-lane project, not a single landing.
- Ranking or screening structural candidates by exact M on main's basin will reject every one of them. Compare them with
  `tools/mdiff.py` (layout) and frame/reg/jump-masked region matches (`tools/regm.py`) first.

## Tools (lane-local paths; adapt `OUT`)

- `tools/ired.py ex/<set>.py [names]`: apply text edits to the slim pre-opt module, score with w17a06 `fx.run`.
- `tools/bsweep.py <slim.ll> <fnregex> <out.jsonl>`: `llvm.expect.i1` true/false on every `br i1` of one function.
- `tools/dis.py <fn.bin>`, `tools/rng.py <fn.bin> lo hi`: minimal sBPF disassembler for oracle blobs.
- `tools/mdiff.py a.bin b.bin [min]`: register/immediate-masked difflib runs between two blobs (shows block moves).
- `tools/regm.py <fn.bin>...`: per-region (E1..tail, w17a01 boundaries) original tokens matched, exact and masked.
- `tools/llcopt.py <m.ll> [llc args]`: re-run SDK llc on a slim post-opt module with extra llc options.
- `tools/split.py`: split `win.py show --full` output into window-offset listings.
- `ex/*.py`: every IR edit set measured here (`c1`, `c1v`, `x3`, `esc`, `pin`, `j1`, `e79`, `dead`).
