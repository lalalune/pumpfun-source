# w14a133-cto-tcfrentlate: TCF program-literal rent_epoch-late lead (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs` line 661), pinned at 27,400 B.
Base: main ebe5387 (0.67316 / 3,123 slots, M 2,247). This lane continues w14a114-cto-irscantail (#3512). Its lead was the
TCF CpiContext program literal (`{let x=a.pump_amm.as_ref();AccountInfo{owner,key,lamports,data,rent_epoch,executable,is_writable,is_signer}}`)
with the `rent_epoch` load placed after the first `lifetime.start` of the TCF accounts struct (`_64` pieces): +4 M.

Ledger approach `tcfrentlate`, keys `0x22a10-w14-ebe5387-tcfrentlate-*`. All numbers come from a raw-IR capture
(`capraw.py`) followed by the `rx.py` opt/llc oracle. The unedited capture has `eq_main` true.

## Result: no source change. The angle is exhausted

### 1. IR permutation table (all orders of the literal's tail; `perm120.jsonl`, `tools/perm.py`)

On main's post-opt IR, the tail of the literal (after the data Rc clone) has five units:
- R: the rent load (x+32)
- E, W, S: the flag loads x+42, x+41, x+40
- L: the three `lifetime.start` of `_64.sroa.{20,21,22}.sroa.11`

This lane ran all 120 orders of those units through llc. Each run takes about 0.4 s and needs no build slot.

| class | orders | best | ratio @ bytes |
| --- | ---: | --- | --- |
| L last (every order a field order or struct-update form can produce) | 24 | REWSL = **main** | 0.67316 @ 27,400 |
| L first | 24 | LREWS (ties main) | 0.67316 @ 27,400 |
| L before R | 60 | EWSLR | **0.67436** @ 27,400 (+4 M) |
| | | SLREW | 0.67376 (+2 M) |
| | | WSLRE | 0.67346 (+1 M) |

Main's order (REWSL) is already the best of the 24 L-last orders. All three gains need the accounts struct's `StorageLive`
to fall between some of the flag loads and the rent load. Rust evaluates call arguments left to right, and each argument
completely. The program literal is argument 1 and the accounts struct is argument 2, so no ordinary spelling can split the
literal around argument 2's `StorageLive`. The only way to get it is a dummy memory-resident local inside the literal, and
that is a steering construct the 03:45 rule forbids.

### 2. Source spellings (raw-IR capture + rx, main ebe5387)

| key | spelling | ratio | bytes |
| --- | --- | ---: | ---: |
| fru1 | struct update `AccountInfo{owner,key,lamports.clone(),data.clone(),..*x}` (base fields in declaration order; IR = RSWEL exactly) | 0.67046 | 27,400 |
| fru6 | struct update `key,owner,lamports,data,..*x` (same IR as fru1) | 0.67046 | 27,400 |
| fru2 | struct update `lamports,data,..*x` | 0.6348 | 27,376 |
| fru3 | `owner,key,lamports,data,executable,is_writable,is_signer,..*x` (rent from the base, last) | 0.63252 | 27,416 |
| fru5 | `owner,lamports,data,..*x` (key from the base) | 0.649 | 27,416 |
| fru7 | `owner,key,lamports,data,executable,..*x` | 0.61605 | 27,416 |
| acc1 | accounts bound first: `{let accounts=TransferCreatorFeesToPumpV2{..};CpiContext::new(literal,accounts)}` | 0.57147 | 27,328 |
| acc2 | acc1, with `x` bound before the accounts | 0.58124 | 27,368 |
| lit1 | `CpiContext{accounts:..,remaining_accounts:Vec::new(),program:literal,signer_seeds:&[]}` (accounts evaluated first) | 0.58412 | 27,488 |
| bindp | `let program=literal;CpiContext::new(program,accounts)` (w14a90 bindp, retested) | 0.66817 | 27,368 |
| bindfru | bindp with the fru1 literal | 0.66547 | 27,368 |
| pre1 | `let x=a.pump_amm.as_ref()` bound in a block before the call | **= main (eq_main)** | 27,400 |
| pre2 | pre1, with `x` also used for the accounts `program:` field (drops the reload of accounts+88) | 0.6263 | 27,232 |

- **Struct update (`..*x`)** is a new spelling family. It compiles because every remaining AccountInfo field is Copy. The
  base fields are read after the explicit fields, in declaration order (rent, is_signer, is_writable, executable). This is
  the declaration-order IR that w14a114 inferred for the original. On this literal it costs 9 M against main (chunks
  0x2800 -15 and 0x2c00 -7; chunk 0x3000 +13): the same RSWEL clone-run RA shift as the field-order spellings.
- **Building the accounts struct first** (acc1, acc2, lit1) moves all 10 TCF clones ahead of the program literal and
  collapses the clone run (-0.09).
- **bindp's -32 B** costs 18 M in all, 13 of them in chunks 0x3800 to 0x4400. That does not leave 32 B of slack worth spending: at
  0.66817 / M 2,229, bindp would need +18 M from size knobs just to tie main.

## Tools (`tools/`, experiment only)

- `perm.py`: permutes the literal-tail units on renumbered main IR and scores each order with w14a114's `px2.py`.
- `gen.py`: spelling generator. It extracts the program literal (PROG) and the accounts struct (ACCTS) from line 661 and
  writes exact-edit files.
- `capvar.sh` and `runq.sh`: per-variant capture plus rx, as a queue.

## Next ideas (outside this angle)

- The IR-only leads stand. Only a code-shape change elsewhere can reach them, one that moves the accounts
  `StorageLive` or removes the `_64` piece allocas. An example would be TCF accounts sub-literals that SROA promotes fully.
  Each of those changes the clone run.
- fru1 has the declaration-order shape and sits at 0.67046 @ 27,400, a -9 M RA shift. It is a candidate base if a
  clone-run RA lever (w14a117's 1684/1671 levers, w14a84's RAPRIO pricing) recovers chunk 0x2800.
