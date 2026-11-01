# w17a24-shim-annfence: `llvm.annotation` as a value fence that survives CodeGenPrepare (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Wave 17 SHIM track. Ledger approach `annfence`, keys `0x22a10-w17-<sha7>-annfence-<item>-v1`
(probe row `0x22a10-w17-ac37d74-plan24-annprobe-v1` from the replanner).

Bases: main 4d09af488 (0.68514, M 2,287, oracle sig `85d273bcd66a`) for calibration and beam 1; main aab087f32
(w17a19 lifetime shims, 0.68724, M 2,294, sig `60f85431781c`) for beam 2; main 53ec7fb53 (0.68754, M 2,295, sig
`61dcfe87f489`; later mains to e0c7eba85 change only `programs/pump/recovered/`) for beam 3 and the combination screens;
w17a16's outline base WXvp on 53ec7fb (M 2,300 @27,328) for the repay prices.

**Result: notes only, no gain.** The construct is calibrated byte-identical and its fold table is below. Four beams
(13,000+ single edits, pre- and post-opt) and every combination screen (additive combos, greedy with repay, off-size x
repay pairs, neutral pairs, triples, a positional-slots tie-break) stay at or below main at 27,400 B, and annotation
knobs do not close the outline base's 72 B repay.

## 1. The construct

```rust
extern "C"{#[link_name="llvm.annotation.i64.p0"]fn ann(v:u64,s:*const u8,f:*const u8,l:u32)->u64;
           #[link_name="llvm.annotation.i1.p0"]fn ann1(v:bool,s:*const u8,f:*const u8,l:u32)->bool;
           #[link_name="llvm.annotation.i8.p0"]fn ann8(v:u8,s:*const u8,f:*const u8,l:u32)->u8;
           #[link_name="llvm.ptr.annotation.p0.p0"]fn pann(p:*const u8,s:*const u8,f:*const u8,l:u32,a:*const u8)->*const u8;
           #[link_name="llvm.sideeffect"]fn sidefx();}
```

Declared on line 8 (no new line; `link_llvm_intrinsics` is already on lib.rs line 1), string arguments
`core::ptr::null()`. Both annotation intrinsics are `IntrInaccessibleMemOnly`: `opt -O3` keeps them even with an unused
result and does not CSE two identical calls. They survive CodeGenPrepare and are dropped by SelectionDAGBuilder
(`setValue(&I, getValue(operand))`), so they emit no instruction, no section and no static. `llvm.bpf.passthrough`
(w17a15) is `IntrNoMem` and is deleted by `BPFCheckAndAdjustIR` before CodeGenPrepare.
Never use `llvm.ssa.copy` (SIGSEGV in IPSCCP).

## 2. Calibration (main 4d09af488)

| variant | slim oracle | real build (`measure.sh`) |
| --- | --- | --- |
| main (capture `main0`) | M 2,287 @27,400, sig `85d273bcd66a` | 0.68514, 3,092 slots |
| cal0: the five declarations only | identical (rustc emits no declaration for an unused extern) | - |
| cal2: + `quote_locked:unsafe{ann1(quote_locked,N,N,0)}` in the CtoState literal (same-block use, IR cell `ai:execute:28869`) | sig `85d273bcd66a` | **0.68514, 3,092 slots, 27,400 B, 1034/1034, zero losses; masked admin_cto sig `85d273bcd66a` = the fresh main build** |

So a neutral annotation, including its MIR Call terminator, is byte-identical. (The `current-baseline` had already moved
to 638fce2a3 when cal2 was scored, which is why the cal2 file sha differs from that baseline; the admin_cto bytes equal
the main0 oracle exactly.)

### Fold table (`tools/zaprobe.rs` + the replanner's `zfprobe.rs`, identity rustc, sbpf-solana-solana, -O3, ~1 s)

| fold | plain | `ann`/`pann` | `llvm.bpf.passthrough` | probe |
| --- | --- | --- | --- | --- |
| CGP address-mode sinking: address formed before a call, load after it in one arm | load hoisted above the branch, `ldxdw [r7+40]` | `add64 r6,40` (MachineSink puts it in the arm) then `ldxdw [r6+0]` | load stays in the arm, `ldxdw [r6+40]` | l0/l4/l5 vs l1 |
| one GEP used by loads in both arms | `[r6+40]` hoisted, `[r6+48]` in the other arm | ONE address register `add64 r6,40`, `[r6+0]` / `[r6+8]` per arm | (as plain after the pt is removed) | g0/g1 |
| field address passed as a call argument (memcmp/memcpy-like) after an earlier call | `add64 r6,24; mov64 r1,r6` after the call | identical | identical | p0/p1/p2, mm0/mm1 |
| compare before a call, branch after it (BPF fuses cmp+br) | `jlt r7,r6` after the call | identical (`ann1` on the i1) | identical | k0-k2, b0/b1 |
| compare before a call used as a VALUE after it | `jlt` + `mov 1/0` phi, `and` | identical with `ann1`; `ann(i64)` of the zext keeps the arm as a branch (no `and`) | - | c0/c1/c2 |
| zext of a loaded byte, used after a call | `add64 r6,r0; mov64 r0,r6` | operand order flips: `add64 r0,r6` | - | e0/e1 |
| `llvm.sideeffect` in an otherwise speculatable arm | arm speculated into a select (`add64 r2,r1`) | branch kept (`jeq r2,0; add64 r1,1`) | same as pt b1 | s0/s1 |
| unused-result `ann` on a load before a call | load before the call | identical (MachineSink still decides) | (a pt with no use is deleted) | u0/u1, zuprobe u1 |
| two identical annotations | - | both kept (no CSE) | CSE'd unless `seq` differs | zuprobe u3 |

Mechanism summary: the annotation only blocks address folding when the annotated value is USED IN ANOTHER BLOCK than
its definition (CopyFromReg boundary). Within one block ISel maps the result straight to the operand node and the DAG
combiner re-folds the offset.

## 3. Beam 1 (main 4d09af488, slim pre-opt oracle, `tools/anngen.py` + `tools/screenp.py`)

3,270 single edits over validate/execute/wallet/sweep: `ai` (int annotation after every iN def, all uses rerouted, 646),
`ap` (ptr annotation after every non-alloca GEP/ptr def, 871), `ax` (only uses outside the def block, 11: pre-opt IR
keeps nearly every cross-block value in an alloca), `au` (unused-result anchor after the def, 1,517), `se`
(`llvm.sideeffect` at every block head, 225).

| family | singles | change code | at 27,400 B | best |
| --- | ---: | ---: | ---: | --- |
| ai | 646 | 355 | 46 | +1 @-8 B (`ai:validate:27949`, the 312 compare i1) |
| ap | 871 | 341 | 22 | +1 @-8 B (`ap:execute:28845/28853`, accounts pointer of CtoState mayhem / holder_reward) |
| au | 1,517 | 477 | 24 | +1 @-8 B (`au:execute:28904`, unused ann on execute's `holder=hopt==Some(true)`) |
| ax | 11 | 8 | 0 | -18 |
| se | 225 | 67 | 2 | 0 @0 B |

No single is above main at 27,400 B. 400 size-neutral additive combos (`tools/combo2.py`, k <= 4, predicted up to +2):
best 2,287 = main.

### Which fold class? (passthrough twins, `tools/ann2pt.py` + `tools/classify.py`)

Every changed `ai`/`ap`/`ax` cell (618) was re-run with `llvm.bpf.passthrough` at the same IR point and the same
rerouting. If the twin is byte-identical to main, the cell's effect is CodeGenPrepare/ISel only (the new fold class);
if the twin reproduces the cell's signature, it is an opt-level fold that passthrough already reaches.

| class | cells | best (dM, dB) |
| --- | ---: | --- |
| CGP/ISel only (pt twin byte-identical) | 236 (177 `ap`, 59 `ai`) | 0, +8 B |
| opt-level, pt reproduces it exactly | 247 (159 `ai`, 83 `ap`, 5 `ax`) | +1, -8 B (all three +1 cells) |
| both differ | 135 | -6, +16 B |

A post-opt beam (`tools/anngen_post.py` + `tools/screen_post.py`, llc only, 1,736 edits on the optimised execute body:
825 GEPs, 240 ptr loads, 180 compares, cross-block-only reroutes) isolates the CGP/ISel class completely: only 146
change code and the best is -1 M. The new fold class is real but flat on admin_cto as a single lever.

## 4. Targeted: the original's early `&curve.creator` (orig 0x22d60)

The original spills the curve pointer and forms `r9 = curve+8` right after the quote_locked default memcmp
(`stxdw [r10-0x910],r9; add64 r9,8`), then copies the creator from `[r9+0..0x18]` after quote_locked. That is exactly
the annotation's shape (address formed in an earlier block, CGP cannot sink it). IR (main aab087f): a GEP `curve+8` on
the quote_locked curve pointer plus `ptr.annotation`, placed after the curve load, after the default memcmp, at the
use site, or on the base pointer, with the creator memcpy source rerouted (`spec/e1a..e1d`): all four give the same
output, **M 1,701 @27,552**. Reusing the quote_locked curve pointer keeps it live across the memcmp and
`slice_contains` calls, and the RA renames from the first instruction (accounts pointer r8 -> r6). Not reachable as a
single fence.

## 5. Beams 2 and 3, and the combination screens

Main moved three times during the lane (4d09af4 -> 638fce2 -> aab087f -> 53ec7fb; the last later merges only touched
`programs/pump/recovered/`). Every cell is base-specific, so the beam was re-run on each new main.

| base (oracle M @27,400) | singles | best single at 27,400 B | combination screens | best at 27,400 B |
| --- | ---: | --- | --- | --- |
| 4d09af4 (2,287) | 3,270 | 0 | 400 size-neutral additive combos (k <= 4) | 2,287 = main |
| aab087f (2,294) | 3,270 + 1,159 pt/weight/volatile-field | 0 | greedy forward selection with repay pairs (27 sig-distinct candidates); 45 off-size improver x exact-repay pairs | 2,294 = main |
| 53ec7fb (2,295) | 3,270 | 0 (17 cells, 11 signatures, tie) | 105 neutral pairs; 50 shrink x grow pairs; 90 triples (tie pair + neutral cell) | 2,295 = main |

Per family (53ec7fb): `ai` 646 / 355 change code / 47 at 27,400 B; `ap` 871 / 341 / 20; `au` 1,517 / 477 / 24;
`se` 225 / 67 / 3; `ax` 11 / 8 / 0. The off-size +1 cells of the earlier bases (the 312 compare i1, the unused anchor on
execute's `holder`) are -1 @-8 B on 53ec7fb. A shrink cell plus a grow cell is super-additive by 2 (two -1 cells give
2,295) but never above main.

**Positional slots tie-break.** land.py ranks admin_cto by (size, -ratio, slots), so a tie in M with fewer differing
slots would land. Oracle masked slots for main 53ec7fb are 3,095 (target_metric 3,096); all 179 tie candidates have
3,095-3,108. The annotation ties are register/schedule swaps inside slots that already differ.

Free repay knobs on main (aab087f): annotating the `From<PumpError> for u32` error-code results at 306/307/312
(codes 89, 30, 19) adds +8 B each at 0 M; every other error-code annotation costs 7-19 M. On 53ec7fb the same three
cost 1 M each.

## 6. The outline base (w17a16 WXvp): annotation repay prices

w17a16's outline + original-validate-order base WXvp is 2,300 @27,328 on 53ec7fb (sig `28877df3c8b1`; my capture of
WXvp plus the annotation declarations reproduces it exactly). It needs +72 B at a cost of at most 4 M (it has two fewer
lddw, so it must reach 2,296). Annotation singles on WXvp (412 screened, the `ai` family through wallet):

| cell | dM | dB | what |
| --- | ---: | ---: | --- |
| `ai:wallet:31109/31111` | **+1** | +8 | ann on the `collection_native` memcmp byte (conflicts with w17a16's `cnat` knob, which rewrites the same compare) |
| `ai:wallet:31038/31039/31067/31074/31082/31088` | -1 | +24 | ann on the wallet `token_frozen(..)?` Result tag (the `?` residual cells w17a16 found; no source spelling) |
| `ai:validate:27883` | -3 | +8 | ann on the 306 error code (89) |
| `ai:validate:28335` | -4 | +8 | |
| other error codes (91/83/84/90), CtoState flag bytes | -7..-10 | +8 | |

The only additive +72 B assembly at >= 2,296 is `31109 + 31038 + cnat` (predicted 2,297), and it is not realisable:
31109 and `cnat` act on the same compare and 31038 has no source spelling. So annotation knobs do not close the
outline repay either.

**Re-check of a lifetime lead in w17a16's screens.** Their `es_vst` llc-only screen shows an extra lifetime start of
`%sharing_update.sroa.6` (the 32 B payload piece) at the head of validate's `bb7.i` at M 2,302 @27,400. That base
(`lt/v_st.ll`, sig `d68881a49c42`) is n6_v plus the unsafe early END of `st` at `bb31.i`. On every valid base the same
edit collapses: n6_v 2,292 -> 1,910, n7_a 2,294 -> 1,912, n7_c 1,912, n7_vp 1,910, WXvp 2,300 -> 1,918 @27,328. Not a lead.

## 7. Conclusion and leads

- `llvm.annotation` / `llvm.ptr.annotation` are a correct zero-footprint shim (calibrated byte-identical) and reach a
  fold class nothing else reaches (CodeGenPrepare address-mode sinking; the only visible shape is an address formed in
  one block and used as `[rX+0]`/`[rX+8]` in another). On admin_cto that class is flat: 236 CGP/ISel-only cells, best
  0 M; the post-opt beam best is -1.
- The original's three unmatched address-in-register shapes (`addrscan2.py`) are the PDA-first memcmp argument
  (0x22bc8), the early `&curve.creator` (0x22d68, collapses to 1,701, section 4) and the `new` payload pointer of the
  7/9-piece copy (0x23620, the newpieces structure). None is a single-fence target; all three need the original RA basin.
- The opt-level effects of annotation equal passthrough's (247 cells reproduce exactly). The annotation-only
  opt-level effects (unused anchors that block one-use folds, no CSE) are the `au` family: flat too.
- Useful for other lanes: the annotation error-code knobs are size knobs (+8 B each) whose price depends on the base
  (free on aab087f at 306/307/312, -1 on 53ec7fb, -3 on WXvp). `ai:wallet:31109` (+1 @+8 B on WXvp) is the cheapest
  positive repay found for the outline base, if its compare is left to it instead of `cnat`.

## Tools (`tools/`, experiment only)

- `anngen.py <slim.ll> <edits.jsonl> [families]`: the annotation families above, in w17a06's edit format.
- `anngen_post.py`, `screen_post.py`: the same on post-opt IR, llc only.
- `screenp.py`: a process-pool version of w17a06 `screen.py` (the thread version is GIL-bound at ~60 edits/min under
  load; this one runs ~100-150/min with 6 workers) that skips the LCS when the output equals the base signature.
- `greedyp.py`: greedy forward selection at 27,400 B with repay pairs for off-size improvers.
- `combo2.py`: size-neutral additive subsets of signature-deduplicated cells.
- `ann2pt.py`, `classify.py`: passthrough twins and the fold-class split.
- `irx.py`: hand IR edits (insert/replace by line) scored with the slim oracle; `spec/e1*.json` are the section-4 edits.
- `pairs.py` (off-size improver x exact repay), `npairs.py` (k-subsets of sig-distinct neutral cells), `slots.py`
  (oracle M plus masked positional slots for the land.py tie-break).
- `addrscan.py`, `addrscan2.py`: original vs candidate `mov64 rX,rY; add64 rX,imm` / non-frame `add64` address
  formations with LCS alignment status.
- `zaprobe.rs`/`zaprobe.sh`: the fold-table probe.
- The oracle itself (`capraw.py`, `preslim.py`, `fx.py`, `oracle.py`, `modparse.py`, `screen.py`) is in
  `~/.cache/pumpfun-reconstruction/lanes/w17a06-shim-irbeam/tools/`; copies with this lane's paths are in
  `~/.cache/pumpfun-reconstruction/lanes/w17a24-shim-annfence/tools/`.
