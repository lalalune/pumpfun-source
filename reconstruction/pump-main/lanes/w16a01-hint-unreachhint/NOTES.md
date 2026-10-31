# w16a01-hint-unreachhint (wave 16)

Target: `0x3b598` `v2_native_payments::ensure_rent_exempt` (416 B, normalized and raw on main), and its three
v2 callers `0x13b9b8` buy_handler, `0x13f630` buy_exact_quote_in_handler and `0x144508` sell_v2. Goal: replace
`if _size != 0 { unsafe { core::hint::unreachable_unchecked() } }` (#1412) with ordinary Rust and keep the build
byte-identical.

## Landing

#3828 merged into main as `9bd38c7d5`. Another agent merged it at 23:00:12Z while `land.py 3828 --allow-neutral`
was verifying. land.py's own merge build (PR head + main 1cc487926) was 1034/1034 with zero losses; it then found
the PR merged and returned `merged: true`. The new baseline `baseline-main-9bd38c7d5` has zero losses against
`baseline-main-1cc487926` and the same stripped sha (`d96c8927...`). Its unstripped sha is `d0c733f6...`, the same as
trial t1.

## Result

The size parameter becomes a safe zero-only type, used where the rent minimum is computed:

```rust
pub fn ensure_rent_exempt<'info>(size: ZeroRentSize, ..) -> Result<()> {
    let minimum = Rent::get()?.minimum_balance(size as usize);
    ..
}
#[repr(usize)]
pub enum ZeroRentSize { Zero = 0 }
```

The three callers pass `native_payments::ZeroRentSize::Zero` instead of `0`, on the same lines. Nothing follows the
call on those lines, so no panic `Location` moves.

| build (base e61121452 = 9120883a9 programs/) | normalized / raw | losses | admin_cto | swap_hop | stripped candidate.so sha256 | unstripped sha256 |
| --- | --- | --- | --- | --- | --- | --- |
| main baseline (unsafe hint) | 1034 / 1034 | - | 0.67376 / 3124 / 27,400 B | 1.0 / 0 / 18,584 B | `d96c8927...7cd3b8` | `dc79dde7...d095c8c` |
| t1 `ZeroRentSize` (this PR) | 1034 / 1034 | none | 0.67376 / 3124 / 27,400 B | 1.0 / 0 / 18,584 B | `d96c8927...7cd3b8` (identical) | `d0c733f6...51ff5` |

The stripped program is byte-identical. The unstripped ELF differs in 15 bytes of `.strtab`: the helper's
legacy-mangling hash goes from `h689afedc8db3f484` to `h7cc49ba9a19934cf`, because rustc hashes the function
signature into the symbol. Every section, address and other symbol is unchanged. No safe spelling can keep a
`usize` parameter, because a plain `usize` has no zero-only invariant without a runtime check (see the table).
The codegen-forcing count under `programs/` (land.py NOFORCE) drops from 6 to 5.

## Why the original keeps the argument (IR evidence)

Captured with `-print-before/after=deadargelim` on copies of the crate (lane-local `capture_ir.py`, never in source):

- The helper is `define hidden { i64, ptr } @..ensure_rent_exempt..(i64 noundef %0, ..)`. It has external
  (hidden) linkage because its callers are reachable, inlinable program items, so IPSCCP cannot track its
  arguments. `pub(crate)` produces the same binary (t3 = t2, sha `5d832ac1`).
- No hint (t0): before DeadArgumentElimination `%_size` has no use. DAE's `removeDeadArgumentsFromCallers` (which
  also applies to non-local exact definitions) then strips `noundef` and rewrites all three call sites to
  `call @..ensure_rent_exempt..(i64 poison, ..)`. The callers lose `mov r2,0` and its reuse for the `None` spill:
  1031 / 301, losses `0x13b9b8 0x13f630 0x144508`.
- Zero type (t1): rustc's MIR builder lowers `enum as int` to `discriminant` plus `assume(discr <= max)` whenever the
  tag's valid range is not the whole integer. With the single value 0 the IR is
  `%_14 = icmp eq i64 %0, 0; call void @llvm.assume(i1 %_14)`. This is the same no-code use the unsafe hint produced,
  so DAE keeps the argument and the call sites pass `i64 noundef 0`. GVN folds the cast to 0 at the
  `minimum_balance(.., i64 noundef 0)` call, so the body keeps the original `mov64 r2, 0x0`.

The helper sits in the main crate's object in default codegen order (it is not in `link/ordered.ld`). So the original
also compiled it in the same LLVM module as its callers, and its source needed a no-code use of the size at DAE time:
an assume-style invariant like the hint, or a range-restricted type like this one. The bytes cannot tell these apart,
so this PR keeps the safe form.

## Forms tried

This lane's rows were measured on current main with `measure.sh`. Rows marked RA come from the rent-argument lane
(Jonas van Ravenstein, commits `f2b5c234d` and `bb2302976`, ref `pr/1384`, `reconstruction/pump-main/lanes/rent-argument/`
on that ref), which first found the zero-only type on base 381dc30/094a06f but was never merged.

| form | result | IR reason |
| --- | --- | --- |
| t0: drop the hint, `_size` unused | 1031/301, callers 13b9b8 13f630 144508 lost | no use at DAE, so call-site args become `poison` |
| t2: `minimum_balance(size)`, `size: usize` | 1033/343, helper lost (432 B, ratio 0.7925) | hidden linkage, so no IPSCCP fold: body keeps size in r8 and passes `mov r2,r8` |
| t3: t2 as `pub(crate)` | identical to t2 | still hidden: the callers are exported program items |
| RA: `#[no_mangle] extern "C"` | no loss, callers worse | DAE poisons call sites of exact external definitions too |
| RA: `extern "C"` ABI | same as control | as t0 |
| RA: function-pointer use (address taken) | same as control | DAE marks it live, but still poisons unused args at direct calls |
| RA: generic size parameter | 3 windows lost | instantiation is internal: IPSCCP and ArgPromotion reshape the helper |
| RA: `assert_eq!(size, 0)` | helper lost | panic path adds code |
| RA: zero-only enum, ignored in the body | same as control | no use of the enum |
| RA: separate path crate (helper + transfer) | 88 raw lost | new object moves layout; also needs Cargo.lock edges |
| t1: zero-only enum cast in `minimum_balance` (selected) | 1034/1034, 0 losses, stripped identical | enum-cast assume `icmp eq %0, 0`, so the arg stays live and folds to 0 |

## Ledger

`0x3b598-w16-e611214-unreachhint-zerorentsize-enum-cast-v1` (built), `-control-nohint-v1`, `-usesize-pubfn-v1`,
`-usesize-pubcrate-v1` (rejected).
