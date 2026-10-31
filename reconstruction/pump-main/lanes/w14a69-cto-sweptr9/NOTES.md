# w14a69-cto-sweptr9: swept -> Err-payload class / r9, priced with an exact coalescer-order MIR oracle (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
This lane continues dead lane w14a61-cto-sweptr9, which had no ledger rows and no PR (its uncommitted tools came from w14a06).
Angle: put `swept` (the sweep's Ok amount) into the Err-payload class and onto r9, as in the original.
Bases:
- 304b03a (0.65788 / 3,223 slots), used for the IR threading oracles;
- 39eb377 (#3386, 0.66477 / 3,230 slots), used for everything else.

Scratch is in `~/.cache/pumpfun-reconstruction/lanes/w14a69-cto-sweptr9/` (deleted at the end).
Ledger: approach `swept-coalesce`, keys `0x22a10-w14-{304b03a,39eb377}-sweptr9-*`.

**Result: no source change.** Even an ideal coalescer visit order, with the CFG left unchanged, costs 0.067. Pinning the class to r9,
the original's register, costs 0.19. The swept-r9 residual is a register-allocation consequence and does not unlock anything by itself.

## 1. Map on 39eb377 (raw-IR capture + `tools/rx.py`, `eq_main=true`; `tools/coal.py`, `tools/blk.py`)

| class | vreg | loads | reg | note |
| --- | --- | ---: | --- | --- |
| Err payload | `%1664` | 22 | r8 | the return block stores `[r4+8]` from r8 (the original uses r9) |
| swept (event `+184` store) | `%1633` | - | split, spilled `[r10-0x968]` | weight 9.9e-07, range 21232r..68096r |

Payload copies and the degree of each copy's block (`payload-copies-39eb377.txt`):
- `bb.270.bb88`, the sweep Err edge, copies `%1664 = COPY %287`, the sweep-result chain. It has 2 preds and 1 succ, degree 3.
  It is the IR `bb86`/`bb88` inttoptr block, and early tail-dup gives it the 2nd pred.
- `bb.339.bb65`, the post-sweep Err join (sharing CPI, pool CPI, the two emit/Clock Errs), copies `%1664 = COPY %362`.
  It has 4 preds and 1 succ, degree 5.

RegisterCoalescer visits blocks by loop depth, then pred+succ count, then block number (`coalescer-visit-order-39eb377.txt`).
It visits bb65 14th and bb88 184th. bb65 merges the post-sweep payload chain first, and that chain is defined before each CPI's tag branch
(`%1659 = COPY %355` at 63904r/63952r, where swept is still live). Later, bb88's merge fails with `interference at %1664:27@63952r`.

**This is the original's order reversed.** In the original, swept is in the payload class (`ldxdw r9,[0x828]` at 0x3c40, then the event stores r9 at 0x5030).
The post-sweep join keeps an unmerged copy, `mov64 r9, r1` at 0x54e0, and its tail-dup is at 0x55a8. Its preds are 4aa0 (sharing), 4e48 (pool), 54c8 and 5588.
The CPI payloads load into r1 at 4a80, 4e38, 54d0 and 5518 instead of straight into the class register.

## 2. New oracle: coalescer order without a CFG change (`tools/coalor.sh`)

w14a06's oracles reached the coalesced state only through CFG edits. Those edits re-lay blocks, so they mixed two effects. This oracle isolates the coalescer order:
1. `llc -stop-before=register-coalescer` writes MIR.
2. `tools/ufclass.py` reads the coalescer's `Success: A -> B` lines from the debug-llc log and lists the pre-coalescing vregs in swept's final class (31 on 39eb377).
3. `tools/mirren.py` renames them all to the payload vreg.
4. `llc -start-before=register-coalescer` finishes the build.
5. `tools/objscore.py` scores the result.

`objscore.py` re-biases r10+N outgoing-arg stores by -0x1000, because MIR does not serialize the SBF fixed-stack bias. With that fix the round trip
is exact: `tools/mirrt.sh rx/m1/m.ll mir/m1` gives 0.66477 with `eq_main=true`.

| oracle (39eb377) | swept in class | class reg | bytes | ratio |
| --- | --- | --- | ---: | ---: |
| main | no | r8 | 27,400 | **0.66477** |
| c1: ideal order (swept merged pre-coalescing) | yes | r6, after evicting the sharing tag `%59` | 27,408 | 0.59817 |
| c1 + `{r9}` asm pin at the event store | yes | r9 | 27,384 | 0.47678 |
| c1 + `{r8}` pin | yes | r8 | 27,376 | 0.45946 |
| `{r9}` pin alone (no coalescing) | no | r8 | 27,400 | 0.66477 (= main) |
| `{r8}` pin alone | no | r9 | 27,256 | 0.62631 |
| s1 (w14a47/w14a60: all 7 sharing AccountInfos `to_account_info()`) | no | r8 | 27,344 | 0.63638 |
| s1 + ideal order | yes | r6 | 27,352 | 0.58171 |

Per-0x800 matched tokens (`tools/frseg.py`, main → c1): plain, frame-masked, and frame+register-masked.
- 0x2800 / 0x3000 / 0x3800 / 0x4000: plain 178/157/174/107 → 128/89/137/70; frame-masked 203/181/204/143 → 203/180/171/108;
  FR 251/244/233/101 → 251/242/208/131.
- Totals: frame-masked 2,521 → 2,430 (**-91**), FR 2,796 → 2,806 (+10).

What the table shows:
- The coalesced code shape is slightly more original-like (FR +10 tokens, about +0.003). Examples: swept stays in a register through the post-sweep
  region, and the join copies become `mov r6,r1` at 0x54d8/0x55a0, the original's `mov r9,r1` sites.
- Register assignment loses about 91 tokens and the frame loses the rest. No frame repair can recover a deficit in frame-masked tokens.
- **Why r6:** with swept merged in, the payload class is the largest interval (16,992 against 4,336 on main). Greedy allocates it first and takes
  the first callee-saved register, r6, by evicting `%59`. In the original it ends on r9, which means three other classes
  (r6 = the reloaded tag / entry value, r7 = the return tag, r8 = the accounts pointer `%0`) were allocated before it.
- Forcing r9 with a copy hint makes the hinted class allocate first. The whole function then re-colours from the entry block
  (`mov r7,r5; mov r8,r1` instead of main's `mov r9,r5; stxdw [0x8f0],r1`): 0.477.
- MIR `preferred-register` hints are dropped. The debug log shows no `hints:` line for the class, so a pure hint oracle is not available.
- The "unlock" hypothesis (w14a01/w14a47/w14a60) is false on this main: s1 + ideal order is 0.582, below s1 alone (0.636).

## 3. CFG routes (post-opt IR, `edits/w14a69/post-opt/thr.py`, base 304b03a = 0.65788)

`thr.py` threads selected `bb56.i` preds straight into the sweep Err copy block, with phis added, to raise its degree.

| trial | threaded preds | swept in | class reg | bytes | ratio |
| --- | --- | --- | --- | ---: | ---: |
| t1 | TCF Err `bb82.i147` | no | r8 | 27,392 | 0.50936 |
| t2 / t3 | + PumpError `bb16.i115` (+ `bb62.i`) | yes | r6 | 27,392 | 0.49019 |
| t4 | TCF + seeds `bb60.i112` | yes | r6 | 27,392 | 0.47940 |
| t5 | TCF + token join `bb52.i123` | yes | r6 | 27,368 | 0.46133 |
| t6 | `bb16.i115` + `bb62.i` | yes | r6 | 27,408 | 0.59128 |
| t6 + `{r9}` / `{r8}` | | yes | r9 / r8 | 27,264 / 27,256 | 0.56044 / 0.53740 |

Even without coalescing, t1 loses 0.15 through block re-layout. CFG routes are strictly worse than the no-CFG oracle in section 2.

## 4. Source forms (raw-IR capture + rx + coal, `edits/w14a69/src/`)

| form | swept in | bytes | ratio |
| --- | --- | ---: | ---: |
| `swept={let r=(..).transpose();r?.unwrap_or(0)}` | no | 27,400 | 0.66477 (main tokens) |
| `match (..){Some(r)=>r?,None=>0}` | no | 27,400 | 0.66477 |
| `(swept,)=(..transpose()?.unwrap_or(0),)` | no | 27,400 | 0.66477 |
| `if let Some(r)=(..){r?}else{0}` | no (payload on r7) | 27,280 | 0.45969 |

These add to the ledger's 486 earlier swept rows, which cover gate spellings, `mut`, closures, scopes, and w14a06's f1-f7.

## 5. Conclusion and bounds

- Moving swept into the payload class is a coalescer-order effect: bb65, degree 5 and visited 14th, runs before bb88, degree 3 and visited 184th.
  Fixing the order needs bb88 at degree ≥5 or bb65 at ≤3, and both are CFG changes. Section 3 shows that every CFG change re-lays blocks and costs ≥0.07.
- Even a free, perfect order is worth -0.067 on 39eb377, because the merged class becomes the largest interval and takes r6.
  Getting it onto r9 means changing greedy's allocation order for three other whole-function classes, which no source form here controls.
- The bound is the FR-masked token count: c1 is only +10 tokens (about +0.003) above main even if every register and frame offset were repaired.
  That is not enough to pursue through a cascade this large.

Untried ideas (low plausibility):
1. Use `coalor.sh` as a filter for any future change to the whole-function classes (tag `%1665`, `%0`, the entry-r5 value).
   The question to ask is whether the merged payload class then lands on r9 without a pin.
2. A greedy-priority experiment would need a patched debug llc (a priority override for one vreg), and the shared llvm-dbg build must not be modified.
   It would need a private build tree.

## Tools (`tools/`, text only)

- New:
  - `coalor.sh <m.ll> <name>`: ideal-coalescer-order MIR oracle;
  - `mirrt.sh <m.ll> <prefix> [sed]`: exact MIR round trip with an optional sed edit;
  - `mirren.py`: renames vregs in a MIR body;
  - `ufclass.py <ra.log> <vreg>`: union-find of the coalescer's merges, giving the pre-coalescing members of a class;
  - `objscore.py <o>...`: ratio, slots and eq_main, with the SBF fixed-stack re-bias.
- Fixed: `coal.py` finds swept's event store at `+184` on any stack-coloured slot (the event alloca now merges into `_55.i94`/`_55.i95`).
- The other tools and `edits/post-opt`, `edits/src` come from w14a06 and target the 308b545 IR names.
- `payload-copies-39eb377.txt` lists the payload copies with their block degrees. `coalescer-visit-order-39eb377.txt` lists the block visit order.
