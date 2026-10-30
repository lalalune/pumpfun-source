# Lane w6r2-buyexactquote-ir (wave 6, round 2): IR-oracle loop on `0x1489f8`

Target: `pump_recovered::trade::buy_exact_quote` (v3), original 7856 B. Base: origin/main a7135a6a6 (1027 normalized / 276 raw).
On base the target is 7872 B, ratio 0.8510, masked 0.9675. The oracles (post-opt llc and raw-opt) reproduce fastbuild exactly.

This lane has no source change. The PR from this lane carries analysis only.

## Findings
1. **The lifetime-only `?` error blocks also exist in the original.** After `v3_trade_fees(available)` and `net_quote_for_budget`, the original has
   `jeq r1,0,+1; ja EXIT`, which is an empty MBB. So the earlier oracle that deletes the lifetime.end in `bb136`/`bb137` (0.9276) gets its gain from a
   coincidental register-allocation flip. It does not reproduce the original's structure.
2. **The real structural residual is a missing hoist.** The offset-8 load of the non-whitelist `tokens_for_quote(curve,net)` result is not hoisted into the call block,
   while the whitelist arm's is. With the hoist, the original tail-merges the two tfq error blocks. A post-opt oracle that hoists it gives 0.8813 / masked 0.9811,
   with 952 insns (the original's count). The sibling lane w6r2-sem found the same thing independently.
3. **Why there is no hoist.** The BPF target hoists common instructions only in its peephole-EP SimplifyCFG, which runs first at pass 38, right after InstCombine 35.
   SROA (pass 9) creates `ptrtoint(net_fees.protocol_fee)` in the net_quote Ok block. The ptr type comes from the Error-box slice at result+16.
   The try_from-ok block empties at InstCombine 18 and is folded at SimplifyCFG 19. InstCombine 35 then sinks the ptrtoint to the head of the tfq Ok block,
   and that blocks the hoist at 38.
4. **SROA order is the lever, but on its own it overshoots.** Processing the MIR-SRoA local `net_fees32` earlier puts the ptrtoint into the try_from-ok block.
   That happens in the raw alloca-move oracle and in the source `let (net,ref net_fees)=..?; (*net_fees,tokens,net)` (a02/b02). The tfq load is then hoisted,
   but the non-whitelist arm keeps its own copy block (the original has none). Result: 7856 B, 0.7941. The FRU and field-destructure spellings also hoist,
   but they split the net_quote Ok/Err loads by type (i64 vs ptr): 7768 B, 0.7649.
5. On top of the hoist oracle, deleting quote_fee's error-join lifetime.end gives **0.9464** (masked unchanged at 0.9811), which fixes the r6/r9 rotation.
   The remaining masked residuals are the prologue lea, the `fees` slot (-0x40 vs -0x160) and a few spill placements.

## Trials (ledger keys `0x1489f8-main-a7135a6-*`)
| trial | mechanism | bytes | ratio | hoist |
|---|---|---:|---:|---|
| a01 | `let r=..?; (r.1,tokens,r.0)` | 7872 | 0.8510 | no |
| a02/b02 | `ref net_fees` + `*net_fees` / `.clone()` | 7856 | 0.7941 | yes (+ extra block) |
| a03 | `net_fees.clone()` | 7872 | 0.8510 | no |
| b01 | inline tokens in the tail tuple | 7872 | 0.8510 | no |
| b03 | ref + FRU | 7872 | 0.8510 | no |
| b04/c1 | FRU / field destructure | 7768 | 0.7649 | yes |
| b05 | `mut net_fees` | 7872 | 0.8510 | no |
| c4/c5 | `try_into` in the non-whitelist arm / both arms | 7872 | 0.8510 | no |

## Next ideas
- A spelling where the ptrtoint stays in the net_quote call block until pass 38. Two ways: the phi's incoming block for the non-whitelist arm is not a direct
  successor of the call block when InstCombine 35 runs, or the ptrtoint has users in two blocks.
- The whitelist-split helper h01 (w6r1) fixed the rotation. Check whether it can be combined with a hoisting spelling.
