# w13a51-cto-h2pair (wave 13, continued in wave 14)

Target `0x22a10` `admin_cto::execute`, pinned 27,400 B. Notes only: no source change is landable on the current main.
All numbers are from the lane's raw-IR opt+llc oracle (`capvar.sh`), which reproduces main byte-for-byte
(eq_main true on 53abf28, 769f331 and cef0574), unless marked measure.sh.

## 1. The h2pair angle is dead (main 53abf28, 0.62672)

w13a38's h2 (validate `ho:&mut bool` holder phi, holder-first curve stores, pool holder local) and its pairings:

| variant | ratio | bytes | fm | rm |
| --- | ---: | ---: | ---: | ---: |
| main | 0.62672 | 27,400 | 0.72169 | 0.84991 |
| h2 | 0.60232 | 27,200 | 0.7214 | 0.8528 |
| h2 + holder_key by value (w13a33 v1) | 0.5348 | 27,096 | 0.69027 | 0.82103 |
| holder_key by value alone | 0.54976 | 27,368 | 0.69784 | 0.81865 |
| store swap only | 0.62253 | 27,400 | 0.7175 | 0.85021 |
| ho phi only | 0.59375 | 27,240 | 0.71484 | 0.85216 |
| ho phi + pool local | 0.60232 | 27,200 | 0.7214 | 0.8522 |
| pool holder local only | 0.62405 | 27,424 | 0.72017 | 0.84923 |
| phi used only for pool arg / curve store / event | 0.568 / 0.577 / 0.570 | 27,400 / 27,328 / 27,416 | | |

The h2 fm gain (+0.009 on 9b9440f) is gone since entrycopy3: fm is now flat or lower and the raw ratio loses 0.02-0.06.
w13a43 v2 (289 nested) shrinks execute by 432 B on this main; it is not a code-adding partner.

## 2. Stack built from other lanes' genes (each superseded by stitch9/w14 landings before it could land)

| main | stack | ratio | bytes | note |
| --- | --- | ---: | ---: | --- |
| 53abf28 0.62672 | scu_bs + o_ab_late + s_rent_local + pu_amm_keyfn + fee unwrap | **0.62753** | 27,400 | measure.sh 0 losses, sha 912090fb8be7561b |
| 23322b0 0.62882 | scu_bs + o_ab_late + pool owner `==&a.pump_amm.key()` + event fee from curve (no `nf`) + wl_ts_clockvar | **0.62932** | 27,400 | measure.sh 0 losses, sha 505c0fd261f1d733 |
| 769f331 0.63241 | same stack | 0.63052 | 27,400 | below main |
| cef0574 0.63421 | same stack | 0.63082 | 27,400 | below main |

Genes: `scu_bs` = w13a46 skip-first inner tuple `(skip,collect_old,sharing_update)` + `args=&(new,)` before `CtoState`;
`o_ab_late` = w13a19 hand-expanded execute `emit_cpi!` with `authority_bump` read after `ix`.

## 3. scu_bs is the strongest open gene, but it is 56 B short

| main | scu_bs alone | + o_ab_late | + o + pool owner `==&a.pump_amm.key()` |
| --- | --- | --- | --- |
| 23322b0 (0.62882) | 0.63128 / 27,344 | 0.63117 / 27,328 | 0.62953 / 27,408 |
| 769f331 (0.63241) | 0.63488 / 27,344 | 0.63477 / 27,328 | 0.63282 / 27,408 |
| cef0574 (0.63421) | **0.63578 / 27,344** | 0.63507 / 27,328 | 0.63372 / 27,408 |

Partner screens: no catalog partner (sizeknobs-cto.json) repays it.
- All 56 applicable catalog knobs on scu_bs (23322b0): the cheapest positive knobs are +16 wl_ts_clockvar/g_w_clock_local
  (-0.0005), +8 ev_cb_local (-0.0019), +80 pu_amm_keyfn (-0.0028), +8 fee unwrap (-0.0028), +64 w_ev_creator_first (-0.0053).
  `sh_key_borrow` is -80 B and +0.0007.
- The 8 best additive-estimated +56 B combos all fall to 0.6225-0.6257 at 27,400.
- 34 knobs on scu_bs+o+pool-key (27,408): no -8 B partner is near neutral. cu_fee_replace costs 0.003 and `a.pool.data_len()!=0` costs 0.0017.
  On 769f331, ref-compare `a.pool.owner==a.pump_amm.key` is -80 B.
- main vs scu_bs: scu_bs removes about 20 spill, reload and move instructions in the validate/skip-tree region
  (0x2b0-0x1970). The original keeps more of them, so a faithful partner would add register pressure in that region,
  not code at the tail.

Tools (out dir, deleted at finish; the pattern is simple to recreate): `capvar.sh` (crate copy + EDITS -> raw IR -> opt -O3 -> llc
-> ratio, about 15 s plus the IR capture), `capfile.sh` (the same from a full admin_cto.rs), `comp.py` (composes catalog knobs).
