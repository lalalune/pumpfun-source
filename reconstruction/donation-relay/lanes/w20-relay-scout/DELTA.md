# Donation Relay: delta between the live program and the old source

`DELTA.json` holds the same rows with more fields. Boundaries come from `relaylib.Elf.functions()`, which reproduces all 492 symbols of the old build exactly (no extras, no misses, same sizes).

## Summary

| | functions | .text bytes |
|---|---:|---:|
| identical, against the old source rebuilt on v1.54 | 443 | 588,792 |
| modified, against the old source rebuilt on v1.54 | 16 | 40,120 |
| added, against the old source rebuilt on v1.54 | 112 | 222,976 |
| removed: old source functions on v1.54 with no partner | 6 | 24,280 |
| new functions identical to a function of the old deployed ELF (v1.48) | 105 of 571 | |
| matched by the current skeleton (`swarm/w20-relay-scout`) | 542 of 571 | 769,080 of 851,888 |

`identical` means same length and same bytes after masking internal call immediates and relocated lddw values, the same normalization the scorer uses. Most of the difference from the old deployed ELF is the compiler (v1.48 to v1.54), not the source.

## Open functions, by cluster

| cluster | target addr | size | status | reading | similarity to old source function |
|---|---|---:|---|---|---:|
| C1-distribute-bps | `0x18478` | 1656 | added | distribute_after_just_swapping prechecks (shared with exact) | 0 |
| C1-distribute-bps | `0x18af0` | 4496 | added | distribute_after_just_swapping_v1 handler | 0 |
| C1-distribute-bps | `0x1a6d8` | 2488 | added | distribute_after finish: reload, burn_and_close (shared with exact) | 0 |
| C1-distribute-bps | `0x1b090` | 1920 | added | distribute_non_swap prechecks (shared with exact) | 0 |
| C1-distribute-bps | `0x1b810` | 4200 | added | distribute_non_swap_output_mint_v1 handler | 0 |
| C1-distribute-bps | `0x1d2d0` | 2488 | added | distribute_non_swap finish: reload, burn_and_close (shared with exact) | 0 |
| C1-distribute-bps | `0x24578` | 2376 | added | tools::distribution::shared::distribute | 0 |
| C1-distribute-bps | `0x25f00` | 4424 | added | tools::distribution::shared transfer worker (bps) | 0 |
| C2-bridge-handlers | `0x20580` | 4232 | added | admit_bridge_payment handler body | 0 |
| C2-bridge-handlers | `0x21608` | 4328 | added | recover_bridge_payment handler body | 0 |
| C2-bridge-handlers | `0x933a0` | 3160 | added | #[program] recover_bridge_payment_v1 wrapper | 0 |
| C2-bridge-handlers | `0x99d70` | 3336 | modified | #[program] admit_bridge_payment_v1 wrapper | 0.655 |
| C3-distribute-exact | `0x8eb0` | 528 | added | drop_in_place of the 4 AccountInfo clones in distribution CPIs | 0 |
| C3-distribute-exact | `0x19c80` | 2648 | added | distribute_exact_after_just_swapping_v1 handler | 0 |
| C3-distribute-exact | `0x1c878` | 2648 | added | distribute_exact_non_swap_output_mint_v1 handler | 0 |
| C3-distribute-exact | `0x24ec0` | 4160 | added | tools::distribution::shared exact distribution | 0 |
| C3-distribute-exact | `0x27048` | 4336 | added | tools::distribution::shared exact transfer worker | 0 |
| C4-jupiter-swap | `0x11668` | 2328 | modified | cpi::jupiter::invoke_jupiter | 0.859 |
| C4-jupiter-swap | `0x11f80` | 2832 | modified | cpi::jupiter::swap_observed | 0.509 |
| C4-jupiter-swap | `0x1ec18` | 5960 | modified | swap_then_distribute_v1 handler | 0.899 |
| C5-donate | `0x28e48` | 3680 | added | tools::donate::shared::donate_shared | 0 |
| C5-donate | `0x29ca8` | 5272 | added | tools::donate::shared signed transfer core (called by donate_shared and admit) | 0 |
| C6-checks | `0x227e8` | 912 | modified | tools::checks native mint for program | 0.595 |
| C6-checks | `0x22b78` | 432 | added | tools::checks::native_mint_pair | 0 |
| C6-checks | `0x22f08` | 808 | modified | tools::checks::check_relayer | 0.759 |
| C6-checks | `0x23230` | 4448 | modified | tools::checks::typed_mint_safe | 0.69 |
| C7-framework-layout | `0x1590` | 1992 | added | anchor_lang::error::Error::with_values, third instance (14 try_accounts closures call it) | 0 |
| C7-framework-layout | `0xb3278` | 408 | added | alloc::raw_vec::RawVec<T,A>::grow_one (spl_token::instruction::transfer_checked) | 0 |
| C7-framework-layout | `0xbcac0` | 312 | added | alloc::raw_vec::finish_grow, separate instance | 0 |

## Removed against the old source on v1.54

| old-source-on-v1.54 addr | size | name |
|---|---:|---|
| `0x1f430` | 7656 | donation_relay_source_proposal::tools::donate::shared::donate_shared |
| `0x1cc30` | 6896 | donation_relay_source_proposal::tools::distribution::shared::distribute |
| `0x175a0` | 4064 | donation_relay_source_proposal::settlement_handlers::distribute_non_swap |
| `0x16728` | 3704 | donation_relay_source_proposal::settlement_handlers::distribute_after |
| `0x58f0` | 1288 | spl_token_2022::extension::BaseStateWithExtensions::get_extension |
| `0x1c990` | 672 | donation_relay_source_proposal::tools::checks::admit_shares |

## All target functions

| addr | size | status | skeleton | name |
|---|---:|---|---|---|
| `0x120` | 128 | identical | yes | <anchor_lang::accounts::interface::Interface<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x1a0` | 904 | identical | yes | <alloc::vec::Vec<T> as alloc::vec::spec_from_iter_nested::SpecFromIterNested<T,I>>::from_iter |
| `0x528` | 136 | identical | yes | <anchor_lang::accounts::interface_account::InterfaceAccount<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x5b0` | 136 | identical | yes | <anchor_lang::accounts::interface_account::InterfaceAccount<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x638` | 1992 | identical | yes | anchor_lang::error::Error::with_values |
| `0xe00` | 1936 | identical | yes | anchor_lang::error::Error::with_values |
| `0x1590` | 1992 | added | OPEN | anchor_lang::error::Error::with_values, third instance (14 try_accounts closures call it) |
| `0x1d58` | 392 | identical | yes | anchor_lang::error::Error::with_account_name |
| `0x1ee0` | 408 | identical | yes | anchor_lang::error::Error::with_account_name |
| `0x2078` | 376 | identical | yes | anchor_lang::accounts::account_info::<impl anchor_lang::Accounts<B> for solana_account_info::AccountInfo>::try_accounts |
| `0x21f0` | 1072 | identical | yes | anchor_lang::accounts::interface_account::InterfaceAccount<T>::try_from |
| `0x2620` | 1040 | identical | yes | anchor_lang::accounts::interface_account::InterfaceAccount<T>::try_from |
| `0x2a30` | 424 | identical | yes | anchor_lang::accounts::boxed::<impl anchor_lang::Accounts<B> for alloc::boxed::Box<T>>::try_accounts |
| `0x2bd8` | 424 | identical | yes | anchor_lang::accounts::boxed::<impl anchor_lang::Accounts<B> for alloc::boxed::Box<T>>::try_accounts |
| `0x2d80` | 944 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from_unchecked |
| `0x3130` | 1000 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from_unchecked |
| `0x3518` | 1000 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from_unchecked |
| `0x3900` | 952 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from_unchecked |
| `0x3cb8` | 1048 | added | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x40d0` | 1000 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from_unchecked |
| `0x44b8` | 776 | added | yes | anchor_lang::accounts::account::Account<T>::try_from_unchecked |
| `0x47c0` | 984 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from_unchecked |
| `0x4b98` | 776 | added | yes | anchor_lang::accounts::account::Account<T>::try_from_unchecked |
| `0x4ea0` | 640 | identical | yes | anchor_lang::accounts::account::Account<T>::reload |
| `0x5120` | 640 | added | yes | anchor_lang::accounts::account::Account<T>::reload |
| `0x53a0` | 1000 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x5788` | 992 | added | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x5b68` | 944 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x5f18` | 952 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x62d0` | 1016 | added | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x66c8` | 1000 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x6ab0` | 1000 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x6e98` | 984 | identical | yes | anchor_lang::accounts::account::Account<T>::try_from |
| `0x7270` | 440 | identical | yes | <anchor_lang::accounts::interface::Interface<T> as core::convert::TryFrom<&solana_account_info::AccountInfo>>::try_from |
| `0x7428` | 272 | identical | yes | spl_token_2022::extension::ExtensionType::try_calculate_account_len |
| `0x7538` | 1280 | identical | yes | spl_token_2022::extension::BaseStateWithExtensions::get_extension |
| `0x7a38` | 1560 | identical | yes | spl_token_2022::extension::StateWithExtensions<S>::unpack |
| `0x8050` | 48 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0x8080` | 104 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0x80e8` | 48 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0x8118` | 24 | identical | yes | <&T as core::fmt::Display>::fmt |
| `0x8130` | 288 | identical | yes | <T as alloc::string::SpecToString>::spec_to_string |
| `0x8250` | 288 | identical | yes | <T as alloc::string::SpecToString>::spec_to_string |
| `0x8370` | 96 | identical | yes | core::fmt::num::<impl core::fmt::Debug for u8>::fmt |
| `0x83d0` | 40 | identical | yes | core::fmt::Write::write_fmt |
| `0x83f8` | 400 | identical | yes | core::ptr::drop_in_place<donation_relay_source_proposal::instructions::v1::relayer_only::distribute::just_swap::JustSwap |
| `0x8588` | 400 | identical | yes | core::ptr::drop_in_place<donation_relay_source_proposal::instructions::v1::relayer_only::distribute::swap_then_distribut |
| `0x8718` | 8 | identical | yes | core::ptr::drop_in_place<alloc::string::String> |
| `0x8720` | 104 | identical | yes | core::ptr::drop_in_place<std::io::error::Error> |
| `0x8788` | 152 | identical | yes | core::ptr::drop_in_place<solana_account_info::AccountInfo> |
| `0x8820` | 8 | identical | yes | core::ptr::drop_in_place<solana_program_error::ProgramError> |
| `0x8828` | 528 | identical | yes | core::ptr::drop_in_place<[solana_account_info::AccountInfo; 4]> |
| `0x8a38` | 656 | modified | yes | core::ptr::drop_in_place<donation_relay_source_proposal::tools::donate::shared::SignedDonationContext> |
| `0x8cc8` | 488 | identical | yes | core::ptr::drop_in_place<alloc::collections::btree::set::BTreeSet<solana_pubkey::Pubkey>> |
| `0x8eb0` | 528 | added | OPEN | drop_in_place of the 4 AccountInfo clones in distribution CPIs |
| `0x90c0` | 464 | identical | yes | core::ptr::drop_in_place<anchor_lang::context::CpiContext<anchor_lang::system_program::Allocate>> |
| `0x9290` | 880 | identical | yes | core::slice::sort::shared::pivot::median3_rec |
| `0x9600` | 848 | identical | yes | core::slice::sort::stable::driftsort_main |
| `0x9950` | 5912 | identical | yes | core::slice::sort::stable::drift::sort |
| `0xb068` | 9400 | identical | yes | core::slice::sort::stable::quicksort::quicksort |
| `0xd520` | 48 | identical | yes | <core::fmt::Error as core::fmt::Debug>::fmt |
| `0xd550` | 544 | identical | yes | <alloc::string::String as core::fmt::Write>::write_char |
| `0xd770` | 192 | identical | yes | <alloc::string::String as core::fmt::Write>::write_str |
| `0xd830` | 656 | identical | yes | alloc::raw_vec::finish_grow |
| `0xdac0` | 360 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xdc28` | 424 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xddd0` | 424 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xdf78` | 376 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xe0f0` | 424 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xe298` | 640 | identical | yes | alloc::raw_vec::RawVecInner<A>::reserve::do_reserve_and_handle |
| `0xe518` | 112 | identical | yes | <solana_pubkey::PubkeyError as core::fmt::Debug>::fmt |
| `0xe588` | 592 | identical | yes | <alloc::string::String as borsh::de::BorshDeserialize>::deserialize_reader |
| `0xe7d8` | 88 | identical | yes | <core::num::error::TryFromIntError as core::fmt::Debug>::fmt |
| `0xe830` | 256 | identical | yes | <solana_account_info::AccountInfo as core::clone::Clone>::clone |
| `0xe930` | 1240 | identical | yes | <solana_program_error::ProgramError as core::fmt::Debug>::fmt |
| `0xee08` | 1736 | added | yes | <alloc::vec::Vec<T> as borsh::de::BorshDeserialize>::deserialize_reader |
| `0xf4d0` | 1296 | identical | yes | <alloc::vec::Vec<T> as borsh::de::BorshDeserialize>::deserialize_reader |
| `0xf9e0` | 1656 | identical | yes | <alloc::vec::Vec<T> as borsh::de::BorshDeserialize>::deserialize_reader |
| `0x10058` | 2328 | identical | yes | <alloc::vec::Vec<T> as borsh::de::BorshDeserialize>::deserialize_reader |
| `0x10970` | 128 | identical | yes | <anchor_lang::accounts::signer::Signer as anchor_lang::Accounts<B>>::try_accounts |
| `0x109f0` | 128 | identical | yes | <anchor_lang::accounts::signer::Signer as anchor_lang::Accounts<B>>::try_accounts |
| `0x10a70` | 136 | identical | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10af8` | 152 | identical | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10b90` | 136 | added | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10c18` | 136 | identical | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10ca0` | 136 | identical | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10d28` | 136 | identical | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10db0` | 136 | added | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10e38` | 136 | added | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10ec0` | 136 | identical | yes | <anchor_lang::accounts::account::Account<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x10f48` | 400 | identical | yes | <anchor_lang::accounts::program::Program<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x110d8` | 512 | identical | yes | <anchor_lang::accounts::program::Program<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x112d8` | 512 | added | yes | <anchor_lang::accounts::program::Program<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x114d8` | 400 | identical | yes | <anchor_lang::accounts::program::Program<T> as anchor_lang::Accounts<B>>::try_accounts |
| `0x11668` | 2328 | modified | OPEN | cpi::jupiter::invoke_jupiter |
| `0x11f80` | 2832 | modified | OPEN | cpi::jupiter::swap_observed |
| `0x12a90` | 2488 | identical | yes | donation_relay_source_proposal::donation_handlers::donate_v1_handler |
| `0x13448` | 5904 | identical | yes | donation_relay_source_proposal::donation_handlers::donate_native_v1_handler |
| `0x14b58` | 5904 | identical | yes | donation_relay_source_proposal::donation_handlers::donate_native_pubkey_config_id_v1_handler |
| `0x16268` | 2488 | identical | yes | donation_relay_source_proposal::donation_handlers::donate_pubkey_config_id_v1_handler |
| `0x16c20` | 2488 | identical | yes | donation_relay_source_proposal::donation_handlers::donate_pubkey_config_id_with_payer_v1_handler |
| `0x175d8` | 3744 | modified | yes | donation_relay_source_proposal::settlement_handlers::close_epoch |
| `0x18478` | 1656 | added | OPEN | distribute_after_just_swapping prechecks (shared with exact) |
| `0x18af0` | 4496 | added | OPEN | distribute_after_just_swapping_v1 handler |
| `0x19c80` | 2648 | added | OPEN | distribute_exact_after_just_swapping_v1 handler |
| `0x1a6d8` | 2488 | added | OPEN | distribute_after finish: reload, burn_and_close (shared with exact) |
| `0x1b090` | 1920 | added | OPEN | distribute_non_swap prechecks (shared with exact) |
| `0x1b810` | 4200 | added | OPEN | distribute_non_swap_output_mint_v1 handler |
| `0x1c878` | 2648 | added | OPEN | distribute_exact_non_swap_output_mint_v1 handler |
| `0x1d2d0` | 2488 | added | OPEN | distribute_non_swap finish: reload, burn_and_close (shared with exact) |
| `0x1dc88` | 3984 | modified | yes | donation_relay_source_proposal::settlement_handlers::just_swap |
| `0x1ec18` | 5960 | modified | OPEN | swap_then_distribute_v1 handler |
| `0x20360` | 544 | identical | yes | donation_relay_source_proposal::instructions::v1::relayer_only::upsert_mint_whitelist::upsert_whitelist |
| `0x20580` | 4232 | added | OPEN | admit_bridge_payment handler body |
| `0x21608` | 4328 | added | OPEN | recover_bridge_payment handler body |
| `0x226f0` | 248 | identical | yes | donation_relay_source_proposal::tools::checks::native_program_supported |
| `0x227e8` | 912 | modified | OPEN | tools::checks native mint for program |
| `0x22b78` | 432 | added | OPEN | tools::checks::native_mint_pair |
| `0x22d28` | 480 | modified | yes | donation_relay_source_proposal::tools::checks::check_message |
| `0x22f08` | 808 | modified | OPEN | tools::checks::check_relayer |
| `0x23230` | 4448 | modified | OPEN | tools::checks::typed_mint_safe |
| `0x24390` | 488 | modified | yes | donation_relay_source_proposal::tools::checks::check_bps |
| `0x24578` | 2376 | added | OPEN | tools::distribution::shared::distribute |
| `0x24ec0` | 4160 | added | OPEN | tools::distribution::shared exact distribution |
| `0x25f00` | 4424 | added | OPEN | tools::distribution::shared transfer worker (bps) |
| `0x27048` | 4336 | added | OPEN | tools::distribution::shared exact transfer worker |
| `0x28138` | 2832 | identical | yes | donation_relay_source_proposal::tools::distribution::shared::burn_and_close |
| `0x28c48` | 256 | identical | yes | donation_relay_source_proposal::tools::donate::shared::deserialize_token_account |
| `0x28d48` | 256 | identical | yes | donation_relay_source_proposal::tools::donate::shared::deserialize_mint |
| `0x28e48` | 3680 | added | OPEN | tools::donate::shared::donate_shared |
| `0x29ca8` | 5272 | added | OPEN | tools::donate::shared signed transfer core (called by donate_shared and admit) |
| `0x2b140` | 3296 | identical | yes | donation_relay_source_proposal::tools::fair_distribution::fair_amounts |
| `0x2be20` | 10128 | identical | yes | donation_relay_source_proposal::business_error_codes::ErrorCode::name |
| `0x2e5b0` | 440 | identical | yes | donation_relay_source_proposal::business_error_codes::<impl core::convert::From<donation_relay_source_proposal::business |
| `0x2e768` | 1392 | identical | yes | <donation_relay_source_proposal::business_error_codes::ErrorCode as core::fmt::Display>::fmt |
| `0x2ecd8` | 1000 | identical | yes | <donation_relay_source_proposal::events::v1::donation_epoch_closed::DonationEpochClosedV1Event as borsh::ser::BorshSeria |
| `0x2f0c0` | 1976 | identical | yes | <donation_relay_source_proposal::events::v1::donation_epoch_just_swapped::DonationEpochJustSwappedV1Event as borsh::ser: |
| `0x2f878` | 2296 | identical | yes | <donation_relay_source_proposal::events::v1::donation_epoch_processed::DonationEpochProcessedV1Event as borsh::ser::Bors |
| `0x30170` | 2104 | added | yes | <donation_relay_source_proposal::events::v1::donation_epoch_processed_exact::DonationEpochProcessedExactV1Event as borsh |
| `0x309a8` | 1792 | identical | yes | <donation_relay_source_proposal::events::v1::donation_made::DonationMadeV1Event as borsh::ser::BorshSerialize>::serializ |
| `0x310a8` | 1912 | added | yes | <donation_relay_source_proposal::events::v1::bridge_donation_admitted::BridgeDonationAdmittedV1Event as borsh::ser::Bors |
| `0x31820` | 2256 | added | yes | <donation_relay_source_proposal::events::v1::bridge_payment_recovered::BridgePaymentRecoveredV1Event as borsh::ser::Bors |
| `0x320f0` | 12184 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate::DonateV1 as anchor_lang::Accounts<donatio |
| `0x35088` | 4568 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate::DonateV1 as anchor_lang::Accounts<donatio |
| `0x36260` | 4520 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate::DonateV1 as anchor_lang::Accounts<donatio |
| `0x37408` | 3328 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate::DonateV1 as anchor_lang::Accounts<donatio |
| `0x38108` | 3336 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_pubkey_config_id::DonatePubkeyConfigIdV1 a |
| `0x38e10` | 12312 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native::DonateNativeV1 as anchor_lang::Acc |
| `0x3be28` | 4568 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native::DonateNativeV1 as anchor_lang::Acc |
| `0x3d000` | 4520 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native::DonateNativeV1 as anchor_lang::Acc |
| `0x3e1a8` | 12376 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native::DonateNativeV1 as anchor_lang::Acc |
| `0x41200` | 3320 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native_pubkey_config_id::DonateNativePubke |
| `0x41ef8` | 12312 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native_pubkey_config_id::DonateNativePubke |
| `0x44f10` | 4568 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native_pubkey_config_id::DonateNativePubke |
| `0x460e8` | 4520 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native_pubkey_config_id::DonateNativePubke |
| `0x47290` | 12376 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_native_pubkey_config_id::DonateNativePubke |
| `0x4a2e8` | 12184 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_pubkey_config_id::DonatePubkeyConfigIdV1 a |
| `0x4d280` | 4568 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_pubkey_config_id::DonatePubkeyConfigIdV1 a |
| `0x4e458` | 4520 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_pubkey_config_id::DonatePubkeyConfigIdV1 a |
| `0x4f600` | 12416 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_pubkey_config_id_with_payer::DonatePubkeyC |
| `0x52680` | 4568 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_pubkey_config_id_with_payer::DonatePubkeyC |
| `0x53858` | 4520 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_pubkey_config_id_with_payer::DonatePubkeyC |
| `0x54a00` | 3336 | identical | yes | <donation_relay_source_proposal::instructions::v1::public_api::donate::donate_pubkey_config_id_with_payer::DonatePubkeyC |
| `0x55708` | 12696 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::close_donation_epoch::CloseDonationEpochV1 as anchor_la |
| `0x588a0` | 6504 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::close_donation_epoch::CloseDonationEpochV1 as anchor_la |
| `0x5a208` | 3264 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::close_donation_epoch::CloseDonationEpochV1 as anchor_la |
| `0x5aec8` | 3808 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::close_donation_epoch::CloseDonationEpochV1 as anchor_la |
| `0x5bda8` | 12144 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::distribute_after_just_swapping::DistributeA |
| `0x5ed18` | 3240 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::distribute_after_just_swapping::DistributeA |
| `0x5f9c0` | 10888 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::distribute_non_swap_output_mint::Distribute |
| `0x62448` | 2296 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::distribute_non_swap_output_mint::Distribute |
| `0x62d40` | 15400 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::just_swap::JustSwapV1 as anchor_lang::Accou |
| `0x66968` | 6224 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::just_swap::JustSwapV1 as anchor_lang::Accou |
| `0x681b8` | 3288 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::just_swap::JustSwapV1 as anchor_lang::Accou |
| `0x68e90` | 3568 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::just_swap::JustSwapV1 as anchor_lang::Accou |
| `0x69c80` | 13776 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::swap_then_distribute::SwapThenDistributeV1  |
| `0x6d250` | 3656 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::distribute::swap_then_distribute::SwapThenDistributeV1  |
| `0x6e098` | 3632 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::upsert_mint_whitelist::UpsertMintWhitelistV1 as anchor_ |
| `0x6eec8` | 4304 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::upsert_mint_whitelist::UpsertMintWhitelistV1 as anchor_ |
| `0x6ff98` | 824 | identical | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::upsert_mint_whitelist::UpsertMintWhitelistV1 as anchor_ |
| `0x702d0` | 14808 | added | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::admit_bridge_payment::AdmitBridgePaymentV1 as anchor_la |
| `0x73ca8` | 5872 | added | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::admit_bridge_payment::AdmitBridgePaymentV1 as anchor_la |
| `0x75398` | 5872 | added | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::admit_bridge_payment::AdmitBridgePaymentV1 as anchor_la |
| `0x76a88` | 4568 | added | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::admit_bridge_payment::AdmitBridgePaymentV1 as anchor_la |
| `0x77c60` | 4520 | added | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::admit_bridge_payment::AdmitBridgePaymentV1 as anchor_la |
| `0x78e08` | 3328 | added | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::admit_bridge_payment::AdmitBridgePaymentV1 as anchor_la |
| `0x79b08` | 3832 | added | yes | <donation_relay_source_proposal::instructions::v1::relayer_only::admit_bridge_payment::AdmitBridgePaymentV1 as anchor_la |
| `0x7aa00` | 12432 | added | yes | <donation_relay_source_proposal::instructions::v1::recover_bridge_payment::RecoverBridgePaymentV1 as anchor_lang::Accoun |
| `0x7da90` | 5872 | added | yes | <donation_relay_source_proposal::instructions::v1::recover_bridge_payment::RecoverBridgePaymentV1 as anchor_lang::Accoun |
| `0x7f180` | 5872 | added | yes | <donation_relay_source_proposal::instructions::v1::recover_bridge_payment::RecoverBridgePaymentV1 as anchor_lang::Accoun |
| `0x80870` | 2736 | added | yes | <donation_relay_source_proposal::instructions::v1::recover_bridge_payment::RecoverBridgePaymentV1 as anchor_lang::Accoun |
| `0x81320` | 456 | identical | yes | <donation_relay_source_proposal::state::v1::debouncer::DebouncerV1 as anchor_lang::AccountSerialize>::try_serialize |
| `0x814e8` | 1000 | identical | yes | <donation_relay_source_proposal::state::v1::debouncer::DebouncerV1 as anchor_lang::AccountDeserialize>::try_deserialize |
| `0x818d0` | 1168 | identical | yes | <donation_relay_source_proposal::state::v1::debouncer::DebouncerV1 as anchor_lang::AccountDeserialize>::try_deserialize_ |
| `0x81d60` | 536 | identical | yes | <donation_relay_source_proposal::state::v1::distribution::DistributionV1 as anchor_lang::AccountSerialize>::try_serializ |
| `0x81f78` | 1016 | identical | yes | <donation_relay_source_proposal::state::v1::distribution::DistributionV1 as anchor_lang::AccountDeserialize>::try_deseri |
| `0x82370` | 1272 | identical | yes | <donation_relay_source_proposal::state::v1::distribution::DistributionV1 as anchor_lang::AccountDeserialize>::try_deseri |
| `0x82868` | 472 | identical | yes | <donation_relay_source_proposal::state::v1::epoch_tracker::EpochTrackerV1 as anchor_lang::AccountSerialize>::try_seriali |
| `0x82a40` | 1016 | identical | yes | <donation_relay_source_proposal::state::v1::epoch_tracker::EpochTrackerV1 as anchor_lang::AccountDeserialize>::try_deser |
| `0x82e38` | 1208 | identical | yes | <donation_relay_source_proposal::state::v1::epoch_tracker::EpochTrackerV1 as anchor_lang::AccountDeserialize>::try_deser |
| `0x832f0` | 520 | identical | yes | <donation_relay_source_proposal::state::v1::mint_whitelist::MintWhitelistV1 as anchor_lang::AccountSerialize>::try_seria |
| `0x834f8` | 1032 | identical | yes | <donation_relay_source_proposal::state::v1::mint_whitelist::MintWhitelistV1 as anchor_lang::AccountDeserialize>::try_des |
| `0x83900` | 472 | identical | yes | <donation_relay_source_proposal::state::v1::mint_whitelist::MintWhitelistV1 as anchor_lang::AccountDeserialize>::try_des |
| `0x83ad8` | 344 | identical | yes | <donation_relay_source_proposal::state::v1::swap_receipt::SwapReceiptV1 as anchor_lang::AccountSerialize>::try_serialize |
| `0x83c30` | 1016 | identical | yes | <donation_relay_source_proposal::state::v1::swap_receipt::SwapReceiptV1 as anchor_lang::AccountDeserialize>::try_deseria |
| `0x84028` | 616 | identical | yes | <donation_relay_source_proposal::state::v1::swap_receipt::SwapReceiptV1 as anchor_lang::AccountDeserialize>::try_deseria |
| `0x84290` | 168 | added | yes | <donation_relay_source_proposal::state::v1::bridge_membership::BridgeSourceV1 as anchor_lang::AccountSerialize>::try_ser |
| `0x84338` | 168 | added | yes | <donation_relay_source_proposal::state::v1::bridge_membership::BridgePaymentV1 as anchor_lang::AccountSerialize>::try_se |
| `0x843e0` | 1992 | modified | yes | donation_relay_source_proposal::anchor_framework::entry |
| `0x84ba8` | 3888 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__idl::__idl_dispatch |
| `0x85ad8` | 3280 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__idl::__idl_create_account |
| `0x867a8` | 1896 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__idl::__idl_resize_account |
| `0x86f10` | 40 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__idl::__idl_close_account |
| `0x86f38` | 128 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__idl::__idl_create_buffer |
| `0x86fb8` | 616 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__idl::__idl_write |
| `0x87220` | 120 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__idl::__idl_set_authority |
| `0x87298` | 1064 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__idl::__idl_set_buffer |
| `0x876c0` | 2336 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::donate_v1 |
| `0x87fe0` | 2336 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::donate_pubkey_config_id_v1 |
| `0x88900` | 2312 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::donate_native_v1 |
| `0x89208` | 2312 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::donate_native_pubkey_config_id_v1 |
| `0x89b10` | 2336 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::donate_pubkey_config_id_with_payer_v1 |
| `0x8a430` | 2792 | modified | yes | donation_relay_source_proposal::anchor_framework::__private::__global::admit_bridge_payment_v1 |
| `0x8af18` | 2280 | added | yes | donation_relay_source_proposal::anchor_framework::__private::__global::recover_bridge_payment_v1 |
| `0x8b800` | 1840 | added | yes | donation_relay_source_proposal::anchor_framework::__private::__global::close_donation_epoch_v1 |
| `0x8bf30` | 1744 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::swap_then_distribute_v1 |
| `0x8c600` | 1480 | added | yes | donation_relay_source_proposal::anchor_framework::__private::__global::just_swap_v1 |
| `0x8cbc8` | 2064 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::distribute_after_just_swapping_v1 |
| `0x8d3d8` | 2064 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::distribute_non_swap_output_mint_v1 |
| `0x8dbe8` | 2064 | modified | yes | donation_relay_source_proposal::anchor_framework::__private::__global::distribute_exact_non_swap_output_mint_v1 |
| `0x8e3f8` | 2064 | added | yes | donation_relay_source_proposal::anchor_framework::__private::__global::distribute_exact_after_just_swapping_v1 |
| `0x8ec08` | 696 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__global::upsert_mint_whitelist_v1 |
| `0x8eec0` | 1312 | identical | yes | donation_relay_source_proposal::anchor_framework::__private::__events::__event_dispatch |
| `0x8f3e0` | 3264 | identical | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::donate_v1 |
| `0x900a0` | 3264 | identical | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::donate_pubkey_config_id_v1 |
| `0x90d60` | 3264 | identical | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::donate_native_v1 |
| `0x91a20` | 3264 | identical | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::donate_native_pubkey_config_id_ |
| `0x926e0` | 3264 | identical | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::donate_pubkey_config_id_with_pa |
| `0x933a0` | 3160 | added | OPEN | #[program] recover_bridge_payment_v1 wrapper |
| `0x93ff8` | 448 | identical | yes | entrypoint |
| `0x941b8` | 272 | identical | yes | _RNvCscR3e5J6VSLN_7___rustc12___rust_alloc |
| `0x942c8` | 8 | identical | yes | _RNvCscR3e5J6VSLN_7___rustc14___rust_dealloc |
| `0x942d0` | 328 | identical | yes | _RNvCscR3e5J6VSLN_7___rustc14___rust_realloc |
| `0x94418` | 304 | identical | yes | _RNvCscR3e5J6VSLN_7___rustc19___rust_alloc_zeroed |
| `0x94548` | 200 | identical | yes | custom_panic |
| `0x94610` | 3152 | added | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::distribute_exact_after_just_swa |
| `0x95260` | 3152 | added | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::distribute_exact_non_swap_outpu |
| `0x95eb0` | 3152 | identical | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::distribute_non_swap_output_mint |
| `0x96b00` | 3152 | identical | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::distribute_after_just_swapping_ |
| `0x97750` | 3208 | added | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::just_swap_v1 |
| `0x983d8` | 3256 | identical | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::swap_then_distribute_v1 |
| `0x99090` | 3296 | modified | yes | donation_relay_source_proposal::anchor_framework::relay_anchor_idl_reconstruction_probe::close_donation_epoch_v1 |
| `0x99d70` | 3336 | modified | OPEN | #[program] admit_bridge_payment_v1 wrapper |
| `0x9aa78` | 3576 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlCloseAccount as anchor_lang::Accounts<donation_r |
| `0x9b870` | 960 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlCloseAccount as anchor_lang::AccountsExit>::exit |
| `0x9bc30` | 2736 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlSetBuffer as anchor_lang::Accounts<donation_rela |
| `0x9c6e0` | 1488 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlSetBuffer as anchor_lang::AccountsExit>::exit |
| `0x9ccb0` | 2536 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlCreateBuffer as anchor_lang::Accounts<donation_r |
| `0x9d698` | 800 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlCreateBuffer as anchor_lang::AccountsExit>::exit |
| `0x9d9b8` | 2832 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlResizeAccount as anchor_lang::Accounts<donation_ |
| `0x9e4c8` | 800 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlResizeAccount as anchor_lang::AccountsExit>::exi |
| `0x9e7e8` | 2264 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlAccounts as anchor_lang::Accounts<donation_relay |
| `0x9f0c0` | 800 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlAccounts as anchor_lang::AccountsExit>::exit |
| `0x9f3e0` | 4528 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlCreateAccounts as anchor_lang::Accounts<donation |
| `0xa0590` | 296 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlAccount as anchor_lang::AccountSerialize>::try_s |
| `0xa06b8` | 536 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlAccount as anchor_lang::AccountSerialize>::try_s |
| `0xa08d0` | 1000 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlAccount as anchor_lang::AccountDeserialize>::try |
| `0xa0cb8` | 488 | identical | yes | <donation_relay_source_proposal::anchor_framework::__private::__idl::IdlAccount as anchor_lang::AccountDeserialize>::try |
| `0xa0ea0` | 16 | identical | yes | _RNvCscR3e5J6VSLN_7___rustc26___rust_alloc_error_handler |
| `0xa0eb0` | 8 | identical | yes | _RNvCscR3e5J6VSLN_7___rustc35___rust_no_alloc_shim_is_unstable_v2 |
| `0xa0eb8` | 400 | identical | yes | core::ptr::drop_in_place<[solana_account_info::AccountInfo; 3]> |
| `0xa1048` | 528 | identical | yes | core::ptr::drop_in_place<[solana_account_info::AccountInfo; 4]> |
| `0xa1258` | 784 | identical | yes | core::ptr::drop_in_place<[solana_account_info::AccountInfo; 6]> |
| `0xa1568` | 1080 | identical | yes | anchor_spl::associated_token::create |
| `0xa19a0` | 2088 | added | yes | anchor_spl::token::transfer_checked |
| `0xa21c8` | 864 | added | yes | <anchor_spl::token::TokenAccount as anchor_lang::AccountDeserialize>::try_deserialize_unchecked |
| `0xa2528` | 816 | added | yes | <anchor_spl::token::Mint as anchor_lang::AccountDeserialize>::try_deserialize_unchecked |
| `0xa2858` | 2088 | identical | yes | anchor_spl::token_2022::transfer_checked |
| `0xa3080` | 1864 | identical | yes | anchor_spl::token_2022::burn |
| `0xa37c8` | 2064 | identical | yes | anchor_spl::token_2022::initialize_account3 |
| `0xa3fd8` | 1848 | identical | yes | anchor_spl::token_2022::close_account |
| `0xa4710` | 1488 | identical | yes | anchor_spl::token_2022::sync_native |
| `0xa4ce0` | 1008 | identical | yes | <anchor_spl::token_interface::TokenAccount as anchor_lang::AccountDeserialize>::try_deserialize_unchecked |
| `0xa50d0` | 1144 | identical | yes | <anchor_spl::token_interface::Mint as anchor_lang::AccountDeserialize>::try_deserialize_unchecked |
| `0xa5548` | 328 | identical | yes | alloc::raw_vec::finish_grow |
| `0xa5690` | 376 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xa5808` | 360 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xa5970` | 640 | identical | yes | alloc::raw_vec::RawVecInner<A>::reserve::do_reserve_and_handle |
| `0xa5bf0` | 224 | identical | yes | spl_token_2022::extension::get_tlv_indices |
| `0xa5cd0` | 32 | identical | yes | spl_token_2022::extension::adjust_len_for_multisig |
| `0xa5cf0` | 1032 | identical | yes | spl_token_2022::extension::get_tlv_data_info |
| `0xa60f8` | 80 | identical | yes | <spl_token_2022::extension::ExtensionType as core::convert::TryFrom<&[u8]>>::try_from |
| `0xa6148` | 1176 | identical | yes | spl_token_2022::extension::ExtensionType::try_get_total_tlv_len |
| `0xa65e0` | 824 | identical | yes | spl_token_2022::extension::ExtensionType::get_required_init_account_extensions |
| `0xa6918` | 2888 | identical | yes | spl_token_2022::instruction::TokenInstruction::pack |
| `0xa7460` | 776 | identical | yes | spl_token_2022::instruction::initialize_account3 |
| `0xa7768` | 1592 | identical | yes | spl_token_2022::instruction::burn |
| `0xa7da0` | 1560 | identical | yes | spl_token_2022::instruction::close_account |
| `0xa83b8` | 1704 | identical | yes | spl_token_2022::instruction::transfer_checked |
| `0xa8a60` | 584 | identical | yes | spl_token_2022::instruction::sync_native |
| `0xa8ca8` | 744 | identical | yes | <spl_token_2022::state::Mint as solana_program_pack::Pack>::unpack_from_slice |
| `0xa8f90` | 1232 | identical | yes | <spl_token_2022::state::Account as solana_program_pack::Pack>::unpack_from_slice |
| `0xa9460` | 312 | identical | yes | alloc::raw_vec::finish_grow |
| `0xa9598` | 432 | identical | yes | alloc::raw_vec::RawVecInner<A>::reserve::do_reserve_and_handle |
| `0xa9748` | 1736 | added | yes | spl_token::instruction::TokenInstruction::pack |
| `0xa9e10` | 1600 | added | yes | spl_token::instruction::transfer_checked |
| `0xaa450` | 744 | added | yes | <spl_token::state::Mint as solana_program_pack::Pack>::unpack_from_slice |
| `0xaa738` | 1232 | added | yes | <spl_token::state::Account as solana_program_pack::Pack>::unpack_from_slice |
| `0xaac08` | 312 | identical | yes | alloc::raw_vec::finish_grow |
| `0xaad40` | 408 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xaaed8` | 80 | identical | yes | alloc::rc::Rc<T,A>::drop_slow |
| `0xaaf28` | 80 | identical | yes | alloc::rc::Rc<T,A>::drop_slow |
| `0xaaf78` | 176 | identical | yes | std::io::error::Error::new |
| `0xab028` | 48 | identical | yes | core::ptr::drop_in_place<alloc::boxed::convert::<impl core::convert::From<alloc::string::String> for alloc::boxed::Box<d |
| `0xab058` | 16 | identical | yes | core::error::Error::cause |
| `0xab068` | 8 | identical | yes | core::error::Error::provide |
| `0xab070` | 40 | identical | yes | core::error::Error::type_id |
| `0xab098` | 160 | identical | yes | spl_pod::optional_keys::<impl core::convert::From<spl_pod::optional_keys::OptionalNonZeroElGamalPubkey> for core::option |
| `0xab138` | 528 | identical | yes | spl_associated_token_account_client::address::get_associated_token_address_with_program_id |
| `0xab348` | 1296 | identical | yes | spl_associated_token_account_client::instruction::build_associated_token_account_instruction |
| `0xab858` | 40 | identical | yes | spl_associated_token_account_client::instruction::create_associated_token_account |
| `0xab880` | 232 | added | yes | serde_core::de::Error::invalid_value |
| `0xab968` | 224 | added | yes | serde_core::de::Error::invalid_length |
| `0xaba48` | 224 | added | yes | serde_core::de::SeqAccess::next_element |
| `0xabb28` | 4400 | added | yes | solana_pubkey::_::<impl serde_core::de::Deserialize for solana_pubkey::Pubkey>::deserialize |
| `0xacc58` | 104 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xaccc0` | 48 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xaccf0` | 48 | identical | yes | <&T as core::fmt::Display>::fmt |
| `0xacd20` | 40 | identical | yes | <&T as core::fmt::Display>::fmt |
| `0xacd48` | 40 | identical | yes | <&T as core::fmt::Display>::fmt |
| `0xacd70` | 48 | added | yes | <T as serde_core::de::Expected>::fmt |
| `0xacda0` | 40 | identical | yes | core::fmt::Write::write_fmt |
| `0xacdc8` | 16 | identical | yes | core::fmt::Formatter::write_fmt |
| `0xacdd8` | 48 | identical | yes | core::ptr::drop_in_place<alloc::string::String> |
| `0xace08` | 48 | identical | yes | <core::fmt::Error as core::fmt::Debug>::fmt |
| `0xace38` | 544 | identical | yes | <alloc::string::String as core::fmt::Write>::write_char |
| `0xad058` | 192 | identical | yes | <alloc::string::String as core::fmt::Write>::write_str |
| `0xad118` | 80 | identical | yes | alloc::rc::Rc<T,A>::drop_slow |
| `0xad168` | 80 | identical | yes | alloc::rc::Rc<T,A>::drop_slow |
| `0xad1b8` | 312 | identical | yes | alloc::raw_vec::finish_grow |
| `0xad2f0` | 640 | identical | yes | alloc::raw_vec::RawVecInner<A>::reserve::do_reserve_and_handle |
| `0xad570` | 40 | identical | yes | <alloc::string::String as core::fmt::Display>::fmt |
| `0xad598` | 1240 | identical | yes | <solana_program_error::ProgramError as core::fmt::Debug>::fmt |
| `0xada70` | 912 | identical | yes | <solana_program_error::ProgramError as core::clone::Clone>::clone |
| `0xade00` | 456 | added | yes | bincode::error::<impl serde_core::de::Error for alloc::boxed::Box<bincode::error::ErrorKind>>::custom |
| `0xadfc8` | 216 | identical | yes | <T as alloc::slice::<impl [T]>::to_vec_in::ConvertVec>::to_vec |
| `0xae0a0` | 88 | identical | yes | anchor_lang::accounts::signer::Signer::try_from |
| `0xae0f8` | 16 | identical | yes | <anchor_lang::bpf_upgradeable_state::ProgramData as anchor_lang::AccountDeserialize>::try_deserialize |
| `0xae108` | 344 | added | yes | <anchor_lang::bpf_upgradeable_state::ProgramData as anchor_lang::AccountDeserialize>::try_deserialize_unchecked |
| `0xae260` | 1936 | added | yes | anchor_lang::bpf_upgradeable_state::<impl anchor_lang::AccountDeserialize for solana_loader_v3_interface::state::Upgrade |
| `0xae9f0` | 272 | identical | yes | <anchor_lang::bpf_writer::BpfWriter<&mut [u8]> as std::io::Write>::write_all |
| `0xaeb00` | 904 | identical | yes | anchor_lang::common::close |
| `0xaee88` | 96 | identical | yes | anchor_lang::common::is_closed |
| `0xaeee8` | 136 | identical | yes | <anchor_lang::error::Error as core::convert::From<anchor_lang::error::AnchorError>>::from |
| `0xaef70` | 160 | identical | yes | <anchor_lang::error::Error as core::convert::From<solana_program_error::ProgramError>>::from |
| `0xaf010` | 64 | identical | yes | anchor_lang::error::Error::log |
| `0xaf050` | 488 | identical | yes | anchor_lang::error::Error::with_pubkeys |
| `0xaf238` | 1800 | identical | yes | anchor_lang::error::ProgramErrorWithOrigin::log |
| `0xaf940` | 1592 | identical | yes | anchor_lang::error::AnchorError::log |
| `0xaff78` | 632 | identical | yes | anchor_lang::error::<impl core::convert::From<anchor_lang::error::Error> for solana_program_error::ProgramError>::from |
| `0xb01f0` | 1040 | identical | yes | anchor_lang::system_program::allocate |
| `0xb0600` | 1040 | identical | yes | anchor_lang::system_program::assign |
| `0xb0a10` | 1240 | identical | yes | anchor_lang::system_program::create_account |
| `0xb0ee8` | 1200 | identical | yes | anchor_lang::system_program::transfer |
| `0xb1398` | 16 | identical | yes | anchor_lang::solana_program::log::sol_log_data |
| `0xb13a8` | 3088 | identical | yes | anchor_lang::error::ErrorCode::name |
| `0xb1fb8` | 584 | identical | yes | <anchor_lang::error::Error as core::convert::From<anchor_lang::error::ErrorCode>>::from |
| `0xb2200` | 2552 | identical | yes | <anchor_lang::error::ErrorCode as core::fmt::Display>::fmt |
| `0xb2bf8` | 40 | identical | yes | solana_invoke::invoke |
| `0xb2c20` | 1112 | identical | yes | solana_invoke::invoke_signed |
| `0xb3078` | 200 | identical | yes | solana_sysvar::rent::<impl solana_sysvar::Sysvar for solana_rent::Rent>::get |
| `0xb3140` | 312 | identical | yes | alloc::raw_vec::finish_grow |
| `0xb3278` | 408 | added | OPEN | alloc::raw_vec::RawVec<T,A>::grow_one (spl_token::instruction::transfer_checked) |
| `0xb3410` | 16 | identical | yes | solana_cpi::set_return_data |
| `0xb3420` | 312 | identical | yes | alloc::raw_vec::finish_grow |
| `0xb3558` | 424 | added | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xb3700` | 3272 | identical | yes | solana_program_entrypoint::deserialize |
| `0xb43c8` | 1576 | identical | yes | solana_pubkey::_::<impl serde_core::ser::Serialize for solana_pubkey::Pubkey>::serialize |
| `0xb49f0` | 8072 | identical | yes | solana_instruction::Instruction::new_with_bincode |
| `0xb6978` | 48 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xb69a8` | 24 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xb69c0` | 104 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xb6a28` | 168 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xb6ad0` | 224 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xb6bb0` | 104 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xb6c18` | 96 | identical | yes | core::fmt::num::<impl core::fmt::Debug for usize>::fmt |
| `0xb6c78` | 416 | identical | yes | core::ptr::drop_in_place<alloc::boxed::Box<bincode::error::ErrorKind>> |
| `0xb6e18` | 312 | added | yes | alloc::raw_vec::finish_grow |
| `0xb6f50` | 640 | identical | yes | alloc::raw_vec::RawVecInner<A>::reserve::do_reserve_and_handle |
| `0xb71d0` | 744 | identical | yes | <alloc::boxed::Box<T,A> as core::fmt::Debug>::fmt |
| `0xb74b8` | 464 | identical | yes | solana_system_interface::instruction::create_account |
| `0xb7688` | 928 | identical | yes | solana_system_interface::instruction::create_account_with_seed |
| `0xb7a28` | 344 | identical | yes | solana_system_interface::instruction::assign |
| `0xb7b80` | 368 | identical | yes | solana_system_interface::instruction::transfer |
| `0xb7cf0` | 288 | identical | yes | solana_system_interface::instruction::allocate |
| `0xb7e10` | 376 | identical | yes | solana_rent::Rent::minimum_balance |
| `0xb7f88` | 400 | identical | yes | solana_rent::Rent::is_exempt |
| `0xb8118` | 120 | identical | yes | solana_account_info::AccountInfo::lamports |
| `0xb8190` | 80 | identical | yes | solana_account_info::AccountInfo::data_len |
| `0xb81e0` | 128 | identical | yes | solana_account_info::AccountInfo::try_data_len |
| `0xb8260` | 104 | identical | yes | solana_account_info::AccountInfo::data_is_empty |
| `0xb82c8` | 408 | identical | yes | solana_account_info::AccountInfo::resize |
| `0xb8460` | 80 | identical | yes | solana_account_info::AccountInfo::assign |
| `0xb84b0` | 48 | identical | yes | <&T as core::fmt::Display>::fmt |
| `0xb84e0` | 24 | identical | yes | <&T as core::fmt::LowerHex>::fmt |
| `0xb84f8` | 1416 | identical | yes | <solana_program_error::ProgramError as core::fmt::Display>::fmt |
| `0xb8a80` | 952 | identical | yes | solana_program_error::<impl core::convert::From<solana_program_error::ProgramError> for u64>::from |
| `0xb8e38` | 1144 | identical | yes | <solana_program_error::ProgramError as core::convert::From<u64>>::from |
| `0xb92b0` | 368 | identical | yes | solana_instruction::Instruction::new_with_bytes |
| `0xb9420` | 112 | added | yes | bincode::error::<impl core::convert::From<std::io::error::Error> for alloc::boxed::Box<bincode::error::ErrorKind>>::from |
| `0xb9490` | 288 | identical | yes | solana_pubkey::Pubkey::create_with_seed |
| `0xb95b0` | 312 | identical | yes | solana_pubkey::Pubkey::find_program_address |
| `0xb96e8` | 424 | identical | yes | solana_pubkey::Pubkey::create_program_address |
| `0xb9890` | 16 | identical | yes | solana_pubkey::Pubkey::log |
| `0xb98a0` | 6624 | identical | yes | solana_pubkey::write_as_base58 |
| `0xbb280` | 40 | identical | yes | <solana_pubkey::Pubkey as core::fmt::Debug>::fmt |
| `0xbb2a8` | 416 | identical | yes | borsh::de::unexpected_eof_to_unexpected_length_of_input |
| `0xbb448` | 160 | identical | yes | solana_sha256_hasher::hashv |
| `0xbb4e8` | 40 | added | yes | <&T as core::fmt::Debug>::fmt |
| `0xbb510` | 40 | identical | yes | core::fmt::Write::write_fmt |
| `0xbb538` | 1312 | added | yes | <serde_core::de::Unexpected as core::fmt::Display>::fmt |
| `0xbba58` | 48 | identical | yes | <serde_core::de::value::Error as core::fmt::Display>::fmt |
| `0xbba88` | 32 | added | yes | <dyn serde_core::de::Expected as core::fmt::Display>::fmt |
| `0xbbaa8` | 528 | added | yes | <serde_core::de::WithDecimalPoint as core::fmt::Display>::fmt |
| `0xbbcb8` | 256 | added | yes | <<serde_core::de::WithDecimalPoint as core::fmt::Display>::fmt::LookForDecimalPoint as core::fmt::Write>::write_str |
| `0xbbdb8` | 96 | added | yes | <<serde_core::de::WithDecimalPoint as core::fmt::Display>::fmt::LookForDecimalPoint as core::fmt::Write>::write_char |
| `0xbbe18` | 48 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xbbe48` | 40 | added | yes | <&T as core::fmt::Debug>::fmt |
| `0xbbe70` | 96 | identical | yes | core::fmt::num::<impl core::fmt::Debug for i32>::fmt |
| `0xbbed0` | 48 | identical | yes | core::ptr::drop_in_place<alloc::boxed::convert::<impl core::convert::From<alloc::string::String> for alloc::boxed::Box<d |
| `0xbbf00` | 48 | identical | yes | core::ptr::drop_in_place<alloc::string::String> |
| `0xbbf30` | 16 | identical | yes | core::error::Error::cause |
| `0xbbf40` | 8 | identical | yes | core::error::Error::provide |
| `0xbbf48` | 40 | identical | yes | core::error::Error::type_id |
| `0xbbf70` | 40 | identical | yes | <alloc::string::String as core::fmt::Debug>::fmt |
| `0xbbf98` | 16 | identical | yes | <std::io::error::Error as core::fmt::Debug>::fmt |
| `0xbbfa8` | 376 | identical | yes | std::io::error::Error::new |
| `0xbc120` | 128 | identical | yes | std::io::error::Error::_new |
| `0xbc1a0` | 1184 | identical | yes | std::io::error::<impl core::fmt::Debug for std::io::error::repr_bitpacked::Repr>::fmt |
| `0xbc640` | 8 | identical | yes | std::process::abort |
| `0xbc648` | 8 | identical | yes | _RNvCscR3e5J6VSLN_7___rustc17rust_begin_unwind |
| `0xbc650` | 112 | identical | yes | <std::io::error::ErrorKind as core::fmt::Debug>::fmt |
| `0xbc6c0` | 16 | identical | yes | std::sys::pal::sbf::sol_log |
| `0xbc6d0` | 16 | identical | yes | std::sys::pal::sbf::panic |
| `0xbc6e0` | 8 | identical | yes | std::sys::pal::sbf::abort_internal |
| `0xbc6e8` | 40 | identical | yes | std::alloc::rust_oom |
| `0xbc710` | 8 | identical | yes | _RNvCscR3e5J6VSLN_7___rustc8___rg_oom |
| `0xbc718` | 40 | identical | yes | core::fmt::Write::write_fmt |
| `0xbc740` | 48 | identical | yes | core::ptr::drop_in_place<alloc::string::String> |
| `0xbc770` | 48 | identical | yes | <core::fmt::Error as core::fmt::Debug>::fmt |
| `0xbc7a0` | 88 | identical | yes | alloc::raw_vec::capacity_overflow |
| `0xbc7f8` | 280 | identical | yes | alloc::raw_vec::RawVec<T,A>::grow_one |
| `0xbc910` | 432 | added | yes | alloc::raw_vec::RawVecInner<A>::reserve::do_reserve_and_handle |
| `0xbcac0` | 312 | added | OPEN | alloc::raw_vec::finish_grow, separate instance |
| `0xbcbf8` | 32 | identical | yes | alloc::raw_vec::handle_error |
| `0xbcc18` | 32 | identical | yes | alloc::alloc::handle_alloc_error |
| `0xbcc38` | 24 | identical | yes | <alloc::boxed::convert::<impl core::convert::From<alloc::string::String> for alloc::boxed::Box<dyn core::error::Error+co |
| `0xbcc50` | 40 | identical | yes | <alloc::boxed::convert::<impl core::convert::From<alloc::string::String> for alloc::boxed::Box<dyn core::error::Error+co |
| `0xbcc78` | 40 | identical | yes | <alloc::boxed::convert::<impl core::convert::From<alloc::string::String> for alloc::boxed::Box<dyn core::error::Error+co |
| `0xbcca0` | 584 | identical | yes | alloc::fmt::format::format_inner |
| `0xbcee8` | 24 | identical | yes | <alloc::string::FromUtf8Error as core::fmt::Display>::fmt |
| `0xbcf00` | 232 | identical | yes | <alloc::string::String as core::clone::Clone>::clone |
| `0xbcfe8` | 176 | identical | yes | <alloc::string::String as core::fmt::Write>::write_str |
| `0xbd098` | 528 | identical | yes | <alloc::string::String as core::fmt::Write>::write_char |
| `0xbd2a8` | 1400 | added | yes | core::num::flt2dec::strategy::dragon::mul_pow10 |
| `0xbd820` | 8592 | added | yes | core::num::flt2dec::strategy::dragon::format_shortest |
| `0xbf9b0` | 7648 | added | yes | core::num::flt2dec::strategy::dragon::format_exact |
| `0xc1790` | 4344 | added | yes | core::num::flt2dec::strategy::grisu::format_shortest_opt |
| `0xc2888` | 2472 | added | yes | core::num::flt2dec::strategy::grisu::format_exact_opt |
| `0xc3230` | 928 | added | yes | core::num::flt2dec::strategy::grisu::format_exact_opt::possibly_round |
| `0xc35d0` | 648 | added | yes | core::num::flt2dec::digits_to_dec_str |
| `0xc3858` | 160 | identical | yes | <core::ops::range::Range<Idx> as core::fmt::Debug>::fmt |
| `0xc38f8` | 48 | identical | yes | <core::cell::BorrowError as core::fmt::Display>::fmt |
| `0xc3928` | 48 | identical | yes | <core::cell::BorrowMutError as core::fmt::Display>::fmt |
| `0xc3958` | 152 | identical | yes | core::cell::panic_already_borrowed |
| `0xc39f0` | 152 | identical | yes | core::cell::panic_already_mutably_borrowed |
| `0xc3a88` | 2304 | identical | yes | core::char::methods::<impl char>::escape_debug_ext |
| `0xc4388` | 40 | identical | yes | core::option::unwrap_failed |
| `0xc43b0` | 168 | identical | yes | core::option::expect_failed |
| `0xc4458` | 568 | identical | yes | <core::panic::panic_info::PanicInfo as core::fmt::Display>::fmt |
| `0xc4690` | 48 | identical | yes | core::panicking::panic_fmt |
| `0xc46c0` | 104 | identical | yes | core::panicking::panic |
| `0xc4728` | 200 | identical | yes | core::panicking::panic_bounds_check |
| `0xc47f0` | 120 | added | yes | core::panicking::assert_failed |
| `0xc4868` | 680 | added | yes | core::panicking::assert_failed_inner |
| `0xc4b10` | 232 | identical | yes | core::result::unwrap_failed |
| `0xc4bf8` | 1256 | identical | yes | <core::fmt::builders::PadAdapter as core::fmt::Write>::write_str |
| `0xc50e0` | 216 | identical | yes | <core::fmt::builders::PadAdapter as core::fmt::Write>::write_char |
| `0xc51b8` | 856 | identical | yes | core::fmt::builders::DebugStruct::field |
| `0xc5510` | 240 | identical | yes | core::fmt::builders::DebugStruct::finish |
| `0xc5600` | 640 | identical | yes | core::fmt::builders::DebugTuple::field |
| `0xc5880` | 336 | identical | yes | core::fmt::builders::DebugTuple::finish |
| `0xc59d0` | 1912 | added | yes | core::fmt::float::float_to_decimal_common_exact |
| `0xc6148` | 1480 | added | yes | core::fmt::float::float_to_decimal_common_shortest |
| `0xc6710` | 40 | added | yes | core::fmt::Write::write_fmt |
| `0xc6738` | 48 | added | yes | <core::fmt::Arguments as core::fmt::Display>::fmt |
| `0xc6768` | 1000 | identical | yes | core::fmt::write |
| `0xc6b50` | 1544 | identical | yes | core::fmt::Formatter::pad_integral |
| `0xc7158` | 184 | identical | yes | core::fmt::Formatter::pad_integral::write_prefix |
| `0xc7210` | 1320 | identical | yes | core::fmt::Formatter::pad |
| `0xc7738` | 1312 | added | yes | core::fmt::Formatter::pad_formatted_parts |
| `0xc7c58` | 776 | added | yes | core::fmt::Formatter::write_formatted_parts |
| `0xc7f60` | 48 | identical | yes | <core::fmt::Formatter as core::fmt::Write>::write_str |
| `0xc7f90` | 96 | identical | yes | core::fmt::Formatter::debug_struct |
| `0xc7ff0` | 408 | identical | yes | core::fmt::Formatter::debug_struct_field2_finish |
| `0xc8188` | 136 | identical | yes | core::fmt::Formatter::debug_tuple |
| `0xc8210` | 720 | identical | yes | core::fmt::Formatter::debug_tuple_field1_finish |
| `0xc84e0` | 48 | added | yes | <core::fmt::Formatter as core::fmt::Write>::write_char |
| `0xc8510` | 104 | added | yes | <bool as core::fmt::Display>::fmt |
| `0xc8578` | 2032 | identical | yes | <str as core::fmt::Debug>::fmt |
| `0xc8d68` | 48 | identical | yes | <str as core::fmt::Display>::fmt |
| `0xc8d98` | 312 | identical | yes | <char as core::fmt::Debug>::fmt |
| `0xc8ed0` | 520 | added | yes | <char as core::fmt::Display>::fmt |
| `0xc90d8` | 496 | added | yes | core::slice::memchr::memchr_aligned |
| `0xc92c8` | 424 | identical | yes | core::slice::sort::stable::drift::sqrt_approx |
| `0xc9470` | 96 | identical | yes | core::slice::sort::shared::smallsort::panic_on_ord_violation |
| `0xc94d0` | 8 | identical | yes | core::slice::index::slice_start_index_len_fail |
| `0xc94d8` | 8 | identical | yes | core::slice::index::slice_end_index_len_fail |
| `0xc94e0` | 8 | identical | yes | core::slice::index::slice_index_order_fail |
| `0xc94e8` | 1368 | identical | yes | core::str::converts::from_utf8 |
| `0xc9a40` | 1480 | identical | yes | core::str::count::do_count_chars |
| `0xca008` | 352 | identical | yes | <core::str::error::Utf8Error as core::fmt::Display>::fmt |
| `0xca168` | 8 | identical | yes | core::str::slice_error_fail |
| `0xca170` | 1976 | identical | yes | core::str::slice_error_fail_rt |
| `0xca928` | 648 | identical | yes | core::unicode::printable::check |
| `0xcabb0` | 768 | identical | yes | core::unicode::printable::is_printable |
| `0xcaeb0` | 1360 | added | yes | core::num::bignum::Big32x40::mul_pow2 |
| `0xcb400` | 1512 | added | yes | core::num::bignum::Big32x40::mul_digits |
| `0xcb9e8` | 88 | identical | yes | core::panicking::panic_const::panic_const_add_overflow |
| `0xcba40` | 88 | identical | yes | core::panicking::panic_const::panic_const_sub_overflow |
| `0xcba98` | 88 | identical | yes | core::panicking::panic_const::panic_const_mul_overflow |
| `0xcbaf0` | 88 | added | yes | core::panicking::panic_const::panic_const_div_by_zero |
| `0xcbb48` | 168 | added | yes | core::fmt::float::<impl core::fmt::Display for f64>::fmt |
| `0xcbbf0` | 280 | identical | yes | core::fmt::num::<impl core::fmt::LowerHex for i8>::fmt |
| `0xcbd08` | 280 | identical | yes | core::fmt::num::<impl core::fmt::UpperHex for i8>::fmt |
| `0xcbe20` | 288 | identical | yes | core::fmt::num::<impl core::fmt::LowerHex for i32>::fmt |
| `0xcbf40` | 288 | identical | yes | core::fmt::num::<impl core::fmt::UpperHex for i32>::fmt |
| `0xcc060` | 264 | identical | yes | core::fmt::num::<impl core::fmt::LowerHex for isize>::fmt |
| `0xcc168` | 264 | identical | yes | core::fmt::num::<impl core::fmt::UpperHex for isize>::fmt |
| `0xcc270` | 536 | added | yes | core::fmt::num::<impl core::fmt::Debug for u64>::fmt |
| `0xcc488` | 560 | identical | yes | core::fmt::num::<impl core::fmt::Debug for usize>::fmt |
| `0xcc6b8` | 384 | identical | yes | core::fmt::num::imp::<impl core::fmt::Display for u8>::fmt |
| `0xcc838` | 120 | identical | yes | core::fmt::num::imp::<impl core::fmt::Display for u32>::fmt |
| `0xcc8b0` | 192 | identical | yes | core::fmt::num::imp::<impl core::fmt::Display for i32>::fmt |
| `0xcc970` | 776 | identical | yes | core::fmt::num::imp::<impl u32>::_fmt |
| `0xccc78` | 120 | identical | yes | core::fmt::num::imp::<impl core::fmt::Display for u64>::fmt |
| `0xcccf0` | 176 | added | yes | core::fmt::num::imp::<impl core::fmt::Display for isize>::fmt |
| `0xccda0` | 656 | identical | yes | core::fmt::num::imp::<impl u64>::_fmt |
| `0xcd030` | 48 | identical | yes | <&T as core::fmt::Debug>::fmt |
| `0xcd060` | 32 | added | yes | <&T as core::fmt::Debug>::fmt |
| `0xcd080` | 48 | added | yes | <&T as core::fmt::Display>::fmt |
| `0xcd0b0` | 200 | identical | yes | core::slice::index::slice_start_index_len_fail::do_panic::runtime |
| `0xcd178` | 200 | identical | yes | core::slice::index::slice_end_index_len_fail::do_panic::runtime |
| `0xcd240` | 200 | identical | yes | core::slice::index::slice_index_order_fail::do_panic::runtime |
| `0xcd308` | 1096 | identical | yes | core::unicode::unicode_data::grapheme_extend::lookup_slow |
| `0xcd750` | 32 | identical | yes | memcpy |
| `0xcd770` | 40 | identical | yes | memset |
| `0xcd798` | 64 | identical | yes | memcmp |
| `0xcd7d8` | 80 | identical | yes | __udivti3 |
| `0xcd828` | 5128 | identical | yes | compiler_builtins::int::specialized_div_rem::u128_div_rem |
| `0xcec30` | 1208 | added | yes | compiler_builtins::int::specialized_div_rem::u64_div_rem |
| `0xcf0e8` | 512 | identical | yes | __floatundidf |
| `0xcf2e8` | 256 | identical | yes | __gedf2 |
| `0xcf3e8` | 16 | added | yes | __muldf3 |
| `0xcf3f8` | 2008 | identical | yes | compiler_builtins::float::mul::__muldf3 |
| `0xcfbd0` | 184 | identical | yes | __fixunsdfdi |
| `0xcfc88` | 168 | identical | yes | __ashlti3 |
| `0xcfd30` | 176 | identical | yes | __lshrti3 |
| `0xcfde0` | 344 | identical | yes | __multi3 |
| `0xcff38` | 256 | identical | yes | __gtdf2 |
| `0xd0038` | 152 | added | yes | __divdi3 |
