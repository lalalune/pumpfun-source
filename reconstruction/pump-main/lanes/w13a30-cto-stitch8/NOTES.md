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

| metric | main d81d0f588 | this composite |
| --- | ---: | ---: |
| admin_cto bytes | 27,400 | 27,400 |
| ratio | 0.57100 | **0.57160** |
| slots_diff | 3,312 | 3,313 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 |
| gains / losses | | 0 / 0 |
| runtime differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `82c583a1832f785df88e841526f4e4b90a0b982db7d00164f849c8e56ce7a869` |

Ledger: approach `stitch-composite`, keys `0x22a10-w13-stitch8-<variant>-v1`.

## Single-gene screens (bytes / ratio)

On the clonefeat head (0.56741): `t_cus` (skip tree as `(collect_old,sharing_update,skip)`) 27,384 / 0.56758;
`e_reset` 27,392 / 0.56719; `f_iflet` 27,416 / 0.55286; `f_letelse` (w13a05 `let Some(f)=fee else{return Ok(target)};`)
27,344 / 0.51102; `e_hr_curve` 27,392 / 0.56689; `e_cb_local` 27,408 / 0.56492; `w_tf_prog` (w13a09 transfer-CPI
program let) 27,368 / 0.56445; `ok_hold` (w13a16 holder-in-Ok) 27,368 / 0.54976; `x_t4` (w13a23 anchor-literal emit_cpi)
27,400 / 0.51288.

On main d81d0f588 (0.57100): `t_cus` 27,384 / 0.57117; `e_reset` 27,392 / 0.57079; `e_hr_curve` 27,392 / 0.57049;
`u_sof3` 27,408 / 0.55474.

## Review against the later transfer-clone source

The cashback tuple and scalar bump changes were rebuilt together with the revised
#3051 transfer-CPI clone source. This composition measures 0.59197 at 27,400 bytes,
with 3,312 positional differing 8-byte slots. The revised #3051 alone measures
0.59137 and 3,311 slots. Both retain 1,034/1,035 raw and normalized exact windows;
no new exact window is claimed. The increase is in partial sequence alignment.

## Landing record

#3049 (`ok_cb` + scalar bump) did not go through `land.py`. The first land.py run hit a `programs/` conflict after
6968c841d. The second found the PR closed: the codex pass64 merge (cb0a19e87) had already taken commit 3caa0b077 into
main. Main a6412c208 carries both genes (0.59197 with the codex transfer-clone work).

## Skip-first sweep-tuple orders: the strongest structural lead, still unpaired (bytes / ratio)

The inner skip-tree tuple `(sharing_update,collect_old,skip)` written skip-first (`t_scu` = `(skip,collect_old,sharing_update)`)
or with skip in the middle (`t_usc` = `(sharing_update,skip,collect_old)`, `t_suc`) gains on every main measured. It is the
w13a08 sweepphi-9 lead, and its size cost has shrunk from -72..-88 B to -40..-56 B:

| main (ratio) | t_scu | t_usc / t_suc | t_cus | t_csu |
| --- | ---: | ---: | ---: | ---: |
| dfc3693d8 (0.59916) | 27,344 / **0.60669** | 27,360 / **0.60621** | 27,384 / 0.59964 | 27,384 / 0.59964 |
| 16c10e631 (0.62043) | 27,344 / **0.62828** | 27,360 / **0.62779** | 27,384 / 0.62092 | |

On 16c10e631 `e_reset` and `u_sand` are both 27,392 / 0.62022.

No +40/+56 B companion keeps the gain:
- Source knobs (on dfc3693d8): `e_cb_local` +8 B (0.59668), `c_fee_unwrap` +8 B (0.59697) and `f_iflet` +16 B do not add up on
  the usc base. usc + cb + fee_unwrap + iflet is 27,384 / 0.58885, and + `u_sof3` is 27,360 / 0.57173 (scu: 27,344 / 0.5731).
- Clone field moves (`segscan.py` on the usc IR, 228 single moves): only one reaches 27,400 B (`c6:k2`, 0.57849); every
  other move keeps 27,360 B.

## Knob deltas on dfc3693d8 (0.59916), single genes (`tools/genes30.py`)

-8 B: `e_reset` 0.59895, `u_sand` 0.59895, `e_hr_curve` 0.59865. -16 B: `t_cus` / `t_csu` 0.59964 (+0.0005). +8 B: `e_cb_local`
0.59668, `c_fee_unwrap` 0.59697. -32 B: `w_tf_prog` 0.59712. -40 B: `z_o_pf` (owner-early pump_fees ctx clone) 0.58972.
Byte-identical to main at 27,400: `p_prog_let`, `o_skip_first`, `o_su_first`, `o_target_first`, `k_okcb_co`/`skip`/`cfirst`/`mid`.
Lower at 27,400: `s_pbump` 0.59646, `x_einfo_inline` 0.58957 (on a6412c2).

On a6412c208 (0.59197) the fieldscan pair O3071+K3245 (sharing ctx `pump_fees` clone owner-early + sharing `mint` clone
key-late) built as source equals the oracle exactly: 27,400 / 0.59646. Main had already moved to dfc3693d8 (0.59916, codex
1d314d10d rewrote the same sharing clones), so it was not proposed.

## Oracle: `tools/segscan.py` (clone field segments, llc, about 2 s per edit)

Every AccountInfo clone in execute (inlined `clone()` or hand-written literal) has two Rc increments. A plain field (key, owner,
rent_epoch, is_signer, is_writable, executable) is loaded before the first Rc (S0), between the two (S1) or after both (S2).
`segscan.py scan <mod.ll> <out> [--moves ..]` tries every single move `c<i>:<f><seg>`. `greedy` climbs at 27,400 B, and
`list` prints each clone's current literal order (letters k l d o r s w e). The source form of a result is the literal with that order.
It uses w13a21's `ctoracle.py` (`CTORACLE_DIR`), and the IR comes from `tools/cap.sh` (capture build + trim).
It finds 19 clones in execute on dfc3693d8: the 11 transfer-CPI clones and the 8 sharing-CPI clones. The pool CPI and the wallet
clones are not in execute's IR.

On dfc3693d8, 228 single moves give one gain at 27,400 B: `c0:r0` (transfer-CPI ctx `pump_amm` clone, rent_epoch before
lamports) at 0.59946 (+0.0003). The best off-size move is `c1:o1` (system_program clone, owner between the Rc's) at
27,392 / 0.60015. On the cus base it is 27,376 / 0.60093, and no move repays the 24 B. Codex's permutation search has
already left the field orders at a local optimum: 71 of the 228 moves are byte-identical.
