# Lane w6r1-layout-order (wave 6, round 1): function order and placement for raw

Base: origin/main 099b0dd (1027 normalized / 276 raw; 8 unmatched windows). Tools in `tools/` are
small scripts on top of layout-order-census's `census.py`/`refine.py`/`fastmodel.py` and
w3-raw-layout's `m13.py` (copied under `$OUT/tools`, `UNMATCHED_NAMES` cut to the 8 open windows).
The model reproduces the official raw set (276) exactly.

## Why the 751 normalized-only windows are not raw (model census on 099b0dd)

| class | windows | blocker |
| --- | ---: | --- |
| data lddw (.rodata / .data.rel.ro pointer) | 601 | section bases move with `.text` size: cand 0x1b5a10 vs orig 0x1b58d0 (+320 B) |
| call-only | 150 | call distance crosses a size delta, a misplaced handler, or U/D hash order |

`.text` +320 = unmatched size deltas (-192: create_v2 +8, admin_cto +16, swap_hop -256, sweep +48,
v3_buy_costs +16, buy_handler +32, buy_exact_quote_in +32, v3 buy_exact_quote -88) + one ours-only unit,
the 512-B `v2_native_payments::ensure_rent_exempt` black_box wrapper (+512).

What order alone can do at today's sizes (`scen3.py`, `scen5.py`, `movebrute.py`, `extrapos.py`):
- L (local) order is already the original's except the five v2/v3 handler bodies (at their module
  position, about 53 KB away from the original's #[program] position) and the two `pay_out_native`
  instances (symbol-hash order). Moving them: +0 raw now.
- Moving any one of the 8 unmatched functions or the extra unit to any L position: max 276, +0.
- Full original order at today's sizes: 293 (+3 from U hash order, +14 from D hash order). Both are
  symbol-hash order of generic instances, fixed by crate metadata, not reachable from source.

So official raw cannot rise through order changes until the unmatched windows reach their sizes.

## Kept: drop the ensure_rent_exempt wrapper (`857b6b91`)

The matched twin `ensure_rent_exempt_matched` (window 0x3b598) already keeps `_size` live through
DeadArgElim with its `if _size != 0 { unreachable_unchecked() }` hint, so the callers (buy_handler,
buy_exact_quote_in_handler, sell_v2) can call it directly. The wrapper (`size == usize::MAX` arm +
`black_box(size).wrapping_mul(0)`) is deleted and the twin renamed to `ensure_rent_exempt`.

| metric | main 099b0dd | this lane |
| --- | ---: | ---: |
| official normalized / raw | 1027 / 276 | 1027 / 276, 0 gains, 0 losses |
| 8 unmatched windows (bytes, ratio) | | all identical |
| ours-only units | 1 (512 B) | 0 |
| `.text` size vs original | +320 | -192 (= sum of unmatched deltas) |
| model raw once the 8 match in size, our order | 276 | **429** |
| same, handlers at #[program] position | 326 | **653** |
| model raw, full original order, sizes fixed | 1022 | 1023 |

Before this change, fixing all 8 unmatched windows would still have left `.text` 512 B long and every
data window non-raw. Unstripped sha256 8e56a1bcc1f85140...

## Kept: four handler bodies at the #[program] position (`2a9710aa`, `cbded140`, `401dc71c`)

The original keeps the v2/v3 handler bodies inside the #[program] module run (between `create` and
`buy`), with their closures at the module position: the module fn is inlined into an outlined program
fn. Four of the five now sit there with normalized-identical bodies:

| program fn (`#[inline(never)]`) | inlined body (`#[inline(always)]`) | window | body sha1 (normalized) |
| --- | --- | --- | --- |
| `sell_v3` | `pub(crate) trade::sell` | 0x14a8a8 (matched) | cef4e59f, unchanged |
| `buy_v3` | `pub(crate) trade::buy` | 0x147ba0 (matched) | dd61133e, unchanged |
| `buy_exact_quote_in_v3` | `pub(crate) trade::buy_exact_quote` | 0x1489f8 (unmatched) | 9b71a475, unchanged (0.66033) |
| `buy_exact_quote_in_v2` | private `buy_exact_quote_in_handler` (via `buy_v2::execute`) | 0x13f630 (unmatched) | 949506f1, unchanged (0.99635) |

**Why the v3 program-fn form used to fail** (w3-raw-layout `f2409d8a`, layout-order-census `310c3a1f`:
loses 0x147ba0 and 0x859b0 `v3_emit_buy`): an `#[inline(always)] pub fn` in a crate that is also a `lib`
is inlinable by downstream crates, so every private item it calls becomes reachable and gets exported.
`v3_emit_buy` turned from `define internal fastcc` into `define hidden` (IR in `$OUT/cap/t03` vs `cap/t04`),
which turned off ArgPromotion of `ctx` (ctx.accounts + ctx.bumps): r2 got the ctx pointer, the stack
args dropped from 8 to 7, and the callers' register assignment changed. `pub(crate)` on the inlined trade
fns keeps the callees internal and the codegen identical. The same applies to any handler that is
moved into its program fn: the inlined fn must not be `pub`.

| metric | after the wrapper fix | + four program-position bodies |
| --- | ---: | ---: |
| official normalized / raw | 1027 / 276 | 1027 / 276, 0 gains, 0 losses |
| 8 unmatched windows (bytes, ratio) | | all identical |
| L adjacent order: LIS of 482 | 476 | 480 |
| model raw once the 8 match (our order) | 429 | 432 |
| same + buy_handler at the program position | 527 | **648** |

### Not kept: buy_handler in program-fn form (`d6daced5`, t10)
With `buy_v2` as `#[inline(never)]` and `buy_handler` `#[inline(always)]` (through `execute` or called
directly), the body moves to the program position but grows 15512 -> 15520 B (0.97998 -> 0.97129): one of
two consecutive checked adds near buy_v2.rs:345 (original 0x13d130..0x13d198, `a+b` then `+c`) loses its
second overflow check, plus scheduler swaps. buy_handler is private, so this is not the reachability
effect. It also gives raw 0xa868 (the call-displacement coincidence window). This is the last L-order item
worth +217 model raw; it belongs with the buy_handler lanes (diff in `$OUT/out/t05-bh.diff`).

IR (`$OUT/cap/t03` module form vs `cap/t13` program form, `tools/irent.py`): with rustc 1.79-dev, big
`#[inline(always)]` bodies are inlined by LLVM, not by the MIR inliner (`.i` value names,
`noalias.scope.decl`). trade::buy_body is already inlined that way into trade::buy. In program form the
handler is LLVM-inlined into buy_v2, which adds:
- 4 entry `lifetime.start`s for callee allocas that have no markers (`_413` 48 B, emit_cpi!'s `inner_data`
  24 B and `authority_info` 48 B, `creator` 32 B)
- `!noalias` scope metadata from the inlined `noalias ctx` parameter.
buy_exact_quote_in_handler gets the same 4 entry starts, but its code does not change. In buy_handler the
first 498 instructions are equal, and then block placement differs around the checked adds.

| trial | result |
| --- | --- |
| t05 / t10 program fn through `execute` / direct call | 15520 / 0.97129, raw +0xa868 |
| t12 OptionBool passed into the handler | same |
| t13 `input` immutable + `let mut input=input` | same |
| t14 / t15 `#[inline]` / no attribute on the handler | byte-identical to `#[inline(always)]` |
| t19 `{emit!(ev);emit_cpi!(ev);}` block | same |
| t18 `creator` local removed | 0.79378 (much worse) |
| t17 (accidental) thin outlined buy_v2 wrapper around the outlined handler | raw +7 (U->D call windows), but only because the extra unit changes the L size: ballast, rejected |

Handler lanes: measure the final buy_handler in program-fn form, since that is where the original has it.

## Rebased on main 1ef1727 (`6db716dd`)
After the rebase: 1027/276 with 0 losses against main 1ef1727, and the unmatched windows are identical
to main (create_v2 0.82553, admin_cto 0.37637). `.text` -304 B vs the original. Data offsets: 1027 of 1027
windows already point at the original in-section offsets (#2169 fixed the last `.data.rel.ro` pair).
Model raw once the 8 match: 432 (our order), 649 (+ buy_handler), 654 (+ pay_out_native), 1023 (full
original order). The 1023 - 654 gap is U/D symbol-hash order.

## Kept: 0x2bc0 as the upstream generic `Error::with_account_name::<String>` (`0x2bc0-...-trailing-cold-identity-v1`)

The original's 0x2bc0 sits in the U block (upstream generic instances, sorted by symbol) between the
other `anchor_lang::error::Error::with_account_name` instances. Its body is two `String::clone` calls and no
drop. That is `with_account_name::<String>`: `String::to_string` is the specialized clone, and the String
drop disappears because the Solana bump allocator's `dealloc` is a no-op. Earlier attempts used `&String`
(`6fc0151b`, callgraph-census), which goes through the Display-based `ToString`, a different body, and it was
inlined anyway.

The original calls it from set_reserved_fee_recipients at a **cold** call site, where the cold-site
threshold (45) keeps both `alloc::fmt::format` and `with_account_name` outlined. The executable-check site
calls the same instance and inlines it. Source now:

```rust
return Err(rent_exempt_error(Error::from(ErrorCode::ConstraintRentExempt).with_account_name(format!("reserved_fee_recipients[{}]", index))));
...
#[cold] fn rent_exempt_error(error: Error) -> Error {
    error
}
```

The trailing `#[cold]` identity call makes the block cold while the inliner looks at the earlier
`format`/`with_account_name` call sites, and then it inlines away to nothing. The local `with_owned_name` and
`util/account_name.rs` are gone.

| trial | result |
| --- | --- |
| t20 cold helper with `error.with_account_name(name)` inside | with_account_name inlined into the helper; the 232-B helper sits in L; loses 0x6fef8 |
| t21 direct `.with_account_name(format!(..))` | inlined at both sites; loses 0x2bc0, 0x6fef8 |
| t22 `#[cold]` name builder `rent_exempt_name(index)` | with_account_name outlined in U (correct), but the 160-B builder stays outlined; loses 0x6fef8 |
| t23 `#[cold] #[inline(always)]` helper | same as t21 |
| **t24/t25 trailing `#[cold]` identity** | **0 losses; 0x2bc0 matched by the U-block generic** |

Model: P8 432 -> **452**; with buy_handler at the program position 649 -> **671**; also with pay_out_native
654 -> 677. Unstripped dcdcc13c754e7b81 (stripped candidate 9a24fc1e, the same with or without the dead module).

## Kept: `shareholders.to_vec()` (`f059ac34`)

The original U unit 0xcf18 (336 B, same body as our `<Vec<Shareholder> as Clone>::clone`) sits between
`<u64 as BorshDeserialize>` and `<bool as BorshDeserialize>`, which `_ZN67_..Vec..Clone..clone` cannot do in
symbol order. The original spelled the 5 event copies in distribute_creator_fees.rs and
distribute_creator_fee_v2.rs as `shareholders.to_vec()`. That outlines `<T as alloc::slice::hack::ConvertVec>::to_vec`,
which now lands at candidate 0xcf18, the original address. 0 losses, unmatched windows identical. Model P8
452 -> **462**; with buy_handler + pay_out_native 677 -> **702**.

`tools/uanom.py` lists U units whose original neighbours break symbol order (non-hash anomalies). Only three
are left, all `drop_in_place<pump_recovered::..>`: Migrate, AdminCto and Option<PreviousHop>. Each fits the
original's order exactly if the root crate name is 10 characters shorter (`pump`). For example,
`_ZN4core3ptr43drop_in_place<pump::migrate::Migrate>` falls between `..42..std::io::Error` and
`..46..anchor_lang::Error`. That is more evidence that the original crate was named `pump`. The model value is only +3,
and a rename needs Cargo identity and harness changes, so it was not attempted.

## Kept: pay_out_native pair in def order (`raw-main-1ef1727-pay-out-native-owned-fn-before-generic-v1`)

The two instances of the generic `pay_out_native` (856 B for `&AccountInfo`, 1080 B for `AccountInfo` with Rc
drops) were in symbol-hash order, but the original has the 1080-B one first. By-value callers (multi_hop
`to.clone()`/`to_account_info()`, trade_v3 buyback, `transfer_to_owned`) now call a non-generic
`pay_out_native_owned`, defined just before the generic. Def order puts it first. By-reference callers keep the
generic: a non-generic `&AccountInfo` version (t28) resolves `add_lamports` with `Self=AccountInfo` and loses
0x969f0. 0 losses, and the line count of curve_quote_payments.rs is unchanged. The L block now matches the
original order except buy_handler (LIS 480 of 481 paired). Model with buy_handler moved: 696 -> **702**.

## Rebased on main 75b6547 (`17b90005`)
1027/276 with 0 losses against main 75b6547; all 8 unmatched windows identical to main (create_v2 now
0.851 at its original size, swap_hop 0.7332). `.text` -56 B vs the original (main: +456 B). Model raw once the
8 match: 462 (our order), 702 (+ buy_handler), 1023 (full order). U hash order is worth +280 and D +41.
