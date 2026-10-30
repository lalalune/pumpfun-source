# Lane w7r1-buyexactquoteinh-frame (wave 7, round 1): stack-frame oracle for 0x13f630

Target: `buy_v2::buy_exact_quote_in_handler` (orig 0x13f630, 20,184 B).
Base: origin/main 6edd839 (1027 normalized / 276 raw). Base candidate: 20,216 B, ratio 0.99635,
5 diff hunks (mov r7,2 schedule, Complete-if sense, terminal `jne r7,2`, Rc tail duplicate).

Result: analysis only. No source change beat base on ratio. While this lane ran, PR #2269
(regsched lane, on the #2240 program-fn form) reached a normalized match of 0x13f630, and
PR #2264 (errors lane) reached 0.99878 in module form. This lane therefore stops here. The
frame findings below explain why the helper shapes those PRs use keep the frame correct.

## Frame findings

1. **Base frame is already right.** With any LLVM-inlined helper that holds the CompleteEvent
   `emit_cpi!`, every r10 offset in the window equals the original. The frame residuals appear
   only in the no-helper form, where the Complete block is inlined into the handler (w6 `e2`):
   slots -0x28/-0x38/-0x118 against the original -0x100/-0x28/-0x160.
2. **Why the no-helper form loses the merges.** Per-pass MIR dumps (diagnostic only:
   `-Zdump-mir`, `cap.py` + `mirtrack.py`) show that the CompleteEvent CPI temporaries
   `authority_info`, `inner_data` and the `Chain` iterator lose StorageLive/StorageDead in
   **GVN** (pass 005-015). The cause is the macro's own moves: `_x = move authority_info;
   [move _x]` and `into_iter(move inner_data)` make GVN reuse those SSA locals and drop
   their storage markers. Without markers, StackColoring never merges them. Source in the
   handler cannot change this, because the moves come from anchor's `emit_cpi!` expansion.
   The TradeEvent CPI temporaries lose their markers the same way, and the original has no
   markers on them either.
3. **The markers come from the LLVM inliner, not the MIR inliner.** The original's markers on
   those temporaries are call-scoped. rustc 1.79's MIR inliner applies its cost threshold even
   to `#[inline(always)]` (threshold 100), and an `emit_cpi!` body costs far more. Optimized
   MIR still shows `complete_and_prepare` / `snapshot_quote_mint` / `emit_complete_cpi` as call
   terminators, and renaming the helper changes nothing. So the original helper was
   LLVM-inlined (InlineFunction adds call-scoped lifetime markers to static allocas that have
   none), and its callee was simplified on its own first.
4. **Moving the TradeEvent CPI into the same helper keeps the frame** (a8/a9). Its
   temporaries get call-scoped markers, but StackColoring produces the same slots.
   `emit!(ev)` inside the helper does change the frame: one extra 24 B slot, every offset
   +0x18 (a7, a11).

## CFG findings (from llc oracle on saved IR; `llcor.py`/`irx.py` from w6r1-buyexactquotei-ir)

- **Complete-if sense.** The original `jeq r1,0,+1; ja` appears whenever the then-block is
  *not* the next IR block at ISel. ISel inverts only when then is next, and BPF cannot reverse
  a branch later. LLVM splices an inlined helper's blocks contiguously after the call block,
  so a helper whose entry is the Complete cond always gives `jne` (t1, base). Any block
  between the cond and the then-block fixes it (oracle o6). The TradeEvent CPI Err chain
  between them, as in e2, also fixes the 0x1431a8 weak-dec tail merge (oracle o5: dist 21->12).
- **CPI Err tag test.** A helper returning the niche `Result<()>` leaves `icmp eq tag,2` on
  the CPI Err path, because `Error::from(ProgramError)` is external and returns `{i64,ptr}`
  of unknown range (e5). The original has no such test. PR #2264 (errors lane) solved this
  with a tagged `Result<Pubkey>` return.
- **Prepare rewrap.** The original's `jne r7,2,X; mov r7,2; ja X` needs the prepare Err edge
  to go straight to a shared error phi, with the Ok edge going through its own block (oracle
  r2: dist 14->8). In a tail helper the Ok and Err paths merge at the helper exit, which gives
  `mov r7,2; jeq r1,2; mov r7,r1` instead.
- **is_mayhem select at 0x1436c0.** This regresses when the handler has no `?`/return exit
  after `ev` is built (a8/a9). The `post_fee_amount(..)?` exit inside the TradeEvent literal
  then gets an unshared, mergeable shareholders drop chain that lands right after the cond.
  In e2/base, the later TradeEvent CPI `?` shares the exit drop tree, and its drop flag keeps
  that chain elsewhere.

## Trials (all 1027/276, zero losses; outputs under $OUT/out)

| id | form | bytes | ratio |
| --- | --- | ---: | ---: |
| base | main 6edd839 | 20216 | 0.99635 |
| e2 | drop(ev)+inlined Complete+prepare? (w6 form, repro) | 20184 | 0.99432 |
| e5 | CPI-only helper by ref (w6 form, repro) | 20216 | 0.98865 |
| t1/a0/a5 | drop(ev); complete_and_prepare tail | 20184 | 0.99188 |
| a1/a3 | tail helper, prepare returned directly / match | 20160 | 0.99168 |
| a2 | tail helper, if let Err prepare | 20136 | 0.80658 |
| a6 | bool cond computed in caller | 20192 | 0.97991 |
| a7/a11 | ev by value with emit! or implicit drop in helper | 20224/20200 | 0.63 |
| a8/a12 | emit!(ev); cap_eq(ctx,ev,ts){emit_cpi!;drop(ev);Complete;prepare?} | 20224 | 0.99047 |
| a9 (=b1,b3,b4,b7) | emit!(ev); cap_eq(ctx,&ev,ts) | 20200 | 0.9931 |
| c1/c2 | cond in handler, tail helper in then + prepare in else | 20256/20296 | 0.88/0.87 |
| d1/d2 | explicit `return cap_eq(..);` | 20464/20488 | 0.955/0.952 |

Ledger attempt ids: 21e7db9c, 31908006, 3b5c93e2, df59a2d6, 3b608927, 316a505a, d20d0731,
de1f4cf0, 691725c4, 8925240a, 85370621, ee4af94d.

## Tools in this directory

- `cap.py <src> [outname]`: fastbuild with `--emit=link,llvm-ir,mir`. `EXTRA='-Z...'` adds
  diagnostic flags with RUSTC_BOOTSTRAP. It uses its own work dir (`WS` suffix). It is for
  diagnosis only, not for proposals.
- `mirtrack.py <dump dir> authority_info,inner_data,...`: prints, pass by pass, whether each
  named debug local still has StorageLive.
- `mk2.py`, `t.sh`, `pair.sh`: tail-helper spec generator and build/score runner.
