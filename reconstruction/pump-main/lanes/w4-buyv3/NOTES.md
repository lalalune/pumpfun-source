# Lane w4-buyv3 (wave 4): `trade::buy` (buy_v3) at 0x147ba0

Base: origin/main 630a07412 (1023 normalized / 277 raw). buy_v3 on base: 3680 B (original 3672 B), ratio 0.87739, 79 differing slots on the llc oracle.

## Result so far
| state | bytes | ratio | oracle slots | official |
|---|---:|---:|---:|---|
| base 630a07412 | 3680 | 0.87739 | 79 | 1023 / 277 |
| **t44 (committed): `let can_cross=v3_can_cross(..)` reusing the existing non-inline helper (one-line diff, byte-identical to t40)** | 3680 | **0.93138** | **38** | 1023 / 277, 0 losses, sha ff15a582 |
| t40: t03 with no inline attribute on `v3_cross_ok`** (LLVM inlines it, not MIR) | 3680 | **0.93138** | **38** | 1023 / 277, 0 losses |
| t03: fee-exempt test as a `v3_cross_ok` helper, `curve.is_mayhem_mode==false && *user!=global.whitelist_pda`, guard `amount>real && can_cross` | 3680 | **0.88414** | **72** | 1023 / 277, 0 losses |

## Mechanism (tools/rpo.py)
rustc creates LLVM blocks in first-reference order while it codegens MIR blocks in reverse postorder.
The postorder DFS visits successors last-first. A 2-target switchInt creates its case-0 target before `otherwise`; a switch with more targets creates `otherwise` first.
`rpo.py` rebuilds the CFG from rustc's unoptimized IR (`-C no-prepopulate-passes`) and reproduces the raw block order exactly. With `flip:BB` you can ask what a reversed switch would do.

Oracle findings (llc on the optimized IR, `tools/scan.py` moves one block to every position):
1. The umin block (bb8) must follow the partial_fill test (bb7), and the crossing block (bb6) must sit anywhere outside bb7..bb11. In MIR terms, the DFS has to reach the crossing chain from the memcmp path *before* bb7, which means the jump-threaded `exempt`/`can_cross` test must have the crossing block as its last successor. A `can_cross` spelled with `==false` on the mayhem flag does this (t03, t08, t14, t17). The `!x`, `if`, `match` and `!(a||b)` spellings do not (t02, t05, t06, t07, t15): MIR folds the `Not` away.
2. Side effect of (1): the mayhem switch also flips, so the mayhem-true block (`lifetime.end` of the key copy) now precedes memcmp. The oracle wants it after memcmp (`bb59>bb58`, worth 72 -> 51 together with 3). Under a 2-target switch this conflicts with (1), because creation order and DFS order are tied to the same target order. One way out is a forwarder block that MIR keeps and LLVM deletes.
3. The v3_buy_costs Err block (bb79) must come after the last error chain (bb84 / bb86) with ret last: 72 -> 51 on t03 IR, and 21 together with 2. A plain `?` creates it at the call's switch, so it is always early; making it empty (hoisting the +16 load) is worse (157 slots). The original most likely has the Err code in a block that is created late.

## Trials (all scored with score.py against the 630a07412 baseline)
| id | change | buy B | ratio | slots | losses |
|---|---|---:|---:|---:|---|
| t02 | helper `!mayhem && user!=wl` | 3680 | 0.87739 | 79 | 0 |
| t03 | helper `mayhem==false && user!=wl` | 3680 | 0.88414 | 72 | 0 |
| t04 | t02 with `can_cross && amount>real` | 3688 | 0.8764 | 80 | raw 0xa868 |
| t05 | `if mayhem {false} else {user!=wl}` | 3680 | 0.87739 | 79 | 0 |
| t06 | `!(mayhem || user==wl)` | 3680 | 0.87739 | 79 | 0 |
| t07 | `match mayhem {true=>false,false=>..}` | 3680 | 0.87739 | 79 | 0 |
| t08 | `mayhem!=true && user!=wl` | 3680 | 0.88414 | 72 | 0 |
| t09 | `!mayhem && (user==wl)==false` | 3680 | 0.87739 | 79 | 0 |
| t10 | `(mayhem || user==wl)==false` | 3680 | 0.87739 | 79 | 0 |
| t12 | base exempt + `exempt==false` guard | 3688 | 0.8764 | 80 | raw 0xa868 |
| t13 | exempt `mayhem==true || ..` | 3680 | 0.87739 | 79 | 0 |
| t14 | `if mayhem==false {user!=wl} else {false}` | 3680 | 0.88414 | 72 | 0 |
| t15 | `!(mayhem==true || user==wl)` | 3680 | 0.87739 | 79 | 0 |
| t16 | t13 + `exempt==false` guard | 3688 | 0.8764 | 80 | raw 0xa868 |
| t17 | `mayhem==false && !(user==wl)` | 3680 | 0.88414 | 72 | 0 |
| t18 | `let user=a.user.key()` local | 3672 | 0.61261 | 200 | raw 0xa868 (memcmp sunk below amount test) |
| t19 | `let costs=..; costs?` | 3680 | 0.54218 | 295 | 0 |
| t20 | match Ok/`return Err(e.into())` | 3680 | 0.88414 | 72 | 0 |
| t21/t22 | match on v3_buy_costs wrapping the tail | 3688/3680 | 0.458/0.452 | 281/284 | frame +0x18 |
| t24 | helper takes `is_mayhem:u8`, `==0` | 3680 | 0.85489 | 92 | 0 |
| t27 | `can_cross==true` guard | 3680 | 0.88414 | 72 | 0 |
| t28 | nested if with duplicated else | 3736 | 0.68973 | 193 | raw 0xa868 |
| t29/t30/t32 | key temp kept live through match / call in if-condition | 3720/3696/3712 | <=0.875 | | raw 0xa868 |
| t33/t35 | early-return / block rhs helper bodies | 3680 | 0.88414 | 72 | 0 |
| t34 | `if mayhem==true {return false}` | 3680 | 0.87739 | 79 | 0 |
| t38 | two v3_buy_costs call sites | 3768 | 0.70222 | 187 | 30 calls |
| t39 | `let costs=..?; let (..)=costs;` | 3680 | 0.88414 | 72 | 0 |
| **t40** | **no inline attr on v3_cross_ok** | 3680 | **0.93138** | **38** | 0 |
| t41 | `#[inline]` on v3_cross_ok | 3680 | 0.88414 | 72 | 0 |

## t40: LLVM-level inline of the helper (lever 2 solved)
Without `#[inline(always)]`, the MIR inliner leaves `v3_cross_ok` as a call, and LLVM inlines it later. Its blocks (`v3_cross_ok.exit.thread`, `.exit`) are spliced after the call block in the callee's own order, and the jump-threaded mayhem path no longer precedes memcmp. The whole front half (prologue to v3_buy_costs) now matches. The remaining 38 slots are the v3_buy_costs Err placement: on the t40 IR, `bb76>bb83` (Err block after the v3_execute_buy Err) gives 12 slots / 0.982.
| t42 | t40 with `!mayhem && user!=wl` | 3680 | 0.93138 | 38 | 0 |
| t43 | t40 with `!(mayhem || user==wl)` | 3680 | 0.93138 | 38 | 0 |
| **t44** | existing `v3_can_cross` (non-inline, `!v3_fee_exempt`) | 3680 | **0.93138** | 38 | 0 (byte-identical to t40) |

Once the helper is inlined by LLVM, the spelling no longer matters (t42/t43/t44 are identical), so the `==false` helper is dropped. The committed change is a single line: `buy` uses `v3_can_cross` the same way `buy_exact_quote` does.
| t45 | tail (require/execute/emit) in a nested non-inline fn | 2912 | 0.27353 | 462 | not inlined by LLVM (21 calls) |
| t46-t51 | `if let Err(e)=costs{return Err(e)}` / match Err-first forms | 3680 | 0.60067 | 249 | 0 (frame +0x20) |

## Lever 3 (still open): the v3_buy_costs Err block
On the t44 IR, the oracle finds two equivalent fixes: `bb76>bb83` (costs Err after the execute Err; 12 slots, 0.982) and `bb50>bb76` (ret right after the costs Err; 15 slots).
`flipsearch.py` tried reversing the successor order of every 2-way and n-way switch in the raw CFG; no flip gives either layout. A direct `?` always creates its Err arm at the call's switch, early in RPO, and no successor order changes that.
Forms that create the Err arm first (`if let Err`, an Err-first match) change the creation order but grow the frame by 0x20. Wrapping the tail in a `match` keeps the result alive and grows the frame by 0x18. A big helper fn is not inlined by LLVM (hidden linkage).
Untried ideas:
- A small LLVM-inlined (no inline attribute) helper on the Ok path whose callee blocks hold the remaining error chain. It has to stay under LLVM's inline threshold.
- A CFG where the Err payload copy sits in a multi-pred drop-tree node that rustc creates while codegenning the arm, with the arm itself emptied by hoisting the +16 load.
- Check whether the original's +16 load hoist (`ldxdw r3,[r10-0x98]` before the branch) comes from MI-level branch folding rather than IR.
