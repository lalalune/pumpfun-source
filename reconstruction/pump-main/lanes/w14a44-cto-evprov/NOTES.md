# w14a44-cto-evprov: AdminCtoEvent tail provenance and initializer order (admin_cto 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Region: the AdminCtoEvent build + emit + event CPI, orig 0x4e60-0x5538 (ours 0x4e10-0x54e8), line 767
(w14a38 REGIONS.json: +0.0069 if matched, 215 slots, fm 3 / rm 15 / jm 3 / sk 15).
Bases: main 6db95a764 (0.65458, 3,280 slots) and 6e011ea42 (0.65548, 3,280 slots), 1034/1035 normalized and raw.
Ledger: approach `evprov`, keys `0x22a10-w14-6db95a7-evprov-*` (66 rows) and `0x22a10-w14-6e011ea-evprov-n2_*` (13 rows).

**Result: no gain. Every per-field provenance, initializer order and timestamp position is at or below main at
27,400 B.** The best size-neutral composite is `srp_P1_P2`: 0.65368 on 6db95a7 and 0.65458 on 6e011ea, both 0.0009 below main.
`hr_c` (event `is_holder_reward` read back from the curve) gives the original's event-build instruction sequence exactly,
but it is 8 B short, and the register assignment of the long-lived tail values moves the wrong way (see the map).

## Oracle

The oracle is w14a38's raw-IR capture (`tools/capvar.sh` -> `capraw.py`) plus `rx.py` (opt -O3 + llc), re-pointed at this lane.
`m0` reproduces main on both bases (`eq_main` true; 0.65458 and 0.65548 at 27,400). A capture takes about 30 s, and
`tools/drive.py` runs two of them at a time.
- `tools/evreg.py <fn.bin> [lo hi]`: per-level match counts against the original over the call segments whose original start
  lies in [lo,hi). The default is the event tail 0x4e60-0x5538, which is segments 87-98. Levels: L0 raw, L1 frame masked,
  L2 also registers masked, L3 also jumps masked. Main: 195 / 198 / 222 / 227 of 233. Wallet 0x5c38-0x6b08: 355 / 380 / 429 / 449.
- `tools/fnlst.py` lists one fn.bin or diffs two side by side. `tools/seglen.py` lists the call segments whose instruction
  count changed (where the bytes went).
- `e/gen.py` generates the event-literal variants from tokens, `e/genw.py` the wallet-literal variants, and `e/comb.py`
  concatenates edit lists.

## Map: original vs main in the event tail (6db95a7)

The event build is the same instruction skeleton in both: authority key, mint, curve key, new_creator, new fee, two
flag bytes, then stores. The 36 misses are the provenance and register homes of five values that live across the tail:

| value | original | main | `hr_c` (holder from curve) |
| --- | --- | --- | --- |
| is_holder_reward | `ldxb r5,[curve+0xa5]` read in place, loaded before +0xa3 | `holder` local in r9 (`and 255; !=0` materialised at the curve store) | **= original** (`ldxb r5,[+0xa5]; ldxb r3,[+0xa3]`, same stores) |
| is_cashback_coin | `ldxb r3,[curve+0xa3]` | same | same |
| sharing_update tag (sharing_config_reset) | r6, reloaded from [r10-0x8f8] right after the sharing CPI and again at the end of the pool arm | spill [r10-0x8e8], reloaded into r3 at the event | same as main |
| pool_updated | r8 (phi of 1/0) | r6 | r9 |
| swept | r9, live from the sweep return | spill [r10-0x968] | spill |
| old_fee | spill [r10-0x8e0] | spill [r10-0x8f8] | r6 (no spill: this is the 8 B) |
| accounts pointer | spill [r10-0x8d8], reloaded into r2 for authority, then into r6 after the tag dies | spill [r10-0x8e0], reloaded once into r8 | r8 |

The two bytes the brief calls "event words from [r10-0x8d8]/[r10-0x8e0]" are the accounts pointer and old_fee. Swept is
the one the original keeps in r9.

- In the original, holder is dead after the curve store and the pool CPI argument. The pool CPI's `is_holder_reward`
  argument comes from the holder spill [r10-0x950], not from a curve read. Main reads `[curve+0xa5]` into r8 after
  `data_is_empty` (`pargs.1` reads the curve), because the RefCell borrow in `data_is_empty` clobbers the forwarded store.
- `hr_c` frees r9, but greedy RA then hands r6 to old_fee and r9 to pool_updated, and the accounts pointer moves r6->r8
  through the pool CPI clone run (-1 in each of segments 73-79). Every holder form that matches the original's pool argument
  (`ph`, `pa_preh`, `pa_pre`) costs +24..+32 B in an RA cascade in the sweep head (segment 55) and wallet.
- On a -216 B path (`w_qmk`, wallet event `quote_mint:a.quote_mint.key()`, which drops the collect() Pubkey) the event
  region's frame-masked matches jump from 198 to 220. Its RA puts the accounts pointer in r2 then r6, as the original does.
  The event tail's register homes are therefore set by global register pressure (the frame and wallet value count), not
  by the event literal.

## Screen (raw-IR oracle, 6db95a7 main 0.65458 @ 27,400; ev = L0/L1/L2/L3 in the event tail, main 195/198/222/227)

| variant | edit | bytes | ratio | ev |
| --- | --- | ---: | ---: | --- |
| hr_c | `is_holder_reward:a.bonding_curve.is_holder_reward` | 27,392 | 0.65169 | 196/200/222/227 |
| hr_p | `is_holder_reward:pargs.1` | 27,488 | 0.63825 | 32/43/71/74 |
| hr_h2 | `holder==true` | 27,400 | = main | |
| ph | `pargs=(target,holder,fee)` | 27,432 | 0.64611 | = |
| hr_c_ph | both | 27,424 | 0.6468 | 196/200/222/227 |
| pa_pre / pa_preh / pa_inline | pargs before the pool gate / with holder / args inline at the call | 27,432 / 27,432 / 27,400 | 0.64611 / 0.64611 / 0.64769 | = |
| pa_*_hrc | the same with hr_c | 27,424 / 27,424 / 27,392 | 0.6468 / 0.6468 / 0.64659 | 196/200 |
| cb_l | `is_cashback_coin:cashback` | 27,408 | 0.65269 | 191/194/221/226 |
| mint_k | `mint:a.mint.key()` | 27,416 | 0.646 | 168/174/204/209 |
| bc_k | `bonding_curve:*a.bonding_curve.to_account_info().key` | 27,560 | 0.6371 | |
| auth_d | `authority:*a.admin_set_creator_authority.key` | 27,400 | = main (byte-identical) | |
| nc_t / nc_p | `new_creator:target` / `pargs.0` | 27,472 | 0.37996 | 115/170 |
| nf_u / nf_p | `new_creator_fee_bps:fee.unwrap_or(old_fee)` / `pargs.2..` | 27,424 | 0.6465 | 172/180 |
| sr_m / sr_n | `matches!(sharing_update,Some(_))` / `!is_none()` | 27,400 | = main | |
| sr_prepool | `let sr=sharing_update.is_some()` before the pool gate | 27,400 | = main (byte-identical fn) | |
| sr_pre | `let sr=..is_some()` before the curve update block | 27,384 | 0.65358 | = |
| ts_pre | `let timestamp=Clock::get()?..` before the literal | 27,400 | 0.65159 | 186/199/222/227 |
| e_clk | `let clock=Clock::get()?;` before the literal | 27,400 | 0.65159 | 186/199 |
| e_tsmap | `Clock::get().map(\|c\|c.unix_timestamp)?` | 27,400 | = main | |
| ts_prepool | Clock before the pool gate | 27,384 | 0.63051 | 34/53/83/84 |
| ts_at1/2/3 | timestamp initializer 2nd/3rd/4th | 27,464 / 27,528 / 27,600 | 0.64063 / 0.63808 / 0.63602 | 155 / 149 / 145 |
| ts_at5..10, ts_last | timestamp 6th..last | 27,656-27,664 | 0.490-0.492 | 116-122 |
| ord_rev | fields in reverse order (timestamp first) | 27,408 | 0.579 | 153/160/196/202 |
| ord_hrcb | cashback before holder | 27,400 | = main (byte-identical fn) | |

So the timestamp must be the first initializer, evaluated inside the literal. Every later position adds 64-264 B, because
the `?` Err edge then carries the already-built fields. The original's order is the declaration order main already has.

Size pairs (-8/-16 B leads with +8/+16 B partners: P1 = w14a34 `v_f_unwrapor_cur`, P2 = w14a33 `v_old`, P3 = `v_ok0`,
SI = `s_iflet`, TCHEF = w14a34 `v_p_TCHEF`, RR = `Rent::get()?.minimum_balance(0)`, w_clk / w_tspre = wallet `let clock`):

| variant | bytes | 6db95a7 | 6e011ea (main 0.65548) |
| --- | ---: | ---: | ---: |
| srp_P1_P2 (sr_pre+P1+P2) | 27,400 | 0.65368 | 0.65458 |
| srp_P1_P3 | 27,400 | 0.65368 | |
| srpcbl_P1 (sr_pre+cb_l+P1) | 27,400 | 0.65309 | 0.65398 |
| srpcbl_P2 | 27,400 | 0.65249 | |
| hrc_P1 / hrc_P2 / hrc_P3 | 27,400 | 0.65159 / 0.65129 / 0.65129 | 0.65249 (P1) |
| hrccbl_SI (hr_c+cb_l+SI) | 27,400 | 0.65129 | |
| hrc_SI_P1_P2 | 27,400 | 0.65099 | |
| srp_hrc / srp_cbl / tsp_* | 27,376 / 27,392 / 27,384-27,408 | 0.65128 / 0.65288 / 0.6487-0.6506 | 0.65378 (srp_cbl) |
| srp_wclk / srp_wtspre (sr_pre + wallet let clock, +16) | 27,400 | | 0.65398 |
| hrc_wclk_SI | 27,400 | | 0.65159 |
| srp_RR | 27,384 | | 0.65448 (RR is byte-identical on 6e011ea) |

`sr_pre` (-16 B) is the s_iflet single `jne r7,2` at the sharing CPI return, plus a `jne r1,1,+3` fee-tag test in the curve
update. The original has the pair form at the fee test (`jne r1,0,+1; ja +3`), so half of sr_pre's saving is anti-original.

Wallet CollectCreatorFeeEvent (line 564, secondary): the literal is already instruction-for-instruction the original. The only
misses are r8/r9/r7 register homes (w14a35's do_coin cascade). `w_crd`, `w_crctx`, `w_o_cfq`, `w_o_qcf` and `w_tsmap` are
= main. `w_o_tlast` is 0.64931 @ 27,464, and `w_clk` / `w_tspre` are 0.65409 @ 27,416 (+16 B knob). `w_qmk` is 0.55076 @ 27,184,
with the event-tail L1 at 220 (see the map).

## Next ideas

- The event tail's residual is RA of the values that live across the tail (the swept r9 home, the sharing tag r6 home, and
  the accounts pointer spilled rather than held). That belongs to w14a06's swept-coalescing CFG change and to global
  pressure lanes, not to the event literal.
- `hr_c` is the original's event form. Retry it whenever the pool-arm RA changes (for example with w14a34's owner-first pool
  gate) and an independent +8 B appears.
