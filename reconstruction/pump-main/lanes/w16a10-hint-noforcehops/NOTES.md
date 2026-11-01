# w16a10-hint-noforcehops

Wave 16 lane. It replaces three compiler-steering constructs in Pump Main, all outside `admin_cto`, with ordinary
Rust that keeps every window byte-identical.

| site | construct | window(s) | result |
| --- | --- | --- | --- |
| (a) | `admit_associated_token_account(.., payer:*const AccountInfo<'info>, ..)` + `let payer=unsafe{&*payer};` (buy_v2.rs:10, :61) | 0x14910 (callers include swap_hop 0x5b3b0) | **kept**: no safe parameter type reproduces it (IR reason below) |
| (b) | `let _=&c;` dummy borrow before `require_gte!(c.real_token_reserves,..)` (buy_v2.rs:996) | 0x13f630 `buy_exact_quote_in_v2` | **removed**, byte-identical: #3861, merged as 1f4e396b5 |
| (c) | `v3_buy_costs(..).map_err(core::convert::identity)?` (trade_v3.rs:814, #1878) | 0x147ba0 `buy_v3` | **respelled** `.map_err(anchor_lang::error::Error::from)?`, byte-identical (PR -2) |

## (b) dummy borrow: removed, byte-identical (landed)

`let _=&c;` became a `// layout-pad(1)` comment line, so `require_gte!` keeps line 997.

| | main 9bd38c7d5 | b0 |
| --- | --- | --- |
| normalized / raw | 1034 / 1034 | 1034 / 1034, no gains or losses |
| admin_cto | 0.67376 / 3124 / 27,400 B | same |
| swap_hop | 1.0 / 0 / 18,584 B | same |
| unstripped.so | `d0c733f630b54ee7…` | **cmp-equal** (stripped too) |

The borrow is not load-bearing on current main: the whole unstripped ELF is unchanged without it. `land.py 3861
--allow-neutral` merged it as 1f4e396b5 (on main 7e5ba44a7: 1034/1034, zero losses, admin_cto 0.67436 / 3141 before = after).

Ledger: `0x13f630-w16-9bd38c7-noforcehops-dummyborrow-remove-v1`, `0x13f630-w16-7e5ba44-noforcehops-dummyborrow-landed-v1`.

## (c) map_err(identity): respelled with the crate's conversion idiom

| trial | form | result |
| --- | --- | --- |
| c0 | plain `v3_buy_costs(..)?` | 1033 / 301: loses 0x147ba0 (3688 B vs 3672) |
| c1 | `.map_err(Into::into)?` | does not compile (E0282/E0283: `?` applies `From` again, so the `Into` target is ambiguous) |
| c2 | `.map_err(anchor_lang::error::Error::from)?` | **1034 / 1034, zero losses, unstripped.so cmp-equal** to baseline 1f4e396b5 (`a8a70a59…`) |
| c4 | `let costs=v3_buy_costs(..); let (..)=costs?;` | = c0 (1033 / 301, loses 0x147ba0) |
| (w3/w4-buyv3, older base) | `match{Ok(c)=>c,Err(e)=>return Err(e)}`, `Err(e.into())`, `if let Err(e)=costs{return Err(e)}`, scoped blocks, two call sites | all = plain `?` or worse (ledger rows `0x147ba0-main-630a074-costs-*`) |

Mechanism (final IR of `pump_recovered::buy_v3`, main vs c0, captured with `tools/capture2.py`):

- `map_err` re-wraps the call result into a fresh `Result` local (`Ok(t)=>Ok(t)`, `Err(e)=>Err(op(e))`), and `?` then
  matches that local. The `Err(e)` store gives the re-wrapped local a `ptr`-typed slice at `+16`. SROA turns the copy
  from the call's out-parameter into one `load ptr` of `+16` (and one `load i64` of `+8`) above the Ok/Err branch, and
  the Ok arm uses `ptrtoint`. The Err arm (`bb76.i`) is then only `lifetime.end` + `br` to the shared Err return, and
  the original's layout follows: after the costs test it jumps away (`0x148330 mov64 r7, r4; 0x148338 ja +0x58`).
- With plain `?`, and every spelling without a re-wrap (match-return, let-then-`?`, if-let), the `+16` slot is split by
  type: the Ok arm loads it as `i64` and the Err arm as `ptr` (`%_202.1.i = load ptr` in `bb76.i`). The shared return
  block is then laid out right after the costs test (`ldxdw r1,[r10-0x1d8]; stxdw [r1+8],r6; stxdw [r1],r7; exit`),
  and 0x147ba0 becomes 3688 B (orig 3672).
- So the original needs a `Result`→`Result` adapter at this call. `map_err(anchor_lang::error::Error::from)` is the
  crate's ordinary conversion idiom (7 other uses, in trade_types.rs, multi_hop_curve_swap.rs and admin_cto.rs, where it
  converts io/program errors). It is the compiling form of `.map_err(Into::into)`. Here the conversion is the identity
  `From<Error> for Error`, so it is still a no-op at the type level, and it gives the same MIR shape as `identity`. It
  reads as an ordinary (redundant) error conversion rather than an explicit do-nothing function.

Ledger: `0x147ba0-w16-9bd38c7-noforcehops-mapid-plainq-v1`, `-mapid-intointo-v1`,
`0x147ba0-w16-1f4e396-noforcehops-mapid-errorfrom-v1`, `-mapid-letbind-v1`.

## (a) raw-pointer payer: load-bearing, no safe form

| trial | form | result |
| --- | --- | --- |
| a1 | `payer:&AccountInfo<'info>`, no `unsafe` deref; callers unchanged (`a.user.as_ref()`) | 1033 / 349: loses 0x14910 (6072 B vs 6080, ratio 0.6892) |

IR reason (final IR of `admit_associated_token_account`, main vs a1):

- main: `ptr nocapture noundef readonly %payer`. a1: `ptr noalias nocapture noundef readonly align 8 dereferenceable(48) %payer`.
- Without `noalias`, `payer.key` is loaded once for `create_associated_token_account_idempotent(&payer.key(),..)`
  (`%_110`) and loaded **again** after that call for `payer.clone()` (`%_2.i`), because the call may write memory.
  The original does exactly this: `0x154a8 ldxdw r1,[r9+0x0]` before the call at 0x15578, then
  `0x155b0 ldxdw r5,[r9+0x0]` after it, with the payer pointer held in r7/r9 across the call. This reload is the
  only difference between the two final IRs of the function, apart from value numbering. The other field loads of
  the clone come in the same order in both.
- With `noalias readonly`, GVN forwards the first load to the clone (`store ptr %_109, ptr %account_infos`), so the key
  pointer, not the payer pointer, lives across the call. The payer stack arg is then spilled to `[r10-0x308]` and
  owner / token_program swap r6/r7: 8 B shorter, and every later window shifts.

Why no ordinary safe spelling can keep the bytes:

- The callers are matched and pass the payer's `AccountInfo` address (`Signer.info`, one `ldxdw`) in the 8th argument
  slot, so the parameter must be a pointer-sized value holding that address.
- rustc 1.79 gives a `&T` / `&mut T` parameter `noalias` (plus `readonly` and `dereferenceable` for a shared reference)
  whenever `T` is `Freeze` (`Unpin` for `&mut`). It finds the reference through `pointee_info_at` also inside newtypes
  (`Signer<'info>` by value), `Option<&T>` (`noalias readonly dereferenceable_or_null`) and two-field `ScalarPair`
  structs. `AccountInfo` is `Freeze`: its `Rc<RefCell<..>>` fields point to the heap.
  So `&AccountInfo`, `&'info AccountInfo<'info>`, generic `T: ToAccountInfo` with `T=&AccountInfo`, `Option<&AccountInfo>`,
  `Signer` by value, and a `{payer, system_program}` pair all carry `noalias`. `Option` also needs an unwrap.
- Forms without `noalias` change the callers: `&Signer<'info>` (callers pass `&a.user`, an address computation instead
  of the `ldxdw`, and the callee needs one more load), the payer by value (callers clone and copy 48 B), or a struct
  passed by reference (callers build it on the stack).
- Only a raw pointer or `NonNull` carries the address without `noalias`, and both need the same `unsafe` deref.

So (a) stays as it is. It is not counted by land.py's NOFORCE regex. The faithful reading is that the original
callee's payer pointer was not `noalias` at the ATA create call. Lanes that later find an `&AccountInfo`-typed caller
shape with an escaping payer, or a different create-call structure for all six callers, can revisit it.

Ledger: `0x14910-w16-9bd38c7-noforcehops-payer-ref-v1`.

## Tools

- `tools/trial.sh <name> <slot> <edits.json>`: copy the lane crate, apply exact-once string edits that keep the line
  count, run `measure.sh`, and compare `candidate.so` / `unstripped.so` with the baseline's.
- `tools/capture2.py`: w16a01's `capture_ir.py` with raw rustc args as well (`--rustc -Zdump-mir=..`,
  `--llvm -print-after=..`), never used for proposals. Note: `-Zdump-mir='PreCodegen & trade::buy'` dumped only
  `trade::buy` (it calls `buy_body`), so the evidence above is from the final `.ll`, where everything is inlined into
  `pump_recovered::buy_v3`.
