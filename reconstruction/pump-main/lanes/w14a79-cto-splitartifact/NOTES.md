# w14a79-cto-splitartifact: register-allocator split artifacts as a live-set signature (admin_cto::execute, 0x22a10)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `0d04cf460` (0.66507, 3,228 slots, 1034/1034). Ledger approach `splitartifact`, keys
`0x22a10-w14-0d04cf4-splitartifact-*`. Scratch: `~/.cache/pumpfun-reconstruction/lanes/w14a79-cto-splitartifact/`.

**Result: notes only, no source change.** The artifact map, the register-miss attribution and the IR probes all agree
with w14a45-cto-acc108 (#3345). The original spills three long-lived sweep values right after the
`holder_creator_vault` key compare, and ours keeps two of them in callee-saved registers across the TCF clone run.
Forcing the original's spills in IR does not fix the clone-run register names. Every freed register is refilled
(musical chairs), and L1 drops on main and on the faithful first-clone base.

## 1. Tools (`tools/`, experiment only)

| tool | what it does |
| --- | --- |
| `bdis.py fn.bin [lo hi]` | minimal SBF decoder (reads/writes per insn), used by the tools below |
| `artifacts.py` / `dead.py fn.bin...` | CFG register liveness (Rc-overflow `jne rX,1,+1; call abort` is treated as noreturn). Lists **dead stack reloads** (`ldxdw rX,[r10-s]` with rX dead) and **same-slot reload+re-spill pairs** (`ldxdw rX,[s]; stxdw [s],rX`), each tagged with the Rc-increment block it sits in. `reaching()` gives CFG reaching defs. |
| `artmap.py <rxdir> [--lo --hi]` | names every artifact's spilled value: ours directly, through lr.py's unshared-frame twin (`-no-stack-slot-sharing`, debug llc); the original through n2-aligned orig->ours slot votes. Writes `artmap.json`. Caveat: orig names come from the nearest aligned access of a *shared* slot, so treat them as approximate (example below). |
| `blame.py fn.bin [lo hi]` | for each **register-only miss** (L2-equal, L1-different aligned pair), it blames the occupant: the reaching def of the orig's register in ours (or of ours' register in the orig) when that register is live through the aligned insn. |
| `occ.py`, `press.py` | callee-saved occupancy spans and per-Rc-block live-register counts, orig vs ours |
| `regmiss.py` | register-only misses grouped by (orig reg -> ours reg) |
| `spillprobe.py in.ll out.ll %v` | IR probe "spill at def": entry alloca, store after def, a load before every use outside the def block |
| `llcx.py name m.ll [edits]` | llc on a post-opt slim module + score + `fmr.py` L0/L1/L2 per 0x800 chunk |
| `sbs2.py fn.bin lo hi` | L2-aligned side-by-side listing, both sides decoded by bdis |
| copied | w14a74's `fmr.py cls.py rx.py rx_lib.py capraw.py capvar.sh fdelta.py sbs.py`, w14a03's `lr.py` |

## 2. Artifact map (main 0d04cf4; `data/dead-orig-vs-0d04cf4.txt`, `data/artmap-0d04cf4.txt`)

The original has 31 artifact sites and ours has 22. In the clone runs (0x2800-0x4600):

| orig site (Rc block) | orig slots (value) | ours site | ours slots (value) |
| --- | --- | --- | --- |
| 0x2ff8 (rc 0x2fc0) | -0x970 (clone1 owner `%128`) | 0x2fd8 (rc 0x2fa8) | -0x990/-0x950 (`%155` key of accounts+32, `%128`) |
| 0x30b0-0x30c0 (rc 0x3080) | -0x9b0 `%155`, -0x978 `%137` (key of accounts+0), **-0x8e0 = `&a.holder_creator_vault`** | 0x30f8 (rc 0x30c8) | self re-spill -0x8e8 = sharing_update tag `%59` |
| 0x3110 (rc 0x30f8) | -0x988 (`%129` clone1 key) | 0x31b8 (rc 0x3188) | -0x9a8 `%164`, -0x980 `%146`, -0x968 `%137`, -0x970 **`%129`** |
| 0x31e8-0x31f8 (rc 0x31b8) | -0x9a8 `%164`, -0x9a0 `%146`, -0x990 `%137` | 0x3228 (rc 0x3210) | -0x988 **`%130`** (clone1 lamports Rc ptr) |
| 0x3b88, 0x3bb8 (sweep exit) | -0x8e0 (holder ref) | 0x3b68 / 0x3cd0 | -0x8e8 dead + self (tag) |
| 0x44b8/0x44c8, 0x4540-0x4550 | sharing clone keys `%301`, `%334`, `%324`, `%304`; tag self re-spill -0x950 | 0x4568-0x4588 | `%334`,`%324`,`%304`,`%300`,`%291` |

`%127` is the TCF CpiContext program clone (accounts+88). Its key, lamports and owner are `%129`/`%130`/`%128`.
The `%NNN` names are vregs at the start of greedy on main 0d04cf4. The artmap prints orig -0x8e0 as `%59` (the tag),
because ours -0x9b8 holds both the tag and `%121` = `&holder_creator_vault`. Reading the code settles it: orig 0x1f38-0x1f48
spills `r8+264` to -0x8e0, and ours spills `%121` to -0x9b8 at 0x20a0/0x3090/0x5938.

Readings:
- Both sides' artifacts name the same set of TCF clone keys (`%137 %146 %155 %164`), live through the Rc blocks of
  later clones, but in different blocks. The original groups two keys plus the holder ref per block. Ours groups four
  keys plus clone1's key and lamports in one block. **Ours-only:** `%129`/`%130` (the CpiContext program clone's key and
  lamports are spilled and live-through in ours, but held in r9/r7 in the original, orig 0x26c8/0x2698 -> spilled at
  0x2950/0x2958). **Orig-only:** the holder ref (in ours it sits in r6, so no artifact).
- Sharing tag: the original's tail artifacts are on -0x950, ours' on -0x8e8 (same value, `%59`; w14a03 already saw the
  pairing). Ours has 4 self re-spill pairs of it (0x30f8, 0x3cd0, 0x5940, 0x5b18) and the original has 3 (0x1d48, 0x44c8, 0x5b30).

## 3. Register-miss attribution (`data/blame-0x2800-0x4000-0d04cf4.txt`, `data/blame-all-0d04cf4.txt`)

In 0x2800-0x4000 there are 712 L2-matched tokens and **160 register-only misses** (0x2800: 50, 0x3000: 66, 0x3800: 44).

| blame | misses |
| --- | ---: |
| ours occupies the orig's register | 120 |
| orig occupies ours' register | 26 |
| free (pure assignment choice) | 14 |

Top ours occupants (0x2800-0x4000):

| ours occupant | value | misses | original |
| --- | --- | ---: | --- |
| r6 <- 0x1f10 `add64 r6,264` | `&a.holder_creator_vault` (`%121`) | 22 | spilled at def (0x1f48 -> -0x8e0); dead reloads 0x30c0/0x3b88/0x3bb8 |
| r9 <- 0x1d30 `ldxb r9,[r1+35]` | `ctx.bumps.creator_vault` (argpromoted `%ctx.val57`) | 18 | loaded into r7, spilled at 0x1f70 (-0x910) |
| r8 / r5 <- `[r10-0x8e0]` | accounts pointer | 10 + 10 | r8 to 0x30e8, then reloaded from -0x8d8 per use (0x3128, 0x3218, 0x3b80) |
| r0 <- 0x3308 `mov64 r0,r5` | clone temp | 13 | inside-run naming |
| r6 <- 0x3d58, r5 <- 0x3208, ... | clone pieces | 47 | inside-run naming |

The three values that the original's artifacts and spills name (holder ref, bump, accounts pointer) account for
**60/160 = 37.5%** of the clone-run register misses. Ours-occupancy of any kind accounts for 75%. Function-wide there
are 395 register-only misses: 252 ours-occupant, 78 orig-occupant, 65 free.

Pressure (`press.py`, mean live registers on L2-aligned insns in 0x2600-0x3600): orig 7.21, ours 7.82. Ours carries
r6 (holder ref) and r9 (bump) through the first half of the TCF run, where the original has 6-7 live registers.

## 4. Priced live-set probes (post-opt IR + llc, `llcx.py`; L0/L1/L2 = plain / frame-masked / frame+reg-masked ratio)

| probe | bytes | L0 | L1 | L2 | clone-run reg misses | note |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| main 0d04cf4 (eq_main) | 27,400 | 0.66507 | 0.70132 | 0.78310 | 160 | |
| tagmem: sharing tag in a volatile alloca | 27,312 | 0.62356 | 0.67817 | 0.77059 | | 0x2800/0x3000 chunks L1 195/174 -> 176/151 |
| sp328: spill `&holder_creator_vault` at def | 27,384 | (frame) | 0.68355 | 0.77974 | 160 | native takes r6 (0x1dc8) |
| spb: spill bump at def | 27,424 | (frame) | 0.68004 | 0.77736 | | |
| sp2: holder ref + bump | 27,432 | (frame) | 0.66826 | 0.77695 | | native then stays in r9 |
| sp3: holder ref + bump + native (all original head spills) | 27,448 | (frame) | 0.66298 | 0.75905 | 167 | clone1 key now r9 like orig 0x26c8 |
| tai: source, TCF program = `a.pump_amm.to_account_info()` | 27,416 | 0.64241 | 0.68733 | 0.78077 | 177 | the original first-clone shape |
| tai + sp3 | 27,432 | (frame) | 0.65539 | 0.76707 | 213 | pressure now matches orig (7.06 vs 7.20); clone1 key spilled at once (r4) instead of held in r9 |

Each probe's alloca shifts the frame, so judge it by L1/L2, not L0. None is L2-neutral with a rising L1, so none passes the screen.

## 5. Conclusion and next ideas

- The split artifacts show which spilled values are live through each Rc block. The difference that matters is
  three head values (holder ref, bump, native), which the original spills right after the dest compare and ours holds.
  It is not source-reachable. Binding, moving or re-reading these values folds back (w14a45: `hcv` binding and bump
  hoist are byte-identical, `&&Context` = b1 -0.045), and the IR spills lose L1.
- The remaining clone-run naming is decided inside the run. With the original's pressure profile reproduced
  (tai+sp3), ours still spills clone1's key at once where the original holds it in r9 until 0x2958. A lever would have
  to change the clone pieces' spill weights: their use counts or where their final stores sit. The TCF literal and
  field-order space is exhausted (w14a17, w14a23, w14a43, w14a72).
- Next: run `blame.py` on future bases to see whether a candidate removes the r6/r9 head occupants without growing
  clone-run blame. `press.py` per Rc block is a cheap pre-screen for literal or order variants: a candidate should bring
  0x2600-0x2e00 down to 6-7 live registers without the trio IR spills.
