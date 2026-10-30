# w13a15-cto-region3of3: admin_cto::execute (0x22a10), region 3 of 3

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: split the ORIGINAL window into 3 equal byte ranges and own range 3 (orig offsets `0x475a..0x6b08`: the
sharing-config CPI accounts, curve stores, pool CPI, the AdminCtoEvent emit!/emit_cpi!, the native/token sweep
bodies (Rent, ensure_rent_exempt, transfer_native/vault_tokens) and the wallet collect + CollectCreatorFeeEvent).
Base: main 7d7d9e5 (#2927, 0.51228 / 3,334 slots). Ledger keys `0x22a10-w13-<base>-r3-<genes>-v1`.

## Tools (`tools/`)

| tool | use |
| --- | --- |
| `regcon.py <so>... [--frame] [--regs] [--jumps]` | w13a13's region split of target_metric's difflib ratio (R1/R2/R3 matched tokens) |
| `annot.py orig\|<so>` | execute listing with relative offsets and call targets named from the candidate symbol table |
| `rdiff.py o.rel c.rel olo ohi [clo chi] [--frame] [--regs]` | masked range diff (labels stripped so jump offsets mask on both sides) |
| `framemap.py o.rel c.rel [lo hi]` | aligned pairs that differ only by frame offset: (orig slot -> our slot) tally per region |
| `r3run.py <genes.py> <set>...` | gene-set builds through measure.sh (2 at a time) with regcon split; `ledger_sync.py` records them |

## Region-3 residual map (main 7d7d9e5)

R3 = 1,117 original instructions: 689 exact, 844 frame-masked, 1,056 with frame+registers+jumps masked.
So region 3 already has the original's code shape (0.96 of the skeleton); what is left is frame slots and registers.

| orig | statement | original | ours |
| --- | --- | --- | --- |
| 0x4a80-0x4b90 | curve stores | `holder` reloaded from the phi-of-constants slot [-0x950] and stored as is; `cashback` = [-0x958]&1; old_fee (+0x70) read **before** the 0xa5/0xa3 stores | `holder` = `(h&0xff)!=0` from the raw Option<bool> arg byte (spilled at entry), cashback stored first, old_fee read after. Every source store order (q_curve_order, v6_ofirst*, v6_hr2) is byte-identical: the order is data flow, not source order |
| 0x4e20 | pool CPI `holder` | `ldxdw r4,[-0x950]`, pool_updated `mov r8,1` | `(r8&0xff)!=0` recomputed, pool_updated in r6 |
| 0x4fd8-0x5030 | AdminCtoEvent | reads curve `+0x70`, `+0xa5`, `+0xa3` into r4/r5/r3 (is_holder_reward and is_cashback_coin come back from the **curve**) | event flags from the locals (main #2927 q_evboth) |
| 0x50e8-0x5340 | emit_cpi | ix_data ptr spilled to the accounts-pointer slot [-0x8d8]; byte +0x2e kept in r6 | ix_data ptr in r6, byte spilled |
| 0x59c0-0x5b28 | native sweep | creator_vault (+0xd8) from the accounts slot [-0x8d8] into r8; amount in r6 | accounts pointer in a register, holder_creator_vault spilled to a new slot |
| 0x5bd8-0x5cc8 | wallet native/ATA tests | data_is_empty result spilled [-0x918]; `mov r8,0/1` flags in r8 | flags spilled to [-0x938] |

Top frame-slot mismatches inside R3 (`framemap.py`): accounts pointer -0x8d8 -> -0x8e0 (9 uses), holder phi
-0x950 -> -0x8e8 (8), -0x488 -> -0x498 (7, emit_cpi metas); the rest are 1-3 uses each, spread over 60 slots.

## Step 1 (base main 7d7d9e5 = #2927, 0.51228 / 3,334 slots) -- superseded

PR #2963 was closed: the same text (event `is_cashback_coin` from the curve + `reset` inline) reached main through
w13a11-cto-stitch-5 (#2933) before it could land. The table stays as screen evidence.

Single-gene screen of the w12a14/w13a10 library genes that touch region-3 statements (source lines >= 556),
on main 7d7d9e5 (`hc/results.jsonl`, ledger `*-r3-*`):

| gene | bytes | ratio | R1/R2/R3 |
| --- | ---: | ---: | --- |
| main | 27,400 | 0.51228 | 516/505/689 |
| `p_ev_both_curve` (event flags read from the curve) | 27,384 | 0.51393 | 518/505/692 |
| `p_ev_cb_curve` (event is_cashback_coin from the curve) | 27,392 | 0.51356 | 517/505/692 |
| `v6_hrb` (pool CPI holder from the curve) | 27,368 | 0.51349 | 516/506/691 |
| `p_reset_inline` (event `sharing_config_reset:sharing_update.is_some()`) | 27,408 | 0.51221 | 516/506/688 |
| curve store orders, pool forms, sweep dest/keys forms | 27,400 | 0.51228 | identical bytes |
| **`p_ev_cb_curve` + `p_reset_inline`** | **27,400** | **0.51348** | 516/505/**693** |

The last row: 27,400 B, 3,334 slots, 1034/1034 normalized and raw, 0 losses, unstripped sha 620d90b0b2e33a2f.
Runtime differential: 363/363 cases match.

Mechanism: the original's AdminCtoEvent reads `is_cashback_coin` back from the curve (orig 0x4fe8 `ldxb r3,[r3+0xa3]`);
the `reset` local folded into the event literal is the +8 B size companion. Same semantics: the curve field was just
stored from `cashback`, and `reset` was only used by the event.

## Region-3 findings after step 1 (mains f7ce2e3, a87c6bf, 2ca4d03, 1043a51)

**Original holder sources are crossed relative to ours.** The original passes the pool CPI `holder` from its
phi-of-constants slot (orig 0x4e20 `ldxdw r4,[r10-0x950]`) and the AdminCtoEvent reads `is_holder_reward` back
from the curve (orig 0x4fe0 `ldxb r5,[r3+0xa5]`). Main (#2964 pool-CPI holder from the curve, event holder from
the local) has exactly the opposite pair. Restoring the original pair costs size and ratio on every main tried:

| main | variant | bytes | ratio |
| --- | --- | ---: | ---: |
| 1043a51 (0.53206) | pool holder local (`pool_hlocal`) | 27,432 | 0.53024 |
| | event holder from curve (`ev_hr_curve2`) | 27,392 | 0.53064 |
| | both + `sk_inline` (size companion) | 27,400 | 0.53056 |
| | pool local + `sk_inline` + `cb_rev_back` | 27,400 | 0.53146 |

So the pair is not the binding residual on its own; it only pays once the holder is a phi-of-constants value
(the original's [-0x950] slot), which no tree spelling gives (`t_hphi`, per-arm literal holder: byte-identical).

**Final emit_cpi!(e) slot order.** Inside region 3 the 16 B event signer array (orig [-0x488], also the sweep vsigner
and wallet signer group) and the 24 B `ix_data` Vec (orig [-0x470], from_iter sret) are swapped in ours
(`framemap.py`: -0x488 -> -0x468 x7, -0x470/-0x468/-0x460 -> -0x488/-0x480/-0x478). Expanding the macro by hand
(`fe_exp0`) is byte-identical to `emit_cpi!`; a deferred-init declaration of `authority_info`, `inner_data` at any
of 5 positions is byte-identical (declaration position does not move a MIR local's alloca); hoisting the signer
array, `ix_data` or `ix` changes the frame but loses on every main (best 0.53056 vs 0.53206).

**Byte-identical (no-op) region-3 spellings:** curve store order (`q_curve_order`, `v6_ofirst*`, `v6_hr2`),
`curve_flat`, `su_none_first`, `pool_nested`, `pool_owner_deref`, `pool_match_cpi`, `sweep_dest_tuple`,
`sweep_keys_eq`, `s7_ammif`, `sweep_660_match`, `m_oldbump`, `n_vsig_arr`, `sweep_gate_unwrap_default`,
the sharing CPI as `#[inline(always)]` nested fn (`sh_fn_ia`). A plain nested fn (`sh_fn`) is -32 B, -0.0018.

**Size knobs measured on 1043a51 (0.53206):** `sk_inline` -24 B 0.53229, `ev_reset_local` -8 B 0.53184,
`cb_rev_back` -8 B 0.53154, `ev_reset_local+cb_rev_back` -16 B 0.53221, `pool_hlocal` +32 B 0.53024.

## Later mains (1043a51 0.53206, c8e30b0 0.55872)

- **High-index locals via `Ok::<_,Error>(x)?`** (the w13a16 e32late mechanism) on region-3 values are all
  byte-identical on 1043a51: the sharing CPI `val` in its arm (`vh_arm`) or the whole `sharing_update` before the
  match (`vh_su`), `(old_creator,old_fee)` and `old_creator` after the curve block (`oc_hi`, `oc_hi1`), `swept`
  (`sw_hi`). Wrapping the event literal (`ev_hi`) is +72 B / 0.47928; `target` before the pool CPI collapses (0.31029).
- **Temporary-creation order in the final `emit_cpi!(e)`** (the w13a23 wallet mechanism), on c8e30b0 (0.55872):
  block-wrapped `invoke_signed` result (`f_wrap`), block-valued `ix_data` / `ix` (`f_ixd_wrap`, `f_ix_wrap`,
  `f_ixd_then_wrap`) are byte-identical; a named signer array at any position is 0.55722; wrapping the whole body
  is 0.55452. `let res;res={invoke_signed(..)};res.map_err(..)?` is **-296 B** (27,104 B, 0.55099): a large size
  lever if some other change needs that much room.
- On c8e30b0 the signer/ix_data slot swap above is already fixed (other lanes' frame changes). Region 3 is
  911/1117 exact; the remaining R3 frame residual is (a) RA spill slots (accounts pointer -0x8d8 -> -0x8f0 x9,
  holder phi -0x950 -> -0x908 x8, -0x910 -> -0x920 x4) and (b) a uniform +8 B shift of every object from orig
  -0x500 to -0x8c0 (about 60 accesses, about 20 of them in region 3), caused by the 0x440..0x500 band being laid
  out differently (ours has a 7 B piece at -0x52d/-0x530 and no objects at -0x478/-0x4c0 where the original has them).
- Library single-gene screen on 1043a51 (curve/fee/pool/event/sweep/vsigner genes, 40 builds): none above main;
  byte-identical ones are listed in the ledger rows `0x22a10-w13-1043a51-r3-*`.
