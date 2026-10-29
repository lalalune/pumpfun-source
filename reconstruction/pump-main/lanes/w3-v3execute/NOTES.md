# Lane w3-v3execute (wave 3)

Target: `0x83c00` `trade::v3_execute_buy` (programs/pump/src/trade_v3.rs), original 3,440 B.
Base: origin/main 665499915 (1022 normalized / 276 raw), 0x83c00 at 3,456 B, ratio 0.9669.

## IR oracle (reduced-module llc loop)

`scripts` (lane-local, under ~/.cache/pumpfun-reconstruction/lanes/w3-v3execute/scripts):
`reduce.py` turns every other `define` into a `declare` (and drops aliases), so llc of the
single function takes 0.3 s and reproduces fastbuild output exactly (ratio 0.9669, 0 diff).
`irc.py` llc's a reduced module and diffs the function against the original window,
`mv.py` moves one basic block, `ed.py` applies exact text edits, `trial.py` copies the crate,
applies a source edit, captures IR and reports metric + block order + the call-block shape.

Two IR edits give a full match (0 differing instructions) on the base IR:

1. The `transfer_from_user` error payload (`extractvalue {i64,ptr} %r, 1`) must not reach its
   own store block as in base. Either keep that extractvalue in the call block, or (same result)
   send the add-error and transfer-error exits to ONE shared store block with phis. In the
   original both exits jump to the same `ldxdw r8; stxdw [r8+16],r2; stxdw [r8+8],r1` tail
   (0x84428). Alone: 3,448 B, 0.9728.
2. The transfer Ok-continuation block must be the IR layout successor of the call block, so
   SelectionDAG emits `jne r1,2,err` + fallthrough instead of `jeq +1; ja err`. Alone: 3,448 B,
   0.9728. With 1: 3,440 B, exact. The `add()` Ok block (`bb64`) must stay after the call block;
   the `add()` error block may sit before the `is_sol` branch targets or anywhere after.

## Source results

| Trial | Change | bytes | ratio | official | ledger |
| --- | --- | ---: | ---: | --- | --- |
| base 665499915 | - | 3,456 | 0.9669 | 1022 / 276 | - |
| t16 | `match <tuple if-select with add()?> { (amt,user,curve) => transfer_from_user(..)? }` | 3,448 | 0.9728 | 1022 / 276, no gains/losses | 33c9c4486a1c4303bc6147b48624801b |

Mechanism of t16: in edition 2021, temporaries of the scrutinee (including the `add()` result
inside the `if` tail tuple) live to the end of the `match` statement, so the add `?` exit and
the transfer `?` exit run through the same drop-tree node. SimplifyCFG then sinks their
`_0` stores into one phi block (the IR oracle's shape 1). The remaining difference is shape 2.

## Rejected (see ledger, all on 665499915)

`if let Err(e)=..{return Err(e)}` (extract stays but +1 drop_in_place call), `match` with
`Ok(())`, `.map_err(|e|e)`, `.or_else(Err)`, `.map_err(Into::into)` (all byte-identical), `if
!is_sol` (identical), immediately-invoked closure (outlined), `#[inline]` helper (outlined),
`#[inline(always)]` nested helper (0.917 / 0.954), per-branch calls (23 calls), buy_v2-style
inline-if args (0.849, but shows both shapes 1 and 2), `and_then` (23 calls).
