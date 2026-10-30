# w14a31-cto-knob8: size-pairing knobs for admin_cto::execute (0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: find faithful ±8 / ±16 B spellings in the tail, event, wallet, sweep and error-message code (outside the
frame/validate regions), and pair them with the known off-size leads to land exactly at 27,400 B.
Bases: main f100a59 (0.6423, M 2,144), b2e90aa (0.6444, M 2,151), 5ee681d (0.645, M 2,153), e87e001 (0.64709, M 2,160), 81d3d9a (0.65069, M 2,172).
Main moved five times during the lane; every pairing below was re-run on the main it is reported against.
Ledger: approach `sizeknob`, keys `0x22a10-w14-<sha7>-knob8-<name>-v1`.

**Result: no zero-loss gain.** No pair or triple of faithful size knobs beats main at 27,400 B. The knob catalog is
extended below (all `M`/`jM` values are raw-IR capture + opt + llc oracle, `eq_main` holds on b2e90aa and e87e001).

## Oracle and tools (`tools/`, experiment only)

| tool | what |
| --- | --- |
| `capvar.sh <name> <edits.py> <slot>` | w14a03 raw-IR capture + `rx.py` (opt -O3 + llc) re-pointed at this lane; `rx.py` here also prints `M` (matched score tokens). |
| `q.py <res.jsonl> name...` | 2-worker queue over `e/<name>.py` edit lists (deletes the crate copy and IR after each row). |
| `jm.py <name...>` | ratio and `jM` with every jump offset masked: the structural value of a knob, independent of size. |
| `prof.py <fn.bin\|so> [step]` | median candidate-minus-original byte offset per original region (opcode+reg alignment). |
| `jdiff.py <name\|MAIN> [step]` | jumps aligned under jump masking whose raw offsets differ, as (src region, dst region, delta) histogram. |
| `where.py <base> <name...>` | where (candidate offset) a knob changes code, ignoring jump offsets. |
| `shift.py <so>` | **synthetic size-pair oracle**: insert a junk 8 B slot at a block start and/or delete one unmatched instruction, fix every crossing jump, score `M`. It is the upper bound of a pure size knob pair that changes no other code. |
| `rec.py <res.jsonl>` | ledger recorder. |

## Key measurements

- main jM - M is only **26 tokens** (e87e001: M 2,160, jM ~2,186): even a perfect size distribution can add at most ~0.008
  on main. `jdiff.py MAIN` lists 105 mismatched jumps, spread over many (src,dst) regions with mixed ±8..±40 deltas: the
  mismatches are block-layout differences, not one global shift.
- `shift.py` on e87e001 (`STEP=6 GRID=512`, 1,344 pairs): **no single +8 or -8 position gains** (best 0). The best pure
  size pair is **+2 M** (+0.0006): +8 at main 0x24e0 with -8 at main 0x2038; +8 at 0x24e0 with -8 anywhere in
  0x3f38-0x5540 gives +1 M. 11 of 1,344 pairs are above main. So the whole size-pairing family is worth at most ~+0.0006 on
  main, before the code changes the real knobs bring with them.
- Offset profile (`prof.py`, main): orig 0x0400-0x5800 sits at -56..-72 B (-128 at 0x4400-0x4c00), orig 0x5c00+ at 0.
  The +48 B main carries in the sweep native arm (orig 0x5a00-0x5b28: `jeq tag,2,+1; ja` pairs, tag phi through
  `[r10-0x968]`, threaded `jne r7,2`) is the original's out-of-line ensure_rent_exempt Err block (orig 0x62e8, 3 insns,
  24 B) plus an unthreaded sweep join (orig 0x3c58 `jne r7,2,+0x380` reached by both native-arm edges with r7/r9 set).
  That is JumpThreading/block placement, not a size knob.

## Knob catalog (new entries)

Delta vs the base it was measured on. `jM` = jump-masked match count (base jM: b2e90aa 2,177; 5ee681d 2,179).
"=" means token-identical to main.

| name | edit | base | bytes | M (Δ) | jM Δ |
| --- | --- | --- | ---: | ---: | ---: |
| ev_old_fee_curve / ev_nf_drop | event `new_creator_fee_bps: a.bonding_curve.creator_fee_bps` (drop `let nf`) | b2e90aa | **-24** | 2150 (-1) | +2 |
| s_rent_get | `let min=Rent::get()?.minimum_balance(0);` (revert of the `let rent` knob) | b2e90aa | **+16** | 2141 (-10) | **+6** |
| sh_iflet | sharing CPI `if let Some(val)=sharing_update{..}` | b2e90aa | **-8** | 2146 (-5) | +1 |
| k3 (w14a20) | sweep CpiContext pump_amm clone, data via `a.pump_amm` | b2e90aa | +8 | 2146 (-5) | 0 |
| n_ensiflet | native arm `if let Err(e)=ensure_rent_exempt(..){return Err(e);}` | b2e90aa | +8 | 2147 (-4) | 0 |
| wl_writ_eq | wallet `a.current_creator.is_writable==false` | b2e90aa | +8 | 2146 (-5) | -1 |
| n_andthen | native arm `ensure(..).and_then(\|()\|transfer_native(..)).map(\|()\|amount)` | b2e90aa | -8 | 2138 (-13) | -3 |
| n_ensmatch | native arm `match ensure(..){Ok(())=>transfer..,Err(e)=>Err(e)}` | b2e90aa | -8 | 2130 (-21) | -7 |
| tp_dlen | pool gate `a.pool.data_len()!=0` | f100a59 | -8 | 2136 (-8) | |
| wl_coin_dlen | wallet `coin_present=a.coin_creator_vault_ata.data_len()!=0` | f100a59 | -16 | 2132 (-12) | |
| wl_vq_dlen | wallet do_collect `data_len()!=0` | f100a59 | -16 | 2065 (-79) | |
| wl_native_check | wallet `native_mint::check_id(&a.quote_mint.key())` | f100a59 | -40 | 2074 (-70) | |
| s_elseif_dlen | sweep `else if a.coin_creator_vault_ata.data_len()!=0` | f100a59 | -8 | 2013 (-131) | |
| r_minvar | `let rent=Rent::get()?;..saturating_sub(rent.minimum_balance(0))` | e87e001 | 0 | 2156 (-4) | |
| r_inline / r_map | Rent inline in saturating_sub / `Rent::get().map(..)?` | e87e001 | +16 / +32 | 2133 / 2130 | |
| wl_ixlit | event CPI `Instruction{program_id,accounts,data}` literal | b2e90aa | +32 | 2134 (-17) | -13 |
| n_both_and | (not faithful: `and` evaluates transfer eagerly) | b2e90aa | +56 | 2135 | |
| n_qq / n_okq | native arm `ensure?;transfer?;Ok(amount)` | b2e90aa | -24 | 1520 (collapse) | |
| wl_collect_match / wl_inner_iter / s_native_deref / s_amm_dlen / ev_bc_deref / tp_pargs_hold / wl_infos_ref | | | | big losses | |

Token-identical to main (zero-size, no codegen change): tp_ownderef, tp_owneq, tp_ifelse, tp_solog, tp_neg (pool
gate negated with msg first), tp_pargs_split, tp_pool_if, ev_reset_matches, ev_reset_ne, ev_auth_deref, ev_ts_unwrap,
ev_ts_sysvar, ev_emit_ref, ev_swept_local, wl_exec_owner_deref, wl_writable_req (require!), wl_ev_creator_deref,
wl_ev_ts_map, wl_disc_copied, wl_disc_cloned, wl_disc_ref, wl_meta_lit, wl_maperr_q, wl_bump_a, wl_cr_exec_first,
wl_docoin_if, wl_frozen_match, wl_auth_a, s_dest_pk, s_req_if, s_req_if2, s_lamports_sub, s_lamports_max, s_bump_arr,
s_amount_ne, s_tamount_ne, s_map_any, s_ok_zero, s_ensure_let, s_dest_tuple, r410_if, n_flip, n_tmatch,
n_tmatch_errfirst, n_ens_mapamt, n_gt_flip, n_ok0, h_ensfn, h_ensclos, h_tclos, h_blk.
Zero-size losers: wl_gate_swap (-15), wl_cc_and (`if do_coin`, -7), tp_sig_pre (-4).
Outlining helpers (h_clos, h_clos2, h_fn, h_fn2: native arm ensure+transfer in a closure/nested fn) split execute
into a second symbol: call multiset changes, rejected.

## Pairs at 27,400 B (all below main)

On 5ee681d (main M 2,153, 0.645):

| pair | bytes | M | ratio | jM |
| --- | ---: | ---: | ---: | ---: |
| P3 s_rent_get + ev_old_fee_curve + wl_writ_eq | 27,400 | 2150 | 0.6441 | 2186 (+7) |
| P2 s_rent_get + ev_old_fee_curve + k3 | 27,400 | 2149 | 0.6438 | 2187 (+8) |
| P5 s_rent_get + sh_iflet + tp_dlen | 27,400 | 2143 | 0.642 | |
| P6 s_rent_get + ev_old_fee_curve | 27,392 | 2145 | 0.6427 | 2187 |
| P1 s_rent_get + ev_old_fee_curve + n_ensiflet | 27,376 (not additive) | 2133 | | |
| P4 / P7..P11 | 27,376-27,424 | 2130-2143 | | |

The jM gains of P2/P3 (+8) are lost again in jump offsets: the knobs sit at different places (k3/wl_writ_eq at main
~0x2418-0x2500, s_rent_get in the native arm ~0x5700, ev_old_fee_curve in the event ~0x4968), so they shift regions that
main already aligns.

On e87e001 (main M 2,160, 0.64709; pairs picked from the `shift.py` hot spots: +8 near main 0x2418-0x24e0 where
k3 / wl_writ_eq act, -8 in 0x3f38-0x5540 where sh_iflet / tp_dlen / ev_nf_drop act):

| pair | bytes | M | ratio | jM (main 2,188) |
| --- | ---: | ---: | ---: | ---: |
| Q1 k3 + sh_iflet | 27,400 | **2160 (tie)** | 0.64709 | 2189 |
| Q2 wl_writ_eq + sh_iflet | 27,400 | 2160 (tie) | 0.64709 | 2188 |
| Q3 / Q4 k3 / wl_writ_eq + tp_dlen | 27,400 | 2157 | 0.6462 | |
| Q5 / Q6 + n_andthen | 27,400 | 2151 | 0.6444 | |
| Q8 n_ensiflet + sh_iflet | 27,400 | 2155 | | |
| Q10 k3 + wl_writ_eq + sh_iflet + tp_dlen | 27,400 | 2155 | | |
| R2 s_rent_get + ev_nf_drop + k3 | 27,400 | 2156 | 0.6459 | **2196 (+8)** |
| R3 / R6 s_rent_get + ev_nf_drop + wl_writ_eq (+ sh_iflet + k3) | 27,400 | 2157 | 0.6462 | 2195 / 2196 |
| R4 s_rent_get + sh_iflet + tp_dlen | 27,400 | 2150 | | |
| R5 ev_nf_drop + k3 + wl_writ_eq + n_ensiflet | 27,400 | 2156 | | |

Re-measured on 81d3d9a (main M 2,172, 0.65069): Q1 ties again (2,172), R3 2,169, R2 2,168, sh_iflet 2,167 @-8,
k3 2,167 @+8, ev_nf_drop 2,171 @-24, s_rent_get 2,160 @+16. The knob deltas are stable across the four mains.

`shift.py` on R2 (jM +8, M -4): a pure +8 at R2 0x3be0 with -8 at 0x2038 or in 0x40c8-0x5528 would give M +7 (+3 over
main). R2 0x3be0 is the `Rent::get()` Err-conversion block (`Error::from(ProgramError)`, the Ok path jumps to the native
arm). s_rent_get itself removed one instruction there (`ldxdw r1;mov r7,r1` -> `ldxdw r7`). The +8 it wants back is
that same instruction, so the oracle just undoes s_rent_get's jump damage. There is no independent knob.

Vault-seed spellings (`vs_*`, the shift oracle's -8 hot spot at main 0x2038 is the `creator-vault` seed slice): vs_inline,
vs_oldfirst, vs_olda and vs_bytes are token-identical. vs_let (no deferred `vsigner`) gives -4 at 0 B, vs_arr
(`let bump=[..]`) gives -156 at -16 B, and vs_slice1 does not compile.

### v7c (w14a21 validate closure) + repay, on 5ee681d

v7c is now **+32 B** (27,432), jM **2,240 (+61 over main)**, M 2,106. With repay knobs at 27,400:

| pair | bytes | M | jM |
| --- | ---: | ---: | ---: |
| V3 v7c + ev_old_fee_curve + sh_iflet | 27,400 | 2108 | 2243 |
| V6 v7c + ev_old_fee_curve + wl_coin_dlen | 27,400 | 2107 | 2240 |
| V5 v7c + ev_old_fee_curve + tp_dlen | 27,400 | 2105 | 2239 |
| V7 v7c + sh_iflet + wl_coin_dlen + n_andthen | 27,400 | 2096 | 2234 |
| V2 / V4 / V1 / V8 | 27,384-27,416 | 2097-2107 | 2235-2242 |

At the pinned size v7c still has jM - M = 135: its jump mismatches are spread (`jdiff.py V3`), mostly validate-region
block layout (src 0x0000-0x1000 with deltas of hundreds of bytes), so tail repay knobs cannot recover them. The v7c
offset profile is -24..-8 through orig 0x5800 and +56/+32/+8 after: the repay must be ~-56 B inside the native arm plus
the original's 24 B out-of-line ensure Err block later, i.e. the unthreaded sweep join, which no spelling here produced.
`shiftk.py rx/v7c/fn.bin 4` (pure -32 B: delete 4 unmatched instructions at any 0x100 grid position, jumps fixed): the best
position recovers only **+3 M** (2,109 at orig ~0x5c60). Size alone cannot repay v7c.

## Conclusion / next ideas

- The size-pairing family is used up on main. The synthetic bound is +2 M, real pairs reach a tie at best (Q1), and the
  jM-positive knobs (s_rent_get +6, ev_nf_drop +2, sh_iflet +1) lose their gain to jump offsets at the pinned size.
- The remaining jump mismatches (105 on main) come from block layout: the sweep join (orig 0x3c58, one unthreaded
  `jne r7,2`), the ensure_rent_exempt Err block outlined at orig 0x62e8, and the validate error blocks
  (src 0x2000-0x3000 -> dst 0x2000, ±8..-32). A lane that makes the native arm reach one unthreaded sweep join would gain
  both the 48 B native-arm excess and the 24 B tail block, and would also make v7c landable.
- Use `jm.py` (jM) rather than M to screen knobs. M at an off size mixes code value with jump-offset damage.
