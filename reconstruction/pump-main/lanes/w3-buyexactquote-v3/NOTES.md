# Lane w3-buyexactquote-v3 (wave 3)

Target: `0x1489f8`, `trade::buy_exact_quote` (v3), original 7856 B (982 slots, 952 insns).
Base: origin/main 665499915 (1022 normalized / 276 raw). Base target: 7656 B, ratio 0.3129,
66/66 calls.

Approach: semantic reconstruction (callgraph census first, then the IR oracle).

## Tools (scripts/)

- `trial.py NAME EDITS.py`: copies `programs/pump`, applies `(old,new)` edits to `trade_v3.rs`,
  builds with `--emit=link,llvm-ir` (separate `SLOT` work dirs so three builds can run at once;
  a shared work dir makes parallel builds overwrite each other), scores with score.py, and
  prints the target metric, the llc-oracle diff and the buy_v3 and sell_v3 sibling metrics.
- `ir.py NAME EDIT.py`: llc oracle on rustc's optimized IR (SDK llc `-O3 -relocation-model=pic
  -mattr=+store-imm,+jmp-ext`). It reproduces the fastbuild function exactly. It reports raw
  diff slots and ratio, plus a "masked" ratio with registers, stack offsets and branch offsets masked.
- **opt oracle (new)**: `capture_raw.py SRC WORK OUT -C no-prepopulate-passes` gives rustc's
  pre-optimization IR. `opt -O3` (from `~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt`,
  LLVM 18.1.7-rust-dev) followed by llc reproduces `buy_exact_quote` byte for byte (927/927 insns).
  `opt -O3 -print-changed -filter-print-funcs=SYM` together with `passes.py` splits the per-pass
  dumps, which shows which pass makes a given IR shape.
- `bbmap.py`: basic-block map (call names, error-line immediates, branch targets) for the original and a candidate.

## Findings

1. The error-site line order is the same as the original (881, 882, 891, 926, 1001, 993, 935, 971),
   and the 66 calls are the same multiset. The gap (-25 insns) is spread over the whole function:
   the v3_execute_buy argument tail (+14 in orig: post payload copied through two stack temps),
   the crossing guard (orig hoists usub.sat and uses a bitwise `can_cross & (available>first)`),
   a `can_cross` retest after the post merge (orig keeps it; ours is jump-threaded), and the
   v3_buy_costs blocks (+2 each).
2. **can_cross phi (fixed, c11).** The original keeps `can_cross` as a phi
   (`mov r4,0` before the mayhem test, `r4=(memcmp!=0)`), then `mov r1,r4; and64 r1,1; jne ok; jne partial,ok; error 926`.
   Ours had `or i1 memcmp_ne, partial_fill` (brmerge). The opt-pass dump shows that the threading
   is already in rustc's pre-optimization IR: **MIR JumpThreading** runs after the MIR inliner inlines the
   `#[inline(always)] v3_fee_exempt` (the mayhem arm stores the constant `false`). A helper without an
   inline attribute is not MIR-inlined (it is not a leaf, so it is not cross-crate-inlinable). LLVM inlines it later and keeps the phi.
   - c07: dropping `#[inline(always)]` from v3_fee_exempt keeps the phi, but with the *exempt*
     polarity (`jeq exempt,0`). The ratio falls to 0.265.
   - c09/c11: a non-inline helper that returns can_cross (`fn v3_can_cross(..)->bool{!v3_fee_exempt(..)}`)
     gives the original's polarity. The target goes from 7656 B / ratio 0.3129 / masked 0.7100 to
     **7664 B / 0.3287 / masked 0.7415**. buy_v3 and sell_v3 are unchanged (3680/0.8774, 6040/0.9871). Score is 1022/276, no losses.

3. **Post-merge retest and MIR JumpThreading (h01).** In rustc's pre-optimization IR the join after
   `let (post,costs)=if ..` (destructuring plus `if can_cross`) was duplicated into all three arms
   (guard false, estimate None, fit Some). MIR JumpThreading knows `post`'s discriminant on the None
   paths and threads the `match post{..}` that computes base_out. The original has one join with one
   `ldxdw [can_cross]; and64 1; jne` retest. `match &post{Some(p)=>p.base_out,None=>0}`
   (or `post.as_ref().map_or(0,|p|p.base_out)`) borrows `post`, which takes the local out of JumpThreading's tracked places.
   Together with the original's hoisted `let rest=available.saturating_sub(first)` and bitwise
   `can_cross & (available>first)` guard (x01, which was worse on its own), the target goes to **7776 B, ratio 0.6135, masked 0.8532**.
   With `&&` (h02) it gets worse, so the bitwise guard and the borrow belong together.

4. **891 error-block adjacency (open).** What remains at the top of the function is MachineBlockPlacement of the
   [post_fee `?` err, 891 err, EXIT] chain. The original places it after the non-whitelist path, and the v3_trade_fees `?`
   falls through to the whitelist memcmp (`jeq ok,+1; ja err`). llc oracle on the h01 IR: moving bb18 (the 891 err block)
   anywhere except directly after bb23 (the v3_trade_fees call) gives ratio **0.6434 / masked 0.8917**, and so does
   moving it before bb23. `require_neq!` (k01) does make the err block come first, but the error-return join
   (bb112) then lands directly after bb23. k01's IR with bb112 moved to the end gives 0.6434 again. No source spelling
   found yet: k01-k08 cover require_neq, `0u64`, fees before the check (k03 gives 0.6424 but runs fees first, unlike the
   original), match-spelled `?`, and calling fees early.
   - Raw-IR opt oracle (`scripts/rawexp.sh NAME "X>Y"`: reorder rustc's pre-opt IR blocks, opt -O3, llc). A no-op reorder
     reproduces h01 exactly. Creating bb18 last (moving it to the end of the raw IR) gives 0.6434, so the original's 891 error
     block was created late in rustc's codegen order. rustc creates switch targets in [0-target, otherwise] order and
     codegens the 0-target subtree first (k01 shows this: err as 0-target is codegen'd at once, so the scope error-exit join bb112
     is created right after bb23).
5. **Block-order ceiling.** `scripts/hc.py` (greedy single-block moves on the slimmed h01 IR, llc oracle, about 0.2 s per eval)
   reaches 0.6441 → 0.6515 → 0.6607 in 3 rounds (moves: buy_quote block after the cross v3_trade_fees check,
   the cross-arm end copy block bb68 earlier). Block order alone does not get past about 0.67. The rest is register allocation
   and frame layout. The alloca order differs: the original's name String is at -0x180 and to_string's buf at -0x160, ours
   at -0x90 and -0x180. The original's post slices (16 B + 24 B left in memory by SROA) now exist in h01 as
   `%_534/_535.sroa.*` allocas.
6. Prologue now matches the original (ctx in r6, min_tokens_out spilled). The remaining prologue diff is the
   prepare_bonding_curve return-slot lea, which comes after the argument leas in ours and before them in the original. That
   slot is the demoted `{i64,ptr}` return, not an IR sret.

## Attempts (ledger keys `0x1489f8-main-6654999-*-v1`)

| trial | mechanism | bytes | ratio | masked | result |
| --- | --- | ---: | ---: | ---: | --- |
| base | main 665499915 | 7656 | 0.3129 | 0.7100 | |
| x01 | (re-run) bitwise guard + precomputed rest | 7712 | 0.2725 | 0.6797 | rejected |
| c01 | `let exempt` local (buy_v3 idiom) | 7704 | 0.2292 | 0.5761 | rejected |
| c02 | `if !can_cross{require!(partial_fill)}` | 7656 | = base | | identical |
| c03 | `require!(partial_fill||can_cross)` | 7680 | 0.2901 | 0.7088 | rejected |
| c04 | `let amount` before require! | 7656 | = base | | identical |
| c05 | can_cross at top level (before tokens>real) | 7800 | 0.2667 | 0.7359 | rejected (memcmp hoisted) |
| c06 | inline `!(mayhem||key==wl)` | 7648 | 0.3078 | 0.7029 | rejected |
| c07 | v3_fee_exempt without inline attr | 7656 | 0.2650 | 0.6344 | phi kept, wrong polarity |
| c08 | `#[inline]` hint | 7656 | = base | | identical |
| c09 | non-inline `v3_can_cross` (direct) | 7664 | 0.3287 | 0.7415 | partial |
| c10 | c07 + exempt local | 7656 | 0.2650 | 0.6344 | = c07 |
| **c11** | non-inline `v3_can_cross{!v3_fee_exempt}` | 7664 | 0.3287 | 0.7415 | kept |
| g01 | c11 + rest local + `can_cross & (available>first)` | 7720 | 0.2883 | 0.7112 | locally right guard; fit moved to end |
| g02 | c11 + `can_cross && rest>0` | 7664 | 0.3138 | 0.6830 | rejected |
| g03 | c11 + `can_cross & (rest>0)` | 7720 | = g01 | | identical |
| g04/g05 | `let est=estimate(..)?; match est` | | = g01 / = c11 | | identical |
| g06 | est local + `Some(ref mut post)` | 7664 | 0.2915 | 0.6819 | 65 calls, rejected |
| **h01** | g01 + `match &post{..}` for base_out | 7776 | 0.6135 | 0.8532 | **kept** |
| h02 | c11 (&& guard) + `match &post` | 7688 | 0.3038 | 0.6543 | rejected |
| h03 | g01 + `post.as_ref().map_or(0,..)` | 7776 | = h01 | | identical |
| k01 | `require_neq!(available,0)` | 7776 | 0.6135 | 0.8532 | err-first but join adjacent |
| k02 | `require_gt!(available,0u64)` | 7784 | 0.6111 | 0.8528 | rejected |
| k03 | fees line 890, check stays 891 | 7768 | 0.6424 | 0.8843 | rejected (wrong exec order) |
| k04 | post_fee via match | 7776 | = h01 | | identical |
| k06/k07 | fees via match Ok/Err (+/- require_neq) | 7776 | = h01 | | identical |
| k08 | fees call before the check | 7784 | 0.5467 | 0.8570 | 67 calls |
| m01/m02 | non-cross `let mut tokens=tokens;let mut net=net;` | 7776 | = h01 | | identical |
