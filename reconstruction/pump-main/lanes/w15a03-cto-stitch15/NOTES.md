# w15a03-cto-stitch15: integrator lane for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. This lane continues
w14a140-cto-stitch14 (#3631). Ledger approach `stitch15`, keys `0x22a10-w15-<main7>-stitch15-<variant>-v1`.

**Result: no landable change. Main is still the best zero-loss measurement.**

Main moved twice during the lane:
- 90300f9 (0.67346, M 2,248);
- 86e2a6b (#3666, w15a01 `CtoState{fee_configurable:..` first, 0.67376, M 2,249);
- 9120883 (same admin_cto source; programs/pump-amm only).

The lead table below is re-priced on 86e2a6b. Rows written while `$BASE` already pointed at 9120883 are in the same file:
the admin_cto source is identical.

## Oracle (experiment only)

- `tools/scr.py <spec> [workers]` is the stitch14 raw-IR screen, with lane paths and `GENES` selecting the gene module
  (default `genes_s15`). It copies the crate, applies the genes, captures the pre-opt IR (`capraw.py`), runs `rx.py`
  (opt -O3 + llc) and computes exact difflib M.
  - Ratio is 2M/(6676+(bytes-27400)/8).
  - `n0` (main) gives `eq_main: true` on both mains.
  - Two measure.sh builds (`data/meas_*.json`) agree with the oracle exactly.
  - It takes about 15-25 s per variant, with 2 workers.
- `tools/genes_s15.py` is the stitch14 library plus the following:
  - the w14a42 le_vy1 closure family (`lv_*`);
  - event / pool-arg holder flags from the arg (`e0u/e0h/e0s/p0u/p0h/c0h`);
  - holder_key deferred-init placements (`hkl1-3`);
  - `new` copies (`nwl1-3`);
  - sweep-head spellings (`sw_ap*`, `sw_af*`, `sw_fz*`, `sw_ds*`, `sw_nt*`).
- New tools:
  - `tools/enum0.py`: additive-model enumeration of zero-byte gene sets.
  - `tools/mdtab.py`: markdown tables from the result jsonl.
  - `tools/bdis.py`: a minimal SBF decoder and fn.bin diff, so no ELF is needed.
  - `tools/insmapn.py`: the w14a138/w15a01 insmap generalised to an N-slot junk run.
- Data:
  - `data/res-86e2a6b.jsonl` (210 rows), `data/res-90300f9.jsonl` (134), `data/res-90300f9-b.jsonl` (126, 90300f9 source
    scored while `$BASE` was ed47ac7);
  - `data/spec_*.txt`;
  - the insmaps `data/insmap_*.json`.

## 1. Re-priced leads on 86e2a6b (main M 2,249)

| variant | dB | M | dM | note |
| --- | ---: | ---: | ---: | --- |
| crl2 / crl3 | +72 | 2,250 | **+1** | still the only single above main; true LCS +1, all in 0x0-0x800 |
| crl2 + t1n | +48 | 2,249 | 0 | |
| crl2_dv | +64 | 2,249 | 0 | |
| hk_copy, hkl3 (`holder_key=hk.0` moved to the CtoState block head) | 0 | 2,249 | 0 | hkl3 has 3,128 slots |
| sh_iflet + rP_back, ev_reset_early + rP_back | 0 | 2,249 | 0 | **measure.sh: 0.67376 / 3,124 / 1034-1034, ties main exactly** |
| t1n / t3n | **-24** (was -16) | 2,248 | -1 | true LCS: 0x800 +2, 0x1000 +1, 0x2000 -1, 0x5800 -2, 0x6000 -1 |
| I6n | +16 | 2,248 | -1 | |
| I6n + t1n (P1) | **-32** (was -24) | 2,246 | -3 | not additive in size (I6n is -8 B under t1n) |
| vol334_back / dv334 | -8 | 2,248 | -1 | |
| en_feesl, cs_old_fee_first, K_sh_fees_key, K_g_old_fee_first, cu_replace | 0 | 2,248 | -1 | |
| I6ssn | +8 | 2,247 | -2 | true LCS = main (difflib artifact) |
| K_g_canedit_first, m_k_ql, m_k_dest2, m_cb5, K_g_s7_destrev | 0 | 2,247 | -2 | |
| I6sn / p_colnat / K_g_w_clock_local | -8 / +8 / +16 | 2,246 | -3 | |
| cu_unwrapcur / e0u | +8 | 2,245 | -4 | |
| sh_iflet / ev_reset_early | -8 | 2,244 | -5 | the sharing-tag test becomes a single `jne r7,2` as in the original |
| cu_match / m_t1 / amp_inline / m_a1 / ev_nf_inline | -8 / +8 / -16 / -24 / -24 | 2,243-2,241 | -6..-8 | |
| K_sh_prog_let / K_g_s7_dborrow | -32 / -80 | 2,238 / 2,235 | -11 / -14 | |
| hkl2 / hkl1 | -112 / -96 | 2,047 / 2,066 | -202 / -182 | |

The full table is `data/res-86e2a6b.jsonl`. On 90300f9 the 248 untested library singles were screened first
(`data/res-90300f9*.jsonl`). None of them beats main. The only non-identical rows at dM >= -1 were the ones above.

## 2. Pairs and triples at 27,400 B

| family | rows | best | note |
| --- | ---: | --- | --- |
| additive zero-byte sets of the cheap genes (spec_i1: 39 pairs/triples + 5 crl3 quads) | 45 | -1 | crl3 quads -12..-15 |
| 0 B x 0 B pairs on 90300f9 (spec PP_) | 55 | -1 | strictly additive or worse |
| **+8 B (wallet/curve/event) x -8 B (sharing tail) pairs** (spec_x1, spec_f1) | 100 | **0 (sh_iflet/ev_reset_early + rP_back)** | p_colnat/e0u/cu_unwrapcur x sh_iflet/ev_reset_early/lv_sh_ifelse/lv_sh_isnone are all -1, not the -8 the additive model predicts |
| X = p_colnat + sh_iflet, plus each 0 B gene | 22 | -1 | |
| sh_iflet + sweep-head spellings (spec_w1) | 26 | -5 | every `sw_*` spelling is byte-identical alone, except sw_ntrv -3 and sw_apdl/sw_dshv (big losers) |
| PDA-first (m_pdaf*) and crl2/crl3 + PDA-first (0 B / +64 B) | 7 | -310 | entry true LCS +13, but RA churn loses 0x2000 -57 and 0x3000 -183 |
| le_vy1 validate-closure family (v7c + ny/le/cf_skc/h289) | 8 | -143 | dead on current main (v7c alone -576) |

**Mechanism found: size-position tax.** About 2-6 M of a +-8 B single's price is a position tax, not code shape:
- jump offsets across the moved code, mostly the long jumps out of 0x0-0x800;
- the tail chunk 0x6800 (-2 in true LCS for most +-8 B singles).

The tax cancels when the composite returns to 27,400 B. `bdis.py` shows that p_colnat + sh_iflet differs from main in
only two branches:
- the sharing-tag test at 0x4a38, where `jne r7,2` replaces `jeq ...; ja`. That matches the original's 0x274b0.
- the wallet `collection_native` test at 0x5e38, where `jeq ...; ja` replaces `jne`. That does not match.

So the residue is exactly one mismatched `ja`.

## 3. Insertion maps (`insmapn.py`): where a faithful +8 B pays

- **sh_iflet (27,392 B, M 2,244) + one junk 8-byte slot** gives:
  - M 2,250 (**main +1**) at 155 positions: candidate 0x2130-0x2508 (sweep head: the line-719 frozen error block and the
    line-648 creator-vault PDA / ConstraintSeeds block) and 0x53b8-0x5570 (TCF drop-glue);
  - **M 2,251 (main +2)** at 0x54b8.
  - So **any ordinary source change that adds exactly one instruction in the sweep head or the TCF drop-glue, on top of
    sh_iflet, beats main.** None of the 21 library +8 B genes lands there. They land in the wallet, curve, event or
    shared arm and give -1..-7. All 13 sweep-head spellings tried are byte-identical: LLVM folds them.
- **t1n (27,376 B, M 2,248) + a 24 B junk run** at any single position gives at most 2,248. t1n's -1 is code shape, not
  position, so no fill can repay it.

## 4. Next ideas

1. sh_iflet + one faithful sweep-head or TCF-drop instruction (section 3), worth +1 to +2 over main.
   - Candidates are spellings that keep one extra value live or reload one value in the line-648 ConstraintSeeds
     `with_pubkeys` block or in the TCF `AccountInfo` clone and drop sequence (`lamports.clone()`/`data.clone()` order,
     a clone bound to a local).
   - Price each one with `insmapn.py` on its own fn.bin first.
2. crl2/crl3 (+72 B, +1) still needs a free -72 B, and none exists in the library. The size-position tax suggests a
   -72 B entry construct would itself pay about 0. The entry true-LCS +13 of PDA-first shows the entry *can* gain, but
   only if the RA churn of 0x2000-0x3800 is avoided.
3. hkl3 (`holder_key=hk.0;` at the CtoState block head) ties main at 0 B with 3,128 slots. It is an alternative base for
   validate-side genes.
