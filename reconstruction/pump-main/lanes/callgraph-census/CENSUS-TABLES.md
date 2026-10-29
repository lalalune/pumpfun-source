## 0x14f4e0 buy_exact_sol_in  (orig 13224 B / ours 13224 B, ratio 0.999)

calls orig 101 / ours 101, aligned 101, arg-setup diffs at aligned sites 0 (shape-only, stack offsets masked: 0); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 1 hot / 9 cold, ours 1 / 9; AccountInfo::clone orig ~0 hot / 3 cold, ours ~0 / 3


## 0x80df8 trade::v3_buy_costs  (orig 2120 B / ours 2056 B, ratio 0.788)

calls orig 17 / ours 17, aligned 16, arg-setup diffs at aligned sites 2 (shape-only, stack offsets masked: 2); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|

reordered (same count, different position): `core::option::expect_failed`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 2 hot / 0 cold, ours 2 / 0; AccountInfo::clone orig ~0 hot / 0 cold, ours ~0 / 0


## 0x6cd78 legacy_sell::process_cashback_inner  (orig 8544 B / ours 8816 B, ratio 0.735)

calls orig 58 / ours 58, aligned 56, arg-setup diffs at aligned sites 8 (shape-only, stack offsets masked: 6); syscalls orig 1 ours 1

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
| `_<PumpError as core::fmt::Display>::fmt` | 3 | 4 | we call it more often |  |
| `_<T as alloc::string::ToString>::to_string` | 5 | 4 | orig calls it more often | `_<PumpError as core::fmt::Display>::fmt` |

reordered (same count, different position): `PumpError::name`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 3 hot / 5 cold, ours 4 / 4; AccountInfo::clone orig ~5 hot / 0 cold, ours ~5 / 0

error-message form differs (fmt = ToString inlined, to_string = outlined call), by following Source line:

- `None`: orig [] / ours ['fmt']
- `sell.rs:85`: orig ['to_string'] / ours []


## 0x83c00 trade::v3_execute_buy  (orig 3440 B / ours 3408 B, ratio 0.733)

calls orig 22 / ours 22, aligned 22, arg-setup diffs at aligned sites 6 (shape-only, stack offsets masked: 5); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 1 hot / 0 cold, ours 1 / 0; AccountInfo::clone orig ~0 hot / 1 cold, ours ~0 / 1


## 0x13f630 buy_v2::buy_exact_quote_in_handler  (orig 20184 B / ours 20096 B, ratio 0.694)

calls orig 130 / ours 130, aligned 130, arg-setup diffs at aligned sites 41 (shape-only, stack offsets masked: 34); syscalls orig 1 ours 1

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 3 hot / 8 cold, ours 3 / 8; AccountInfo::clone orig ~3 hot / 9 cold, ours ~3 / 9


## 0x13b9b8 buy_v2::buy_handler  (orig 15480 B / ours 15424 B, ratio 0.665)

calls orig 90 / ours 90, aligned 88, arg-setup diffs at aligned sites 29 (shape-only, stack offsets masked: 27); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|

reordered (same count, different position): `buy_v2::buy_handler::_{{closure}}`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 3 hot / 2 cold, ours 3 / 2; AccountInfo::clone orig ~0 hot / 12 cold, ours ~0 / 12


## 0x144508 sell_v2::execute  (orig 13976 B / ours 14104 B, ratio 0.662)

calls orig 80 / ours 80, aligned 79, arg-setup diffs at aligned sites 50 (shape-only, stack offsets masked: 45); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|

reordered (same count, different position): `solana_sysvar::clock::_<impl solana_sysvar::Sysvar for solana_clock::Clock>::get`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 3 hot / 2 cold, ours 3 / 2; AccountInfo::clone orig ~0 hot / 11 cold, ours ~0 / 11


## 0x4c158 migrate_v2::create_token_account_v2  (orig 8368 B / ours 8424 B, ratio 0.563)

calls orig 10 / ours 10, aligned 10, arg-setup diffs at aligned sites 2 (shape-only, stack offsets masked: 0); syscalls orig 1 ours 1

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 0 hot / 0 cold, ours 0 / 0; AccountInfo::clone orig ~12 hot / 0 cold, ours ~12 / 0


## 0x147ba0 trade::buy  (orig 3672 B / ours 3800 B, ratio 0.544)

calls orig 29 / ours 29, aligned 28, arg-setup diffs at aligned sites 19 (shape-only, stack offsets masked: 9); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|

reordered (same count, different position): `memcmp`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 2 hot / 1 cold, ours 2 / 1; AccountInfo::clone orig ~0 hot / 0 cold, ours ~0 / 0


## 0x14a8a8 trade::sell  (orig 6032 B / ours 6056 B, ratio 0.443)

calls orig 47 / ours 47, aligned 47, arg-setup diffs at aligned sites 37 (shape-only, stack offsets masked: 18); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 2 hot / 1 cold, ours 2 / 1; AccountInfo::clone orig ~0 hot / 2 cold, ours ~0 / 2


## 0x1489f8 trade::buy_exact_quote  (orig 7856 B / ours 7800 B, ratio 0.303)

calls orig 66 / ours 66, aligned 58, arg-setup diffs at aligned sites 57 (shape-only, stack offsets masked: 28); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|

reordered (same count, different position): `TARGET trade::v3_buy_costs`, `buy_quote`, `constant_product::tokens_for_quote`, `memcmp`, `trade::buy_exact_quote::_{{closure}}`, `trade::net_quote_for_budget`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 2 hot / 6 cold, ours 2 / 6; AccountInfo::clone orig ~0 hot / 0 cold, ours ~0 / 0


## 0x72810 sweep::execute  (orig 7832 B / ours 7832 B, ratio 0.298)

calls orig 37 / ours 36, aligned 32, arg-setup diffs at aligned sites 25 (shape-only, stack offsets masked: 17); syscalls orig 2 ours 2

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
| `memcmp` | 4 | 3 | orig calls it more often |  |

reordered (same count, different position): `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from`, `alloc::fmt::format::format_inner`, `buy_v2::admit_associated_token_account`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 2 hot / 0 cold, ours 2 / 0; AccountInfo::clone orig ~5 hot / 1 cold, ours ~4 / 1


## 0x1e7c0 create_v2::execute  (orig 15576 B / ours 14848 B, ratio 0.247)

calls orig 125 / ours 126, aligned 90, arg-setup diffs at aligned sites 81 (shape-only, stack offsets masked: 47); syscalls orig 0 ours 0

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
| `_<PumpError as core::fmt::Display>::fmt` | 11 | 6 | orig calls it more often |  |
| `_<T as alloc::string::ToString>::to_string` | 6 | 11 | we call it more often | `_<PumpError as core::fmt::Display>::fmt` |
| `memcpy` | 10 | 11 | we call it more often |  |

reordered (same count, different position): `PumpError::name`, `_<anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from`, `anchor_lang::error::Error::with_pubkeys`, `anchor_lang::error::Error::with_values`, `core::fmt::num::imp::_<impl core::fmt::Display for i32>::fmt`, `core::fmt::num::imp::_<impl core::fmt::Display for u64>::fmt`, `create_v2::check_quote_mint_extensions`, `create_v2::initialize_mayhem`, `create_v2::nested_create::control_account`, `create_v2::nested_create::quote_control`, `create_v2::nested_create::walk`, `memcmp`, `spl_associated_token_account_client::address::get_associated_token_address_with_program_id`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 11 hot / 6 cold, ours 6 / 11; AccountInfo::clone orig ~0 hot / 7 cold, ours ~0 / 7

error-message form differs (fmt = ToString inlined, to_string = outlined call), by following Source line:

- `create_v2.rs:205`: orig ['fmt'] / ours ['to_string']
- `create_v2.rs:210`: orig ['fmt'] / ours ['to_string']
- `create_v2.rs:541`: orig ['fmt', 'fmt'] / ours ['to_string']
- `create_v2.rs:547`: orig [] / ours ['to_string']
- `create_v2.rs:553`: orig [] / ours ['to_string']
- `create_v2.rs:709`: orig ['fmt', 'fmt'] / ours ['fmt']
- `create_v2.rs:732`: orig ['fmt'] / ours ['fmt', 'fmt']
- `create_v2.rs:738`: orig ['fmt', 'fmt'] / ours ['fmt']
- `create_v2.rs:758`: orig ['to_string'] / ours ['to_string', 'to_string']
- `create_v2.rs:778`: orig ['to_string'] / ours []


## 0x77940 token_incentives::claim_token_incentives::cashback::claim_v2  (orig 8832 B / ours 8464 B, ratio 0.167)

calls orig 68 / ours 62, aligned 48, arg-setup diffs at aligned sites 43 (shape-only, stack offsets masked: 26); syscalls orig 2 ours 2

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
| `_<PumpError as core::fmt::Display>::fmt` | 2 | 3 | we call it more often |  |
| `_<T as alloc::string::ToString>::to_string` | 2 | 1 | orig calls it more often | `_<PumpError as core::fmt::Display>::fmt` |
| `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from` | 10 | 8 | orig calls it more often |  |
| `_<solana_account_info::AccountInfo as core::clone::Clone>::clone` | 8 | 6 | orig calls it more often |  |
| `anchor_lang::Lamports::add_lamports [ours-only]` | 0 | 1 | we outline; no such function in original (orig inlines it) | `solana_account_info::AccountInfo::lamports`, `solana_account_info::AccountInfo::try_borrow_mut_lamports`, `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from` |
| `solana_account_info::AccountInfo::data_is_empty` | 1 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `solana_account_info::AccountInfo::lamports` | 3 | 2 | orig calls it more often |  |
| `solana_account_info::AccountInfo::try_borrow_mut_lamports` | 2 | 1 | orig calls it more often |  |

reordered (same count, different position): `PumpError::name`, `_<anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from`, `_<anchor_spl::token_interface::TokenAccount as anchor_lang::AccountDeserialize>::try_deserialize_unchecked`, `anchor_lang::error::Error::with_pubkeys`, `memcmp`, `memcpy`, `solana_account_info::AccountInfo::try_borrow_data`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 2 hot / 2 cold, ours 3 / 1; AccountInfo::clone orig ~4 hot / 8 cold, ours ~2 / 6

error-message form differs (fmt = ToString inlined, to_string = outlined call), by following Source line:

- `None`: orig ['fmt'] / ours ['fmt', 'fmt']
- `claim_token_incentives.rs:305`: orig [] / ours ['fmt']
- `claim_token_incentives.rs:310`: orig ['fmt'] / ours []
- `claim_token_incentives.rs:333`: orig ['to_string'] / ours []


## 0x5b3b0 multi_hop_curve::swap_hop  (orig 18584 B / ours 18056 B, ratio 0.158)

calls orig 107 / ours 94, aligned 47, arg-setup diffs at aligned sites 46 (shape-only, stack offsets masked: 38); syscalls orig 1 ours 1

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
| `PumpError::name` | 5 | 6 | we call it more often | `memcpy` |
| `_<T as alloc::string::ToString>::to_string` | 4 | 5 | we call it more often |  |
| `_<TradeEvent as anchor_lang::Event>::data` | 2 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `_<alloc::vec::Vec<T> as alloc::vec::spec_from_iter::SpecFromIter<T,I>>::from_iter` | 3 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `_<anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from` | 5 | 6 | we call it more often | `memcpy` |
| `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from` | 4 | 1 | orig calls it more often |  |
| `_<solana_account_info::AccountInfo as core::clone::Clone>::clone` | 10 | 11 | we call it more often |  |
| `_<trade::PostCompleteBuyEvent as anchor_lang::Event>::data` | 2 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `_<trade_types::CompleteEvent as anchor_lang::Event>::data` | 2 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `__multi3` | 0 | 2 | we call; orig inlines here (function exists standalone in orig) |  |
| `alloc::alloc::exchange_malloc` | 3 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `buy_fee_market_cap` | 1 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) | `__multi3`, `PumpError::name`, `_<anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from` |
| `constant_product::tokens_for_quote` | 1 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `memcpy` | 5 | 1 | orig calls it more often |  |
| `multi_hop_curve::add [ours-only]` | 0 | 2 | we outline; no such function in original (orig inlines it) |  |
| `multi_hop_curve::div [ours-only]` | 0 | 2 | we outline; no such function in original (orig inlines it) |  |
| `multi_hop_curve::move_lamports [ours-only]` | 0 | 1 | we outline; no such function in original (orig inlines it) | `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from` |
| `multi_hop_curve::route_event [ours-only]` | 0 | 1 | we outline; no such function in original (orig inlines it) | `_<TradeEvent as anchor_lang::Event>::data`, `solana_program::log::sol_log_data`, `memcpy`, `solana_program::program::invoke_signed`, `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from` |
| `multi_hop_curve::route_event [ours-only]` | 0 | 1 | we outline; no such function in original (orig inlines it) | `solana_program::log::sol_log_data`, `memcpy`, `solana_program::program::invoke_signed`, `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from` |
| `multi_hop_curve::route_event [ours-only]` | 0 | 1 | we outline; no such function in original (orig inlines it) | `solana_program::log::sol_log_data`, `memcpy`, `solana_program::program::invoke_signed`, `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from` |
| `multi_hop_curve::sub [ours-only]` | 0 | 5 | we outline; no such function in original (orig inlines it) |  |
| `solana_account_info::AccountInfo::data_len` | 1 | 3 | we call it more often |  |
| `solana_instruction::Instruction::new_with_bytes` | 3 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `solana_program::log::sol_log_data` | 3 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `solana_program::program::invoke_signed` | 3 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `trade::post_complete_buy_event` | 1 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) | `PumpError::name`, `_<anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from` |
| `trade::quote_payments::transfer_native` | 1 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `trade::sub3` | 2 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) | `PumpError::name`, `_<anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from` |

reordered (same count, different position): `_<impl trade_types::BondingCurve>::apply_buy`, `_<impl trade_types::BondingCurve>::apply_sell`, `_<impl trade_types::BondingCurve>::sell_quote`, `anchor_lang::error::Error::with_values`, `legacy_sell::fee_math::get_fees`, `memcmp`, `migrate::native_payments::transfer_native`, `multi_hop_curve::native_buyback`, `multi_hop_curve::swap_hop::_{{closure}}`, `multi_hop_curve::swap_hop::complete_fill`, `multi_hop_curve::transfer_base_out`, `multi_hop_curve::transfer_buyback_out`, `multi_hop_curve::transfer_input`, `trade::net_quote_for_budget`, `trade::validate_buyback_fee_recipient_account`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 1 hot / 4 cold, ours 1 / 5; AccountInfo::clone orig ~1 hot / 10 cold, ours ~1 / 11

error-message form differs (fmt = ToString inlined, to_string = outlined call), by following Source line:

- `multi_hop_curve_swap.rs:581`: orig [] / ours ['to_string', 'to_string']
- `multi_hop_curve_swap.rs:686`: orig ['to_string'] / ours []


## 0x22a10 admin_cto::execute  (orig 27400 B / ours 18464 B, ratio 0.095)

calls orig 154 / ours 178, aligned 80, arg-setup diffs at aligned sites 76 (shape-only, stack offsets masked: 44); syscalls orig 3 ours 3

| callee | orig | ours | kind | depth-2 evidence |
|---|---:|---:|---|---|
| `_<PumpError as core::fmt::Display>::fmt` | 8 | 5 | orig calls it more often |  |
| `_<T as alloc::string::ToString>::to_string` | 7 | 10 | we call it more often | `_<PumpError as core::fmt::Display>::fmt` |
| `_<T as alloc::string::ToString>::to_string` | 0 | 1 | we call; orig inlines here (function exists standalone in orig) | `_<anchor_lang::error::ErrorCode as core::fmt::Display>::fmt` |
| `_<anchor_lang::error::ErrorCode as core::fmt::Display>::fmt` | 1 | 0 | orig-calls; we inline or drop (helper exists standalone in our build) |  |
| `_<solana_account_info::AccountInfo as core::clone::Clone>::clone` | 33 | 54 | we call it more often |  |
| `memcmp` | 14 | 15 | we call it more often |  |
| `memcpy` | 6 | 8 | we call it more often |  |

reordered (same count, different position): `PumpError::name`, `_<CollectCreatorFeeEvent as anchor_lang::Event>::data`, `_<alloc::vec::Vec<T> as alloc::vec::spec_from_iter::SpecFromIter<T,I>>::from_iter`, `_<anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from`, `_<anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from`, `admin_cto::token_frozen`, `admin_cto::token_raw_amount`, `alloc::alloc::exchange_malloc`, `anchor_lang::error::Error::with_pubkeys`, `anchor_lang::error::ErrorCode::name`, `anchor_spl::associated_token::create_idempotent`, `collect_v2::collect`, `collect_v2::transfer_native`, `core::result::unwrap_failed`, `legacy_buy::native_payments::ensure_rent_exempt`, `pump_amm::cpi::collect_coin_creator_fee`, `pump_amm::cpi::transfer_creator_fees_to_pump_v2`, `solana_account_info::AccountInfo::data_is_empty`, `solana_account_info::AccountInfo::lamports`, `solana_instruction::Instruction::new_with_bytes`, `solana_program::log::sol_log_data`, `solana_program::program::invoke_signed`, `solana_pubkey::Pubkey::find_program_address`, `solana_rent::Rent::minimum_balance`, `solana_sysvar::clock::_<impl solana_sysvar::Sysvar for solana_clock::Clock>::get`, `solana_sysvar::rent::_<impl solana_sysvar::Sysvar for solana_rent::Rent>::get`
hot/cold sites (inlined = hot, called = cold; LLVM cold threshold 45 vs 325): error-message to_string orig 9 hot / 7 cold, ours 5 / 11; AccountInfo::clone orig ~21 hot / 33 cold, ours ~0 / 54

error-message form differs (fmt = ToString inlined, to_string = outlined call), by following Source line:

- `admin_cto.rs:296`: orig ['fmt'] / ours ['fmt', 'to_string']
- `admin_cto.rs:298`: orig ['fmt'] / ours []
- `admin_cto.rs:306`: orig ['fmt'] / ours []
- `admin_cto.rs:312`: orig ['to_string'] / ours ['to_string', 'to_string']
- `admin_cto.rs:330`: orig ['to_string', 'to_string'] / ours ['to_string']
- `admin_cto.rs:334`: orig [] / ours ['to_string']
- `admin_cto.rs:338`: orig ['to_string'] / ours []
- `admin_cto.rs:410`: orig ['fmt'] / ours ['to_string']
- `admin_cto.rs:556`: orig [] / ours ['to_string']
- `admin_cto.rs:648`: orig ['fmt'] / ours ['to_string']


