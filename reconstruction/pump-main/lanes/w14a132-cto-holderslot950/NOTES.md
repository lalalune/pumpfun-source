# w14a132-cto-holderslot950: one per-arm holder value for the curve store and the pool CPI (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute`, pinned at 27,400 B. Base: main ebe5387 (0.67316, 3,123 slots, M 2,247).
Ledger: approach `holderslot950`, keys `0x22a10-w14-ebe5387-holderslot950-*`.

**Result: notes only. The angle is dead.** The IR bound is below main. The RA and frame bounds (`fbound.py` fR/rfR/rfjR) are below main too. Following step 2 of the angle, no source forms were tried.

## Original mechanism (or.dis)

The holder value sits in the 8-byte slot `[r10-0x950]`, as a phi of constants spilled per arm:
- validate exits store 0 at 0xe40, 1 at 0x1130, 0 at 0x14e0, and r6 at 0x1830 and 0x18b0;
- the post-sweep join reads it at 0x4a98, before `jne r7,2`;
- the curve store reads it at 0x4b60 (+0xa5), and the pool CPI reads it as r4 at 0x4e20.

## IR oracle

The oracle edits main's post-opt `m.ll` (the w14a107 rx capture, `eq_main` true) and runs it through llc. Edits are in `edits/`.
- `hphi`: `%hph54 = phi [0 bb52.i],[1 bb95.i]` at bb54.i, and `%hph = phi [0 bb45.i],[%hph54 bb65.i],[1 bb44.i]` at bb75, which is validate's single success exit.
- `hcs` / `hpa`: consumers at the curve store and the pool CPI.
- `hal*`: the same constants stored to one alloca at the arm exits.

| variant | ratio | bytes | M | fR | rfR | rfjR |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| main ebe5387 | 0.67316 | 27,400 | 2,247 | 2,295 | 2,623 | 2,622 |
| phi, curve store + pool CPI | 0.51047 | 27,464 | 1,706 | 1,685 | 1,851 | 2,029 |
| phi, curve store only | 0.51630 | 27,480 | 1,726 | 1,705 | 1,848 | 2,029 |
| phi, pool CPI only | 0.55492 | 27,448 | 1,854 | 2,156 | 2,492 | 2,543 |
| i8 alloca, curve store | 0.50007 | 27,456 | 1,671 | 1,704 | 1,845 | 2,024 |
| i8 alloca, pool CPI | 0.63216 | 27,472 | 2,113 | 2,160 | 2,509 | 2,517 |
| i8 alloca, both | 0.49439 | 27,456 | 1,652 | | | |
| i64 alloca (original stxdw width), any | 0.25-0.27 | 27,456-27,472 | 846-889 | | | |

Why it fails:
- **Curve-store consumer.** Changing the curve-store input from `and %0,1` to a computed value changes post-RA spill code. The post-RA BranchFolding tail merge then fails, and MachineBlockPlacement moves about 6 KB of code (main 0x2548-0x3c38) after the curve store. In main and in the original, that code comes before the store.
  - With `-enable-tail-merge=false`, main and the phi build share the same layout: the curve store is at 0x3858 and 0x3870.
  - At that equal layout, the curve-store phi gains **+21 M** (1,642 vs 1,621).
  - So the per-arm value is right for the original. What blocks it is that only main's RA reproduces the original's tail merge.
- **Pool CPI consumer.** This form loses about 90 M under both layouts.
- **i64 alloca.** It shifts the whole frame.

## Next ideas

- Find which tail pair stops merging in the phi-cs build, for example by diffing `-enable-tail-merge=false` against the default on main to list the merged tails. Then look for an RA-side change that keeps that pair identical.
- If that pair is found, the per-arm curve-store phi is worth about +21 M. Its source form is a `(target, holder_flag)` tuple from validate's arms (the #2766 tuple mechanism). The pool CPI should keep its curve re-read.
