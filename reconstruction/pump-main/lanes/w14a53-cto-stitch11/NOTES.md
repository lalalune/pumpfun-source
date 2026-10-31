# w14a53-cto-stitch11: integrator lane for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Ledger approach `stitch11`, keys `0x22a10-w14-<main7>-stitch11-<variant>-v1`. Tools: `genes.py` (stitch10 library plus
new genes at the end), `run.py <spec> [workers]` (measure.sh queue; per-base `results-<main7>.jsonl`, keeps `fn.bin`),
`tools/fnbin.py` (extract the admin_cto bytes of a .so), `tools/segdiff.py` + `tools/splice.py` (from w14a38).

Note: the 14 `0x22a10-w14-0fbf8da-stitch11-df_*-v1` ledger rows marked compile-failed were fastbuild workspace-lock
failures caused by this lane (BlockingIOError), not compile errors. `run.py` now re-queues on that error.

## 1. Near-tie panel (w14a26 stitch10 list) on main 0fbf8da (0.65578, 3,280 slots)

| variant | ratio | bytes | note |
| --- | ---: | ---: | --- |
| main (m0, fresh measure.sh) | 0.65578 | 27,400 | reproduces the baseline |
| cs_swap3, c_ce_cr, n_hk_direct, cmp_pool_rev, cmp_fees_rev, sh_iflet+cu_unwrapcur | 0.65548 | 27,400 | one quantum below main |
| pu_amm_key | 0.65508 | 27,400 | |
| pre_cb_match, pre_cb_not | 0.65578 | 27,400 | tie, distinct sha |
| v_hr_ne | 0.65578 | 27,400 | tie, 1 raw loss |
| sh_iflet | 0.65558 | 27,392 | |
| cu_match (w14a27 t41) | 0.65528 | 27,392 | |
| pu_own (owner-first pool gate) | 0.65059 | 27,408 | |
| w14a27 d4 (token arm `.and_then`) | 0.65528 | 27,368 | |
| w14a27 s_frozen_first alone | 0.62257 | 27,448 | |
| **d4 + s_frozen_first** | **0.65648** | 27,392 | +0.0007 at -8 B |
| **wl_writ_not** (`!a.current_creator.is_writable`, revert of wl_writ_eq) | **0.65618** | 27,392 | +0.0004 at -8 B |
| wl_writ_not + cu_unwrapcur / + ev_cb_local | 0.65548 / 0.65458 | 27,400 | repay loses |

## 2. Main d371f97 (0.65638): the d4 + s_frozen_first lead and +8 B repays

| variant | ratio | bytes | slots |
| --- | ---: | ---: | ---: |
| d4 + s_frozen_first (`d4ff`) | 0.65708 | 27,392 | |
| wl_writ_not | 0.65678 | 27,392 | |
| d4ff + wl_writ_not | 0.65628 | 27,384 | (not additive) |
| sh_iflet | 0.65618 | 27,392 | |
| **d4ff + cu_unwrapcur** | **0.65698** | **27,400** | 3,193, 0 losses |
| d4ff + n_cb_fwd / cu_replace / c_hr_cb | 0.65488 / 0.65428 / 0.65428 | 27,400 | |
| d4ff + wl_writ_not + wl_ts_clockvar | 0.65518 | 27,400 | 3,355 |
| d4ff + wl_ts_clockvar + sh_iflet | 0.65518 | 27,400 | |
| wl_writ_not + n_cb_fwd / cu_replace / c_hr_cb / clockvar+sh_iflet / cu_unwrapcur / ev_cb_local | 0.65428 / 0.65339 / 0.65428 / 0.65488 / 0.65548 / 0.65458 | 27,400 | |

Singles on d371f97 (size probes): cu_unwrapcur 0.65538 @27,408; ev_cb_local 0.65449 @27,408; lf_pr_dl 0.65548 @27,400;
r_getdot, n_amt_ge, cd_holder_dest, ev_reset_m, sh_nonefirst = main (0 B); r_letrent 0.65208 @27,384; sw_ifskip 0.51932 @27,416;
ev_nf_unw 0.6483 @27,424; lf_au_dl 0.63642 @27,416; lf_ea 0.65338 @27,376; lf_mi 0.63811 @27,400; lf_gl 0.63943 @27,440;
pargs_hr_local 0.6479 @27,432; ev_nf_let 0.65459 @27,424; ev_hr_curve 0.65348 @27,392; wl_ts_clockvar 0.65588 @27,416.

d4ff + cu_unwrapcur is exactly what w14a50-cto-frozenrepay landed independently as #3358 (main 6330811, 0.65698,
byte-identical fn). This lane's copy was never pushed.

## 3. Size-shift oracle (w14a31 `shift.py`, copied to `tools/`)

`tools/shift.py <fn.bin>` inserts a junk 8 B slot at each block start (+8) or deletes one unmatched insn (-8), fixes the
crossing jumps and scores M. It isolates the pure jump-distance part of a size knob.
- On d4ff (d371f97, M 2,193 at 27,392): a pure +8 anywhere in cand 0x5930-0x5ca8 (sweep native arm, ensure_rent_exempt /
  transfer_native, and the inlined wallet head: executable / owner memcmp / token_frozen) is **+4 M**; elsewhere <= +1.
  The real +8 knobs tried are all in the tail (curve update / event), which explains why they cost 2-4 M.
- On main 6330811 (M 2,193 at 27,400): best pure -8 is cand **0x16e8 (+5 M)**, a spill store in the validate/flag block
  (`stxdw [r10-0x8d8], r8`, orig ~0x24188); best +8 is at the entry block 0x180/0x1a0 (+1 M); best pair +0x180/-0x16e8 is
  **+6 M** (~+0.0018). So any faithful -8 B inside the validate result/flag block costing <= 4 M, plus +8 B in the entry
  block, would beat main.
