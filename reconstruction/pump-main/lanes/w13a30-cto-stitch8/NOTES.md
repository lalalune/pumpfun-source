# Lane w13a30-cto-stitch8 (wave 13)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: integrator/stitcher, continuing w13a11-cto-stitch (#3008, compose/conflict tables). Screen a gene catalog
(`genes30.py`, 75 newline-preserving source genes keyed on the current main) on each new main, then pair genes.

## Composite 1: cashback carried through the `Ok(..)?` tuple + scalar creator-vault bump

Both genes are from earlier lanes and never landed together:
- `ok_cb` (w13a16-cto-e32late, 0.53235 on 1043a51): `let (target,sharing_update,cashback)=Ok::<_,Error>((target,sharing_update,cashback))?;`
- `w_bump_scalar` (w13a09-cto-cpiclone / w12a14 `seeds_bump_inline_b`): `let bump=ctx.bumps.creator_vault;..&[bump]` in the sweep's vault seeds.

| variant (base) | bytes | ratio |
| --- | ---: | ---: |
| w13a21 clonefeat head (6ac6f9b67 + #3019) | 27,400 | 0.56741 |
| + ok_cb | 27,400 | 0.56771 |
| + w_bump_scalar | 27,400 | 0.56771 |
| main d81d0f588 (#3019 + ace828359) | 27,400 | 0.57100 |
| + ok_cb | 27,400 | 0.57130 |
| + w_bump_scalar | 27,400 | 0.57130 |
| **+ ok_cb + w_bump_scalar** | **27,400** | **0.57160** |

| main 06e6bb829 (+ 6968c841d transfer-CPI system clone) | 27,400 | 0.57669 |
| **+ ok_cb + w_bump_scalar** | **27,400** | **0.57729** |

| metric | main 06e6bb829 | this composite |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| ratio | 0.57669 | **0.57729** |
| slots_diff | 3,312 | 3,313 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 |
| gains / losses | | 0 / 0 |
| runtime differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `d6fd5e60b6421c074ff2246841745d89b2bea21f7e86d88d60ed4dcd927b4547` |

(On d81d0f588 the same pair was 0.57100 -> 0.57160, sha `82c583a1832f785d...`.)

Ledger: approach `stitch-composite`, keys `0x22a10-w13-stitch8-<variant>-v1`.

## Single-gene screens (bytes / ratio)

On the clonefeat head (0.56741): `t_cus` (skip tree as `(collect_old,sharing_update,skip)`) 27,384 / 0.56758;
`e_reset` 27,392 / 0.56719; `f_iflet` 27,416 / 0.55286; `f_letelse` (w13a05 `let Some(f)=fee else{return Ok(target)};`)
27,344 / 0.51102; `e_hr_curve` 27,392 / 0.56689; `e_cb_local` 27,408 / 0.56492; `w_tf_prog` (w13a09 transfer-CPI
program let) 27,368 / 0.56445; `ok_hold` (w13a16 holder-in-Ok) 27,368 / 0.54976; `x_t4` (w13a23 anchor-literal emit_cpi)
27,400 / 0.51288.

On main d81d0f588 (0.57100): `t_cus` 27,384 / 0.57117; `e_reset` 27,392 / 0.57079; `e_hr_curve` 27,392 / 0.57049;
`u_sof3` 27,408 / 0.55474.

On the d81 composite: `ok_cb` plus `holder` in the tuple 27,360 / 0.55464; plus `collect_old` or `skip` byte-identical
ratio 0.5716 (27,400). `w_vsig_ref` (revert of ace828359's deferred `vsigner`) 27,400 / 0.5698; `vsigner` declared
after `bump` or after `old` = main (0.571).
