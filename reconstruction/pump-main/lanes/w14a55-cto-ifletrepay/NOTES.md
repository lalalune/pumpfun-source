# w14a55-cto-ifletrepay: s_iflet paid back inside the sharing CPI

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main 63308119b (0.65698, 3,193 slots, M 2,193). Ledger approach `ifletrepay`, keys `0x22a10-w14-6330811-ifletrepay-*-v1`.
Continues w14a34-cto-curvetail (#3338) next idea 1.

## Result (landable: same ratio, 11 fewer slots)

| | main 6330811 | this branch |
| --- | ---: | ---: |
| admin_cto ratio | 0.65698 | 0.65698 (M 2,193 = 2,193) |
| slots_diff | 3,193 | **3,182** |
| bytes | 27,400 | 27,400 |
| normalized / raw | 1034 / 1034 | 1034 / 1034, 0 losses |
| differential | | 363 cases, 0 mismatches |
| unstripped sha256 | | `1aa5bedc0fe94b7e81a6af40d9b1020eaa0af62853333644629d8ffc8592148b` |

land.py ranks admin_cto by (size, -ratio, slots), so an equal ratio with fewer slots counts as closer.

## Change

1. s_iflet: `match sharing_update{Some(val)=>{..}None=>{}}` becomes `if let Some(val)=sharing_update{..}`. This gives the
   original's single `jne r7,2` CPI-return branch after `admin_cto_sharing_config` (main had `jeq r7,2,+1; ja`), -8 B.
2. Paid back with +8 B inside the sharing CPI clone run (where ours is 9 instructions shorter than the original):
   the pool_authority literal reads `rent_epoch:a.pool_authority.rent_epoch` through the account path instead of `x`.
   The read comes after the two Rc stores, so the AccountInfo pointer is re-loaded (the original reloads per clone).

## Screens (all on 6330811, s_iflet base 0.65678 @27,392, M 2,192)

| family | count | best +8 B partner (27,400) | result |
| --- | ---: | --- | --- |
| pscan `place` (729 each) on 7 sharing clones (ctx program, pool_authority, authority, global, mint, sharing_config, program literal) | 5,103 | authority 120002 0.65339; global 221011 0.65099; sharing_config 222021 0.64769 | far below main |
| pscan `pp` at current and top-6 +8 B placements | ~1,000 | 0.65339 | below |
| re-read singles (field read via the account path after the Rc stores) | 56 | pool_authority rent 2,193 / 3,182 slots; program-literal data 2,193 / 3,191 | **tie M, fewer slots** |
| re-read pairs | 1,540 | 46 variants at M 2,193; best slots 3,182 (all contain pool_authority rent) | no M gain |

- Re-reads placed before the Rc stores are CSEd (no change). Only reads after a store give +8 B.
- The s_iflet loss on 6330811 is pure jump distance (segdiff: -1 in segs 55/135/145/156, +1 in 11/12/67; seg 72 is unchanged).
  The re-read partner restores the per-segment match counts exactly (segdiff delta 0 in every segment).
- Source forms reproduce the IR oracle byte for byte (`sx_rent` = IR `%x:rent`, `sx_pdata` = IR `%x21:data`).

## Tools (`tools/`, experiment only)

- `reread.py <mn.ll> <out.jsonl> X... [--pairs]` (JOBS=file for listed combos): post-opt re-read oracle for x-bound
  AccountInfo literals. `rrdump.py` writes one variant's m.ll / fn.bin. Needs w14a34's `rx.py` next to it.
- `mcount.py` (M per fn.bin), `drift.py` (orig->cand offset drift), `fl.py` (raw listing of fn.bin), `psum.py` (pscan summary).
