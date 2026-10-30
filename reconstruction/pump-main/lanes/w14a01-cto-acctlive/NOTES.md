# w14a01-cto-acctlive: live range of the `ctx.accounts` pointer in admin_cto::execute

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 53abf28b1 (0.62672, 3,305 slots), then main 23322b07c (0.62882, 3,287 slots, after #3200).
Angle: continues w13a44 next_idea 2, w13a33 next_idea 1, w13a35 next_idea 1 and w13a45's register finding.
Scratch: `~/.cache/pumpfun-reconstruction/lanes/w14a01-cto-acctlive/` (not in git).

No source change is proposed yet. This PR holds the reload map, the probe oracle and the source-form screen.

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

## 3. Oracle: per-use reloads in the sharing arm are worth about +0.005

`tools/accprobe.py <m.ll> <out.ll> <lo> <hi>` edits the post-opt slim module. It stores `%_247` (the accounts pointer)
to a new alloca at entry and reloads it before every account load in IR lines [lo,hi]. On main 23322b0's module:

| probe | clonefeat | bytes | ratio | fbsplit all (perfect frame) | sharing segstat |
| --- | --- | ---: | ---: | ---: | ---: |
| main | 2/6 | 27,400 | 0.62882 | 0.60216 | 285 |
| sharing arm (lines 5440-5939, 10 loads) | **6/2** | 27,496 | 0.35167 | **0.60676** | 291 |
| every region after entry (101 loads) | 7/1 | 27,864 | 0.29581 | 0.52866 | 291 |

The sharing-arm form reproduces the original's clone addressing exactly. With the frame held, it is worth about +0.0046.
That agrees with w13a44's bound (+49 tokens over 0x4200-0x4800). Reloading at every use everywhere is worse, because the
original keeps multi-use reloads inside a block (0x3128, 0x4ab8, 0x6010, 0x6130).

llc RA knobs (split-spill-mode, local-reassign, exhaustive search, deferred spilling, eviction cutoff, CSR cost) never move
clonefeat off 2/6.

## 4. Source forms screened (raw-IR capture + rx oracle = build tokens)

Ledger approach `acct-liverange`, keys `0x22a10-w14-53abf28-acctlive-*` and `0x22a10-w14-23322b0-acctlive-*`.

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

No form changes the tag==2 register web (r7 at 18 sites; original r7 at 21 of 26). The only forms that produce
per-clone reloads (3/5, 3/4) evaluate the program clone last or move the CPI behind a helper boundary. Both relayout the
arm and lose 0.02-0.04.

## Tools (`tools/`)

- `accprobe.py`: the per-use reload probe above (post-opt IR, experiment only).
- `reloads.py <fn.bin|orig>`: stack reload/store counts and tag==2 test registers.
- `batch.sh <slot> <names..>`: capvar + llcb + reloads for `edits/<name>.py` into `res.jsonl`.
- `livein.py`, `rng.py`, `llfn.py`: disassembly helpers. `rec.py`: ledger recorder.
- From w13a44/w13a40/w13a35/w13a33: `capvar.sh`, `capraw.py`, `rx.py`, `llcb.py`, `radbg.sh`, `rsplit.py`, `clonefeat.py`,
  `fbsplit.py`, `framebound.py`, `coal.py`, `regdelta2.py` (paths repointed to this lane).
