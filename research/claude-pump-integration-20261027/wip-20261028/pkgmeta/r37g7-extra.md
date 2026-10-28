## Contributions

| lane | windows (vs control) | source change |
|---|---|---|
| pump-hi | `0xea68`, `0xf130`, `0xca628`, `0xcf510`, `0x10a0e0`, `0x10b0b8`, `0x10c0b8`, `0x10d638`, `0x10e938`, `0x10fb38`, `0x1100f8`, `0x110d40`, `0x1113c8`, `0x112220`, `0x1133c8`, `0x113f00`, `0x114d48`, `0x116718`, `0x118360`, `0x119c50`, `0x1255a8`, `0x12a4e0`, `0x12abc8`, `0x137fc0`, `0x163ea8`, `0x17c0f0` | Round37-aware tools/apply_lane_changes.py --with-cpi-7 --with-fee-8 (items already in Round37 are skipped; Round37's own idls/pump_fees.json and pump_fees client are kept): const-generic legacy buy, SetMayhemVirtualParams layout and handler, declare_program!(pump_amm) generated CPI clients (migrate_v2 keeps its hand-built CPIs to stay within the 4 KiB SBF frame), collect_coin_creator_fee client built inside `if !frozen`. That lane reports the 44-suite corpus passing for the equivalent Round36 H7 candidate. Plus migrate_v2::required_quote_account_len rewritten as an #[inline(never)] TLV walk with a u64 seen-bitset (+0x17c0f0); duplicate TLV entries are skipped exactly as the original does, and the lane reports the migrate_v2 suite at 827/827. |
| pump-mid | `0xdd700` | CurveHop constraint compares quote_mint.key()==bonding_curve.quote_mint. |
| pump-lo | `0x2a8e8` | CollectCreatorFeeV2: exported creator-fee collector taking system_program as &AccountInfo (no argument promotion) and emitting the event by reference. That lane independently reproduced the nearmiss changes below (its p02-p04). |
| nearmiss | `0x340`, `0x3b598`, `0x3b738`, `0x8cc58` | require_gt! operand bound before the macro; exported native-payment helpers (external linkage blocks ArgumentPromotion); v2 rent helper keeps an unused leading argument and uses the shared transfer. |
| nearmiss2 | `0xa23f0` | u128 numerator via checked_add(..).ok_or(Overflow)? before checked_mul. |
| libinst | `0x95610`, `0x184e38`, `0x18fc98`, `0x1905a8` | MigrateV2 harvests withheld Token-2022 fees through a pub wrapper around anchor_spl::token_2022_extensions::harvest_withheld_tokens_to_mint. |
| hostid | (raw/order only) | Removes two constructs the original does not contain: runtime pubkey! base58 decoding in create_v2::execute (now consts on the existing MAYHEM_ID line) and u128 Display formatting from a require_gt! on a u128 operand in trade_v3.rs (narrowed with the file's narrow()). The library region then has exactly the original's function set and order: +29 raw windows, no normalized change. |
| libnear3 | `0x524f0`, `0x109488` | migrate's boost_enabled helper reads pump_amm's GlobalConfig through the declare_program! generated try_deserialize + map_or, with the IDL GlobalConfig field set of the older official pump_amm IDL (ending at boost_enabled), which is what the original's deserializer reads. |
| layout-integrator (genuine steps only) | `0x95f38`, `0x96280`, `0x96d48`, `0x970f8`, `0x97580` | Genuine (no-padding) source-structure steps recovered from the coordinate lanes: native transfers moved to their original helper (move_native, x2) and signer seeds built inline (x3). |
| bodyloB | `0x56658` | migrate_v2::refund_pool_authority builds its signer seeds as one nested temporary passed to an inlined transfer closure, giving the original frame order and loading system_program after the seeds. |

Lanes `pump-hi`, `pump-mid` and `pump-lo` are the parallel Claude session's (branches and commits above). `nearmiss`, `nearmiss2`, `libinst` and `hostid` are this session's workflow lanes. Every change keeps the original's observable behaviour: the recovered windows are byte-equal (normalized) to the original's own functions, and the changed call paths are the ones the original executes.

## Toolchain note

With the official Linux x86_64 v1.44 target libraries for `sbpf-solana-solana` (PR #307), this same source reaches **794 / 1,035 normalized and 165 raw**: the five std `TypeId` thunks also match. The packaged ELFs use the repository builder's `linux-v1.44-sbf` profile.
