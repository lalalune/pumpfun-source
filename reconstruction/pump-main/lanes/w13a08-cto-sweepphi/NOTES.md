# w13a08-cto-sweepphi (wave 13)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: the sweep gate and the pool-CPI holder as phis (S5/S10 of w12a09-cto-cleanroom).
Base: main 3912c47ac (0.48772, 3,273 slots, 27,400 B, 1034/1034).

## Result on 3912c47ac: skip flag + vsigner + bump before old (skp3_vsig_bo)

Superseded on main by #2885 (w13a11-cto-stitch, 085e5dffb): the same skip tree + vsigner + bump-first composite with
`reset` bound early as the size companion, also 0.48922 at 27,400 B. This branch now carries notes only.

| build | bytes | ratio | slots_diff | normalized / raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 3912c47ac | 27,400 | 0.48772 | 3,273 | 1034 / 1034 | - |
| skp3_vsig_bo | 27,400 | **0.48922** | 3,302 | 1034 / 1034 | 0 / 0 |

Unstripped sha256 prefix `dd82adee23d07217`. Runtime differential: 363 cases, 0 mismatches.

Three source changes, each keeps every line:
1. The sharing tree also yields the sweep **skip flag** as a phi of constants, in the original's
   order (skip, collect_old, sharing_update): `(false,false,Some(None))` shared+holder,
   `(true,false,Some(new))` shared+!holder, `(true,collect_old,None)` !shared. The sweep is gated with
   `(!skip).then(||sweep(..)).transpose()?.unwrap_or(0)`. The original's gate is one test of a spilled
   phi-of-constants flag (orig 0x1d38 `ldxdw r1,[r10-0x8e0]; jne r1,0`); main tested `shared&&holder` with two compares.
2. **vsigner hoist**: `let vsigner:&[&[&[u8]];1]=&[vaultseeds];` bound once and passed to both sweep transfers
   (the original stores the `{ptr,3}` signer element at seeds time).
3. `let bump=[..];let old=..;` (bump before old) in the sweep seeds: the size companion that brings 1+2
   (+32 B) back to 27,400 B.

The skip tree alone collapses the layout (post-sweep chain moves to the end, w12a07); with vsigner it holds.

## Trials on main 3912c47ac (measure.sh)

| variant | bytes | ratio | note |
| --- | ---: | ---: | --- |
| skip_vsig (tuple order sharing,collect,skip) | 27,440 | 0.49065 | best ratio, +40 B |
| skip_vsig_rl (+ Rent local) | 27,424 | 0.49049 | |
| skp3_vsig (order skip,collect,sharing) | 27,432 | 0.49042 | |
| skp3_vsig_rl | 27,416 | 0.49027 | |
| skip_vsig_bo | 27,408 | 0.48944 | |
| **skp3_vsig_bo** | **27,400** | **0.48922** | landable |
| skip_vsig_rl_bo | 27,392 | 0.48929 | |
| skip_vsig_mv / skp3_vsig_mv (Rent local inside saturating_sub) | 27,424 / 27,416 | 0.48780 / 0.48757 | |
| skiph_vsig (tree also rebinds holder; !shared arm passes holder) | 27,440 | 0.49065 | byte-identical to skip_vsig |
| dotree_vsig (positive sweep_on flag) | 27,440 | 0.49065 | byte-identical to skip_vsig |
| svb_ik (+ split 312 check) | 27,400 | 0.47438 | 157 calls |
| svb_shn / svb_stql | 27,408 | 0.48944 | byte-neutral knobs |
| svrb_vnm / svrb_fu | 27,392 | 0.48869 / 0.48809 | |
| sv_ff (frozen first) | 27,488 | 0.40556 | layout collapse |

Ledger approach `sweepphi`, keys `0x22a10-w13-3912c47-*`. Tools: w12a07-cto-sweepthread's capir/extract/orc oracle,
re-pathed to this lane's out dir (scratch only).
