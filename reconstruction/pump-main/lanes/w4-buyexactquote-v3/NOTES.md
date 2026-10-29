# Lane w4-buyexactquote-v3 (wave 4)

Target `0x1489f8` `trade::buy_exact_quote` (v3), original 7856 B. Base origin/main 630a07412 (1023 normalized / 277 raw):
7776 B, ratio 0.61352 (llc-oracle masked 0.8532), 66/66 calls.

Tools: `scripts/` (copied from w3-buyexactquote-v3, paths pointed at this lane: trial.py, ir.py, rawexp.sh, hc.py, bbmap.py).

## Trials (ledger keys `0x1489f8-main-630a074-*-v1`)

| trial | mechanism | bytes | ratio | masked | result |
| --- | --- | ---: | ---: | ---: | --- |
| base | main 630a07412 | 7776 | 0.6135 | 0.8532 | |
| **t01** | `pub fn buy_exact_quote(..){buy_exact_quote_body(..)} #[inline(always)] fn buy_exact_quote_body(..)` (sell_v3 s04 idiom) | 7776 | 0.6367 | 0.8574 | kept |
| u01/u04 | nested fn / closure wrapping the 891 require | 8000 | 0.3592 | 0.7829 | rejected |
| u02 | 891 require inside a block with rebinding locals | 7784 | 0.6343 | 0.8570 | rejected |
| v01 | `require_neq!(available,0)` on t01 | 7776 | = t01 | | identical |
| v02 | v01 + post_fee via match with the Err arm first | 7776 | = t01 | | identical |
| **x01** | `let (is_sol,quote_fee);` declared before the 881 check, `(is_sol,quote_fee)=check_quote(a)?;`, `require_neq!(available,0)` | 7768 | 0.6519 | 0.8906 | kept (raw drift 0xa868) |
| x02 | x01 declaration with require_gt | 7776 | 0.6220 | 0.8522 | rejected |
| x03 | declaration after the 882 check | 7768 | 0.6603 | 0.8928 | = x04 |
| **x04** | `let (is_sol,quote_fee);(is_sol,quote_fee)=check_quote(a)?;` + `require_neq!(available,0)` | 7768 | 0.6603 | 0.8928 | kept (raw drift 0xa868) |
| x05 | `let quote_fee;` early, `let is_sol;` on the check line | 7768 | = x01 | | identical |
| z01 | `if !(tokens<=real)` cross split | 7776 | 0.5111 | 0.8522 | rejected |
| z02/z03 | `(tokens>real)!=false` / `(tokens<=real)==false` | 7768 | = x01 | | identical |
| z05/z07 | `if can_cross==false{}else{..}` / `if !can_cross{}else{..}` | 7768 | = x01 | | identical |
| z06 | cross tail tuple built before `if can_cross` | 7792 | 0.6055 | 0.8892 | rejected |

t01: the LLVM-inlined body changes the frame layout: the name String now sits at -0x180 as in the original.
Remaining: a global register rotation (orig ctx r6 / 5th arg r9 / return tag r8; ours r9 / r8 / r6), and the
891-error/EXIT chain placement (orig places [891 err, EXIT] after the non-whitelist arm).

## 891 error / exit-join mechanism (x01)

Raw-opt oracle (`scripts/rawexp.sh`, RSYM=buy_exact_quote_body17h): the bad shape is a block of the error-return path
created *directly after* bb23 (the `v3_trade_fees` call block) in rustc's block-creation order. With require_gt that block is the
891 err block (created as the `otherwise` target together with bb23). With require_neq it is bb112, the scope-exit
block (`lifetime.end(quote_fee)`), which the err block creates when it is codegen'd (rustc codegens the 0-target err first; RPO
visits successors with `next_back`). Moving either away from bb23 gives 0.6667 / masked 0.8959 (oracle).
In source (corrected after reading the x01 raw IR): when `quote_fee` is declared without an initializer before its
`check_quote` assignment, its `lifetime.end` moves to an outer exit block (bb113 in x01). The exit block created right
after the v3_trade_fees block is then empty, and opt folds it away. Declaring it at the top (x01) also starts the lifetime
before the 881/882 error temporaries and moves the name String to -0x90. Declaring it on the check_quote line (x04) keeps
-0x180. Official x04: 7768 B, 0.6603 / masked 0.8928.

Open oracle moves on the x01 raw IR (not yet mapped to source): create bb68 (the cross-arm tail tuple block) early, anywhere
from the cross/non-cross split on, giving 0.6568 / 0.8955; place the cross-arm v3_trade_fees block bb148 after its buy_costs
successor bb151, giving 0.6593 / 0.9023; both together give 0.6684 / 0.9081.

Caveat: raw loss `0xa868`. That is a 24-byte `<&T as Debug>::fmt` thunk at 0xa7b0 whose call crosses buy_exact_quote; its
raw match depended on the total byte span matching the original by coincidence. Any change in the target's size breaks it (u02, x01).
PRs #1539 and #1542 report the same drift.

## Return-phi order at the quote_fee exit join (oracle, no source yet)

On the x04 IR, swapping the `_0` phi pair at the quote_fee exit join (`bb113.i`, `%_0.sroa.38.12`/`%_0.sroa.0.12`, ptr phi
first) to i64-first gives ratio 0.6878 (`scripts/phiswap_all.py`, PS=12). That puts ctx in r6 as in the original. Swapping the final
return pair (PS=5) does nothing. Raw-opt: moving the `_0` alloca up 54 or more positions in the entry block (so SROA's LIFO worklist processes it after
about 54 other allocas) flips the order, and 51 or fewer does not. `scripts/phichk.sh` (early SROA only, 0.3 s on the slim raw body) predicts the flip.
rustc always creates `_0` first among locals, after the argument allocas, so it is always last in the entry block. Adding an address-taken
argument alloca below `_0` (`scripts/argalloca.py`) does *not* flip it. Moving the single allocas _90/_91/_92/_93 does not flip it either. The flip depends on how many allocas were processed before `_0`.

## Other oracle results

- Cross-arm tail (`bb68`, tuple build plus post memcpys, then the join) created early: 0.6653 / 0.8976. Cross-arm `v3_trade_fees` block after its
  `v3_buy_costs` successor: 0.6677 / 0.9044. Both together: 0.6769 / 0.9102. Post-opt hill climb (hc3, 3 rounds): 0.6793.
- Move-to-end scan over every raw block (`scripts/rawscan.sh`): no other single creation-order change is worth more than +0.0004.
- Raw drift `0xa868`: `scripts/thunks.py` prints the call immediates of the seven `<&T as Debug>::fmt`-family thunks. The one at
  0xa7b0 calls across buy_exact_quote and matches only while the target is 7776 B.
- z12 (`try_into`): identical. z14 (cross fees via `match`): 0.5701, much worse. x06 (decl at body top): = x01.
