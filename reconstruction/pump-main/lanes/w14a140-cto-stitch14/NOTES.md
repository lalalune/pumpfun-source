# w14a140-cto-stitch14: integrator lane for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Continues
w14a109-cto-stitch13 (#3500). Ledger approach `stitch14`, keys `0x22a10-w14-<main7>-stitch14-<variant>-v1` (101 rows).

**Result: no landable change. Main stays the best zero-loss measurement.** Main moved during the lane, from ebe5387
(0.67316, M 2,247, 3,123 slots) to e88f9d5 (#3621 w14a144 per-arm `sharing_update` local: 0.67346, M 2,248,
3,124 slots), so there are two screens.

Oracle (experiment only): `tools/scr.py <spec> [workers]` copies the crate, applies genes (`tools/genes_s14.py` =
the stitch12/13 library + w14a119 I6 family + w14a108 `mine108` as `m_*` + w14a123 `og` as `o_*` + new
e88f9d5-spellings), captures the pre-opt IR (`capraw.py`), runs `rx.py` (opt -O3 + llc) and computes M (difflib
masked tokens, the measure.sh metric; ratio = 2M/(6676+(bytes-27400)/8)). `m0` is `eq_main` true on both mains.
About 15-35 s per variant at load 15-30. `tools/lcs.py` (w14a128) re-ranks with true LCS; `tools/delmap.py`
(w14a119) is the single-deletion map. Raw rows: `data/res-*.jsonl`, specs `data/spec*.txt`.

## 1. ebe5387 (M 2,247): the leads named in the angle

| variant | genes | dB | M | dM |
| --- | --- | ---: | ---: | ---: |
| H1 | ha + crl2 | -160 | 2,062 | -185 |
| H2 | ha + crl2 + ev_cb_local | -96 | 2,064 | -183 |
| H3 | ha + crl2 + q_arr + hkmut + e_cb + I6 | +72 | 2,059 | -188 |
| H4 | ha + crl2 + K_w_ev_creator_first + hkmut + e_cb + I6 + ev_mint_key + p_colnat | +56 | 2,102 | -145 |
| H5 | ha + crl2 + q_arr + K_w_ev_creator_first + p_colnat | +56 | 1,873 | -374 |
| E1-E6 | ha + one of K_w_ev_creator_first / hkmut / e_cb / ev_mint_key / I6 / p_colnat | -168..-224 | 2,036-2,152 | -95..-211 (I6 best) |
| C1 / C4 | crl2 + t1 / crl3 + t1 | +48 | 2,247 | 0 |
| C2 | crl2 + t1 + ev_nf_inline + n_ensmatch | 0 | 2,231 | -16 |
| C3 | crl2 + t1 + K_cu_typed + su_to_st + cu_match | +8 | 2,233 | -14 |
| D1 | crl2 + t1 + ev_nf_inline + amp_inline + cu_match | 0 | 2,234 | -13 |
| D2 | crl2 + t1 + ev_nf_inline + K_cu_typed + p_colnat | 0 | 2,227 | -20 |
| D3 | crl2 + t1 + n_ensmatch + amp_inline + su_to_st | +8 | 2,233 | -14 |
| D4 | crl2 + K_g_s7_dborrow | -8 | 2,234 | -13 |
| D5 | crl2 + t1 + K_cu_typed + amp_inline | 0 | 2,232 | -15 |
| A1 | crl2 + t1 + amp_inline | +32 | 2,239 | -8 |
| A2 | t1 + amp_inline + p_colnat + cu_unwrapcur + I6 | -24 | 2,242 | -5 |
| W1 | rw7 (wallet gate `if do_coin`) + p_colnat | +8 | 2,236 | -11 |
| W4 / W5 / R2 / R3 / R4 | rw7 + w_dcif / w_docoinif / p_docoin / wl_frozen_let / w_evfee_first | 0 | 2,239 | -8 (= rw7 alone) |
| R1 | rw7 + p_dc_empty | +16 | 2,193 | -54 |
| W6 / W7 | rw7 + w_cpfirst / w_collmatch | +32 / -168 | 2,207 / 1,774 | |
| R5 | rw7 + crl2 + t1 | +48 | 2,242 | -5 |
| I2 | I6 + amp_inline | 0 | 2,240 | -7 |

- **ha is a frame/RA cascade, not a size problem.** Filling ha back to 27,400-27,472 B with faithful byte-adding genes
  keeps M at 2,059-2,102 (-145..-188). The cascade does not unwind when the frame size returns. Dead.
- **crl2 + t1 is exactly additive** (+72/+1 and -24/-1, so +48 B at M = main). Every faithful -48 B repay costs 13-20 M.
- **rw7 has no wallet-r8 partner in the library**: every wallet/do_coin gene on top of rw7 is the rw7 price or worse.

## 2. e88f9d5 (#3621, M 2,248): re-priced singles and pairs

New spellings for the per-arm `sharing_update` tree: `t1n` (`if new.is_none()` holder test), `t3n`, `han` (holder arm
`Some(args.0)`), `I6n` (shared arm `target=..` before the `sharing_update=` store), `I6sn`/`I6ssn` (`target=st.creator`
after / before), `sunew` (`Some(new)`).

| variant | genes | dB | M | dM | true LCS `---` / `rfj` |
| --- | --- | ---: | ---: | ---: | --- |
| m0 | main | 0 | 2,248 | 0 | 2,253 / 3,007 |
| N_crl2 | crl2 | +72 | 2,249 | **+1** | 2,254 / 3,012 |
| N_I6n | I6n | +16 | 2,247 | -1 | 2,252 / 3,008 |
| N_I6ssn | I6ssn | +8 | 2,246 | -2 | 2,253 / 3,008 |
| N_vol | vol334_back (priced only; placeholder owned by devolpair) | -8 | 2,247 | -1 | 2,252 / 3,007 |
| K_sh_fees_key / cs_old_fee_first / en_feesl | | 0 | 2,247 | -1 | |
| N_can | K_g_canedit_first | 0 | 2,246 | -2 | |
| N_crl2t1 / P11 | crl2 + t1n / crl3 + t1n | +56 | 2,246 | -2 | 2,251 / 3,011 |
| N_t1n / N_t3n | t1n / t3n | -16 | 2,245 | -3 | 2,250 / 3,006 |
| N_I6sn | I6sn | -8 | 2,245 | -3 | |
| N_pcol / N_cuuc | p_colnat / cu_unwrapcur | +8 | 2,245 / 2,244 | -3 / -4 | |
| N_cum / N_amp / N_nmap | cu_match / amp_inline / n_mapamt | -8 / -16 / +8 | 2,242 / 2,241 / 2,241 | -6 / -7 / -7 | |
| N_nfin | ev_nf_inline (w14a120 n1) | -24 | 2,240 | -8 | |
| N_rw7 | rw7 | 0 | 2,240 | -8 | |
| N_han | han | -232 | 2,062 | -186 | 2,090 / 2,985 |
| N_sunew | sunew | -32 | 1,604 | -644 | |
| **P1 / P12** | **I6n + t1n / I6n + t3n** | **-24** | **2,247** | **-1** | 2,252 / 3,006 |
| P4 | p_colnat + cu_match | 0 | 2,246 | -2 | |
| P2 / P3 / P9 | I6n + amp_inline / I6ssn + cu_match / + K_sh_fees_key | 0 | 2,239-2,241 | -7..-9 | |
| P5 | I6n + cu_match + cs_old_fee_first | +8 | 2,242 | -6 | |
| P6 / P10 | crl2 + t1n + I6sn + ev_nf_inline + amp_inline (+ cu_match) | +8 / +16 | 2,234 / 2,237 | -14 / -11 | |
| P7 | crl2 + K_g_s7_dborrow | -8 | 2,235 | -13 | |
| Q1 / Q7 | P1 + p_colnat + cu_unwrapcur + n_mapamt (+ K_sh_fees_key) | 0 | 2,238 / 2,237 | -10 / -11 | |
| Q2 / Q3 / Q5 | P1 + e_cb / hkmut / ev_mint_key + p_colnat | 0 / +8 / 0 | 2,231 / 2,234 / 2,216 | | |
| Q4 / Q6 / Q8 | P1 or t1n + crl2 + ev_nf_inline (+ amp_inline + cu_match) | +24 / 0 / +16 | 2,239 / 2,235 / 2,237 | | |

- **P1 (`I6n + t1n`) ties main's ratio off-size**: 27,376 B, M 2,247, ratio 2*2247/6673 = 0.67346 = main. It needs a
  +24 B faithful fill worth at least +1 M (+2 to gain). The junk bound for t1 on ebe5387 was +1 (stitch13), and every
  library fill (Q1-Q7) costs 9-32 M. I6n is not a no-op under t1n on e88f9d5: t1n alone is -16 B / -3, P1 is -24 B / -1.
- **crl2 is still the only single above main (+72 B / +1)**. `delmap.py` on N_crl2: 119 single deletions keep M 2,249, all at
  0x0-0x800 except two in 0x1400; the crl2 creator-copy instructions at 0x80-0xd0 are among them. So the +1 is
  incidental naming (as w14a108 found), and its 72 B can only be repaid at the entry. No faithful entry gene removes
  bytes without loss (en_dlen -88 B / -254).
- Pairs and triples are additive or worse on both mains. The additive model predicts every 0 B composite of the
  cheap genes at <= -2 M, and the measurements match it.


### Entry-region genes on P1 (batch 6, e88f9d5)

Every entry gene in the library is 0 B on P1 (it stays at 27,376 B), so none of them is the +24 B fill.
hk_copy, sk_ref2, v_hkclone, m_k_mint, m_cb1/6/7/8 keep P1 at M 2,247. m_k_ql is -2. m_cb2/3/4 are -8.
m_pdaf/2/3 (PDA before the shared test) cost 308-311 M at -72 B, and m_i312a/b (312 split) cost 354-361 M at -32 B.
On main alone, hk_copy is M 2,248 at 0 B (not byte-identical), and sk_ref2 is byte-identical. S_pdaf is -310.

## 3. Not taken (owned by running lanes)

The read_volatile placeholders (devolpair: VI6, vol334_back pairings), the holder flag (w14a132), head order
(headroute306b), the TCF literal (tcfrentlate2) and the sharing tail slots (tailslotperm2). The w14a114 drop-glue pair is
IR-only (no source form, per w14a114); w14a72's C0 does not apply any more (wl_writ_not2 is main, sm_iflet was reverted
by #3480, ur5r no longer applies).

## 4. Next ideas

- P1 + a +24 B entry-region fill: the only place where pure +8 insertions are M-neutral is 0x0-0x800 (entry and
  validate head). A faithful +24 B entry construct that does not touch the shared tree (for example a holder_key /
  sharing-key copy shape like the original's 4-word runs at orig 0x100-0x198) would tie or gain +1.
- crl2 + -72 B at the entry with no loss. None exists in the library.
