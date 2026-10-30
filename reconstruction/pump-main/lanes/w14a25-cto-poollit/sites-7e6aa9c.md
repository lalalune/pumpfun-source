| site | ours | orig | orig n | ours n | sk | fm | raw |
|---|---|---|--:|--:|--:|--:|--:|
| sharing CPI ret + curve update + pool gate | 0x49f8-0x4c10 | 0x4a78-0x4c48 | 57 | 65 | 48 | 34 | 32 |
| pool CPI clone run + admin_cto_pool call | 0x4c10-0x4df0 | 0x4c58-0x4e28 | 59 | 60 | 57 | 57 | 55 |
| post-pool Clock + AdminCtoEvent build + emit! | 0x4df0-0x50c0 | 0x4e30-0x50f8 | 90 | 90 | 88 | 73 | 72 |
| AdminCtoEvent emit_cpi (clone, data, ix, invoke_signed) | 0x50c0-0x5388 | 0x5108-0x53b0 | 82 | 85 | 81 | 78 | 77 |
| emit_cpi Err/drop + error tails (to_string, AnchorError) | 0x5388-0x5990 | 0x53b8-0x59b0 | 180 | 181 | 178 | 156 | 152 |
| sweep native arm (Rent, ensure_rent_exempt, transfer) | 0x5990-0x5bd0 | 0x59c0-0x5bd0 | 66 | 71 | 57 | 48 | 39 |
| wallet gates (native, data_is_empty, token_frozen) | 0x5bd0-0x5cd0 | 0x5bd8-0x5cb8 | 29 | 32 | 29 | 22 | 20 |
| wallet ATA create #1 clone run + call | 0x5cd0-0x5e40 | 0x5cc0-0x5e28 | 46 | 46 | 46 | 35 | 34 |
| ATA create #2 clone run + call | 0x5e40-0x6000 | 0x5e30-0x5ff8 | 58 | 56 | 52 | 42 | 40 |
| transfer_vault_tokens + collect + Clock | 0x6000-0x62c0 | 0x6000-0x62b8 | 88 | 88 | 86 | 76 | 72 |
| collect Ok/Err joins + do_coin token_frozen | 0x62c0-0x63a0 | 0x62c0-0x63b0 | 31 | 28 | 26 | 21 | 19 |
| CollectCreatorFeeEvent build + emit! | 0x63a0-0x64d8 | 0x63b8-0x64e8 | 39 | 39 | 39 | 32 | 31 |
| collect emit_cpi (authority clone, data, ix, invoke_signed) | 0x64d8-0x6798 | 0x64f0-0x67a8 | 84 | 84 | 84 | 76 | 66 |
| emit_cpi drops + coin gate | 0x6798-0x6878 | 0x67b0-0x6868 | 23 | 27 | 23 | 21 | 20 |
| collect_coin_creator_fee clone run + call | 0x6878-0x6a28 | 0x6878-0x6a20 | 54 | 54 | 54 | 50 | 48 |
| coin CPI Err joins + drops | 0x6a28-0x7000 | 0x6a28-0x6b00 | 28 | 28 | 28 | 26 | 26 |
