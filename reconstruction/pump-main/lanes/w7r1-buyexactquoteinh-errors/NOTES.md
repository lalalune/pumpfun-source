# w7r1-buyexactquoteinh-errors: error-edge structure of buy_v2::buy_exact_quote_in_handler (0x13f630)

Base: origin/main 6edd839 (1027 normalized / 276 raw). Target before: 20,216 B, ratio 0.99635.
After: 20,184 B (original size), ratio 0.99878, 6 differing slots, zero losses (1027 / 276).

## Mechanism (error edges)

The original's tail has three error edges and they are not alike:

* CompleteEvent CPI error (orig 0x144460..0x144500): `call Error::from`, Rc drops, then
  `jne r2,0` straight to the handler's error return (0x141cf0). No re-check of the tag.
* prepare_bonding_curve result (orig 0x144388): `jne r7,2 -> return`, `mov r7,2; ja return`
  (the `?` Ok rewrap), with the Ok block next at ISel.
* Complete `if real_token_reserves == 0` is `jeq +1; ja` (then-block not next at ISel).

main used `complete_and_prepare(ctx,ts)?` (an `#[inline(always)]` helper; LLVM-inlined, not
MIR-inlined because the MIR inliner still applies its cost threshold to inline(always)). Its
`Result<()>` is niche-encoded (Ok = Error-tag value 2), so after inlining the caller's `?` does
`icmp eq <tag returned by Error::from>, 2` on the CPI error path: LLVM cannot know the tag of an
external call, the check stays, and the CPI error edge joins the prepare check (jeq r7,2 tail).

All-in-handler code (w6 e2) gets every branch right but the CompleteEvent CPI temporaries lose
their storage markers (GVN in the handler body removes StorageLive/Dead of authority_info,
inner_data and the Chain iterator), which recolors the frame. The original's CompleteEvent CPI
temporaries are call-scoped, i.e. they come from an inlined callee.

Resolution: keep the Complete `if` and `prepare(..)?` in the handler (rustc first-reference
block order gives the original branch senses), drop the TradeEvent after its CPI, and move only
`emit_cpi!(CompleteEvent)` into an `#[inline(always)]` helper whose Ok type is larger than 8 bytes
(`Result<Pubkey>`). That Result is a tagged enum: Ok/Err tags are constants, the caller's `?`
folds, and the CPI error goes straight to the handler's error return. The LLVM inliner gives the
helper's allocas call-scoped lifetime markers, so the stack coloring matches too.

Controls: same helper returning niche `Result<()>` -> 20,216 B / 0.98865 (re-check returns);
`Result<(u64,u64)>` and `Result<Pubkey>` are byte-identical.

Remaining residual: orig 0x1430d0..0x143100 schedule of `mov r1,0; stxdw [r10-0x8d0]` vs
`mov r9,0` (the mov r7,2 group; regsched lane's subject).

## Trials (ledger dedupe keys 0x13f630-main-6edd839-*-v1)

| trial | mechanism | bytes | ratio |
| --- | --- | ---: | ---: |
| base | main 6edd839 | 20216 | 0.99635 |
| t1 | complete_and_prepare as handler tail expr | 20184 | 0.99188 |
| t3/t4 | TradeEvent + Complete + prepare in one helper | 20200/20232 | 0.633/0.630 |
| t5/t6 | complete_and_prepare returning tagged Result<(u64,u64)>/Result<Pubkey> | 20184 | 0.99716 |
| t7 | if in handler, CPI-only tagged helper | 20192 | 0.99452 |
| t9 | complete_curve(&mut ctx) tagged helper with the if | 20176 | 0.99452 |
| t10/n1 | t7 + drop(ev) after TradeEvent CPI | 20184 | 0.99878 |
| t11 | t10 with niche Result<()> (control) | 20216 | 0.98865 |
| n2 | by-value pass-through Result<CompleteEvent> | 20184 | 0.93425 |
| r1 | regsched d10 (`partial:&bool`) on this head (handler stays inline(never)) | 20184 | 0.96144, loss 0x127b58 |
| e1/e7 | `.ok_or::<Error>(PumpError::Overflow.into())?` at total_bps / quote sub | 20104/20240 | 0.753/0.854 (eager into call) |
| e2 | `let clock=Clock::get()?;` binding | 20184 | byte-identical |
| e6 | bind sharing_config AccountInfo before shareholders | 20192 | 0.80544 |

## Status vs other lanes

PR #2240 (w7r1-buyexactquoteinh-sibling) reaches 0.99959 with the program-fn form (handler
LLVM-inlined into an `#[inline(never)]` program fn, which also scopes the CPI temporaries), and the
regsched lane's `partial:&bool` variant on that base reports a normalized match. This lane's
tagged-Result helper is an independent route to the same CFG and frame (only the mov r7,2 group
left); the `&bool` fix does not carry over to the `#[inline(never)]` handler (r1).
