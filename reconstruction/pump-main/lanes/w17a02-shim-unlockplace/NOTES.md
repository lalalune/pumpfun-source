# w17a02-shim-unlockplace: branch-hint shims for admin_cto block placement and inlining (notes)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 599891304 (0.67436, 3,141 slots, M 2,251) at the start; merged with main 442ae70ca (w17a03 read_volatile pin
and w17a04 weighted Rc-clone trap: 0.67615, 3,141 slots).

**Result: the 312 `t==sharing` compare at 20:12 equal-likely (`llvm.expect.with.probability`, p 0.625) lifts admin_cto
0.67615 -> 0.67645 (+1 M) at 27,400 B with zero normalized/raw losses (merged build `b924a29e`, differential 388/388).**
On 599891304 alone it gave 0.67436 -> 0.67466 (`56e118d3`). The weight on the second compare (`t==*holder_key`) gives
the same bytes.
Ledger: approach `shimunlock`, keys `0x22a10-w17-5998913-shimunlock-<trial>-v1`.

## 1. Which branch-hint spellings work on the identity toolchain (rustc 1.79.0-dev, LLVM 18.1.7)

`tools/hintprobe.sh` compiles `tools/hintprobe.rs` with the identity rustc for `sbpf-solana-solana` (about 1 s, no build
slot) and prints the optimized IR's branches and weights.

| spelling | `!prof` after `-O3` | why |
| --- | --- | --- |
| `core::intrinsics::unlikely(c)` / `likely(c)` (`#![feature(core_intrinsics)]`) | **none** | The intrinsic is codegen'd into a 1-byte alloca (`store`/`load`/`trunc`) before the branch. LowerExpectIntrinsic runs in the early function pipeline, before SROA, so it never sees `br (llvm.expect ..)` and drops the hint. |
| `extern "C"{#[link_name="llvm.expect.i1"]fn expect(b:bool,v:bool)->bool;}` (`#![feature(link_llvm_intrinsics)]`) | **`branch_weights 1:2000`** (or 2000:1) | The call returns an immediate `i1` that the `br` uses directly. The weight survives to llc. |
| `#[cold] fn cold(){}` called in the branch | none in the final IR | BPI's cold-call weight (1:16) exists only until `cold()` is inlined, so it steers the inliner and early passes, not llc. |
| **`extern "C"{#[link_name="llvm.expect.with.probability.i1"]fn expect_p(b:bool,v:bool,p:f64)->bool;}`** | **any ratio** (`p=0.6667` gives `1431727348:715756301` = 2:1) | Same lowering as `llvm.expect`, with the probability as a constant argument. Every IR-oracle `!prof` result (20:12, 12:20, 2:1, 1:16, ...) now has a source spelling. |

So `core::intrinsics::{likely,unlikely}` cannot steer anything here; a shim that needs a persistent weight must use the
`llvm.expect.i1` extern (y1-cto-llvm found the same on 2026-10-30). The feature gate goes on line 1 of `lib.rs`
(`#![feature(link_llvm_intrinsics)]` prepended, no new line). The gate plus the unused extern declaration is
byte-identical to main (trial `fgx`, sha `a8a70a59`). A hint is still lost when MIR re-tests the same value later
(`unwrap`, `?`, `unwrap_or_default` on the hinted Option/Result: MIR jump threading duplicates the test, y1). Reading the
payload through a raw pointer avoids the re-test.

## 2. Outline triggers as shims (full `measure.sh` builds; main 0.67436 / 27,400 B)

| trial | shim | bytes | ratio | note |
| --- | --- | ---: | ---: | --- |
| fgx | feature gate + extern decl only | 27,400 | 0.67436 | byte-identical |
| c306 | `cold()` at the head of the 306 Some arm | 26,992 | 0.58971 | outline + collapse (w14a07 C1 on main) |
| c3 | `cold()` inside the 307 and 312 error branches | 27,040 | 0.58887 | collapse |
| x307 | `expect(t==default,false)` on 307 | 27,256 | 0.57486 | collapse |
| x312 | `expect(..,false)` on both 312 compares | 27,232 | 0.65445 | |
| x3 | x307 + x312 | 27,040 | 0.58224 | collapse |
| tfc306 | tf_g3 creator binding + `cold()` at 306 Some | 27,024 | 0.66385 | = tf_g3_O class (outline, no llc-time weight) |
| tfx306n | tf_g3 + `if expect(new.is_some(),false){new.unwrap_or_default()}` | 27,456 | 0.67335 | no outline: the unwrap re-test drops the hint |
| tfr306n | tf_g3 + `if expect(new.is_none(),true){Err}else{raw payload read}` (None 2000:1) | 27,112 | 0.67148 (M 2,230) | 307/312 outlined (lddw 86), no collapse |
| tfr306s | tf_g3 + same with `false` (Some 2000:1) | 27,288 | 0.67237 (M 2,240) | one to_string outlined (lddw 87) |

Every outline on main's own form collapses (as w15a25/w16a13 found for every V-time trigger). On the tf_g3 base the
transient cold call reproduces the IR-forced O base, so the remaining lever is the llc-time layout weight.

## 3. llc-only weight sweep (`tools/bws.py`, about 1 s per run, no build slot)

`bws.py <m.ll> <out.jsonl> [workers]` sets one `br`'s `!prof` in a slim post-opt module of `execute` (w16a06 `rx/m1/m.ll`
reproduces main 599891304 exactly, M 2,251) and runs llc; `BASEW="i:a:b;..."` fixes other weights first. Weights
20:12, 12:20, 2:1, 1:2, 1:2000, 2000:1 on all 108 conditional branches (648 runs, about 5 minutes):

| IR branch (line) | what | weight | M @27,400 |
| --- | --- | --- | ---: |
| 4462 `%_7.i.i49.i` | Rc `inc_strong` overflow trap (an AccountInfo `lamports`/`data` clone) | 1:2000 | 2,257 (+6) |
| 4549 / 4677 / 4505 | other Rc `inc_strong` traps | 1:2000 | 2,253 / 2,253 / 2,252 |
| 3032 `%97` / 3101 `%113` | 312 memcmp `t==sharing` / `t==holder_key` equal | 20:12 | 2,252 |
| 3338 `%quote_locked` | 326 quote_locked true | 20:12 | 2,252 (the source `expect_p(st.quote_locked,..)` build is byte-identical to main: GVN forwards the flag) |
| 3364 `%or.cond.not.i` | 338 fee range | 12:20 or 1:2 | 2,252 (the source weight on `f==0||f>max` loses: 0.66177) |
| 5410 `%570` | sweep exit tag==2 | 1:2000 | 2,252 |

The Rc trap is the lever w17a04 landed (#3950) with a hand-written `rcinc`. With 3032 fixed at 20:12 the best pair is the
4462 trap (M 2,258). Source builds of the mild weights on 599891304: `x312ah`/`x312bh` 0.67466 (gain), `v326h`
byte-identical, `v326l` byte-identical, `v338h` 0.66177, `v338l` 0.65768 @27,392, `gateh` 0.67286.
