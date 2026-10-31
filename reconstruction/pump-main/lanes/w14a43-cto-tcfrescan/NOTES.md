# w14a43-cto-tcfrescan: TCF clone rescan on main 6db95a7 (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `6db95a764` (0.65458, 3,280 slots). Ledger: approach `tcfrescan`, keys `0x22a10-w14-6db95a7-tcfrescan-*`.
Continues w14a23-cto-tcflit (#3326) and w14a17-cto-sweepr0 (#3306). Their pp/place scans last ran on faf9962;
#3315 (nativejoin) since rewrote the native arm and made the first pump_amm clone read `data` through `a.pump_amm`.

## Result 1: first CpiContext pump_amm clone owner-first

| | main 6db95a7 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.65458 | **0.65488** |
| slots_diff | 3,280 | 3,280 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | 9ed7f3524e3ec6fe |

Change (sweep `transfer_creator_fees_to_pump_v2`, `CpiContext::new` pump_amm clone):
`AccountInfo{key:x.key,owner:x.owner,..}` -> `AccountInfo{owner:x.owner,key:x.key,..}`.
On faf9962 this order tied main (tcflit part 2 found O,K | L,D | R,E,W,S equal to K,O); after #3315 it is +0.0003.

## pp scan (in-position read orders) on a fresh 6db95a7 capture

Raw-IR capture (`tools/capraw.py`) -> `rx.py` (eq_main true) -> `opt -passes=instnamer` -> `pscan.py MODE=pp` per clone.
`pscan.py` fix: after #3315 the first clone's data GEP is on a reloaded pointer (`%_59.i128`), so the data-GEP anchor
falls back to the first `gep .., i64 16` after the lamports GEP.

| clone (IR value on 6db95a7) | pp orders | best at 27,400 |
| --- | ---: | --- |
| `%x.i` first CpiContext pump_amm | 48 | **0.65488** owner,key \| L,D \| R,E,W,S |
| `%_227.i` payer, `%_228.i` quote_mint, `%_229.i` token program, `%_230.i` system program, `%_231.i` ATA program, `%_232.i130` vault authority, `%_249.i136` event authority | 120 each | main |
| `%x11.i` coin_creator_vault_ata | 120 | main |
| `%x12.i` pump_creator_vault_ata | 24 | main |
| `%x13.i` last `program:` pump_amm | 48 | main |
