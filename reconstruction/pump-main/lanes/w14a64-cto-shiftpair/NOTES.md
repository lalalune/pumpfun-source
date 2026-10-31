# w14a64-cto-shiftpair: size-shift oracle pairs for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Continues w14a53-cto-stitch11 (#3361) section 3. Ledger approach `shiftpair`, keys `0x22a10-w14-<main7>-shiftpair-<name>-v1`.
Tools (`tools/`, experiment only): `shift.py`/`rx.py`/`fnbin.py`/`segdiff.py`/`splice.py` (from w14a53),
`mcount.py` (w14a55), `cls.py` (w14a47), `shiftk.py` (w14a31), and new `jwhy.py <fn.bin> [+pos] [-pos]`: applies the pure
shift.py edit(s) and lists exactly which jumps / instructions change matched status (explains a shift-map entry).
`run.py <spec> [workers]` + `genes.py` (stitch11 library plus this lane's genes); run with `SRCBASE=<pristine main crate>`.

## 1. Shift map on main 2e1379d (M 2,194 at 27,400)

- Pure -8: best cand 0x16e8 (+5 M; the `stxdw [r10-0x8d8],r8` holder spill in the post-validate join). `jwhy.py`: only 2 of
  the 5 are jump distances (0x7d0->0x5708, 0x8b0->0x5830, both validate edges to the shared error tail at 0x5708/0x5830);
  the other 3 are local re-alignments that need that exact spill gone (RA, not a size knob). Any -8 in 0x800-0x1c00: +2.
- Pure +8: best entry block 0x180/0x1a0 (+1; the local `jne r0` at 0x178->0x1a0). 0x400-0x1c00: +1; 0x2000+: negative.
- Pairs (top-40 and a 256 B grid): +0x180/-0x16e8 +6, +0x54c0/-0x5a20 +4 (0x6d8->0x5708, 0x54b8->0x5830, 0x6370->0x5830),
  +0x2480/-0x5b20 +3.
- On the -8 lead `cu_iflet2` (curve fee `if let Some(f)=fee{..}`, 27,392 B, M 2,193) a pure +8 anywhere in cand
  0x5930-0x5af8 (sweep native arm: Rent / saturating_sub / ensure_rent_exempt / transfer_native) gives M 2,198 (main+4);
  0x5400-0x6100 gives +3.

## 2. Landed #3379 (main 0d945ea -> fc628cf): `cu_iflet2` + `wl_writ_eq`

`cu_iflet2` (-8 B, M -1) + `wl_writ_eq` (+8 B in the wallet head, the cu_iflet2 shift map's +8 zone): same M, slots 3192 -> 3183.

## 3. Polarity knob screen on fc628cf (`!x` -> `x==false`, every site)

`wl_writ_eq` is a pure block-order +8 knob, so every `!` site was screened (main M 2,195):

| gene | site | bytes | M |
| --- | --- | ---: | ---: |
| p_colnat | wallet `if collection_native==false\|\|coin_present` | +8 | 2,192 |
| p_feecfg | validate `st.fee_configurable==false` | +8 | 2,175 |
| p_dc_empty | wallet do_collect `data_is_empty()==false` | +8 | 2,145 |
| p_ammfz | sweep amm_frozen `data_is_empty()==false` | +16 | 2,192 |
| p_296a / p_296b | validate 296 | 0 | collapse (0.42) |
| p_dc_frozen, p_docoin, p_coinpres, p_elseif, p_skip, p_289, p_shared, p_cb, p_co, p_pool | | 0 | = main (p_289 1 raw loss) |

shift.py on p_colnat (27,408 B, M 2,192): a pure -8 anywhere in cand 0x3e00-0x5400 (the CPI AccountInfo clone run, no
calls between 0x3c80 and 0x4a20) or at 0x2600 gives M 2,198 = main +3.

## 4. p_colnat + CPI literal -8 moves (fc628cf, main 0.65758 / 3,192 slots)

Literals numbered in source order (1 TCF ctx pump_amm, 2 TCF coin vault ATA, 3 TCF vault ATA, 4 TCF program, 5 sharing
pool_authority, 6 authority, 7 global, 8 mint, 9 sharing program). `swK` swaps the lamports/data fields, `urK<f>` replaces a
re-read `a.<acct>.<f>` with `x.<f>`.

| pair | bytes | ratio | slots |
| --- | ---: | ---: | ---: |
| **p_colnat + ur5r** (pool_authority `rent_epoch:x.rent_epoch`) | 27,400 | **0.65848** | 3,229 |
| p_colnat + ur9l (sharing program `lamports:x.lamports.clone()`) | 27,400 | 0.65818 | 3,220 |
| p_colnat + ur3o (vault ATA `owner:x.owner`) | 27,400 | 0.65728 | 3,229 |
| p_colnat + sw3 | 27,400 | 0.62792 | |
| p_colnat + ur3d / ur9d / sw1 / sw2 / sw4..sw9 | 27,408 (0 B moves) | 0.6407-0.65658 | |
