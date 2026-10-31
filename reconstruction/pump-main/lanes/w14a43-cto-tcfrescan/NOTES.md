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

## Part 3 (branch -3, main 0fbf8da): vault ATA literal data-first with owner and data re-read

| | main 0fbf8da | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.65578 | **0.65638** |
| slots_diff | 3,280 | 3,280 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | 09527547fdfca900 |

Change (`pump_creator_vault_ata` in the sweep TCF CPI):
`AccountInfo{key:x.key,data:a.creator_vault_quote_token_account.data.clone(),owner:a.creator_vault_quote_token_account.owner,lamports:x.lamports.clone(),rent_epoch,..flags}`.

How it was found, all on 0fbf8da:
1. Converged scans (no variant above main): pp 1,068, place 8,019, re-read singles + within-clone pairs 388.
2. Rc-order swap per clone (data.clone() before lamports.clone(), #3340's lever), 12 source captures (`e/rc/`):
   event_authority 0.65548, program 0.65518, ATA / ccva / quote_mint / system program 0.65488,
   payer / first pump_amm / token program 0.65458, vault authority 0.61955 at 27,424.
   **The vault ATA with its data re-read goes data-first at -8 B (27,392, 0.65558).** The natural literals of payer and quote_mint
   equal main (`eq_main`), so a to_account_info clone and its literal are the same source.
3. The re-read oracle on that -8 B base: owner re-read 0.65638, vault authority data re-read 0.65608, lamports re-read 0.65608
   (all three source-confirmed: `e/s/s1..s3`). s1 is a local optimum for re-reads, singles and pairs.

-8 B bases tried for +8 B repays (none above main): nB `!is_writable` 0.65618 at 27,392 B with 48 catalog knobs
(`sizeknobs-cto.json`) and all re-reads; sh_iflet 0.65558; tp_dlen 0.65468; ev_hr_curve 0.65288.

## Part 4 (branch -4, mains d371f97 -> 6330811 -> c3e5b51): -8 B wallet repay + sharing `program` data re-read

| | main c3e5b51 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.65698 | **0.65728** |
| slots_diff | 3,182 | 3,192 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | fdf689ca7a561b01 |

Change:
- wallet: `if a.current_creator.is_writable==false` -> `if !a.current_creator.is_writable` (nB, -8 B; this undoes the
  `==false` part of #3315's Q7 repay set);
- sharing CPI `program:` literal: `data:x.data.clone()` -> `data:a.pump_fees.data.clone()` (+8 B re-read).

The TCF clone space is converged on d371f97 and on 6330811 (the post-#3358 main):

| screen (6330811 unless noted) | runs | best at 27,400 | main |
| --- | ---: | --- | ---: |
| re-read singles + within-clone pairs, 11 TCF clones | 388 | = main | 0.65698 |
| Rc-order swap per TCF clone (`e/rc2`) | 10 captures | event_authority 0.65668, program 0.65638 | 0.65698 |
| event_authority swap + a second swap (`e/rcp`) | 5 | program 0.65608 | |
| vault ATA: the other 11 orders of K / D(re-read) / O(re-read) / L with D before L (`e/x12p`, d371f97) | 11 | DOKL / DKOL 0.65548 | 0.65638 |
| -8 B nB (0.65678 @ 27,392) + one TCF re-read | 88 | vault authority data 0.65548 | |
| -8 B nO (vault ATA owner via x, 0.65558) + one TCF re-read | 88 | vault ATA owner re-read 0.65698 (= main) | |
| -16 B nO+nB + 91 cross-clone re-read pairs (d371f97) | 91 | 0.65548 | 0.65638 |
| **-8 B nB + one sharing-clone re-read** (`tools/allclones.py` finds the 4 sharing clones: CpiContext pump_fees, authority, pool_authority, program) | 112 | **program data 0.65728** (sharing authority data 0.65638) | 0.65698 |

Other -8 B repays paired with the sharing program data re-read (c3e5b51): sh_iflet 0.65698 (already on main), tp_dlen 0.65608,
nO 0.65608, ev_hr_curve 0.65428.

## Tools (this lane, `tools/`)

- `rscan.py <mn.ll> <out.jsonl> <threads> <clone ptr ...>`: re-read oracle. For each clone pointer X (`X = load ptr, ptr G`)
  and each field read (key, owner, rent, the three flags, lamports, data), it re-loads X from G right before that read and
  uses the new load. The source form is `a.<account>.<field>`. `PAIRS=1` adds within-clone pairs, and `JOBS=<file>` takes
  explicit `X@f+Y@g` jobs. Source captures match the oracle exactly (x12 data, system program executable, vault ATA
  owner, sharing program data).
- `allclones.py <mn.ll>`: every inlined AccountInfo clone pointer in execute (11 TCF + 4 sharing on 6330811). `names.py` lists only the TCF ones.
- `pscan.py` (from w14a23), patched for a data GEP on a re-loaded pointer; `pscan3.py` adds `XBASE/XOFF` for the
  inline-in-struct accounts (step 2).
- `kv.sh` / `cq.sh` / `capvar.sh`: source-capture queues (`e/klib.py` holds the knob and repay edits).

## Part 5 (branch -5, main 2e1379d): sharing `program` literal data-first + lamports re-read

| | main 2e1379d | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.65728 | **0.65758** |
| slots_diff | 3,192 | 3,192 |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha16 | | bcefc454326055cb |

Change (sharing CPI `program:`): `AccountInfo{data:a.pump_fees.data.clone(),key:x.key,lamports:a.pump_fees.lamports.clone(),owner:x.owner,..}`.
This is the same recipe as part 3 (Rc swap of a literal whose data is already re-read, -8 B, then one more re-read, +8 B).

Screens on 2e1379d (all below or equal to main):
- Move a re-read: remove one (pump_fees data rF, pool_authority rent rP, vault ATA owner nO) or apply a -8 B knob
  (tp_dlen, ev_hr_curve). Then add one re-read over all 15 inlined clones (113-114 runs per base). Best: reverse moves = main.
  Removing the vault ATA data re-read (rD) gives a byte-identical result.
- Two re-read moves (-16 B bases rF+rP, rF+nO, rP+nO, then 66 cross pairs each): best 0.65728.
- Rc swap of the 5 sharing literals (`e/src`): mint 0.65668, authority 0.65219, global 0.64769, pool_authority 0.6414;
  program 0.65678 at 27,392 B, which led to this change.
