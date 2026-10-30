# Lane w13a11-cto-stitch (wave 13)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: integrator/stitcher. Collect unlanded admin_cto source genes from w12/w13 lanes, combine compatible
edits on latest main at exactly 27,400 B, and land zero-loss composites through `land.py`.
Base: main 3912c47ac (programs/ identical on origin/main 5d597ce7a): 27,400 B, ratio 0.48772, slots 3,273.

Tooling (not in git, `~/.cache/.../lanes/w13a11-cto-stitch/tools`): w12a04-cto-k4size's `genes.py`/`run.py`
(queue runner, fastbuild + target_metric, two builds max) with `genes13.py` adding w12a07-cto-sweepthread's
source genes. Every gene keeps the newline count, so every error/require site keeps its `line!()`.

## Composite 1 (this PR): skip flag + vsigner + bump-first + reset early

| metric | main 3912c47ac | this lane | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,400 | **27,400** | 27,400 |
| ratio | 0.48772 | **0.48922** | 1 |
| slots_diff (positional) | 3,273 | 3,303 | 0 |
| calls | 154+3 | 154+3 | 154+3 |
| normalized / raw | 1034 / 1034 | 1034 / 1034 | 1035 |
| losses (norm / raw) | | 0 / 0 | |
| runtime differential | | 363/363 | |

Unstripped sha256 `4fc952ce8efbf4aa8d30036222f6d7c0a94363a6cb1739a09ccfdc50b975354a`.

Genes (source of each):
- `st_skip` (w12a07-cto-sweepthread `skiptree`): the sharing tree yields a `skip` flag as a phi of constants
  (`false` only in the shared+holder arm) and the sweep gate is `(!skip).then(..)`; the original gates the sweep
  on such a flag.
- `st_vsig` (w12a07 `vsig`): `let vsigner:&[&[&[u8]];1]=&[vaultseeds];` once, shared by both sweep transfers.
  These two alone: 27,440 / 0.49065 (+40 B).
- `st_bo` (w12a07 `bumpold`): `let bump=..;let old=..;` order: -32 B (27,408 / 0.48944).
- `h_reset_early` (w12a04-cto-k4size step 4): `let reset=sharing_update.is_some();` before the pool signer
  seeds, used by the event: alone on main 27,392 / 0.48869; here it takes the composite to 27,400.

## Compose / conflict table (measured on main 3912c47ac; bytes / ratio)

| variant | bytes | ratio | note |
| --- | ---: | ---: | --- |
| main | 27,400 | 0.48772 | |
| h_reset_early | 27,392 | 0.48869 | |
| h_ev_cb_global (event `is_cashback_coin` from the curve) | 27,384 | 0.48906 | |
| w_cp_inline (wallet `coin_present` bound inside `do_coin`) | 27,416 | 0.48997 | calls 155+3 |
| st_skip + st_vsig | 27,440 | 0.49065 | |
| + st_bo | 27,408 | 0.48944 | |
| + st_bo + h_reset_early | **27,400** | **0.48922** | composes: landed candidate |
| + st_rl + st_bo | 27,392 | 0.48929 | |
| + st_rl + st_bo + h_reset_early + h_fee_iflet | 27,400 | 0.48742 | fee_iflet conflicts with reset here |
