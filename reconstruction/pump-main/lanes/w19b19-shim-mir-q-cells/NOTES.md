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
