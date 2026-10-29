# Lane w3-raw-layout (wave 3): whole-program raw layout

Started from origin/main 665499915 (1022 / 276) and was rebased three times. It is now on 2c8a7900f
(1023 normalized / 277 raw; 12 unmatched windows). All changes move code without changing line
numbers. There are zero normalized or raw losses, and all 12 unmatched windows keep their exact
ratio and size (`tools/unm13.sh`).

Official raw cannot move until the unmatched windows reach their original sizes. `.text` differs
from the original by a few hundred bytes, all of it from the size deltas of the unmatched windows. The lane
therefore measures layout readiness with the model (`tools/m13.py` builds on layout-order-census's
`fastmodel.py`, which reproduces the official raw set exactly).

## Metrics

| metric | main 2c8a790 | this lane |
| --- | ---: | ---: |
| official normalized / raw | 1023 / 277 | 1023 / 277 |
| data-offset-equal windows (every data lddw already at the original's in-section offset) | 683 | **1021** of 1023 |
| `.rodata` bytes aligned with the original (of 32031) | 31682 | 31993 |
| `.data.rel.ro` slots differing other than `.text` pointers (of 1294) | 130 | 6 (one U-hash pair) |
| `programs/pump/src/*.rs` path-string order mismatches (of 33) | 32 | 1 (admin_cto internal) |
| model raw once the unmatched match in size, full original order, data as built | 683 | **1017** |
| same, original L order (U and D as built) | 481 | 653 |
| P13 (our order, data assumed equal) | 416 | 429 |
| LIS of paired order / L adjacent breaks | 884 / 136 | **970 / 15** |

The two remaining data mismatches are a `.data.rel.ro` entry pair. Its creation order comes from the
U block's hash order (TryFromIntError Debug against GlobalVolumeAccumulator Debug). The rest is a
cst4 S/Y swap whose first user is admin_cto's closure (an unmatched window).

## Mechanisms (all confirmed by builds)

1. **.rodata/.data.rel.ro order is rustc codegen order.** The pre-optimization IR (`tools/capture.py
   ... -C no-prepopulate-passes`, `tools/irg.py`) shows that every constant is created when the first
   function referencing it is codegen'd. Functions are codegen'd in mono-item order: local items by
   def index, and `#[inline]` local fns are still mono items at their def position. Statics are
   emitted at their def position. Macro output (`declare_id!`, `declare_program!`) comes in expansion order.
   MIR inlining matters: a constant that a MIR-inlined callee references is created in the caller.
   - legacy `buy.rs` mounted second (it keeps `#[inline]`; its `native_payments` module becomes
     `legacy_native_payments`). The previous lane's dead end was dropping `#[inline]`; it is not needed.
   - `declare_id!` placed before `declare_program!(pump_amm)`; MAYHEM_ID comes from macro expansion after pump_fees.
   - `process_cashback_inner`: the `MissingCashbackAccounts` error is spelled let-else/err!. The sell.rs
     Source must be created in the parent's own MIR before the PDA seed. In an `ok_or_else` closure,
     the closure mono item is codegen'd after the parent (964 -> 993).
   - `DistributionCurve` is defined after `migrate::execute`. The original first uses the
     `Result::unwrap` message there (993 -> 1013).
   - `time_index` has no `#[inline]`. Its expect string and Location sit at its own def position (after
     add_sol_volume), so the MIR inliner did not inline it into update/update_schedule/end_day (1013 -> 1019).
2. **The original module list is in file order.** This extends layout-order-census's finding to subdirectories:
   - `creator/distribute_creator_fee_v2.rs` comes before `distribute_creator_fees.rs`, and `minimum`
     is inline between get_distribution_amounts and execute.
   - token_incentives: claim, close, init, sync (volume_sync), volume_accumulator. The close/init
     handler bodies are outlined module fns there, and the program fns are thin wrappers.
   - quote_control: `set_quote_control.rs` (admin, mint_reserves, reserves_admin, with their derives) sits
     between initialize_quote_control and state.
   - lib.rs body: trade_types sits after the Global impls and before buy_quote (the original lib.rs had it
     inline). `split_protocol_fee` sits between the impl Global blocks, and `tokens_for_quote` between
     sell_quote and buy_fee_market_cap.
3. **Helper runs that have no Source sites.** `util/payments.rs`, mounted after util/fee.rs, holds the
   original's 25-function run: initialize_mayhem, OptionBool deserialize, sharing_config_shareholders,
   trade_event, and 21 native/token transfer helpers from 9 modules, in the original's interleaved order.
   After util/transfer_fee.rs come `util/withheld.rs`, the curve `quote_payments` module and
   `util/user_payments.rs`. **Visibility must be kept exactly**: making a `pub(crate)` fn `pub` gives it
   external linkage, which changes codegen (t08 lost 0x2b490/0x33c50/0x8d5c8).
4. **MergeFunctions**: the lexicographically smallest mangled name survives, and its body sits at its
   own def position.
   - The uqp curve and recipient fns (identical bodies) move together.
   - `declare_program!(mayhem)` comes from a minimal `idls/mayhem.json` (one instruction, flags taken from
     the old emulation; only one MAYHEM_ID static is emitted, as in the original). The collect module is
     mounted as `creator::collect_creator_fee` so that mayhem's 2632-B ToAccountInfos is the smallest
     name in its group.
   - The pump_amm IDL has no `sweep_creator_fee`/`sweep_protocol_fee`: the 3144-B group survives at
     pump_amm ClaimTokenIncentives' position, as in the original.
   - The mayhem IDL also has `initialize_fee_recipient` (8 accounts, flags from programs/mayhem). Its
     ToAccountInfos is the smallest name in the 2216-B group, so that group sits at the mayhem slot as
     in the original. Its metas merge into an existing group, its unused cpi fn is not emitted, and no
     extra unit appears.
5. Site-free fns moved into pad lines in collect_creator_fee, migrate, migrate_v2, create_v2,
   volume_accumulator and trade_v3. In multi_hop, swap_hop's header and first two statements move to
   line 478, so complete_fill, token_program_for and require_ata become module items before
   native_buyback, transfer_input and swap_hop. A second zero-checked curve lamport generic,
   `pay_out_native`, follows move_native.
6. **Panic Locations are data.** `tools/drr.py` compares `.data.rel.ro` slot by slot. It found two
   Locations that my moves had shifted:
   - burn_pool_authority_lp must stay at migrate.rs:659
   - `declare_program!(pump_amm)` must start at lib.rs:83 col 1, so `declare_id!` goes on line 82
   Both are fixed.

## Not kept / rejected

| attempt | result |
| --- | --- |
| `067f03ab` DistributeCreatorFeesV2 struct into the v2 file (derive order) | loses 0x2d920/0x2fa60: derive output order changes distribute_tokens codegen |
| t08 transfer helpers made `pub` | loses 3 windows (linkage) |
| `80989f5b`, t37 buy_v2 / buy_exact_quote_in_v2 as `#[inline(never)]` program fns | P13 +83..+98, but buy_v2 drops: 0.95334 -> 0.95256 (main 9f9d94c) and 0.97682 -> 0.96813 (main 2c8a790, +8 B, also raw loss 0xa868); left to the handler lanes |
| `f2409d8a` v3 trio in program-fn form | buy_v3 0.87739 -> 0.77928 but exactly 3672 B (the original size); buy_exact_quote_in_v3 0.61352 -> 0.61555; loses 0x859b0 v3_emit_buy (diff in `$OUT/out/t35-v3pf.diff`) |
| `4af96169` rename pay_out_native to re-roll its instances' hash order | unchanged; not pursued (hash fishing) |

## What is left for raw

- The five v2/v3 handler bodies (buy_v2, buy_exact_quote_in_v2, trade::buy/buy_exact_quote/sell) sit
  at the original #[program] position, between `create` and `buy`. With them there, P13 would rise
  428 -> 511 -> 623 (model, `tools/plan.py`). That is the largest remaining L-order item, and it belongs
  to the handler lanes: their final match has to be the program-fn form.
- pay_out_native's two instances are in symbol-hash order (856, 1080). The original has 1080, 856.
- U and D hash order: unreachable from source (crate metadata).
