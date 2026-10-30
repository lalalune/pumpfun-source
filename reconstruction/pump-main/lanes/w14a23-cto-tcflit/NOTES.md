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

## Part 2 (branch -2, main e87e001, 0.64709): first pump_amm clone in-position order

| | main e87e001 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.64709 | **0.64979** |
| slots_diff | 3,170 | 3,170 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | a4d90a7ab8c06e82 |

Change (sweep TCF CPI, the `CpiContext::new` pump_amm clone): `key,owner,lamports,data,rent_epoch,is_signer,is_writable,executable`
-> `key,owner,lamports,data,rent_epoch,executable,is_writable,is_signer`. The three flags are read in reverse after the data clone.

How it was found: `tools/pscan.py` (from w14a30-cto-shareauthport, built on w14a17-cto-sweepr0's `fscan.py`) with
`MODE=pp`. This mode keeps each clone's placement and tries every read order inside each position. The scan ran over all
11 TCF clones of the post-opt module of main 06967d3 (`tools/ppall.sh`, about 1,000 llc runs, about 3 minutes with
4 threads). I fixed one bug in my copy of pscan: it put a read that sits between the two Rc clones in P0. The current
placement now comes from the read's position relative to the lamports and data GEPs.

| clone (TCF, IR value on 06967d3) | pp orders | best at 27,400 |
| --- | ---: | --- |
| payer, quote_mint, token/system/ATA programs, vault authority, event authority (`%_227.i` .. `%_249.i136`) | 120 each | main order (to_account_info) |
| coin_creator_vault_ata (`%x11.i`, key-mid) | 120 | main |
| pump_creator_vault_ata (`%x12.i`, owner-mid) | 24 | main |
| last `program:` pump_amm (`%x13.i`) | 48 | main (= every flag order) |
| **first CpiContext pump_amm (`%x.i`)** | 48 | **0.64919**: K,O \| L,D \| R,E,W,S (also O,K \| L,D \| R,E,W,S) |

Source-confirmed with the raw-IR capture on 06967d3 (0.64649 -> 0.64919). On e87e001 measure.sh gives 0.64979.

## Raw-IR capture screens (all rejected, ledger approach `tcflit`)

| screen | main | variants | result |
| --- | --- | ---: | --- |
| s1: 10 plain TCF accounts x 8 literal orders + 2 direct `a.X.f` forms | 7e6aa9c | 98 | none above main. The natural literal equals to_account_info. The coin_creator / pump_creator_vault (inline AccountInfo fields) literals lose 0.03-0.06 in every order. |
| s2: all 49 single-field moves of the #3260 vault ATA order | 7e6aa9c | 49 | local optimum (later beaten by sweepr0's owner-mid placement) |
| s3: hoist `let hp:&AccountInfo=..` before the CPI, pass `hp.clone()` | 7e6aa9c | 10 | inline fields equal ratio, all others lose 0.007-0.10 |
| s4: pairs of near-main singles | 7e6aa9c | 4 of 81 | additive losses (stopped when main moved) |
| s5: 7 plain accounts x 5 non-canonical after-data orders | 65df90f | 35 | none above main |

`tools/clonemap.py <listing> lo hi` reports which block (before lamports | between | after data) loads each scalar
field of every AccountInfo clone. On the original, every TCF clone has the natural block map `K||EWSRO`; the last
program clone is `K||SWERO`. The gaining literals move away from this map, so the block map does not predict gains.
The lever is the register and schedule side effect, and the pscan llc oracle predicts that well.
