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

## Part 2 (branch -2, mains 28ab23a -> 6e011ea): move the data reload from the first pump_amm clone to the vault ATA

| | main 28ab23a | main 6e011ea (#3340) | this branch |
| --- | ---: | ---: | ---: |
| admin_cto ratio | 0.65488 | 0.65548 | **0.65578** |
| slots_diff | 3,280 | 3,280 | 3,280 |
| bytes | 27,400 | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | | 363 cases, 0 mismatches |
| unstripped sha16 | | | be9a70f9fbdf0eb5 |

Change (sweep `transfer_creator_fees_to_pump_v2`):
- first `CpiContext::new` pump_amm clone: `data:a.pump_amm.data.clone()` -> `data:x.data.clone()` (nA, -8 B);
- `pump_creator_vault_ata`: `{key,lamports,owner,data:a.creator_vault_quote_token_account.data.clone(),rent,flags}` (+8 B).
  This replaces #3340's data-first order `key,data,owner,lamports` on the same clone.

How it was found: `tools/rscan.py`, a post-opt re-read oracle. For each of the 11 TCF clones and each field read
(key, owner, rent, the three flags, lamports, data) it re-loads the AccountInfo pointer from its accounts slot right
before that read (source form: `a.<account>.<field>`), as singles and within-clone pairs. On main 28ab23a no single
re-read beats main at 27,400 B. #3315 paired the first clone's `a.pump_amm.data` re-read (+8 B) with -8 B repays, so
reverting it (nA) or the `is_writable==false` repay (nB) gives two -8 B bases above main:

| base (27,392 B) | ratio | best +8 B re-read on it (27,400 B) |
| --- | ---: | --- |
| nA: first clone `data:x.data` | 0.65498 | **x12 (vault ATA) data 0.65578**, vault authority data 0.65548, system program executable 0.65518 |
| nB: `!a.current_creator.is_writable` | 0.65528 | token program data 0.65488 (= main) |

Other -8 B repays on 28ab23a (source captures, 27,392 B): sh_iflet 0.65468, tp_dlen 0.65378, ev_hr_curve 0.65199.

## Step results (all on 28ab23a, post-opt llc oracle)

| scan | runs | result |
| --- | ---: | --- |
| place (729 placements) x 11 TCF clones | 8,019 | main placement best for every clone |
| fpair: top-3 non-main placements per clone, cross-clone pairs | 495 | best 0.65428 (below main) |
| step 2: coin_creator / pump_creator_vault as `AccountInfo{..}` literals of `&a.current_creator` / `&a.creator_vault` | 2 captures + 2 x 729 | natural literal 0.58207 @ 27,456 / 0.61405 @ 27,408. The literal re-loads the Rc pointer field after each overflow check (the inlined `Clone` scope is gone), so no placement recovers: best 0.61863 @ 27,400 (`tools/pscan3.py`, XBASE/XOFF mode) |
| step 3: w14a20's `%x.i@exit.i` lead (first clone data via `a.pump_amm`) | | already on main through #3315 (Q7 repay set). On 28ab23a it is worth -0.0001 against `x.data` at -8 B, and the +8 B is better spent on the vault ATA re-read (part 2) |
