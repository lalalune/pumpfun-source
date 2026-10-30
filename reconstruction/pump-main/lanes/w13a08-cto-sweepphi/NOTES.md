# admin_cto: curve field access order

This candidate changes two lines in `programs/pump/src/creator/admin_cto.rs`.
After assigning the creator, it reads the old creator fee, stores the holder flag,
and then stores the cashback flag. These are ordinary accesses to distinct fields;
there is no intervening fallible operation, CPI, serialization or account reload.
The final values and the saved old fee are unchanged. All 24 macro call sites
remain on their original lines.

## Verified measurements

The baseline source inventory is
`5571f6efadb7003d11becbf574ca1c21c369423f91883c1d4b3e60959d709832`,
verified against main `f4d156d70dec49c67a6e5bffef68379e695f5517`.
A fresh identity build of this candidate produced:

| Measure | Baseline | Candidate |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| Sequence diagnostic ratio | 0.49101 | 0.49131 |
| Differing normalized instruction slots | 3,280 | 3,280 |
| Raw / normalized matched windows | 1,034 / 1,034 | 1,034 / 1,034 |

The official inventory contains 1,035 windows. There are no missing or resized
windows and no lost raw or normalized matches. This is a partial-window sequence
improvement; the matched-window completion percentage does not change.

All 363 signed admin_cto differential cases matched the captured program using
genuine dependency CPIs. This is bounded runtime evidence, not whole-program
semantic equivalence or whole-ELF identity.

Candidate source inventory:
`d44d67269eb5ab2aaa962a2497a6552bb53254a6bb33bd0015f5d8103b62a4c0`.
Unstripped ELF: `3b87f921556f0d99afd6143641b42866489ed3e6a3006b5856b0506421053ce1`.
Runtime ELF: `f60dc66a2ee354d6a1ff98175ff74660ab80ce25573184a5dd8e60f555137286`.

Validation used `reconstruction/harness/fastbuild.py` (identity recipe), `score.py`,
`compare_scores.py`, `target_metric.py` and `scripts/pump_admin_cto_differential.py`.

## S10: pool-CPI holder read back from the curve (hrb)

The original passes `holder` to `admin_cto_pool` with one `ldxdw r4,[r10-0x950]` right before the call (orig +0x4e20).
Ours re-derived it at the call with `(x&-3)!=0` as a 3-insn select (`mov r4,1; jne; mov r4,0`): CodeGenPrepare sinks the
holder `icmp` into every use. Passing `a.bonding_curve.is_holder_reward` (the field just stored) gives the call a
plain load, as in the original:

| base | hrb | + companions |
| --- | --- | --- |
| main 9eb6c00 (0.49131) | 27,360 / 0.49288 | + old-before-bump + Rent inline + reset early: 27,400 / **0.49431** (slots 3,167) |
| main 1f1a717 (0.49431) | 27,360 / 0.49408 | + old-before-bump + Rent inline: 27,400 / **0.49611** (0 losses) |
| main 8f050a2 (0.50929) | 27,368 / 0.51079 | old-before-bump is now byte-neutral; + `&Rent` ref 27,352 / 0.51094 |
| main 74b3171 (0.51348) | 27,368 / 0.51469 | (companion screen running) |

A `let holder=a.bonding_curve.is_holder_reward;` rebinding before the pool test is weaker (27,392 / 0.49109 on 9eb6c00).

### Skip-tree tuple order is base-sensitive

On main 8f050a2 (0.50929) the skip-first orders were a large win at a large size cost: `(skip,collect_old,sharing_update)`
27,312 B / 0.51883, `(skip,sharing_update,collect_old)` and `(sharing_update,skip,collect_old)` 27,328 B / 0.51837,
collect-first orders 27,384 B / 0.50944. With hrb: 27,280 / 0.51854. Companions measured on scu: CollectCreatorFeeEvent
creator-first +64 B (0.51461), reset late +8 B (0.51785), holder_key first +120 B (0.49491), dropping vsigner collapses (0.420).
On main 74b3171 (stitch-5: args before CtoState) the same orders collapse to 0.3865 at 27,392 B.

## Landable on main f7ce2e34 (pfclimb-5, 0.51378): hrb + two +B companions

| build | bytes | ratio | slots_diff | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main f7ce2e34 | 27,400 | 0.51378 | - | 1034 / 1034 | - |
| hrb + `cashback=st.cashback&&!holder` + `let sk=a.sharing_config.key();` before validate | 27,400 | **0.51408** | 3,327 | 1034 / 1034 | 0 / 0 |

Unstripped sha256 prefix `60eeb1759fa3b924`; differential 363/0. hrb alone is 27,368 / 0.51439 here; the two companions are
+8 B (cashback operand order) and +24 B (sharing key bound once before validate, as w13a13 measured).

Other trials on 74b3171 / f7ce2e34:
- `#2766` tuple carry: the curve block yields `curve.is_holder_reward` (read back after the store) and the pool CPI takes it:
  27,400 / 0.51408 on 74b3171 (0 losses), but byte-equal to main once pfclimb-5 moved the old-fee read first (0.51378 on f7ce2e34).
  Carrying plain `holder` through the tuple is byte-identical to main.
- IR oracle (hrb IR, 74b3171): the original's gate polarity (`br skip, post, sweep`, orig `jne skip,0 -> post`) alone collapses
  the layout exactly like the if-gate source (0.38165). A 2000:1 weight scan over all 147 branches on that IR finds at best
  0.512 (collect_old `!holder_reward` test 1:2000), so the gate polarity does not pay off without a different validate layout.

## Reviewed composition with wallet-event signer layout

Composed with current main after #2961 before building. The primary instruction-token
ratio remains **0.51857**, while positional differing 8-byte slots improve from
**3,335 to 3,327** in the original-sized 27,400-byte window. The raw and normalized
exact-window totals remain 1,034/1,035, with no missing, resized or lost windows.
All 363 signed admin comparisons and 408 one-hop swap/boundary comparisons pass.
The latter disable AMM PDA signature verification; this is bounded runtime evidence,
not a whole-program identity or all-input equivalence proof.

## Landable on main 2f268ad (0.51857): skip tree in (collect_old, skip, sharing_update) order

| build | bytes | ratio | slots_diff | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 2f268ad | 27,400 | 0.51857 | 3,335 | 1034 / 1034 | - |
| csu + pool holder from `holder` + `reset` local + `!holder&&st.cashback` | 27,400 | **0.51887** | 3,326 | 1034 / 1034 | 0 / 0 |

Unstripped sha256 prefix `0c691d9e7175e5ae`; differential 363/0. Tuple orders on this main: (skip,collect,sharing) 27,312 / 0.52183,
(skip,sharing,collect) and (sharing,skip,collect) 27,328 / 0.52197, (collect,skip,sharing) 27,384 / 0.51963. Only csu has a
cheap +16 B companion: the pool CPI takes `holder` again (+32 B here), and `reset` / the cashback operand order give -8 B each.
The skip-first orders still need +72..+88 B; `CollectCreatorFeeEvent` creator-first + fee unwrap store reach 27,400 but at 0.51528.
