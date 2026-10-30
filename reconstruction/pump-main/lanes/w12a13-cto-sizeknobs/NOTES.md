# Lane w12a13-cto-sizeknobs (wave 12, pool a)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: a size-compensation catalog. Small, ordinary, semantics-preserving single edits to `admin_cto.rs`,
each measured alone with the identity recipe (`measure.sh`): byte delta, ratio delta, losses and the
entry spill offset (frame proxy). Composites that gain ratio but miss 27,400 B by 8-56 B can pick
compensators from it.

Machine-readable catalog: `pump-main-swarm/w11/sizeknobs-cto.json` (copy: `sizeknobs-cto.json` here).
Builds and scratch: `~/.cache/pumpfun-reconstruction/lanes/w12a13-cto-sizeknobs/` (not in git).
Ledger approach `size-knob-catalog`, keys `0x22a10-w12-20a1ae9-sizeknob-<base>-<knob>-v1`.

## Bases

| base | admin_cto.rs | bytes | ratio | first spill |
| --- | --- | ---: | ---: | ---: |
| `main` | main 20a1ae9c0 (= h1, #2642) | 27,400 | 0.43919 | `[r10-0x8f0]` |
| `j3` | main + `wallet_flags` (#2518) | 27,312 | 0.45251 | |
| `k4` | main + wallet_flags, region2_tree, fee_unwrap, canedit_first, old_fee_first (w9r2 k4) | 27,384 | 0.4525 | `[r10-0x8f0]` |
| `L1` | k4 + `s_bump_first` + `p_share_match` (#2749, w12a04-cto-k4size) | 27,400 | 0.45147 | `[r10-0x8f0]` |
| `L2` | L1 + can_edit cleared after the fee store (#2792) | 27,400 | 0.45177 | |
| `C2` | L2 + curve store `if let Some(f)=fee` (fee_unwrap reverted) | 27,392 | 0.45213 | `[r10-0x8f0]` |
| `C3` | C2 + validate fee test as `match fee{Some(f)=>{..}None=>{}}` | 27,384 | **0.47618** | `[r10-0x8f0]` |
| `Av` | w12a14 b53cbd23e405 (L1 + amm_cb_local + k4_oldfee_after + v326 match) | 27,392 | 0.48569 | `[r10-0x8f8]` |
| `A2` | w12a14 6f262fb34c9e (Av + curve store in original order) | 27,384 | 0.48607 | |
| `D` | w12a14 d7acbb3d549a = #2831 | 27,400 | 0.48652 | `[r10-0x8f8]` |
| `M2` | main 1905fba85: D + nested pool-authority signer seeds (#2808 spelling) | 27,400 | 0.48742 | |
| original | | 27,400 | 1 | `[r10-0x928]` |

## How to use

- `tools/knobs.py` holds every knob as exact `(old, new)` substitutions, `tools/genes.py` the bases.
  `tools/trial.py <name> <base> <work_idx> <knob>...` builds one variant through `measure.sh` and refuses any
  edit that changes the line count or moves an `error!`/`require!`/`msg!` site off its line (line!() values are code).
- Byte deltas are **not additive** (x1-integrator: sweep knobs b=-16 and e=+16 composed to g=+16, not 0).
  Pick candidates from the table, then measure the combination.
- `=` means the build is byte-identical to its base (the knob does not change codegen).
- `tools/cdiff.py a.so b.so` diffs two candidate builds of `admin_cto::execute` (what a knob really changed);
  `tools/jumpmap.py cand.so` aligns against the original with jump offsets masked and shows where inserting
  k slots would fix or break aligned jumps; `tools/frame.py` prints the entry spill offset.

## Catalog (one row per knob and base; measured here unless noted)

| knob | category | base | Δbytes | Δratio | ratio | first spill | calls | measured by |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- |
| `prep_match` | ? vs explicit match | C2 | +0 | -0.04074 | 0.41139 | -0x8f0 | 154+3 | here |
| `v_fee_split` | combined vs split check | L1 | +200 | -0.01253 | 0.43894 | -0x900 | 157+3 | here |
| `v_ik_split` | combined vs split check | L1 | -8 | -0.00819 | 0.44328 | -0x900 | 157+3 | here |
| `v_ik_split` | combined vs split check | Av | -8 | -0.04204 | 0.44365 | -0x908 | 157+3 | here |
| `s_dest_borrow` | copied-vs-borrowed Pubkey | L1 | -80 | -0.00173 | 0.44974 | -0x8f0 | 154+3 | here |
| `s_old_borrow` | copied-vs-borrowed Pubkey | main | -80 | -0.00295 | 0.43624 | -0x8f0 | 154+3 | here |
| `sh_key_borrow` | copied-vs-borrowed Pubkey | L1 | -80 | +0.00008 | 0.45155 | -0x8f0 | 154+3 | here |
| `val_sh_borrow` | copied-vs-borrowed Pubkey | L1 | -152 | -0.02215 | 0.42932 | -0x8e8 | 154+3 | here |
| `L_canedit_revert+L_fee_match` | curve-store form | L1 | -8 | +0.00007 | 0.45154 | -0x8f0 | 154+3 | here |
| `L_canedit_revert+L_feeunwrap_revert` | curve-store form | L1 | -8 | +0.00066 | 0.45213 | -0x8f0 | 154+3 | here |
| `L_canedit_revert+L_feeunwrap_revert+v_fee_match` | curve-store form | L1 | -16 | +0.02471 | 0.47618 | -0x8f0 | 154+3 | here |
| `L_fee_unwrap_again` | curve-store form | C3 | +8 | -0.00037 | 0.47581 | -0x8f0 | 154+3 | here |
| `p_canedit_after_creator` | curve-store form | L1 | +0 | +0.00000 | 0.45147 |  |  | w12a04 |
| `p_canedit_revert` | curve-store form | L1 | +0 | +0.00030 | 0.45177 |  |  | w12a04 |
| `p_canedit_revert` | curve-store form | k4+s_bump_first | +0 | +0.00030 | 0.45124 |  |  | w12a04 |
| `p_cb_before_hr` | curve-store form | C2 | +0 | +0.00000 | 0.45213 | -0x8f0 | 154+3 | here |
| `p_feeunwrap_revert` | curve-store form | k4+s_bump_first | -8 | +0.00096 | 0.4519 |  |  | w12a04 |
| `p_oldfee_revert` | curve-store form | k4+s_bump_first | +0 | +0.00000 | 0.45094 |  |  | w12a04 |
| `v_new_match` | early-return form | C3 | +0 | -0.00060 | 0.47558 | -0x8f0 | 154+3 | here |
| `v_new_match` | early-return form | Av | +0 | -0.00060 | 0.48509 | -0x8f8 | 154+3 | here |
| `D_holder_phi` | gene (other lane) | D | = |  | 0.48652 | -0x8f8 | 154+3 | here |
| `L_canedit_revert+w_collect_match` | if let vs match | L1 | -8 | -0.00533 | 0.44614 | -0x8f0 | 154+3 | here |
| `L_share_none_first` | if let vs match | C2 | = |  | 0.45213 | -0x8f0 | 154+3 | here |
| `p_su_match` | if let vs match | k4+s_bump_first | +8 | +0.00053 | 0.45147 |  |  | w12a04 |
| `s_rent_local` | let binding | main | +16 | -0.00103 | 0.43816 | -0x8f0 | 154+3 | here |
| `gate_rev` | other | k4+s_bump_first | +0 | +0.00000 | 0.45094 |  |  | w12a04 |
| `p_pool_ifexpr` | other | L2 | -8 | -0.00083 | 0.45094 |  |  | w12a04 |
| `r2_skipflag` | other | L2 | -8 | -0.08383 | 0.36794 |  |  | w12a04 |
| `r2_sweepflag` | other | L2 | -8 | -0.08383 | 0.36794 |  |  | w12a04 |
| `r2_sweepflag_if` | other | L2 | -8 | -0.08383 | 0.36794 |  |  | w12a04 |
| `target_rebind_drop` | other | k4+s_bump_first | +0 | +0.00000 | 0.45094 |  |  | w12a04 |
| `L_bump_inline` | seed bump inline | Av | -8 | +0.00157 | 0.48726 | -0x8f8 | 154+3 | here |
| `p_pb_inline` | seed bump inline | Av | +0 | +0.00090 | 0.48659 | -0x8f8 | 154+3 | here |
| `p_pb_inline` | seed bump inline | D | +0 | +0.00090 | 0.48742 | -0x8f8 | 154+3 | here |
| `s_bump_inline` | seed bump inline | D | = |  | 0.48652 | -0x8f8 | 154+3 | here |
| `g_old_fee_first` | statement / evaluation order | main | +48 | +0.00080 | 0.43999 | -0x8f0 | 154+3 | here |
| `p_ev_ts_last` | statement / evaluation order | L1 | +280 | -0.04974 | 0.40173 | -0x8f8 | 154+3 | here |
| `s_frozen_first` | statement / evaluation order | k4+s_bump_first | -64 | -0.01326 | 0.43768 |  |  | w12a04 |
| `st_ql_first` | statement / evaluation order | main | = |  | 0.43919 | -0x8f0 | 154+3 | here |
| `w_create_rev` | statement / evaluation order | L1 | +272 | -0.02345 | 0.42802 | -0x960 | 159+3 | here |
| `w_ev_creator_first` | statement / evaluation order | L1 | +64 | -0.00443 | 0.44704 | -0x8f0 | 154+3 | here |

| prior knob on main (ledger; admin_cto.rs identical to main 20a1ae9c0) | Δbytes | ratio | Δratio | source |
| --- | ---: | ---: | ---: | --- |
| genes.G wallet_flags (#2518 do_collect/do_coin) | -88 | 0.45251 | +0.01332 | w9r2-admincto-harvest j3 (re-measured here) |
| sharing_update/collect_old as one if-tree (#2515) | +16 | 0.43995 | +0.00076 | w9r2-admincto-harvest j5 |
| curve.creator_fee_bps=fee.unwrap_or(old_fee) | +8 | 0.43822 | -0.00097 | w9r2-admincto-sibling h4 |
| curve.can_edit_creator_fee=false right after the old reads | +48 | 0.43969 | +0.00050 | w9r2-admincto-sibling h3 |
| pool_updated tests !data_is_empty() first | +0 | 0.43859 | -0.00060 | w9r2-admincto-harvest i4 |
| is_holder_reward stored before creator (#2621) | +0 | 0.43919 | +0.00000 | w9r2-admincto-harvest i1 (same ratio/slots) |
| cashback computed at the curve store (!holder&&cashback) | -104 | 0.30977 | -0.12942 | w9r2-admincto-harvest j1 |
| sharing CPI CpiContext::new(..).with_signer(..) | +24 | 0.40844 | -0.03075 | w9r2-admincto-harvest j2 |
| validate returns st.creator when shared (#2564) | -24 | 0.28893 | -0.15026 | w9r2-admincto-harvest j4 |
| holder.unwrap_or(false) + cashback with & (#2550) | -184 | 0.4371 | -0.00209 | w9r2-admincto-harvest j6 |
| if !(f>0&&f<=st.max_fee) (pump-amm sibling spelling) | +0 | 0.43919 | +0.00000 | w9r2-admincto-sibling v3 (byte-identical) |
| sweep native arm: let rent=Rent::get()?;let min=rent.minimum_balance(0); | +16 | 0.43816 | -0.00103 | w12a11-cto-sibling sib-rent-local |
| sharing CPI with_signer (re-measured) | +24 | 0.40844 | -0.03075 | w12b12-cto-cpi cpi-sws |
| signer seeds as inline literal in both signed CPIs (no pb/poolseeds/signer_seeds locals) | +184 | 0.39982 | -0.03937 | w12b12-cto-cpi seedsinline |

| prior knob on k4 (ledger) | Δbytes | ratio | Δratio | source |
| --- | ---: | ---: | ---: | --- |
| sweep native arm named Rent local | -32 | 0.45217 | -0.00033 | w12a11-cto-sibling sib-k4-rent-local |
| sweep binds bump before old (l1) | +8 | 0.45094 | -0.00156 | w9r2-admincto-harvest l1 |
| curve.creator stored after is_holder_reward (l2) | -48 | 0.45231 | -0.00019 | w9r2-admincto-harvest l2 |
| pool_updated tests !data_is_empty() first (l3) | -8 | 0.45197 | -0.00053 | w9r2-admincto-harvest l3 |
| k4 without region2_tree (l4) | -16 | 0.45174 | -0.00076 | w9r2-admincto-harvest l4 |

| w12a04-cto-k4size knob on k4+s_bump_first (27,392 / 0.45094) | Δbytes | ratio | Δratio |
| --- | ---: | ---: | ---: |
| `gate_rev` | +0 | 0.45094 | +0.00000 |
| `p_canedit_revert` | +0 | 0.45124 | +0.00030 |
| `p_feeunwrap_revert` | -8 | 0.4519 | +0.00096 |
| `p_oldfee_revert` | +0 | 0.45094 | +0.00000 |
| `p_su_match` | +8 | 0.45147 | +0.00053 |
| `s_frozen_first` | -64 | 0.43768 | -0.01326 |
| `target_rebind_drop` | +0 | 0.45094 | +0.00000 |

## Findings

- **Validate fee test as `match` (+0.024).** `match fee{Some(f)=>{..}None=>{}}` in place of `if let Some(f)=fee{..}` in
  validate (line 326) took C2 0.45213 -> C3 0.47618 at -8 B. The same gene was found independently by w12a14
  (`v326_match`) and w12a09 (t02, None-first spelling) and is part of #2831.
- **Compensators that keep ratio:** on Av the pool-seed bump inline (`p_pb_inline`) is 0 B / +0.0009 and the vault-seed
  bump inline (`L_bump_inline`, bump-first form) is -8 B / +0.00157. On D, `p_pb_inline` gives 27,400 B / 0.48742 with 0 losses,
  the same ratio as main's nested pool seeds (w12b12 spelling, integrated in 1905fba85), so this gain is already on main.
- **+8 B compensators** on the C/A/D family: curve store `fee.unwrap_or(old_fee)` instead of `if let` (+8, about -0.0004);
  `match sharing_update` instead of `if let` (+8 on k4+bump, +0.0005; #2749). `if let` vs `match` for the sharing update
  arm order (`L_share_none_first`) and for the curve-store fee is 0 B.
- **-80 B compensators:** every borrowed-instead-of-copied Pubkey compare removes one 32 B copy:
  `sh_key_borrow` (-80, +0.00008 on L1), `s_dest_borrow` (-80, -0.0017), `s_old_borrow` (-80, -0.003 on main).
- **Frame movers** (entry spill): splitting a combined check into two error sites (`v_ik_split`, `v_fee_split`) adds two
  outlined `to_string` calls (157 calls) and moves the spill 16 B deeper; `p_ev_ts_last` +8 B; `w_create_rev` +112 B.
  None of the cheap knobs moves it.
- Reorders of side-effect-free reads (`st_ql_first`) are byte-identical; `?` -> explicit `match` on
  `prepare_bonding_curve` is 0 B but -0.04 ratio.
- `holder` as a phi of constants in validate (w12a09 t14) is a no-op on D: `amm_cb_local` already gives that shape.
