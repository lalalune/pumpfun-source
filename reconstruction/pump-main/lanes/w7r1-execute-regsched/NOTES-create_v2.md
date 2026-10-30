# Lane w7r1-execute-regsched (wave 7, round 1): create_v2::execute (0x1e7c0)

This lane name is shared by two agents; NOTES.md covers sweep::execute (0x72810), this file covers create_v2::execute.

Target: `0x1e7c0` `pump_recovered::create_v2::execute` (original 15,576 B, 1,859 insns, 125 calls).
Approach: register-allocation / scheduling residuals via the llc IR oracle (SDK llc on rustc's IR
reproduces fastbuild exactly), minimal IR permutation, then the Rust spelling.

Base: origin/main 2b85821 (1027/1035 normalized, 276 raw), target 0.96854 at 15,584 B.

## Results

| Build | Bytes | Ratio | slots_diff | Official | unstripped sha256 |
| --- | ---: | ---: | ---: | --- | --- |
| main 2b85821 | 15,584 | 0.96854 | n/a (size differs) | 1027 / 276 | 37965968 |
| c1 = creator stored after `token_total_supply` | 15,584 | 0.97284 | n/a | 1027 / 276, 0 losses | 0dcf3b47 |
| fb = c1 + nested `if creator_fee_bps.0==0 {} else {..}` | 15,576 (= orig) | 0.98763 | 42 | 1027 / 276, 0 losses, 0 raw losses | 2517bda7 |
| **so = fb + store order vqr, ivqr, vtr (mechanism of w7r1-execute-frame / sibling, #2297)** | **15,576** | **0.98870** | **43** | 1027 / 276, 0 losses, 0 raw losses | 7f095a06 (branch head with sweep change: bba24089) |

## Mechanism c1: creator memcpy position

Since #2229 `init_curve` takes `&mut BondingCurve`, so the creator destination is a separate SSA
pointer (`mov r4,r7; add r4,8` right after the sol memcmp). With that, the memcpy is no longer
re-scheduled by the DAG to the front: writing `bonding_curve.creator=creator;` after the
`token_total_supply` store reproduces the original store sequence (ivqr, vqr, vtr, rtr, rqr, tts,
creator, mayhem, ...). IR oracle (memcpy moved after the tts store) predicted 0.97284 exactly.

## Mechanism fb: `?` continuation must follow validate_metadata's exit block

BPF's `analyzeBranch` cannot handle conditional branches, so the ISel-time fall-through decides
`jne tag,2,<err>` (original) versus `jeq tag,2,+1; ja <err>` (+8 B). ISel inverts the `?` test
only when the Continue block (`bb116`) is the next IR block. In ours, the creator-fee check blocks
(`bb47/48/52/54`) sat between the inlined `validate_metadata` exit and `bb116`: rustc creates LLVM
blocks in first-reference order, and `&& creator_fee_bps.0>0` lowers to a bool switch
`[0: join, otherwise: fee-check]`, so the join (which later holds init_curve, validate_metadata
and, after inlining, the validate exit) was created before the fee-check block, which then landed
right after the exit. IR oracle: moving `bb116`+`bb118` after the exit, or the fee blocks before
`bb58`, or after `bb118`, all give 0.98763 at exactly 1,859 insns. Rust spelling: nest the test and
use `==0` with an empty then-arm, `if matches!(..) {if creator_fee_bps.0==0 {} else {..}}`; the
`Eq` switch `[0: fee-check, otherwise: join]` references the fee-check block first.
`!matches!(..) || fee==0 {} else {..}` is byte-identical to c1.

Behaviour: unchanged (`u64 > 0` == `!= 0`; field stores reordered within one straight-line block).
Line numbers: unchanged (edits stay on their lines).

## Residual (so, 43 slots) and register-allocation analysis

1. Two `mov r2,0` / `mov r7,0` swaps: the bb112 phi order (quote-word0 ptr phi `_84.sroa.31` last).
   IR oracle: moving it before the source-tag phi gives 0.98978. `-print-after=sroa` capture: the order is
   already set by SROA's mem2reg in the first SROA run after inlining validate_quote_mint (phis are
   inserted at block front, so the order is the reverse of PromotableAllocas; `.31`, the [16,24) slice
   shared by the Err Box pointer and quote_mint word 0, is promoted last). Spellings tried: main
   return `Ok((mint.key(),..))` / `Ok((*mint.key,..))` (0.53448, much worse).
2. Creator pointer in r2 (original r4) with the name-pointer reload at its use instead of at the top
   of the curve-store block. In the original, the name split interval (r2, from block entry) is
   allocated before the creator pointer; in ours after it. Every IR-level lever tried on so+phi
   (0.98978) leaves this unchanged:
   - every legal single-instruction move in the fee join, bb2.i73, bb1.i75, bb9.i, exit (526);
   - every adjacent legal instruction swap in the whole function (437);
   - each block moved to the end / swapped with neighbours (506);
   - successor swap with negated condition on every conditional branch (90; changes ISel RPO and
     vreg numbering);
   - `!prof` 1:1000 / 1000:1 on every conditional branch (180; block frequencies);
   - creator GEP position x creator memcpy position (1395);
   - two neutral-drift random walks (~1500 accepted moves).
   None produces `mov r4,r7; add r4,8` or the early reload (flag-checked, not just ratio). The
   residual is not an order/frequency effect of this IR; it needs a structurally different IR (other
   live ranges), probably the same root cause as the phi order (validate_quote_mint's result
   construction).

## Ledger

Lane `w7r1-execute-regsched`, dedupe keys `0x1e7c0-main-2b85821-*`.
