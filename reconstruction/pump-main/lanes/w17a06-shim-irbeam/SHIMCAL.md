# SHIMCAL: calibrated shim constructs for admin_cto.rs (rustc 1.79.0-dev, LLVM 18.1.7, sbpf)

> Historical experiment notes. The private tools and probe execution paths from this lane are not maintained or admitted. An independent genuine LLVM control showed that the reducer changed an outside-alias fixture and accepted a missing root. Its broad oracle mask also differs from canonical score.py. Claims and trial results below are retained as historical author reports, not current acceptance evidence. See QUALIFICATION.md for the selected source, canonical build/score and bounded signed runtime qualification.

Lane `w17a06-shim-irbeam`. Every construct was put ONCE into `programs/pump/src/creator/admin_cto.rs`, on main
1647da0f2 (programs/ = 599891304: M 2,251, 0.67436, 27,400 B), without adding any line. Each variant was captured
with capraw (pre-opt IR) and scored with the exact slim oracle (`tools/preslim.py` + `tools/fx.py`; see NOTES.md).
The variants are in `tools/calvars.py`; `tools/irpat.py <variant>` prints the pre-opt and post-opt IR diff against main.
A small standalone probe of the same constructs (`probe/cal.rs`, identity rustc, about 1 s, no build slot) shows the
IR shapes in isolation.

NOFORCE is the number of `land.py` NOFORCE regex matches the edit adds. **A `/*shim: ...*/` comment that names the
construct (for example "black_box") counts too.** Write shim comments without the construct names if the count matters.

## Table (deltas against main 2,251 @ 27,400)

| construct | source form used | pre-opt IR (after MIR) | post-opt IR in execute | dM | dbytes | identical? | NOFORCE |
| --- | --- | --- | --- | ---: | ---: | --- | ---: |
| feature gate `core_intrinsics` | `#![feature(core_intrinsics)]` prepended to lib.rs line 1 | none | none | 0 | 0 | yes | 0 |
| feature gate `link_llvm_intrinsics` | prepended to lib.rs line 1 | none | none | 0 | 0 | yes | 1 |
| unused `extern` llvm.expect.i1 decl | on an existing blank line | none | none | 0 | 0 | yes | 2 |
| `read_volatile` of an account field | `let nf=unsafe{read_volatile(&a.bonding_curve.creator_fee_bps)}` (761) | temporary alloca + `load volatile i64` of the field; SROA removes the temporary | `load volatile` at the same place | 0 | 0 | yes | 1 |
| `read_volatile` of a field (w17a03 v4320) | sweep TCF program clone `owner:read_volatile(&x.owner)` (659) | `load volatile ptr` | `load volatile`; pinned ahead of the Rc stores | +1 | 0 | no | 1 |
| `read_volatile` of a local | `if unsafe{read_volatile(&pool_updated)}` (762) | `load volatile` of the local's alloca | the local stays in an **alloca** (`%x.sroa.0`): a new frame slot shifts the frame | -754 | +216 | no | 1 |
| `read_volatile` of a pointer param (32 B) | `t==unsafe{read_volatile(holder_key)}` (312) | `load volatile [32 x i8]` | a 32 B volatile load is split into 32 byte loads | -510 | +768 | no | 1 |
| unused volatile u8 read (placeholder form) | `unsafe{read_volatile(&holder_key as *const Pubkey as *const u8)};` (581) | `load volatile i8`, result unused | one `ldxb` kept | -3 | +8 | no | 1 |
| `write_volatile` of a field | `write_volatile(&mut curve.can_edit_creator_fee,false)` (758) | `store volatile i8` | same store, same place | 0 | 0 | yes | 1 |
| `black_box` of a value | `let nf=black_box(a.bonding_curve.creator_fee_bps)` | value stored to a new 8 B alloca, `asm sideeffect "" "r,~{memory}"(ptr)`, reload | the alloca survives (frame slot) and memory is clobbered | -6 | +32 | no | 2 |
| `black_box` of a reference | `let nf=*black_box(&a.bonding_curve.creator_fee_bps)` | as above with the pointer | as above | -6 | +40 | no | 2 |
| `black_box(())` (ZST) | (beam cell `fence`, see below) | `asm sideeffect "" "~{memory}"()`: no alloca, no input | a pure compiler memory barrier; emits no instruction | +-0..2 | 0 | varies | 1 |
| `unreachable_unchecked` in an impossible arm | sweep `(false,true)=>unsafe{unreachable_unchecked()}` (660) | `unreachable` target | arm removed | -4 | +8 | no | 1 |
| `if c {unreachable_unchecked()}` as assume | `if holder&&new.is_some(){unreachable_unchecked()}` after validate (339) | a 33 B copy of `new` and the extra test | folded away; LLVM already knows it | 0 | 0 | yes | 1 |
| `core::intrinsics::likely` | `if core::intrinsics::likely(pool_updated)` (762) | `llvm.expect.i1` stored to a 1 B alloca, reloaded before the `br` | **no `!prof`**: the hint is lost (confirms w17a02 #3934) | 0 | 0 | yes | 1 |
| `core::intrinsics::unlikely` | same, `unlikely` | same | no `!prof` | 0 | 0 | yes | 1 |
| `core::intrinsics::assume` | `assume(!(holder&&new.is_some()))` after validate | `&&` is lowered as control flow to build the bool, then `llvm.assume` | the bool-building branches stay; execute reshapes | -257 | -96 | no | 1 |
| extern `llvm.expect.i1` | `if unsafe{expect(pool_updated,true)}` (762) + decl + gate | direct `call i1 @llvm.expect.i1` feeding the `br` | `!prof` 2000:1 survives (confirms w17a02) | -471 | +2,784 | no | 3 |
| `*const` param: validate `holder_key` | `holder_key:*const Pubkey` + `let holder_key=unsafe{&*holder_key};` | only the param attributes change | identical after inlining | 0 | 0 | yes | 0 |
| `*const` param: sweep `holder_key` | same in sweep | same | identical | 0 | 0 | yes | 0 |
| `*const` param: sweep `ctx` | `ctx:*const Context<AdminCto>` + `let ctx=unsafe{&*ctx};` | **MIR changes**: `ctx.accounts` is reloaded at every `a.x` access (no `&` immutability) | the accounts pointer is reloaded in the sweep | -141 | +8 | no | 0 |
| `*const` param: wallet `ctx` | same in wallet | same as sweep (76 changed lines) | reloads in the wallet | -6 | 0 | no | 0 |
| `ptr::write` instead of assignment | `unsafe{ptr::write(&mut curve.creator,target)}` (754) | identical IR | identical | 0 | 0 | yes | 0 |

Probe-only findings (`probe/cal.rs`): `ptr::write`, `ptr::copy_nonoverlapping` and `ptr::read` give the same IR as
plain assignment, and rustc's MergeFunctions aliases the probe functions. A `MaybeUninit` local is promoted like a
plain local. The Option tag byte test (`*(&o as *const Option<u64> as *const u8)&1`) keeps an `and 1` test plus an
`assume(tag==1)`, where `if let Some` gives `icmp eq 1`. `transmute::<Option<bool>,u8>(o)==1` gives
`assume(o<3)` plus `icmp eq 1`, where `unwrap_or(false)` gives `and 1`. A `*const T` param drops
`noalias/readonly/align/dereferenceable` pre-opt; function-attrs restores `readonly nocapture`; and MIR no longer
merges repeated reads through it.

## What the IR beam says about the alphabet (single edits on main's pre-opt IR, see NOTES.md section 2)

- Dropping `noalias`/`dereferenceable`/`readonly` on validate/wallet/sweep params at the IR level is byte-identical
  for every param except sweep's `ctx`, which is what the `*const` source form shows. Once inlined, the noalias
  scopes do not reach the BPF backend (no AA in the DAG, w14a122).
- A volatile load of an **accounts-struct pointer** (the `ctx.accounts` / `a.x` loads) blocks the GVN merge of the
  repeated loads. That collapses (-150..-700 M). A volatile load of the **final field** is almost always byte-identical,
  or a small pin like v4320.
- Volatile stores never help on their own (w17a03 found the same at post-opt).
- Branch weights in validate collapse it (-10..-1,100 M). In execute/wallet/sweep most are byte-identical.
