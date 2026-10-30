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
| **fb = c1 + nested `if creator_fee_bps.0==0 {} else {..}`** | **15,576 (= orig)** | **0.98763** | **42** | 1027 / 276, 0 losses, 0 raw losses | 2517bda7 |

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

## Residual (fb, 42 slots)

- curve-store block: creator pointer in r2 (orig r4) and the `[r10-0x718]` (name ptr) reload at the
  block end (orig: at the block start, which takes r2).
- two `mov r2,0` / `mov r7,0` order flips (lines ~140 and ~1068 of the window).

## Ledger

Lane `w7r1-execute-regsched`, dedupe keys `0x1e7c0-main-2b85821-*`.
