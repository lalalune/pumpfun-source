# w15a05-cto-rw7walletr8: rw7 (`if do_coin`) plus a wallet-r8 RA partner (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main `90300f9d2`: 0.67346, M 2,248, skM 2,810, 3,124 slots, 27,400 B, 1034/1034. The unedited raw-IR capture `m0`
reproduces main exactly (`eq_main: true`).
Angle: w14a118-cto-chunkrw15's (#3503) next idea. rw7 (`if coin_present&do_coin{` -> `if do_coin{`) gains +1 skM but loses
8 M through register assignment in the wallet. The plan was to pair it with ordinary source that keeps the wallet flag in r8.
Ledger: approach `rw7walletr8`, keys `0x22a10-w15-90300f9-rw7walletr8-<trial>-v1` (23 source rows plus the `forcebound` row).

**Result: notes only, no gain. The angle is dominated.** Even a perfect wallet-r8 partner, applied as private-llc colour
forces, takes rw7 only to 0.67496. The same forces on main reach 0.67705. So any source that produced the partner would be
worth more on main without rw7. None of the 22 ordinary-source partner forms beats rw7's own 0.67106: 9 fold to rw7, 1 folds
to main and 12 lose.

## 1. Which flag is in r8 in the original

The task text says do_collect. The original's disassembly (orig 0x5be0-0x5cc0, `tools/side.py`) shows a different set:

| value | original | rw7 (ours) | main (ours) |
| --- | --- | --- | --- |
| collection_native memcmp result | r9 | r7 (%720) | r7 (%722) |
| coin_present (`data_is_empty` of +0x88) | spilled at its def, `stxdw [r10-0x918],r0` | **r8** (`mov r8,r0`) | r8 |
| do_collect | r6 (`mov r6,0/1`) | r6 | r6 |
| **do_coin** | **r8** (`mov r8,0/1/0` at 0x5c30/0x5ca0/0x5cb8, 0x6100) | spilled at its def (`stxdw [r10-0x920]` after every `mov r1,0/1`) | spilled |
| accounts `%0` piece over the ATA CPI | r7 (`ldxdw r7,[r10-0x8d8]` at 0x5cc0) | r8 (%1669) | r8 (%1671) |
| ATA account-array base (`[r10-1104]`) | r9 | r7 (%740) | r7 (%742) |

So the r8 flag is **do_coin**, not do_collect. In both of our builds do_collect is already in r6, as in the original.
The flag pieces that miss are do_coin's: root %91 on rw7, with pieces 1866-1871; root %1588 on main, with pieces 1864-1868.
This is the same rotation that w14a116 (#3504) describes on ebe5387.

## 2. Bound: rw7 plus a perfect partner, against main plus the same partner

The forces use w14a84's private RAPRIO llc, copied with its tools into `$OUT/r`. The jobs are the `colmap.py` rows whose sites
are in the wallet (`0x5b00-0x6c00`), and `climb.py --size 27400` runs a greedy climb over them.
Data: `data/rw_*.jsonl` (singles), `data/cw_*.jsonl` (climb), `data/r1_rw7.jsonl` and `data/r0_m0.jsonl` (hand sets).

| base | forces | ratio | slots | bytes | L2 |
| --- | --- | ---: | ---: | ---: | ---: |
| main | none | 0.67346 | 3,124 | 27,400 | 0.7855 |
| main | 1671=r7 (accounts piece) | 0.67555 | 3,117 | 27,400 | 0.7855 |
| main | do_coin pieces 1864-1868=r8 | 0.67496 | 3,123 | 27,400 | 0.7855 |
| main | **1671=r7 + 1864-1868=r8 (climb optimum)** | **0.67705** | 3,116 | 27,400 | 0.7855 |
| main | 1671=r7 + root 1588=r8 | 0.62743 | - | 27,416 | 0.7790 |
| rw7 | none | 0.67106 | 3,171 | 27,400 | 0.7846 |
| rw7 | 1669=r7 | 0.67316 | 3,171 | 27,400 | 0.7846 |
| rw7 | do_coin pieces 1866+1867=r8 | 0.67226 | 3,167 | 27,400 | 0.7846 |
| rw7 | **1669=r7 + 1866/1867/1870/1871=r8 (climb optimum)** | **0.67496** | 3,167 | 27,400 | 0.7846 |
| rw7 | root 91=r8 (alone, or with 1669=r7) | 0.60859 / 0.61069 | - | 27,440 | 0.7780 |
| rw7 | the original's wallet colouring without the gate spill (91=r8, 1669=r7, 740=r9, 720=r9) | 0.61069 | - | 27,440 | 0.7780 |
| rw7 | coin_present 720 spilled (the original) | 0.66966 | - | 27,440 | 0.7828 |
| rw7 | 720=spill + 91=r8 + 1669=r7 | 0.54267 | - | 27,328 | 0.7380 |

How to read the table:
- **rw7's skeleton gain is not real at L2.** It is +1 skM, but at L2 (frame and registers masked) rw7 is 0.7846 against
  main's 0.7855. Per orig chunk (`chunkprof.py`), the extra orig-only tokens are spread over 0x5a00-0x6400. That is register and
  frame naming, not block shape.
- **The partner is worth more on main than on rw7:** +0.0036 on main against +0.0039 from rw7's lower start, and rw7's best is
  -0.0021 below main's best. With rw7 the CPI gate reloads do_coin at both coin CPI sites (0x5e50 and 0x6858, 3 misses each,
  r2 against r8). Main's `coin_present&do_coin` gate keeps coin_present in r8, so that miss does not occur there.
- **Forcing the do_coin root into r8 always cascades** (27,416-27,440 B, -0.05 or worse). So does spilling coin_present as the
  original does. Only the split pieces can take r8 without a cascade, and ordinary source does not choose which pieces split.

## 3. Ordinary-source partner screen (raw-IR capture + opt/llc oracle, `tools/cs.sh`; `data/res-90300f9.txt`)

| trial | form | bytes | M | ratio | skM | verdict |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| m0 | main | 27,400 | 2,248 | 0.67346 | 2,810 | = main |
| rw7 | gate `if do_coin{` | 27,400 | 2,240 | 0.67106 | 2,811 | base of this lane |
| a7 | rw7 + `token_frozen(..)?==false` | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| a9 | `if !do_coin{}else{cpi}` | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| a10 | `match do_coin{true=>cpi,false=>{}}` | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| a11 | rw7 + `!{token_frozen(..)?}` | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| a12 | rw7 + do_coin if-expr with `let f=token_frozen(..)?;!f` | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| a13 | `if !do_coin{return Ok(());}` before the coin CPI | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| a15 | rw7 + ATA gate `!(collection_native&&!coin_present)` | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| a16 | rw7 + do_coin `!(!coin_present\|\|frozen?)` | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| a17 | rw7 + `token_frozen(&a.coin_creator_vault_ata)` | 27,400 | 2,240 | 0.67106 | 2,811 | = rw7 |
| s4r / s4m | flags tuple `let flags=(do_collect,do_coin)`, gates `flags.0` / `flags.1` | 27,400 | 2,240 / 2,248 | 0.67106 / 0.67346 | | = rw7 / = main |
| a5 | rw7 + `let mut do_coin=false;if coin_present{do_coin=!frozen?}` | 27,384 | 2,189 | 0.65598 | 2,718 | loss |
| a6 | rw7 + `let mut do_collect=true;if !native{do_collect=..}` | 27,408 | 2,157 | 0.64610 | 2,715 | loss |
| a14 | rw7 + ATA gate `coin_present\|\|!native` | 27,408 | 2,226 | 0.66677 | 2,790 | loss |
| s6r / s6m | `let need_ata=!native\|\|coin_present` bound right after coin_present (coin_present dies early) | 27,368 / 27,408 | 2,184 / 2,221 | 0.65468 / 0.66527 | | loss |
| s7 | do_coin as `Option<bool>` (`Some(!frozen?)` if present), ATA gate `is_some()`, CPI gate `==Some(true)` (coin_present folded into do_coin) | 27,320 | 2,231 | 0.66937 | 2,794 | loss (-17 M at -80 B) |
| s1r / s1m | coin CPI as a nested `fn coin_cpi(a:&AdminCto)` | 3,632 | 60 | 0.03164 | | wallet outlined |
| s2r / s2m / s2b | wallet tail as a nested `fn pay(ctx, do_collect, [coin_present,] do_coin)` with the flags as by-value bools | 6,704-6,728 | 161 | 0.077 | | wallet outlined |

What the screen shows:
1. **Every gate or flag spelling that keeps the CFG folds to rw7.** That covers polarity, match, early return, `==false`,
   blocks, De Morgan forms and the tuple. The do_coin flag reaches the same phi of constants.
2. **Mutable-flag forms** (a5, a6) and the **ATA-gate reorders** (a14, s6) change the CFG and lose 22-91 M.
3. **A by-value bool parameter of a nested helper** (the task's first option) outlines the wallet. execute drops to
   3.6-6.7 KB, so call counts and the whole layout change. A nested fn in `wallet` is not inlined back.
4. **Folding coin_present into do_coin** (s7) is the only form that changes which flag lives across the ATA CPI. It costs 17 M at
   -80 B.

## 4. Reading / next

- Drop rw7 as a base. Its +1 skM is cancelled at L2, and it lowers the wallet ceiling from 0.67705 to 0.67496.
- The real wallet lead is the **main** partner: 1671=r7 plus the do_coin pieces in r8, worth +0.0036 at 27,400. Its upstream
  cause is still the w14a116 chain: `!holder` %465 holds r9 at greedy step 322, so the ATA buffer %742 takes r7 and the
  accounts piece takes r8. The sweep-gate piece holds r9 over the rest of the wallet. A source candidate for it has to pass
  `colmap.py` with `ldxdw r7,[r10-0x8d8]` at 0x5cc0 and do_coin in r8 at 0x5c30/0x5ca0/0x5cb8 before it is worth a build.
- The task's remaining options are covered elsewhere and were not re-run here:
  - shortening the sweep gate's live range: w14a46, w14a82, w14a03 and w13a49 rows; every form collapses or outlines the sweep;
  - deriving do_collect from the ATA owner check: there is no such check in the sibling `collect_creator_fee.rs`; it only tests
    `quote_mint==native_mint`.

## Tools (lane copies; paths repointed to `$OUT`)

- `tools/cs.sh <name> <edits.py> <slot>`: copies the crate, applies the EDITS (exact, line count kept), does a raw-IR capture
  and runs `rx.py` (opt -O3 + llc) and `mm.py`. Use `KEEPIR=1` to keep `ir/<name>.ll`.
- `tools/q.sh <names..>`: runs cs.sh 2 at a time and writes a ledger row through `tools/rec.py`.
- The private-llc tools are copied from w14a143 (`$OUT/r/tools`: colmap.py, screen.py, climb.py), and the llc from
  `w14a143-cto-eventlive/llvmb`. Use `colmap.py ../rx/<name>/m.ll cm/<name>`, then filter `rows[].sites` to the wallet range
  to get the job lists in `data/rw_*.jsonl`.
