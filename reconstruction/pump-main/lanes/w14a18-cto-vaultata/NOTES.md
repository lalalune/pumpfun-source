# w14a18-cto-vaultata: explicit pump_creator_vault_ata AccountInfo clone (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: origin/main `b174038c1` (w14a17-cto-sweepr0, ratio 0.63571).

## Result

| | main b174038 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.63571 | **0.63781** |
| slots_diff | 3,173 | 3,173 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 192 | 1034 / 192, 0 losses |
| differential | | 363 cases, 0 mismatches |

**Change (sweep, `transfer_creator_fees_to_pump_v2`):**
`pump_creator_vault_ata:a.creator_vault_quote_token_account.to_account_info()`
-> explicit eight-field `AccountInfo{...}` clone from `creator_vault_quote_token_account`
(lamports then data Rc increments; field order as prior vault-ata clone lane).

Mechanism: the natural `to_account_info()` path loads fields in Anchor's default order.
The hand-written clone keeps key/rent_epoch first and matches the original clone skeleton
more closely in this CPI account slot without changing call counts (154 internal / 3 syscall)
or handler size. Rebased onto main after #3250's ATA-program `to_account_info()` win; that
edit is preserved.

## Evidence

- Fresh-main unstripped: `6ac12d7ac16b8f26c22770f26acc5c12b22a59ad54c6ccc89104940b72f87f24`
- Candidate unstripped (two independent identity builds): `d4f603b71e01448a0a4fea44ca4c44dfc8048acbe291590e77f914729174ed3a`
- Candidate runtime: `3dc9f24557adf1b39c60b80d22dcc1ad2750804388757e93ecfba5cb68868a7d`
- Full score vs baseline: empty `gains`/`losses`/`raw_gains`/`raw_losses`
- `python3 scripts/verify_evidence.py` — OK
- `python3 scripts/test_tooling.py` — 228 OK
- `python3 scripts/pump_admin_cto_differential.py` — 363/0

This is a partial similarity gain, not a new complete-window match or whole-ELF identity.
