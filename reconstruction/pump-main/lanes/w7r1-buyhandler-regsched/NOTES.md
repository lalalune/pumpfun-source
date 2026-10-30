# w7r1-buyhandler-regsched

Target: `0x13b9b8` `buy_v2::buy_handler` (orig 15,480 B). Angle: register allocation and
instruction-scheduling residuals, via an llc oracle on our own IR (permute IR, find the Rust spelling).

Base: origin/main 6edd839 (1027 normalized / 276 raw in this lane's scoring). buy_handler 15,512 B,
ratio 0.97998, llc masked dist 42 (14 hunks).

## Residual inventory (base, llc masked diff)

| Orig insn | Residual | Kind |
| --- | --- | --- |
| 699-703 | whitelisted zero movs `r4,r2,r1,r3` vs ours `r3,r1,r4,r2` | phi order (scheduling of phi copies) |
| 738-818 | checked-add overflow blocks / tf Err block order, ret slot -0x6c0/-0x6d0 | block order |
| 1375/1380, 1487/1491 | spill slots -0x750/-0x790, -0x7d0/-0x7d8 swapped | select order (scheduling) |
| 1678 | `jeq;ja` vs `jne` | tail (shared with eq) |
| 1848, 1894 | terminal prepare test / weak-dec | tail (shared with eq) |

## Results

### A1 (kept): TradeEvent literal evaluates `virtual_sol_reserves` before `real_sol_reserves`

IR oracle (`scripts/ora.py` + `edits/selperm.py`): the two spill-slot swaps are the order of the three
`is_sol` selects. The original computes `quote`, `virtual_quote_reserves`, `real_quote_reserves`
(permutation 0,2,1 is the only one that removes both hunks, 42 -> 38). Struct-literal field order is
evaluation order, so writing `virtual_token_reserves, virtual_sol_reserves:..., real_sol_reserves:...`
in the `TradeEvent{..}` literal reproduces it.

buy_handler 0.97998 -> 0.98209, llc dist 42 -> 38, 15,512 B; official 1027/276, no gains/losses.
unstripped sha256 2ae74f243fdc83e691a7fa19d3f29fae5ad6a6cb4ad66162611bb7f5feb19cba. Ledger cf839887.

### B1 (analysis): fee-zero phi order is sell_v2's cf-first tuple

All 24 phi permutations through llc: only phi order (cf, pf, pbps, cbps) reproduces the original zero
movs. sell_v2's matched form `let (cf,pf,pbps,cbps)=if wl{(0,0,0,0)}else{let (pf,cf,p,c)=trade_fees(..)?;(cf,pf,p,c)}`
gives exactly that, and the add1/add2 code then matches too, but `?` moves inside the else arm so the
trade_fees Err block is created before add1: 15,504 B, 0.96179, dist 66. On B1's IR, moving that one
block (bb215) after add2 (bb219) gives **llc dist 9**: only the tail residual shared with eq remains.
Variants that keep the same IR (byte-identical or same metric): explicit match/return Err, map closure
(inner or outer `?`), tuple indexing, negated if.

### Err-block position (oracle sweep on B1 IR)
- dist 9 only when the trade_fees Err block (bb215) sits after add2 (bb219) and before the cmp block
  (bb223), or after the order OVF1,OVF2,CMP. With Err still before add1, every order of
  OVF1/CMP/OVF2 gives 66-73. Err at the function end or after cmp gives 66. Folding Err into the edge
  gives 93. Adding likely/unlikely weights on the Err edge gives 170/66.
- Why module form cannot do it: rustc creates LLVM blocks on first reference while it walks the MIR in
  RPO. The Err arm is created at the trade_fees switch, before add1/add2 exist, and the LLVM pipeline
  keeps that order (print-changed dumps: the order is the same from Start to the end of opt).
- Rejected source forms: `not_whitelisted` binding (0.97471, dist 71, Err becomes the TF fallthrough),
  nested plain `fn total_cost` (not inlined, loses closure windows 0xac2b8/0xac4c0), nested
  `#[inline(always)] fn total_cost` (0.73, frame changes).

### Outcome
PR #2225 (w7r1-buyhandler-inline) combines the program-fn form and inline Complete emission with this
lane's A1 (select order) and B1 (cf-first fee tuple). In program-fn form the Err block lands where the
original has it, and buy_handler is a **normalized match**. Independent rebuild of 8b8ebe781 here:
1028/276, gain 0x13b9b8, no losses, sha 5a670388f726ef26... (ledger d89c14c3).
