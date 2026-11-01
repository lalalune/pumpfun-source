# w19b19-shim-mir-q-cells: `?` tag cells at external callees through a custom MIR forwarder

Target `0x22a10` `admin_cto::execute`, shim track. Ledger approach `mir-q-cells`.

## The neutral call-site wrapper (calibrated)

w17a35's enum carrier solves `?` shims for helpers we own. An external callee needs a conversion from `Result<T>` to the carrier, and every ordinary
spelling leaves a temporary (transmute: not neutral). A custom MIR forwarder has no temporary, because the callee writes straight into the wrapper's return place:

```rust
enum Q<T>{Ok(T),Err(Error)} /* FromResidual and Try copied from Result */
#[custom_mir(dialect="runtime",phase="optimized")]fn q_ci<'a,'b,'c,'d>(c:CpiContext<'a,'b,'c,'d,Create<'d>>)->Q<()>{use core::intrinsics::mir::*;mir!{let p:*mut Q<()>;let r:*mut Result<()>;{p=core::ptr::addr_of_mut!(RET);r=p as *mut Result<()>;Call((*r)=create_idempotent(Move(c)),ReturnTo(bb1),UnwindUnreachable())}bb1={Return()}}}
```

The caller writes `q_ci(..)?`. Its MIR is identical except for the callee name, and LLVM inlines the forwarder. `#![feature(try_trait_v2,custom_mir,core_intrinsics)]` on lib.rs line 1.

Calibration on a596efe59 (slim oracle, M 2,361, sig `5f276a2085e0`): declared unused, then create_idempotent, then create_idempotent + collect_coin_creator_fee + token_frozen at L560: **every step has sig `5f276a2085e0`.**
Works for pair returns (`Result<()>`, `{i64,ptr}`) and sret returns (`Result<bool>`, `Result<u64>`).

## Reaching the tag

- **Weight on the `?` test (`!prof`, IR cell `sw1`/`sw2`):** a carrier whose `branch` is `#[inline(always)]`, with `let s=ManuallyDrop::new(self);let p=&s as *const _ as *const u64;if expect(*p==2,true){Continue(())}else{Break(Err(read(p as *const Error)))}`.
  Capture signature = IR cell `sw1:execute:30473` (`6dd63220ed77`). `self` must not be dropped: a `Drop` in `branch` keeps the MIR inliner out (M 2,086 / 1,789).
- **Passthrough on the tag:** inside the forwarder, `t=(*w).0;Call(u=pt64(7_u32,t),ReturnTo(bb2),..);bb2={(*w).0=u;Return()}`. Toy: the IR is `icmp eq i64 (passthrough tag), 2`; same code when nothing folds.
- Two `Return()` blocks in a forwarder do not carry a weight: SimplifyCFG hoists the identical `ret`s and drops the branch. Put the weight in `branch`.

## First gain: the sweep `?` carries the pin repay

On e59b48eb1 (0.81611, M 2,725) the only repay is the 32 B `st` byte read at the holder_enabled test; without it the union is M 2,810 at 27,368 B. The sweep `?` residual cell repays the same 32 B in the cold error path: `vs:execute:29284` in the `.trq()` carrier (w17a35 form `w0`), M 2,813 at 27,400 B, real build 0.84247, 1,657 slots.

## Second gain: the original's call slot at the 326 error

Orig 0xb48 `add64 r1,-688`: `name()` writes the AnchorError `error_name` field directly, so the 3-word String copy (6 tokens, 48 B) that every other error block has is missing at 326. MemCpyOpt's call slot optimization has a block-local restriction (`-debug-only=memcpyopt`: "Call Slot: block local restriction"). An inlined `to_string` puts a branch between `name()` and the memcpy, so ordinary `error!` never forwards. BFI at the validate inliner: 326 is at 2.8 %, cold below 2 %.
`e326()`, one custom MIR body, spells it: `Call(g.error_name=PumpError::name(X326),..)` into the field place, then `to_string`, then the remaining fields in `error!`'s order, then `From::from`. LLVM inlines it. -48 B, code equal to the original's block.

Union on 1f7ca411c: e326 + native tail `if amount>0{..map(|()|amount)}else{Ok(0)}` + no fills: M 3,082 at 27,368 B, all3 3,265. Fill screen on that base (`tools/fillgen.py`, one volatile byte read at each of 221 block starts): `fl:validate:27574` (before the holder_reward test) M 3,104 at 27,400 B. Source form has the same signature `96745e98dee9`.
