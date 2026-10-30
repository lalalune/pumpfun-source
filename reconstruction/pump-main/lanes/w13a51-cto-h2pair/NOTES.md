# w13a51-cto-h2pair (wave 13, continued in wave 14)

Target `0x22a10` `admin_cto::execute`, pinned 27,400 B. Base main 53abf28b1 (0.62672 / 3,305 slots).

## Result

`0.62672 -> 0.62753` at 27,400 B, 1034/1034 normalized/raw, 0 losses (measure.sh, sha 912090fb8be7561b).

Composite of same-semantics spellings (newline counts unchanged, every `line!()` site kept):

| gene | source | alone on 53abf28 (raw-IR oracle) |
| --- | --- | --- |
| `scu_bs`: skip-first inner tuple `(skip,collect_old,sharing_update)` + `args=&(new,)` before `CtoState` | w13a46-cto-scugap (n3_scu_bs) | 0.62918 / 27,344 |
| `s_rent_local`: `let rent=Rent::get()?;let min=rent.minimum_balance(0);` | w13a19 | 0.62691 / 27,384 |
| `o_ab_late`: execute's `emit_cpi!` hand-expanded, `authority_bump` read after `ix` | w13a19 | 0.62601 / 27,384 |
| `pu_amm_keyfn`: `*a.pool.owner==a.pump_amm.key()` (pump_amm is `Program<PumpAmm>`, so same check) | w13a34 catalog | filler, +80 B |
| `L_fee_unwrap_again`: `curve.creator_fee_bps=fee.unwrap_or(old_fee)` | catalog | filler, +8 B |

Oracle chain on 53abf28: o_ab_late+s_rent_local 0.6274/27,368; + scu_bs 0.63016/27,312 (additive);
+ pu_amm_keyfn 0.62852/27,392; + fee unwrap 0.62753/27,400. Better +8 B partners are the open lever
(0.62852 at -8 B is the ceiling of this stack).

## The h2pair angle itself (dead on 53abf28)

w13a38's h2 (validate `ho:&mut bool` holder phi, holder-first curve stores, pool holder local) no longer gains:

| variant | ratio | bytes | fm | rm |
| --- | ---: | ---: | ---: | ---: |
| main | 0.62672 | 27,400 | 0.72169 | 0.84991 |
| h2 | 0.60232 | 27,200 | 0.7214 | 0.8528 |
| h2 + holder_key by value (w13a33 v1) | 0.5348 | 27,096 | 0.69027 | 0.82103 |
| holder_key by value alone | 0.54976 | 27,368 | 0.69784 | 0.81865 |
| store swap only | 0.62253 | 27,400 | 0.7175 | 0.85021 |
| ho phi only | 0.59375 | 27,240 | 0.71484 | 0.85216 |
| pool holder local only | 0.62405 | 27,424 | 0.72017 | 0.84923 |
| phi used only for pool arg / curve store / event | 0.568 / 0.577 / 0.570 | 27,400 / 27,328 / 27,416 | | |

w13a43 v2 outline shrinks execute by 432 B on this main (not +248), so it is no code-adding partner.
Fillers that do NOT compose with o_ab_late+s_rent_local: ev_nf_pre / ev_cb_pre + fee unwrap (0.62522),
w_ev_creator_first + ev_* (0.62493), w_ev_creator_first + pool holder local (0.62403).

Tools (out dir): `tools/capvar.sh` (crate copy + EDITS -> raw IR -> opt/llc oracle, exact on main),
`tools/capfile.sh` (same from a full admin_cto.rs), `tools/comp.py` (compose catalog knobs).
