# Lane layout-order-census: function order and data layout, preparing the raw step

Baseline: origin/main d2cb88d (`$BASE/unstripped.so`, 1019 normalized / 188 raw, 831 normalized-only).
Analysis only so far: no maintained source changes. Tools in `tools/` (paths point at this lane's
`$OUT=~/.cache/pumpfun-reconstruction/lanes/layout-order-census`; they reuse the harness `score.py` masking).

| file | what |
| --- | --- |
| `tools/census.py`, `tools/refine.py` | pair all 1035 original windows with candidate units (normalized class, then callee-consistency and pointee-bytes refinement for the 62 ambiguous classes; the 16 unmatched pinned by name). Result: 8218 call operands point at the paired callee, 1226 identical immediates, 6 inconsistent (ambiguity residue). |
| `tools/predict.py` | layout model: recompute every unit address for a hypothetical order/size set and re-check every masked operand of the 1019 matched windows (relative call distance, absolute `.text` lddw, data lddw). Reproduces the official 188 raw on the baseline exactly. |
| `tools/breaks.py` | adjacent-pair order breaks, classified. Output: `order-breaks-baseline.txt`. |
| `tools/rodiff.py` | byte alignment of `.rodata`. Output: `rodata-diff-baseline.txt`. |
| `tools/xbuild.py`, `tools/rustc-linuxvv`, `tools/rustc-linux-v2` | experiment-only builder (crate rename, Linux-host cargo metadata shims). Never a proposal recipe. |
| `predict-baseline.txt` | all model scenarios below. |

## 1. How the compiler orders functions (verified on our build)

- Main crate = one CGU (codegen-units=1). Inside it rustc emits mono items sorted by
  `(local def index or None, symbol name)`:
  - **U block** (0x120..0x149e0, 142 units): instances of *upstream* generic items
    (`anchor_lang`, `core`, `alloc`, `borsh` ...) sorted by mangled name, hence by the legacy
    `17h<hash>` suffix within one generic (`Account<T>::try_from` x9, `Error::with_values` x6, ...).
    That hash mixes in the instantiating crate's StableCrateId (crate name plus Cargo `-C metadata`)
    and the def-path hashes of the type arguments.
  - **L block** (0x149e0..0x17c930, 483 units): local items in def-index order. That is source order
    with `mod` files expanded in place, and derive/attribute-macro output (`Accounts`
    `try_accounts`/`exit`, `Event::data`) in a second pass after all hand-written items.
    Closures of one function are sorted by hash.
- **D block** (after `__rust_alloc_error_handler`, 410 units): dependency objects in link order.
  Inside each one the order is again by symbol hash, fixed by the dependency's own metadata.

## 2. Order census (original vs baseline)

- 291 adjacent-pair breaks: 166 main-local (def order), 62 main same-generic (hash), 31 main
  upstream, 14+13+2 dependency, 3 mixed. LIS of the paired order = 854/1035.
- Hash groups with 2 or more members whose internal order differs from the original:
  U 16/18, L 1/16 (closures), D 6/27.
- Two units sit in a different block in the original:
  - `0x2bc0` = our local `account_name::with_owned_name`. The original has it in the U block,
    between the `Error::with_account_name` instances. It is the upstream generic
    `Error::with_account_name::<&String>` (same body), not a local helper.
  - `0x17c0f0` = `migrate_v2::required_quote_account_len`. The original has it after
    `pump_token_ext`, so it was compiled in another crate or CGU, not the root's local block.
- Structural facts in the original's local order:
  1. The six unmatched v2/v3 handlers (`0x13b9b8` buy_v2, `0x13f630` buy_exact_quote_in_v2,
     `0x144508` sell_v2, `0x147ba0` buy_v3, `0x1489f8` buy_exact_quote_v3, `0x14a8a8` sell_v3)
     lie inside the `#[program]` module run, between program fns `create` (`0x138b20`) and `buy`
     (`0x14c038`), in instruction order. In the original they *are* the `#[program]` fns: the
     handler body lives in, or is inlined into, the program fn. In our build these are module
     functions (`buy_v2::buy_handler` at 0x16c88 ...) and the program wrappers are inlined into the
     dispatchers. Their closures stay at the module site (0x16bb8 ...).
  2. The original has one contiguous run of payment/transfer helpers (0x8b818..0x95610:
     `transfer_native*`, `transfer_*_tokens*`, `transfer_*_out` from user_quote_payments, migrate,
     legacy_buy, collect_v2, multi_hop_curve, buy_v2, sell_v2). Our build spreads them over 9
     modules. In the original they shared one def-order position, which points to shared, probably
     generic, helpers.
  3. Otherwise the module sequence is the same as ours, in both the hand-written pass and the
     derive pass. The original module runs are listed in `module-runs-baseline.txt`.
- 8 units exist only in our build (12,824 B): `multi_hop_curve::{add,sub,div,move_lamports}`, three
  `multi_hop_curve::route_event` instances, and `anchor_lang::Lamports::add_lamports`.
  The original inlines them. They are the 0xa10 `.text` surplus beyond the 16 size deltas
  (0x1b62e0 vs 0x1b58d0).

## 3. Data layout census

- `.data.rel.ro` has the same size (0x2870). 1328 of 1453 differing data.rel.ro pointers have the
  same offset; the rest are swapped vtable/entry pairs. `.rodata` is 40 B smaller (0x7cf7 vs 0x7d1f).
  Its base moves with `.text` size (+0xa10), so every one of 593 data-pointer windows fails today.
- `.rodata` byte alignment (`rodata-diff-baseline.txt`): 31,379 of 32,031 bytes align. The
  differences are (a) order of string literals (`programs/pump/src/*.rs` paths, account-name
  seeds, error messages) and 32-byte Pubkey constants, all of which follow first-use order in
  function order; (b) a few literals present only on one side, e.g. our second
  `called \`Result::unwrap()\` on an \`Err\` value` and 5 zero bytes.

## 4. Raw prediction (model, `predict-baseline.txt`)

| scenario | raw of 1019 |
| --- | ---: |
| S0 baseline as built (model check) | **188** (= official) |
| S2b all 16 matched in size+code, 8 extras gone, data identical, **our order** | 286 |
| ... + original order inside L only | 646 |
| ... + original order inside U+L | 965 |
| S3 full original order | 1014 (5 residual = pairing ambiguity) |
| S7c original order except U hash groups kept in our hash order | 759 |
| S7d original order except L closure groups in our hash order | 1006 |
| C1 today's sizes/data + original L order | 272 |
| C2 today + original U order | 191 |
| C4 today + full original order | 293 |

So once the 16 match, **order rather than size is the main obstacle** (733 of 1019 windows fail on
call distance). The U block's hash order alone costs about 255 windows, and only the original
crate identity can restore it.

## 5. Experiments (ledger)

| attempt | result |
| --- | --- |
| `730dc227` model census | analyzed (above) |
| `5785b0ba` Linux-host cargo metadata (`rustc -vV` host shim, experiment only) | 1019/183 (raw +2 −7). The shim reproduces the AMM metadata map's Linux values (typenum `48277d0b39ab7f75`, cfg_if `4938d2d8ea051e56`). U-order agreement unchanged (3/18 groups). |
| `8f9651c8` crate renamed `pump` (+ `#[program] mod pump`), mac metadata | U groups 2/18, pairwise 126/231 (chance) |
| crate `pump` + Linux `-vV` shim | 3/18, 123/231 |
| crate `pump` + speed-lane shim v2 (Linux `-vV` + host `--print=cfg` + cpufeatures libc) | 2/18, 133/231 |

The U-block hash order depends on the root StableCrateId and on every upstream crate's metadata
(anchor-lang features, the Cargo.lock graph, RUSTFLAGS in cargo 1.79's metadata, the workspace path).
"pump/0.1.0 on Linux" does not reproduce it. With no original Cargo inputs, this part of raw order
cannot be reached through `programs/pump` source. The other programs reached whole-ELF identity
through ordered link scripts (`programs/{mayhem,pump-fees}/build_exact.py`, AMM `ordered-native.ld`).

## 6. What a source change could still do

- Order levers that keep line numbers: (1) permute `mod` lines in lib.rs lines 1-63. Module order
  already matches, so expect no gain. (2) Put each v2/v3 handler body in its `#[program]` fn, or
  make it inline into a non-inlined program fn. That needs code-level work in the unmatched-handler
  lanes; on its own it gives +0 raw in the model (C5) until the rest of L order matches.
  (3) Use `error.with_account_name(name)` instead of `account_name::with_owned_name`. That moves 0x2bc0 into the U block,
  where the original has it.
- Raw gains before the 16 match are limited to call-only windows. The model ceiling with today's
  sizes and data is 293 (full original order), 272 with L order alone.

### Source trial: upstream generic for 0x2bc0 (`6fc0151b`, rejected)
Replacing `account_name::with_owned_name(error, &name)` with `error.with_account_name(&name)` gives
1018/188 against the main HEAD control's 1020/188. It loses 0x2bc0 and 0x6fef8 because the generic
instance gets inlined into `set_reserved_fee_recipients`. In the original the instance is outlined and
sits in the U block, so the original call site must look different (for example, a second caller keeps
it out of line).

## Round 2: the L tail (raw 188 -> 276, zero losses)

Base: origin/main 65826a7c (1020 normalized / 188 raw). New fast model `tools/fastmodel.py`
(reproduces the official raw set exactly; 0.5 ms per layout) and `tools/moves.py` (apply
source-level unit moves, report raw/P16/LIS).

### Suffix census (`tools/suffix.py`)
A window whose callees all lie in the L tail or in D only depends on the layout from itself to D.
Putting the original order on the L suffix starting at `__rust_alloc` (orig 0x156fe8) gives +84
raw with today's sizes and zero losses; no other suffix start gives anything in between
(+4 at `__rust_realloc`, +84 from `__rust_alloc`, flat before). `tools/taildiff.py` lists what
differs in that suffix:

| needed change | why |
| --- | --- |
| `migrate_v2::required_quote_account_len` into the `pump_token_ext` crate, after `quote_extensions_supported` and before `Fee` | the original has it inside the pump_token_ext object (0x17bc48 qes, 0x17c0f0 rqal, 0x17c3d8 Fee::calculate_fee) |
| `CompleteEvent`, `PostCompleteBuyEvent`, `SetParamsEvent` defined in lib.rs right after `TradeEvent` | their `Event::data` sit after TradeEvent in the original derive pass |
| `AdminGlobal` between `Initialize` and `Create`; `LegacySell` after `LegacyBuy` (lib.rs) | original tail derive order |
| `AdminReadonly` (end of sell_v2.rs), `UpdateGlobalAuthority` (global_init.rs), `CloseUserVolume` (end of claim_token_incentives.rs), `CollectCreatorFee` (start of collect_creator_fee.rs) and `CollectCreatorFeeEvent` (end of it) out of the lib.rs tail | original places their derives in the module derive run |
| the 14-account `ToAccountInfos::to_account_infos` survivor must be pump_amm's `InitBoost` | see below |

### MergeFunctions survivor rule (new finding)
Identical `to_account_infos` bodies are merged by LLVM MergeFunctions, which keeps the function
with the lexicographically smallest mangled name. Groups in our build confirm it (SetCreator `_ZN122`
over `_ZN134/146/154`, CollectCreatorFeeV2 `_ZN141` over `_ZN155/162/163/172`, GetFees `_ZN124`,
CreatePool `_ZN129`, CollectCoinCreatorFee `_ZN153` over `_ZN158`). Today root `Create`
(`_ZN100_$LT$pump_recovered..__cpi_client_accounts_create..Create`) beats pump_amm `InitBoost`
(`_ZN127`) and LegacySell (`_ZN122`), so the survivor sits in the tail. The original keeps it at the
pump_amm position (orig 0x113f00, between InitBoost metas and TransferCreatorFeesToPumpV2), which
fits a root crate named `pump` (Create would be `_ZN90`). Source fix: Create/LegacyBuy/LegacySell
live in a lib.rs module `bonding_curve_instruction_accounts` (glob re-exported), making their names
`_ZN13x`, so InitBoost survives in place.

### Result (`tools/tail_relocate.py --wrap`, all moves line-neutral)
| build | normalized | raw | gains | losses | unstripped sha256 |
| --- | ---: | ---: | --- | --- | --- |
| main 65826a7c | 1020 | 188 | | | 65826a7c... |
| relocation without the module wrap (`fb2ed22e`) | 1020 | 192 | raw +4 | 0 | b26d5f30... |
| relocation + module wrap (`7f028dee`) | 1020 | **276** | raw +88 | 0 | 017b902d... |

The tail windows depend only on tail + D, so these 88 survive any future fix of the 16 mid-L
functions.

### v2 handlers outlined as the #[program] fns (`0fe43b05`, kept; `310c3a1f` all six, rejected)
Round 1 found the six unmatched v2/v3 handlers inside the original's #[program] module run. Putting
`#[inline(never)]` on the program fns and `#[inline(always)]` on the module handlers makes the program
fn the outlined unit (Source sites stay in the handler files, closures stay at the module site):

| window | before (ratio, bytes) | after | orig bytes |
| --- | --- | --- | ---: |
| 0x13b9b8 buy_v2 | 0.94776, 15464 | **0.95384, 15472** | 15480 |
| 0x13f630 buy_exact_quote_in_v2 | 0.97361, 20168 | **0.97889**, 20168 | 20184 |
| 0x144508 sell_v2 | 0.86599, 13952 | **0.87883**, 13952 | 13976 |

Official 1020/276 unchanged, no losses (unstripped 6048baa7...). Doing the same for the v3 trio
(trade::buy/buy_exact_quote/sell) is worse (buy 0.876 -> 0.778) and loses 0x859b0 `v3_emit_buy`, so
the v3 handlers stay as they are (`tools/handlers_as_program_fns_all6.py` reproduces the rejected one).

### Data layout: MAYHEM_ID as a static (`rodata-main-ef8e276-mayhem-id-static-v1`, kept)
`tools/dwe.py` counts matched windows whose data lddw already point at the original's in-section
offsets (they turn raw once .text size and section bases match). The first `.rodata` difference was
MAYHEM_ID: ours sat in the merged 32-byte constant pool at 0x2b8, while the original has it in the
align-1 stream right after "Global", next to the `declare_id!`/`declare_program!` ID statics. Making it
`pub static` moves it there: equal-offset data windows 105 -> 156 of 593, mismatched .rodata operands
3113 -> 2053, official 1020/276 unchanged (unstripped 3e02f014...). The pool region (< 0xd80) now
differs only by five swapped 4-byte constants (lld shard order follows first use). No other pubkey sits
in the wrong region. The string stream after 0xd80 follows first-use order; in the original it starts
with `admin_set_idl_authority.rs`, `buy.rs`, `buy_v2.rs`, `create_v2.rs`, `creator/admin_cto.rs` (file
order), which our module order does not reproduce yet.

### Def-order prep: module mounts (`eda8f43e`, kept)
Pairing fix in `tools/census.py`: the v2 handlers are now pinned under their program-fn names too.
P16 = model raw once all 16 match in size and code, extras gone, data equal, our order (U and D as
built). With that pairing, the handler commit kept P16 at 415 and raised LIS 871 -> 874 (breaks 150 -> 144).
`tools/def_order_mounts.py` (all line-neutral) then:
- mounts `util/fee.rs` after `constant_product` and moves `trade_fees` into it between `fee` and
  `calculate_fee_tier` (the original's run 0x88908..0x89ec8 has `util/fee.rs` sites there)
- mounts `account_name` first, so `with_owned_name` (0x2bc0, in the original's upstream-generic block)
  precedes all local code
- mounts `fee_recipient.rs` after `extend` (original run: extend, fee_recipient, migrate)
- defines `prepare_bonding_curve` in extend_account.rs between `execute` and `fund_bonding_curve_rent`
  (original 0x3b8d8, 0x3cd50, 0x3d250)

Official 1020/276 unchanged, no losses (unstripped 6e1f13e4...). P16 415 -> 423, LIS 874 -> 881, L adjacent
breaks 144 -> 136. With U and D as built, the source-only P16 ceiling (original L order) is about 647;
a full original order is 1014.

### The original's module list is sorted by file path (`d39235b3`, kept)
The original's derive pass and its .rodata file strings both follow the file paths in alphabetical
order, which is what rustfmt's `reorder_modules` produces for a lib.rs `mod` list:
- derive pass: AdminSetIdlAuthority (`admin_set_idl_authority.rs`) first, then buy_v2, create_v2,
  creator/admin_cto, CollectCreatorFee, creator/collect..., creator/distribute..., creator/migrate...,
  creator/set_*, extend_account, `mayhem_virtual_params` (between extend and migrate), migrate,
  migrate_v2, multi_hop..., quote_control, sell_v2, AdminReadonly (set_reserved_fee_recipients.rs),
  sweep_fees, token_incentives/..., trade_v3, then the lib.rs body (declare_program!, entry, program, ...)
- `.rodata` string stream from 0xdeb: `programs/pump/src/admin_set_idl_authority.rs`, `buy.rs`, `buy_v2.rs`,
  `create_v2.rs`, `creator/admin_cto.rs`, `creator/collect...`, `creator/distribute...`, `creator/migrate...`,
  ..., `extend_account.rs`, `fee_recipient.rs`, `migrate.rs`, ... Our stream starts with `buy_v2.rs`.

`tools/alphabetical_mounts.py` mounts `idl_authority` first, `mayhem_virtual_params` after `fee_recipient`, and
moves `BondingCurve::sync_virtual_quote_reserves` (no sites) next to `reserved_bonding_curve_fees` (lib.rs), where
the original's hand-written order has it. Official 1020/276, no losses (unstripped ab7d1ade...). LIS 881 -> 886,
breaks 136 -> 131, mismatched `.data.rel.ro` operands **125 -> 42**, `.rodata` 2051 -> 2008, equal-offset data
windows 156 -> 157.

### Rebased on main ef400863 (round-1 PR #1260 merged at b65ea16)
After the merge, the buy_v2 trio gained from buyv2-sibling-transplant. Re-measured there, outlining helps
only sell_v2, so buy_v2 and buy_exact_quote_in_v2 are back to main's attributes (`fc077350`).

| metric (vs main ef400863) | main | this branch |
| --- | ---: | ---: |
| official normalized / raw | 1020 / 188 | 1020 / **276** (raw +88, 0 losses) |
| 0x144508 sell_v2 ratio | 0.93984 | 0.95152 |
| P16 (model raw once the 16 match) | 286 | 416 |
| LIS / L adjacent breaks | 854 / 167 | 884 / 136 |
| equal-offset data windows (of 593) | 163 | 257 |
| mismatched .rodata / .data.rel.ro operands | 2758 / 125 | 1457 / 42 |

Unstripped sha256 37a078b8c743a0cc95c8aefc145d5b2e497a967fe39ae7e7f084ff513d5cb432. Main's .rodata is now the
original's size (0x7d1f).

### Rejected in round 2
- all six handlers as program fns (`310c3a1f`): v3 trio worse, loses 0x859b0
- `buy_exact_sol_in` without `#[inline]` (`ba219e5d`), with or without mounting buy.rs second: loses 0x14f4e0
- MAYHEM_ID static defined in the lib.rs body (`178c5a67`): no data-layout change
