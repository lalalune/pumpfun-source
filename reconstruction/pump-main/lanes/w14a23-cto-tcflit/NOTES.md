# w14a23-cto-tcflit: AccountInfo literal field order in the sweep TCF CPI (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `1b0ae7021` (0.63661, 3,173 slots). Ledger: approach `tcflit`, keys `0x22a10-w14-1b0ae70-tcflit-*`.

## Step 0: #3260 reproduced on main 1b0ae70 (credit: #3260, w14a18-cto-vaultata, KutluhanETH)

| | main 1b0ae70 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.63661 | **0.63871** |
| slots_diff | 3,173 | 3,173 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | 12e4d8aed9ef0b56 |

Change (sweep `transfer_creator_fees_to_pump_v2`): `pump_creator_vault_ata:a.creator_vault_quote_token_account.to_account_info()`
-> `{let x:&AccountInfo=a.creator_vault_quote_token_account.as_ref();AccountInfo{key:x.key,rent_epoch:x.rent_epoch,lamports:x.lamports.clone(),is_signer:x.is_signer,data:x.data.clone(),owner:x.owner,is_writable:x.is_writable,executable:x.executable}}`.
It composes with #3257 (+0.0021 on top of it, the same gain #3260 measured on b174038).

Mechanism: each AccountInfo clone in the CPI is three blocks split by the two Rc overflow checks
(B0 = before the lamports store, B1 = between lamports and data, B2 = after data, shared with the next clone's B0).
A non-Rc field is loaded in the block its source position falls in, so the literal's field order chooses which
block (and so which spill slot / register window) loads key, owner, rent_epoch and the flags.
