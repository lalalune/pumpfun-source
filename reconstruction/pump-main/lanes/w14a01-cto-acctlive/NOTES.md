# w14a01-cto-acctlive: live range of the `ctx.accounts` pointer in admin_cto::execute

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 53abf28b1 (0.62672, 3,305 slots), 23322b07c (0.62882, #3200), 308b545f1 (0.63062, #3207) and 769f331fe
(0.63241, #3215).
Angle: continues w13a44 next_idea 2, w13a33 next_idea 1, w13a35 next_idea 1 and w13a45's register finding.
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w14a01-cto-acctlive/` (not in git).

No source change is proposed. This PR holds the reload map, the probe oracle and the source-form screen.

**Result.** No source form found raises the ratio. Source forms that produce per-clone `[r10-X]` reloads of the
accounts pointer in the sharing CPI (clonefeat: original 6/2, main 2/6; stack reloads: original 537, main 505-506;
tag==2 tests on r7: original 21, main 18):

| form | clonefeat | stack reloads | tag==2 on r7 | size delta | ratio vs main |
| --- | --- | ---: | ---: | ---: | ---: |
| `let accs=AdminCtoSharingConfig{..}` before the CpiContext (program clone evaluated last) | 3/5 | 504 | 18 | -80 B | -0.026 |
| sharing CPI in `#[inline(always)] fn share(&AdminCto,seeds,val)` | 3/4 | 503 | 18 | -64 B | -0.034 |
| sharing CPI as `CpiContext::new(..).with_signer(seeds)` | 3/5 | 507 | 18 | +16 B | -0.024 |
| IR probe only: accounts pointer reloaded from an entry slot before each sharing clone | **6/2** | 517 | 18 | +88-96 B | +0.0096 frame-held |

The full 6/2 form needs the register allocator to spill the pointer across the sharing arm. That happens only when the
callee-saved registers hold swept, the sharing tag and pool_updated, as in the original (section 3). Those are the
swept/Err-payload (w13a40/w13a44/w13a49) and holder-phi (w13a38) representations, not accounts-pointer source forms.

## 1. Where the original reloads the accounts pointer

The original spills the accounts pointer once at entry (orig 0x280 `stxdw [r10-0x8d8], r8`). After that it reloads it
32 times and almost always uses each reload once (`tools/` one-off scan, see the table). Main (`[r10-0x8e0]`) reloads it 19
times and keeps it in r5/r8 across whole regions.

| region | original reload sites (fn offsets) | main 23322b0 |
| --- | --- | --- |
| validate/entry | 0x540 | 0x528 |
| wallet head | 0x1a50, 0x1c90, 0x1d68 | 0x1748, 0x1848, 0x1c98, 0x1d58 |
| wallet AMM collect clones | 0x3128 (5 uses), 0x3218, 0x3330 | 0x3300 only (r8 holds it at 0x30f8-0x31e0) |
| sweep exit | 0x3b80 | 0x3b50 |
| sharing CPI clones | 0x3d88, 0x3e30, 0x3f38, 0x4050, 0x4178, 0x42a0, 0x43c8, 0x44f8 (one per clone) | 0x3d38 once, then r5 for all 8 clones |
| pool CPI / event | 0x4ab8, 0x4c50, 0x4e80, 0x4f38 | 0x4a48, 0x4e40 (kept in r8 for the event) |
| emit_cpi / tail | 0x52e0, 0x59d0, 0x5a70, 0x5c18 .. 0x6878 (10) | 0x5a28, 0x5bd0 .. 0x6878 (9) |

In the event block the original holds the sharing_update tag in r6, pool_updated in r8 and swept in r9, and reloads the
accounts pointer at 0x4f38. Main holds pool_updated in r6, the accounts pointer in r8 and `nf` in r9, and spills the tag and
`swept`. The accounts pointer only gets a register where the original's long-lived small values are spilled.

## 2. The sibling hits are ordinary region reloads

The byte-matched windows that also use `ldxdw rA,[r10-X]; ldxdw rB,[rA+off]` before an AccountInfo clone belong to:

| address | function |
| --- | --- |
| 0x1d008 | `create_v2::mint_supply` |
| 0x34cc8, 0x36198 | `holder_distribution::execute` |
| 0x7f310, 0x7f960 | `trade::check_quote` |
| 0x4d618 | `migrate_v2::create_token_account_v2` |

In each one the accounts pointer is reloaded once at the start of a clone run and then kept in a register (for example
0x34cc8 `ldxdw r5,[r10-0x3a0]; ldxdw r2,[r5+0x38]`, with r5 reused for the next account). None reloads per clone, so they
show no source idiom for the per-clone form. Their source uses plain `ctx.accounts.x.to_account_info()` like ours.

## 3. Oracle: per-clone reloads in the sharing arm are worth about +0.0096 with the frame held

`tools/accprobe.py <m.ll> <out.ll> <lo> <hi> [blk]` edits the post-opt slim module. It stores `%_247` (the accounts
pointer) to a new alloca at entry, then reloads it before every account load in IR lines [lo,hi]. With `blk` it reloads
once per basic block, like an RA reload reused within its block. Scores use w13a35 `fbsplit.py` "all" (perfect frame
remap), because the probe's alloca shifts the frame. The null probe (alloca and store, no reloads) scores 0.59757,
against main's 0.60216. Main 23322b0's module:

| probe region (IR lines of `rx/base1/m.ll`) | loads | clonefeat | bytes | fbsplit all | vs null |
| --- | ---: | --- | ---: | ---: | ---: |
| none (null probe) | 0 | 2/6 | 27,408 | 0.59757 | |
| **sharing arm 5440-5939** | 10 | **6/2** | 27,488 | **0.60715** | **+0.0096** |
| wallet AMM-collect clones 2700-3600 | 5 | 2/6 | 27,368 | 0.59982 | +0.0023 |
| 4900-5200 | 2 | 2/6 | 27,416 | 0.59689 | -0.0007 |
| 5940-6345 (pool CPI, event, emit) | 15 | 2/6 | 27,432 | 0.59461 | -0.0030 |
| 4300-4640 | 9 | 2/6 | 27,472 | 0.58998 | -0.0076 |
| 3600-3900 | 17 | 2/6 | 27,424 | 0.58871 | -0.0089 |
| 5200-5440 (sweep AMM transfer) | 11 | 2/6 | 27,416 | 0.58850 | -0.0091 |
| every load after entry (per use) | 101 | 7/1 | 27,864 | 0.52866 | -0.069 |

The sharing-arm probe reproduces the original's clone addressing exactly (`ldxdw r1,[r10-X]; ldxdw rB,[r1+0x98|0x68|..]`
before each of the 8 clones). It is the only region where spilling the accounts pointer pays. Elsewhere the original
keeps a reload live across several uses in a block (0x3128, 0x4ab8, 0x6010, 0x6130), and forcing more reloads loses.

The llc RA knobs (split-spill-mode, local-reassign, exhaustive search, deferred spilling, eviction cutoff, CSR cost) never
move clonefeat off 2/6.

### Why main keeps the pointer in a register: callee-saved occupancy

The debug-llc trace on 23322b0 (`radbg.sh`, `rsplit.py ra.log 0`) splits %0 into r8 over 94 bundles. In the r8 region,
every sharing-arm block is "live-through, straight through" with no interference ("intf invalid-invalid"), so the arm
stays in the register region. Its first use reloads into r8, and a later eviction moves the piece to r5. The original's
arm is in the stack complement, so it spills everywhere and reloads once per clone.

The tail shows what fills the registers in the original:

| | original (0x4e00-0x5030) | main 23322b0 (0x4de8-0x4ff0) |
| --- | --- | --- |
| r6 | sharing_update tag, reloaded after the sharing call (0x4a90) and kept to the event | pool_updated |
| r7 | CPI Result tag | CPI Result tag |
| r8 | pool_updated | accounts pointer (reloaded once at 0x4e40) |
| r9 | swept (from the sweep exit 0x3c40 to the event store 0x5030) | nf (the #3200 event fee local) |
| accounts | reloaded per use (0x4e80, 0x4f38) | in r8 |

The same holds in the native sweep (orig 0x59b0 `mov64 r9,0` = swept; main spills swept to `[r10-0x968]`). All four
callee-saved registers are taken by long-lived small values in the original, so a pointer live across calls has none.
Main spills swept and the tag, which leaves r8 free for the pointer. This is w13a44's R1 (swept in the Err-payload class,
r9) plus w13a49's finding that the holder phi moves the payload class to r9. The accounts-pointer form follows from those
value representations. It is not a separate source lever.

## 4. Source forms screened (raw-IR capture + rx oracle = build tokens)

Ledger approach `acct-liverange`, keys `0x22a10-w14-{53abf28,23322b0,308b545,769f331}-acctlive-*`.

| form | base | ratio | bytes | clonefeat | stack reloads |
| --- | --- | ---: | ---: | --- | ---: |
| main | 53abf28 | 0.62672 | 27,400 | 2/6 | 505 |
| sharing arm `let a=&ctx.accounts` / `&*ctx.accounts` / `ctx.accounts.x` | 53abf28 | = main | | 2/6 | |
| sharing CPI in `#[inline(always)] fn share(&Context,..)`, pool-arm rebinding | 53abf28 | = main | | 2/6 | |
| sharing CPI: every clone into locals first (program first) | 53abf28 | 0.62350 | 27,368 | 2/6 | 505 |
| sharing CPI: `let accs=AdminCtoSharingConfig{..}` first (program clone last) | 53abf28 | 0.60096 | 27,320 | **3/5** | 504 |
| sharing CPI: `let cpi=CpiContext::new_with_signer(..)` first | 53abf28 | 0.53685 | 27,400 | 2/6 | 505 |
| sharing CPI in `#[inline(always)] fn share(&AdminCto,..)` | 53abf28 | 0.59268 | 27,336 | 3/4 | 503 |
| same as a plain fn | 53abf28 | 0.59124 | 27,304 | 3/4 | 503 |
| signer seeds inline in each CPI | 53abf28 | 0.41525 | 27,712 | 3/5 | 521 |
| signer seeds bound inside the sharing arm | 53abf28 | 0.53632 | 27,640 | 2/6 | 517 |
| wallet takes (&AdminCto, &AdminCtoBumps) | 53abf28 | 0.61154 | 27,496 | 2/6 | 517 |
| sweep takes (&AdminCto, &AdminCtoBumps, holder_key) | 53abf28 | 0.55032 | 27,168 | 2/6 | 503 |
| main | 23322b0 | 0.62882 | 27,400 | 2/6 | 506 |
| `let reset=sharing_update.is_some()` before the sharing match | 23322b0 | 0.62742 | 27,392 | 2/6 | 506 |
| `if let Some(val)=sharing_update` | 23322b0 | 0.62742 | 27,392 | 2/6 | 506 |
| `match &sharing_update{Some(val)=>{let val=*val;..` | 23322b0 | 0.61693 | 27,392 | 2/6 | 505 |
| tail order nf / pool_updated / pargs (4 permutations) | 23322b0 | 0.62624-0.62644 | 27,416-27,424 | 2/6 | 506-507 |
| reset bound early / in a block at the event | 23322b0 | = main | | | |
| accounts struct first at the wallet create_idempotent / AMM collect / sweep create_idempotent / pool CPI | 23322b0 | 0.27-0.54 | 27,400 | 2/6 | 506 |
| same at the sweep AMM transfer | 23322b0 | 0.54406 | 27,368 | 2/6 | 512 |
| locals-first at the to_account_info CPIs (wallet x2, sweep create, pool) | 23322b0 | = main | | | |
| locals-first at the sweep AMM transfer | 23322b0 | 0.56795 | 27,264 | 2/6 | 508 |

| main | 308b545 | 0.63062 | 27,400 | 2/6 | 506 |
| `if let Some(val)=sharing_update` | 308b545 | 0.62921 | 27,392 | 2/6 | 506 |
| tail pool_updated/nf/pargs orders (3) | 308b545 | 0.62564-0.62734 | 27,416-27,424 | 2/6 | 506-507 |
| main | 769f331 | 0.63241 | 27,400 | 2/6 | 506 |
| sharing CPI as `CpiContext::new(..).with_signer(seeds)` | 769f331 | 0.60797 | 27,416 | 3/5 | 507 |
| pool CPI as `CpiContext::new(..).with_signer(seeds)` | 769f331 | 0.54224 | 27,400 | 2/6 | 506 |

No form changes the tag==2 register web (r7 at 18 sites; original r7 at 21 of 26). The only forms that produce
per-clone reloads (3/5, 3/4) evaluate the program clone last or move the CPI behind a helper boundary. Both relayout the
arm and lose 0.02-0.04.

## Tools (`tools/`)

- `accprobe.py`: the per-use / per-block reload probe above (post-opt IR, experiment only).
- `csrlive.py <dis> <lo> <hi>`: callee-saved registers read after each call before being written.
- `reloads.py <fn.bin|orig>`: stack reload/store counts and tag==2 test registers.
- `batch.sh <slot> <names..>`: capvar + llcb + reloads for `edits/<name>.py` into `res.jsonl`.
- `livein.py`, `rng.py`, `llfn.py`: disassembly helpers. `rec.py`: ledger recorder.
- From w13a44/w13a40/w13a35/w13a33: `capvar.sh`, `capraw.py`, `rx.py`, `llcb.py`, `radbg.sh`, `rsplit.py`, `clonefeat.py`,
  `fbsplit.py`, `framebound.py`, `coal.py`, `regdelta2.py` (paths repointed to this lane).
