# w17a21-shim-sweepdup: per-exit post-sweep Result test (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Wave 17 shim track.
Base: main ac37d7415 (#4019): 0.68424, M 2,284, 3,313 slots, 27,400 B, Pump Main 1034/1034. The lane started on 8330455eb
(0.68244) and merged ac37d74 before the first trial; every number below is on ac37d74.
Ledger: approach `sweepdup`, keys `0x22a10-w17-ac37d74-sweepdup-<item>-v1` (14 rows).

`M` = scorer matched tokens. `m1`/`m2`/`m3` = the same difflib count with r10 frame offsets masked / plus jump offsets /
plus registers (`tools/skel.py`; main is m1 2,358, m2 2,530, m3 2,805). `Mperm`/`Mhc` = w17a06 `mp.py` (best legal
spill-slot relabel / plus vote climb).

**Result: notes only. The angle's kill test is met: every per-exit form is below main, including its RA-forced and
spill-relabelled bounds.** The angle did find the ordinary-source form of the original's sweep-exit join shape (section
3), an exact placement fix for it in IR (section 3), and a skeleton on which the newpieces and faithful-tail leads no
longer collapse (section 4). What blocks landing is register naming, not layout (section 5).

## 1. The sites

| site | original | main ac37d74 |
| --- | --- | --- |
| 648 with_pubkeys exit | 0x2490 `ldxdw r9,[-0x7c8]; ldxdw r7,[-0x7d0]; ldxdw r1,[-0x950]; jne r7,2,exit; ja post` | 0x2450 `ldxdw r3; ldxdw r7; ja test` |
| 660 CtoSharedVaultFrozen | 0x25f8, the same copy | 0x25a8, the same jump |
| 719 CtoSharedVaultFrozen | 0x2220 `ldxdw r9; ldxdw r7; ja 0x3c58` (into the shared test, after its r1 reload) | 0x21e8 `ldxdw r3; ldxdw r7; ja test` |
| Rent::get Err (From) | 0x3c38 call, falls into the shared test 0x3c40-0x3c60 (`.. ldxdw r1,[-0x950]; ldxdw r6,[-0x8f8]; jne r7,2,exit`) and the post chain 0x3c68 | 0x3c00 call, falls into the shared test 0x3c18 (`jne r7,2`), then `stxdw [-0x968],r3` spills the payload |
| token_frozen / token_raw_amount `?` Err (AMM part) | threaded: `ja 0x6360` = `ldxdw r9,[-0x2c8]; ja exit` | `ldxdw r3,[-0x2c8]; ja test` |
| TCF CPI `?` Err | threaded: `ldxdw r9,[-0x7e8]; ja exit` | `ldxdw r3,[-0x7e8]; ja test` |
| token path Ok(amount) | threaded: 0x60f0 `ja post` (with the r6/r1 reloads) | through the Ok-join copy of the test (0x5af8) |
| return block payload | r9 (22 of 24 jumps load r9 directly) | r8 via `mov64 r8,r3` trampolines |

The 648 site at 0x2490 is what the task text calls the "native exit", and the 0x3c40 copy is the Rent::get Err block's
fallthrough into the shared test (w15a31 named them the same way).

Main's MIR: sweep.exit (the test) has two preds, the Err join bb60 (648, 660, the three AMM `?` Errs and the vsigner
Err join bb57) and the Ok join bb53 (native returns, built by `.map(|()|amount)`). Early tail-dup copies sweep.exit into
bb53 and merges it into bb60, so main has the test twice (0x3c18 and 0x5af8) and never in 648/660.

## 2. IR bounds on main (post-opt slim module, llc only; `tools/dup2.py`, `tools/j60.py`)

| form | what | M @ bytes | m3 | note |
| --- | --- | --- | ---: | --- |
| main | | 2,284 @27,400 | 2,805 | Mperm 2,310, Mhc 2,318 |
| d648 / d660 / d2 | test copied into 648 / 660 / both, `jeq` polarity (Err block falls through) | 2,231 / 2,281 / 2,230 @27,400-27,408 | | jeq polarity moves the 648 chunk to the function end |
| **n2** | copies in 648 + 660 with the original's polarity (`jne r7,2,err; ja post`), Rent-Err pred stays the shared test's fallthrough | **2,282 @27,416** | 2,806 | all three sites have the original's shape; payload r3 at the copies, one `mov64 r8,r3; ja exit` trampoline (+16 B = the two `jne`) |
| n3 / nrent | n2 + a copy into the Rent-Err pred / that copy alone | 2,255 / 2,256 | | the original keeps that site as the fallthrough |
| n2 + RA forces (private RAPRIO llc, sticky) | copy payload 1744=r9 / return payload 1671=r9 / both / 1744=r8 (no trampoline) | 2,027 / 2,246 @27,328 / 2,246 / 2,236 @27,400 | | payload r9 is below main in every force |
| thread3 / n2+thread3 / n2+thread(64,86) / n2+thread(84) | the AMM `?` Err preds routed straight to the error exit (as the original) | 1,633 / 1,701 / 2,106 / 1,760 | | MBP cliff (w15a31 d1): the 713-insn sweep body moves |
| **o3** | sweep.exit's test folded into bb60 and bb53 (`j60`), bb57 laid out right before bb60, so early tail-dup copies bb60+test into 648/660/AMM Errs and merges it into bb57 | 1,967 @27,424 | **2,863** | +58 m3, all in C1; Mperm 2,157, Mhc 2,189 |
| o3 + payload class 282=r9 | | 2,076 @27,384 | 2,854 | m1 2,260 < main's M |
| o2 | o3 + the AMM `?` Errs threaded | 2,008 @27,408 (r9 forced: 2,127 @27,336) | 2,802 | |
| j60 alone (no bb57 move) | | 1,658 @27,456 | | bb60+test is also copied into bb57 |

`n2` is the closest bound to main: per-exit copies are neutral in exact tokens (the 10 tokens that change are all jump offsets), because
the copies carry r3, not r9, and no `ldxdw r1,[-0x950]`. Nothing beats main at 27,400 B, so step 2 (source
realisation with marked steering constructs) was not built as a landing candidate.

## 3. The ordinary-source form of the original's join shape: `s_nat1`

Native tail, line 664:

```rust
// main
(if amount>0{ensure_rent_exempt(..)?;transfer_native(..)}else{Ok(())}).map(|()|amount)}else{
// s_nat1
if amount>0{ensure_rent_exempt(..)?;transfer_native(..)?;}Ok(amount)}else{
```

Post-opt IR of `s_nat1` (capture `fx/s_nat1/m.ll`):
- sweep.exit has exactly three preds: 648, 660 and the inner vsigner-scope Err join bb58 (the original's shape);
- JumpThreading threads the Ok returns (bb48, bb42, native bb91/bb95) straight to the post chain (`sweep.exit.thread`)
  and the three AMM `?` Errs (bb65, bb85 TCF, bb87) straight to the error exit (`sweep.exit.thread301`), which is the
  original's threading at 0x60f0, 0x6360 and after the TCF CPI;
- early tail-dup copies the test into 648 and 660: `ldxdw r6,[-0x7c8]; ldxdw r7,[-0x7d0]; jne r7,2,exit; ja post`, and the
  719 site jumps into the shared test (`ja 0x3c18`), all as in the original except r6 for r9 and the dead r1 reload.

As built it collapses: **M 1,295 @27,424** (m3 2,416). The cause is the IR block order. The native-arm blocks (bb91, bb90
Rent Err, bb35, bb95, bb94, bb96) sit between bb58 and sweep.exit, so sweep.exit has no fallthrough pred, is copied into
bb58 as well, and MBP puts a 462-insn native/token chunk between the TCF CPI and the shared test.

Moving bb58 right before sweep.exit in the post-opt IR (`pipe.MV58`) restores the original's layout (the Rent-Err call
falls into the shared test, which falls into the post chain at 0x3c20):

| form | M @ bytes | m1 | m3 | Mperm / Mhc |
| --- | --- | ---: | ---: | --- |
| main | 2,284 @27,400 | 2,358 | 2,805 | 2,310 / 2,318 |
| s_nat1 + MV58 | 2,114 @27,384 | **2,363** | 2,859 | 2,198 / 2,227 |
| s_nat1 + MV58, payload class 284=r9 | 2,110 @27,248 | 2,241 | 2,849 | |
| s_nat1 + n1 + MV58 (`h_n1`) | 2,177 @27,320 | 2,287 | 2,862 | |
| s_nat1 + evd + n1 + MV58 (`h_evdn`) | 2,180 @27,296 | 2,289 | 2,864 | |
| s_nat1 + m2hdn + MV58 (`h_tail`) | 2,030 @27,168 | 2,122 | 2,854 | |

No source spelling found for the MV58 placement:
- every bool spelling of the arm order (`if !native`, `==true`, `!=false`, `match native{true/false}`, `{false/true}`) is
  byte-identical to s_nat1 (MIR normalises the switch); `native==false` gives 1,295 @27,448; `match native as u8` reverts
  to main's two-join shape (1,717, m3 2,185);
- 292 branch weights (1:2000 and 2000:1 on each of execute's 146 conditional brs) on s_nat1: best 1,811. The layout is
  set by the IR order (whether the inner join is sweep.exit's fallthrough pred at early tail-dup), not by probabilities;
- why: rustc creates LLVM blocks in first-reference order over a MIR RPO that visits the token arm before the native arm
  (`Postorder` takes successors with `next_back`), so the token arm's `?` returns create the join before the native-arm
  blocks exist. A form whose join is first referenced after both arms (for example the vsigner part as an inlined nested
  fn whose return block becomes the last callee block) is the untested next step.

Other source forms on ac37d74: `if skip{0}else{sweep?}` = `if !skip{..}` 1,874 @27,464; `if skip{Ok(0)}else{sweep}?`
1,730 @27,472; `match (!skip).then(..){..}` byte-identical; `transfer_native(..).map(..)}else{Ok(0)}` (s_nat0) 2,278
@27,408 (neutral skeleton); token path without the early `return Ok(amount)` 2,155; both tails 1,602.

## 4. A cliff-free skeleton for the newpieces and tail leads

The per-exit shapes keep the w17a10 newpieces and w17a13 faithful-tail structures in place (pre-opt slim edits through
`tools/pipe.py`; captures for the tail forms):

| lead | on main | on n2 | on o3 |
| --- | --- | --- | --- |
| w17a10 c1a | 1,472 @27,656, m3 2,166 (808-insn C1 move) | 1,281, m3 2,737 (C1 stays; the AMM-arm mode of w17a13 appears) | 1,759 @27,632, m3 2,896 |
| w17a10 e79v | 1,428 @27,512, m3 2,185 | 1,723, m3 2,866 | 1,700 @27,536, **m3 2,912** (+107 over main) |
| w17a13 m2hdn (faithful tail) | 2,149 @27,400, m3 2,703 | 2,142, m3 2,704 (still collapsed) | 2,056 @27,312, m3 2,857 |
| w17a13 evd / m2n (n1) | 2,278 @27,392 / 2,276 @27,376 | 2,277 / 2,272 | 1,976 / 1,974, m3 2,865 / 2,864 |

So with the original's join shape the sweep-join placement cliff is gone for these leads (the skeleton stays at m3
2,857-2,912). Their exact M is still far below main.

## 5. Why none of it lands: one payload class, in r6

In o3, s_nat1+MV58 and h_n1 the coalescer joins the Result payload of the validate errors, every sweep exit, `swept`
and the event store into one vreg (o3 `%282`, s_nat1 `%284`, 30-odd defs). That is the original's structure, but greedy
gives the class **r6**, which is the original's sharing-tag register. The sharing tag and the C1/tail temps cascade from
there: C1 -51..-84, tail -39, W1S1 -14 exact tokens on s_nat1. Forcing the class to r9 (sticky) shrinks the code by
40-136 B but stays at 2,076-2,127, and Mperm/Mhc stay below main's plain M. Main's 27,400 B basin is tuned (weighted
Rc traps, volatile pins, passthroughs) for the split payload pieces (r3 at the sweep exits, r8 at the return block).

## Next ideas (not done here)

1. A source form for the MV58 placement on s_nat1 (join first referenced after both arms; see section 3). That would put
   the original's tag-test skeleton and threading in source, at m1 2,363 (above main) and m3 2,859.
2. Then re-tune the h_n1 basin (2,177 @27,320; T1 already equals main's 490) for C1 and the tail: the payload class in
   r9 needs the sharing tag in r6 over C1, which main's C1 shims were not tuned for. A sticky RA climb (w15a24 `sclimb.py`)
   on h_n1+MV58 prices how much is naming.
3. Re-price c1a/e79v on s_nat1+MV58 (they kept m3 2,896/2,912 on o3).

## Tools (`tools/`, experiment only; paths point at this lane's `$OUT`)

- `capmain.sh`, `capvar.sh <name> <variants.py>`, `batch.sh <variants.py> <names..>`: source capture (crate copy, exact
  line-kept edits, capraw pre-opt IR, preslim, fx score), two at a time in `work1`/`work2` (w17a06 capraw/preslim/fx).
- `irf.py`: parse execute's post-opt IR into blocks / preds / succs. `dup2.py`: copy the sweep test into a pred
  (`dup`, polarity and placement options) or thread a known-Err pred to the error exit (`thread`); `setnames` finds the
  joins and sites by content. `j60.py`: fold sweep.exit's test into its two preds. `pipe.py`: pre-opt edits, `opt -O3`,
  post-opt transforms (`N2`, `O3`, `MV58`), llc and score. `post.py` / `post2.py`: price captured variants under them.
- `lx.py`: llc-only oracle (`--llc sdk|dbg|p`; `p` is the private RAPRIO llc, env `RAPRIO_FORCE=v=r9 RAPRIO_STICKY=1`).
- `skel.py`: M at the four mask levels. `regs.py`: per-region matched original tokens (w17a01 region bounds).
  `rdiff.py`: masked diff ops for one region. `d.py`: disassembler with function-relative absolute jump targets.
- `variants/`: every source variant measured (`s1_gate`, `s2_tails`, `s4_flip`, `s5_natfirst`).
