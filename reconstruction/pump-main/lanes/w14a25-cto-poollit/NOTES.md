# w14a25-cto-poollit: AccountInfo spellings at the tail CPIs (pool CPI, collect emit_cpi)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 1b0ae7021 (0.63661, 3,173 slots) and, after #3272/#3267 landed, main 7e6aa9caa (0.64140, 3,174 slots).
Ledger: approach `poollit`, keys `0x22a10-w14-{1b0ae70,7e6aa9c}-poollit-*` (20 rows).

**Result: no gain. The angle is exhausted.** Both CPIs already have the original's call skeleton.
- In the pool CPI, all 8 accounts clone through an outlined call to `<AccountInfo as Clone>::clone`, in the original's
  order: program [a+0x58], payer +0x0, global_config +0x60, pool +0x70, pool_authority +0x68, system +0x30,
  event_authority +0x78, program +0x58. The frame slots match too (0x2b8, 0x450, 0x420 ... 0x330, memcpy 0x150).
- The collect `emit_cpi` `authority_info` is also an outlined `AccountInfo::clone` call in the original (orig 0x64f0).
- So a per-field load order only exists where a clone is inlined. Every inline `AccountInfo{..}` literal at these
  sites removes a call (call count 154 drops to 152/153) and loses badly. Every spelling that keeps the call is
  byte-identical to main.

## Screen (measure.sh builds, all at 27,400 B unless noted)

| name | main | change | ratio | bytes | calls | result |
| --- | --- | --- | ---: | ---: | --- | --- |
| pdc | 1b0ae70, 7e6aa9c | pool fields `(*a.X).clone()` | = main | 27400 | 154 | byte-identical |
| pas | 1b0ae70 | pool fields `a.X.as_ref().clone()` | = main | 27400 | 154 | byte-identical |
| pufcs | 1b0ae70 | pool fields `AccountInfo::clone(a.X.as_ref())` | = main | 27400 | 154 | byte-identical |
| ptai | 1b0ae70 | pool fields `ToAccountInfo::to_account_info(&a.X)` | = main | 27400 | 154 | byte-identical |
| plit_prog | 1b0ae70 | pool CpiContext program as an inline literal (sweep form) | 0.62493 | 27784 | 153 | loss |
| plit_pool | 1b0ae70 | pool field as an inline literal | 0.50415 | 27912 | 156 | loss |
| porder_gp | 1b0ae70 | AdminCtoPool literal global_config before payer | 0.63085 | 27456 | 155 | loss (orig order = main) |
| ecl / eufcs / ea | 1b0ae70 | collect authority_info `.clone()`, `AccountInfo::clone(&..)`, `a.` instead of `ctx.accounts.` | = main | 27400 | 154 | byte-identical |
| elit | 1b0ae70 | collect authority_info inline literal | 0.30057 | 27704 | 152 | loss |
| w_es_before_if | 7e6aa9c | deferred `event_signers` declared before `if do_collect` | 0.61789 | 27464 | 154 | loss |
| w_es_blk | 7e6aa9c | `event_signers` declared in the emit block | 0.63092 | 27400 | 154 | loss |
| w_es_after_infos | 7e6aa9c | `event_signers` after `event_infos` | 0.56531 | 27400 | 154 | loss |
| w_es_in_inner | 7e6aa9c | `event_signers` inside the invoke block | 0.55902 | 27400 | 154 | loss |
| w_bump_arr | 7e6aa9c | `let bump_arr=[authority_bump]` before `event_infos` | 0.64140 (3175 slots) | 27400 | 154 | neutral, not identical |
| w_bump_arr_ab | 7e6aa9c | bump array right after `authority_bump` | 0.63950 | 27384 | 154 | loss |
| w_inner_out | 7e6aa9c | `event_inner` bound before `event_infos` | 0.62403 | 27400 | 154 | loss |
| w_ab_first | 7e6aa9c | `authority_bump` read before the clone | 0.64110 | 27400 | 154 | loss |

## Tail per-site table (main 7e6aa9caa)

`tools/sites.py <unstripped.so>`: the original and the candidate aligned with a skeleton (frame and registers masked)
SequenceMatcher. For each site it counts matched instructions: sk (skeleton), fm (frame-masked) and raw (call and jump
immediates masked). The ranges are main's offsets; the sites follow main's call anchors.

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

Readings:
- **The pool CPI is 55/59 raw already.** Its only non-frame residuals are register choices made upstream:
  - The original reloads the accounts pointer from its spill slot at the start of the clone run
    (`ldxdw r6,[r10-0x8d8]`). The curve update before it uses r3. Ours keeps the pointer in r6 from the curve
    update on, and loads the holder from the curve (`ldxb r8,[r1+0xa5]`) at the start of the run.
  - The original loads `[r10-0x8f8]` into r6 before the last clone.
  - The holder arg is `ldxdw r4,[r10-0x950]` (the holder phi slot) in the original and `mov64 r4,r8` in ours.
  - `pool_updated` is r8 in the original and r6 in ours, both before the call (`=0`) and after it (`=1`).
  - Frame only: the fee stack args come from 0x8e8/0x930 in the original and 0x910/0x928 in ours.
  These are the holder-phi and accounts-pointer reload residuals other lanes already worked: the hrb/n5hp/h2
  families, w14a01 acctlive, w14a12 o5_hlate and w14a20 e3.
- **The collect emit_cpi is sk 84/84** and loses 18 raw:
  - The original's temporary class is r9 (`mov64 r9,r10; add64 r9,-0x450`, `mov64 r3,r9`), ours is r7, and the
    authority pointer is r7 there against our r8. The original keeps the wallet coin flag in r8 across the whole
    collect region (`and64 r8,0x1; jne r8` at orig 0x6858). Ours spills `coin_present` and the flag and recomputes
    `!x|y` at 0x6840 (+4 insns). This is w14a03's wallet-flag RA swap.
  - Frame: the original spills the bump to 0x918 and the data length to 0x920 (ours 0x940/0x948). The bump byte /
    `event_signers` slots are swapped (orig 0x548/0x680, ours 0x658/0x540). No `event_signers` or bump-array
    declaration position reproduces that swap (the w_* rows).
- **The largest raw deficits in the tail** are:
  - the error tails (-28);
  - the sweep native arm (-27; sk -9: the `ensure_rent_exempt`/`transfer_native` Result joins have an extra
    `jeq r1,2 / ja` pair and a phi slot 0x968 that the original lacks);
  - the curve update (-25; sk -9);
  - the AdminCtoEvent build (-18, frame).
  None of these is a CPI spelling.

## Tools (`tools/`)

They read the original disassembly from `$OUT/orig.rel`, a copy of w14a15's lane file, which is not committed.
- `disso.sh <so|o>`: disassembles execute from an unstripped .so or an rx object.
- `ann.py <so>`: adds the callee name to every call.
- `amap.py <so> off..`: maps candidate offsets to original offsets.
- `sbs.py <so> lo hi`: aligned side by side. `*` marks a skeleton or register diff, `f` a frame or immediate diff.
- `sites.py <so>..`: the per-site table above.
- `ch.py [-c0x400] [-f0x4000] <so|rxname>..`: per-chunk raw/fm/sk counts (ch3 on .so files).
- `vrun.py q out.jsonl 2`: a two-worker measure.sh queue over `e/gen.py` genes.
- `rec.py`: ledger recorder.
