# w16a05-cto-skelsplice: region-local re-rank and two-region splices of the archived admin_cto builds (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B. Base: main 9bd38c7d5
(admin_cto source = 86e2a6b74; 0.67376, 3,124 slots, M 2,249), taken from `$BASE`. Ledger approach `skelsplice`, keys
`0x22a10-w16-9bd38c7-skelsplice-<variant>-v1` (screens) and `...-skelsplice-index-envelope-v1` (the index and envelope).

**Result: notes only, no landable change.** Main is still the best zero-loss measurement. The archive has two-region splice
bounds up to M 2,281 (+32), but the composites that realise them stay below main: the best is M 2,217 (-32, at exactly
27,400 B) for the validate-closure family and M 2,235 (-14) for the cashback-early basin (section 4). Section 5 gives the
mechanism that eats the validate-closure family's back half.

Families named in these notes (the archive uses `L` for two different things):

- **VC**: the le_vy1 validate closure of w14a21/w14a42/w15a03 (`v7c+lv_ny+lv_le+lv_cf_skc+lv_h289`, w15a03 `L_N3h`).
- **CB**: the cashback-early + t1n basin of w15a16 (`mv_5_1+t1n+m_crl2+devol`, w15a16 `L`; `A_t1a` adds `t1a`).

## 1. Index (`tools/idx.py`, `data/fnbins.txt`)

- 10,027 archived builds: every `$C/lanes/*/rx/*/fn.bin` (168 lane dirs, w13-w16) plus the 42 w13-w16 measure outputs
  (`t/*/unstripped.so`). Deduped by bytes and limited to 26-29 KB with res ratio >= 0.60 (or no res.json): **3,576 unique
  builds**. For each build `idx.py` stores, per original instruction, its difflib partner under the scorer mask (M, the
  measure.sh metric) and, with `--skel`, under the skeleton mask (`xled.fmask`: registers, frame offsets, jump offsets,
  lea immediates and call immediates masked). Partners are int16 arrays in an npz (not committed: 3-4 MB; rebuild in
  about 2 min for M and 25 min for skeleton on the loaded machine, 5-6 workers).
- `tools/prov.py <lane/rx/name>` finds a build's ledger row (genes, edits, base main). Builds without `res.json` and the
  `*p2`/`*ra`/`*perm` outputs are spill-permutation or RA-force oracles, not source; every table below excludes them.
- Sub-regions (`tools/regs.py`, original offsets): entry.pda 0x0-0x280, entry.ql 0x280-0x420, entry.st 0x420-0x700,
  holder_head 0x700-0xb00, nonholder 0xb00-0xe60, e306_296_326 0xe60-0x1258, e312_307 0x1258-0x1490, fee_chain
  0x1490-0x1800, join 0x1800-0x1c00, sweep_head 0x1c00-0x2600, tcf 0x2600-0x3c00, sharing_cpi 0x3c00-0x4a00,
  tail_hot 0x4a00-0x5400, cold_err 0x5400-0x5a00, wallet 0x5a00-0x6c00.

## 2. Region-local re-rank (`tools/regtab.py`; `data/regtab_near.txt`, `data/regtab_all.txt`)

Per sub-region, builds ranked by skeleton gain dSk (original tokens skeleton-matched in the region, minus main's), with the
region's own dM and the M collateral outside it. Source builds with M >= 2,190 (near-main bases, so the collateral is the
build's own and not base staleness):

| region | best dSk | its dM | dM elsewhere | build |
| --- | ---: | ---: | ---: | --- |
| entry.pda | +13 | +1 | -1 | w15a03 `H_hkl2crl3` (27,472 B; skM +20 at M = main) |
| entry.st | +7 | -1 | 0 | w15a03 `H_hkl2` (27,400 B, M 2,248) |
| holder_head | **+55** | +13 | -58 .. -69 | w14a75 and1polar `k_*` (the and-1 holder test; VC has the same +55) |
| nonholder | +13 | +1 | -44 | w15a02 `Tb_g1` / `T_g1` (to_string helpers) |
| e306_296_326 | +11 | +2 | -61 | w14a78 `rt0` |
| fee_chain | +4 | 0 | +2 | w15a02 `M_g1` (+120 B) |
| join | +7 | -1 | -26 | w15a16 `mv51_crl2` (CB) |
| sweep_head | +2 | 0 | -23 | w14a86 `x_g_pu_own` |
| tcf | +8 | -29 | -9 | w15a17 `jl111` |
| sharing_cpi | **+86** / +84 | -26 / -50 | -28 / -3 | w14a81 `lat_pa_au_gl` / w15a03 `L2_lf_au` (authority literal, Rc locals first) |
| tail_hot, cold_err, wallet | <= +4 | < 0 | < 0 | |

Two near-free skeleton leads for other lanes: `H_hkl2crl3` (holder_key deferred init next to validate + crl3) is skM +20
at M = main, and `L2_lf_au` is skM +84 in the sharing CPI for M -50 there and only -3 elsewhere: its loss is naming
inside the region, not collateral.

## 3. Two-region splice envelope (`tools/pairs.py`, `tools/splcheck.py`, `tools/splice2.py`)

For every original token k at which both builds are aligned, front-of-A (A's code before its partner of k) plus
back-of-B (B's code from its partner of k). `pairs.py` ranks pairs by prefM_A(k) + sufM_B(k) from the index (top 6
fronts x top 6 backs at each k); `splcheck.py` prices the top 400 with exact difflib M on the spliced sequence and
rejects non-functions: the splice must have the original's 157 calls and the original's multiset of error-line
immediates (284-719). Splices inside a duplicated or dropped error block fail this (for example every `le306` front at
0x1060 gives 162 calls and +900 B). **180 of the top 400 are clean.** `data/top20.json`, `data/pairs_checked.txt`.

Top 20 clean pairs, one row per front build (M 2,249 = main; bytes of the splice itself):

| # | front (A) | back (B) | cut (orig) | M_A | M_B | splice M | bytes | realised composite (section 4) |
| ---: | --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| 1 | w15a03 `L_N3h` (VC) | w15a02 `M_g1` | 0x1c68 sweep_head | 2,105 | 2,251 | **2,281 (+32)** | 27,400 | VC+g1 2,100; best VC 2,203 |
| 2 | w15a03 `L_N3` (VC) | w15a02 `M_g1` | 0x1c68 | 2,104 | 2,251 | 2,280 (+31) | 27,408 | LN3_c0s 2,189 |
| 3 | w15a03 `L_N3cl` (VC) | w15a02 `M_g1` | 0x1c68 | 2,102 | 2,251 | 2,280 (+31) | 27,408 | |
| 4 | w15a03 `L_vy1` (VC) | w15a02 `M_g1` | 0x1c68 | 2,102 | 2,251 | 2,278 (+29) | 27,408 | |
| 5 | w15a16 `A_t1a` (CB) | w14a114 `e1` (IR scan) | 0x2e40 tcf | 2,235 | 2,182 | 2,272 (+23) | 27,408 | not source (e1 is an IR edit) |
| 6 | w15a16 `mv51_t1n_crl2` (CB) | w14a114 `e1` | 0x2e40 | 2,235 | 2,182 | 2,272 (+23) | 27,408 | |
| 7 | w15a03 `N_m_crl3__t1n` | w15a03 `L_N3` (VC wallet) | 0x5b58 wallet | 2,249 | 2,104 | 2,271 (+22) | 27,424 | needs VC's wallet RA (section 5) |
| 8 | w15a16 `B_t1hu` (CB) | w14a114 `e1` | 0x2e40 | 2,234 | 2,182 | 2,271 (+22) | 27,432 | |
| 9 | w15a16 `F03` (CB) | w14a114 `e1` | 0x2e40 | 2,217 | 2,182 | 2,271 (+22) | 27,336 | |
| 10 | w15a16 `F10` (CB) | w14a114 `e1` | 0x2e40 | 2,231 | 2,182 | 2,271 (+22) | 27,336 | |
| 11 | w15a16 `L_K_g_canedit_first` (CB) | w14a114 `e1` | 0x2e40 | 2,232 | 2,182 | 2,271 (+22) | 27,400 | |
| 12 | w15a21 `cs7` | w15a03 `L_N3` (VC wallet) | 0x5b58 | 2,249 | 2,104 | 2,271 (+22) | 27,480 | |
| 13 | w15a21 `tf_f6` | w15a03 `L_N3` | 0x5b58 | 2,249 | 2,104 | 2,271 (+22) | 27,488 | |
| 14 | w15a02 `M_g1` | w15a03 `L_N3` | 0x5b58 | 2,251 | 2,104 | 2,270 (+21) | 27,496 | |
| 15 | w15a03 `N_t3n` | w15a03 `L_N3` | 0x5b58 | 2,248 | 2,104 | 2,270 (+21) | 27,352 | |
| 16 | w15a07 `fs_1617_r3` (RA force) | w15a03 `L_N3` | 0x5b70 | 2,251 | 2,104 | 2,270 (+21) | 27,376 | not source |
| 17 | w15a16 `T_mv_1_0` | w15a03 `L_N3` | 0x5b58 | 2,248 | 2,104 | 2,270 (+21) | 27,424 | |
| 18 | w15a16 `A_hkmut` (CB) | w14a114 `e1` | 0x2e80 | 2,221 | 2,182 | 2,269 (+20) | 27,432 | |
| 19 | w15a16 `F11` (CB) | w14a114 `e1` | 0x2e60 | 2,220 | 2,182 | 2,269 (+20) | 27,336 | |
| 20 | w15a16 `F16` (CB) | w14a114 `e1` | 0x2e60 | 2,228 | 2,182 | 2,269 (+20) | 27,400 | |

The CB rows with the source back `fru1` (w14a133 TCF struct update) price the same as `e1` (2,272 at 0x2e40); the
cut falls inside the TCF clone run, where fru1 rearranges the run (front -29, back +18), so it is not a region composite.

**Frontier** (`tools/frontier.py`): at every cut, no source build gains in front without losing behind. At 0x1c68 (front
= entry + validate + join, main 463; back main 1,786): VC `L_N3h` +27/-171, CB `A_t1a` +13/-27, CB `F17` +6/-26,
`N_m_crl3__t1n` +4/-4, `N_m_crl2` +1/0, `fs_1617_r3` -1/+3, `M_g1` -3/+5. Every top pair is "a front family whose back
collapses" + "a near-main build with a +2..+5 back", so the bound is the front family's front gain.

## 4. Realising the top pairs as source (`screen/scr.py`, `screen/genes_w16.py`; `data/res-9bd38c7.jsonl`)

`scr.py` is the w15a03/w15a16 raw-IR screen (capraw identity build + `opt -O3` + `llc`, exact M, per-region dM vs main),
pointed at this lane; `m0` reproduces main exactly (`eq_main: true`). Genes are the w15a16 `genes_mp` library plus `g1`
and the curve-store spellings `c0*` in `genes_w16.py`.

| variant | genes | bytes | M | dM | front dM to 0x1c68 | back dM |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| m0 | main | 27,400 | 2,249 | 0 | 0 | 0 |
| LN3h | VC | 27,224 | 2,105 | -144 | +27 | -171 |
| LN3h_g1 | VC + g1 (pair #1 as source) | 27,256 | 2,100 | -149 | | |
| g1 | g1 alone | 27,520 | 2,251 | +2 | -3 | +5 |
| LN3h_c0il / c0m | VC + store `if let` / `matches!` | 27,224 | 2,105 | -144 | | |
| LN3h_c0ne | VC + store `!=None&&!=Some(false)` | 27,208 | 1,965 | -284 | | |
| **LN3h_c0s** | VC + store `holder==Some(true)` | 27,376 | 2,189 | -60 | +11 | -71 |
| LN3_c0s | without h289 | 27,384 | 2,189 | -60 | | |
| LN3h_c0s_shnf | + sharing `None` arm first | 27,376 | 2,189 | -60 | | |
| **LN3h_c0s_shie** / _shif | + sharing `if let ..{}else{}` / `if let` | 27,376 | **2,203** | **-46** | +11 | -57 |
| Lsh | VC + `if let ..{}else{}` (closure-form store kept) | 27,224 | 2,139 | -110 | +26 | -136 |
| **Lsh_t1n** | VC + sh_ifelse + t1n (`if new.is_none()` in the shared arm) | **27,400** | **2,217** | **-32** | | |
| Lsh_c0s_t1n | + c0s | 27,392 | 2,202 | -47 | | |
| Lsh_c0s_mv51 | VC + c0s + sh_ifelse + mv_5_1 (CB's cashback-early literal) | 27,360 | 2,213 | -36 | | |
| Lsh_mv_5_1 / Lsh_m_crl2 | Lsh + mv_5_1 / m_crl2 | 27,264 / 27,304 | 2,089 / 2,096 | -160 / -153 | | |
| Lsh_fru2 / s_tai2 / tai_tv / k3 / sw1 | Lsh + one TCF-line gene | 27,224-27,232 | 2,129-2,154 | -95..-120 | | |
| At1a | CB + t1a (w15a16) | 27,408 | 2,235 | -14 | +13 | -27 |
| At1a_fru1 | CB + t1a + fru1 (pair #5/#10 as source) | 27,408 | 2,226 | -23 | | |
| At1a_fru6 | + fru6 | 27,408 | 2,234 | -15 | | |
| Lb_fru1 | CB + fru1 | 27,400 | 2,225 | -24 | | |

Region dM: `Lsh` (VC + sh_ifelse) is entry.pda -4, entry.ql +4, entry.st +2, holder_head +14, e306 +6, e312_307 -3,
fee_chain +5, join +2, sweep_head -10, **tcf -122**, sharing_cpi -15, tail_hot -2, cold_err -2, **wallet +15**: everything
but the TCF/sharing/sweep naming is at or above main. `Lsh_t1n` (27,400 B exactly, 3,042 slots) trades that for
entry.pda -2, entry.st +1, holder_head +12, e306 +3, e312_307 -5, join +1, sweep_head -4, tcf -12, sharing_cpi -5,
tail_hot -4, cold_err -3, wallet -14.

## 5. Mechanism: why the VC front cannot be spliced onto main's back

The post-opt IR of LN3h and main differs after validate in exactly two places (normalised IR diff, `m.ll`):

1. **The curve store.** Main stores `curve.is_holder_reward=holder.unwrap_or(false)` as `and i8 %holder,1` computed at
   the store from the spilled raw argument (`ldxdw r2,[r10-0x8e8]; and64 r2,1`). This re-derivation is #3409
   (w14a82 walletweight, +0.0048). In VC the closure computes the same `and i8 %holder,1` for its holder test, and GVN
   reuses it at the store, so the masked holder is live from validate to the curve store. **That is what the original
   does**: it reloads the masked holder from `[r10-0x950]` at the store (orig 0x4b60) and in the sweep native arm
   (orig 0x5a40), and LN3h uses the same slot. But main's back half (TCF, sharing CPI, tail, all landed after #3409) was
   tuned without that live range; with it the TCF accounts pointer moves from r8 (original and main) to r6 and the TCF
   loses 122 M.
   - An IR-oracle edit that recomputes `and i8 %0,1` at the store (`iro/ln3h_st.ll`) gives M 2,187: TCF -122 -> -12.
   - The source spelling `holder==Some(true)` (c0s) reproduces it (2,189): it is GVN'd to the outer block's
     `and i8 %0,-3; icmp ne` holder instead. `if let`, `matches!` and `unwrap_or_default` keep the closure's form (2,105).
   - But the RA change is global: with c0s the front gain falls from +27 to +11 and the wallet from +15 to -15.
2. **The fee-Some test** at the curve store is `icmp eq %fee.tag,0` (VC) against `icmp eq %fee.tag,1` (main). Flipping
   it back in the IR oracle changes nothing (2,187 both).

**Two register-allocation basins** (`tools/regmap.py`: original register -> ours, over skeleton-matched instructions):

| build | TCF orig r8 (accounts) | TCF orig r9 | wallet orig r9 | wallet orig r7 | TCF dM | wallet dM |
| --- | --- | --- | --- | --- | ---: | ---: |
| main | r8 33/43 | r0 19/24 | r7 22/37 | r7 31, r8 12 /45 | 0 | 0 |
| Lsh_t1n (basin A) | r8 33/43 | r0 19/24 | r7 22/37 | r7 32, r8 11 /45 | -12 | -14 |
| Lsh, LN3h (basin B) | r6 20, r9 13 /42 | r5 19/23 | **r9 32/38** | **r7 43/47** | -122 | +15 |

Basin A has main's TCF (accounts pointer in r8, as in the original) and main's wallet swap (original r9 in r7, original r7
partly in r8). Basin B has the original's wallet registers but moves the TCF accounts pointer to r6. The VC family sits
in basin B by default; `c0s`, `c0h` and `t1n` move it to basin A, and every basin-A VC variant pays the wallet back.
The original has the basin-A TCF and the basin-B wallet at once; no archived build or screened composite does.

The remaining tail_hot loss is w14a42's curve-block placement (the curve update block is pre-merged after the sharing
test instead of falling through); `if let Some(val)=sharing_update{..}` repairs 14 of its 34.

**Conclusion for the angle.** Two-region composites from the archive do not beat main. Every clean splice above main pairs
a front family (VC or CB) whose back collapses with a near-main back worth +2..+5. Realised as source, the VC family's
front gain is entangled with a long live range that the original has and main's back was tuned against; the CB family's
back loss is the w15a16 spill-colour rotation. Best realisations: VC 2,217 (-32, `Lsh_t1n`), CB 2,235 (-14), against
main 2,249.

## Next ideas

1. VC is more faithful than main in two places at once: the and-1 holder test (holder_head skeleton +55, M +14) and the
   masked holder live to the curve store and the sweep native arm (the original's `[r10-0x950]`). A lane could adopt VC
   with the closure-form store (LN3h) and re-tune the back half under it, rather than splicing main's back on. The
   back-half levers landed since #3409 (#3430, #3437, #3480, #3495, #3621, #3666) are the first candidates to revisit.
2. `L2_lf_au` (sharing CPI skeleton +84, M -50 in-region only) and `H_hkl2crl3` (skM +20 at M = main) are skeleton bases
   whose losses are naming inside one region; a region-local RA/frame repair there is worth more than any splice found.
3. The index makes re-ranking cheap: `idx.py` on new captures, then `pairs.py` + `splcheck.py` (about 3 min).
