# w13a48-cto-vaultspill: which early spills of `admin_cto::execute` can source control?

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Main 52c0b087c: 0.62103, 3,306 slots, 1034/1034. Continues w13a29-cto-spillslot109 (next ideas 2 and 3) and
w13a32-cto-hkfirst2 (next idea 1). Ledger keys: `0x22a10-w13-52c0b08-vaultspill-*` (40 rows).

Notes only: no source change beats main. Every number below is `measure.sh` at the built size unless it is marked
"IR" (post-opt `llc` oracle on the 52c0b08 raw-IR capture, `eq_main=true`).

## The residual on 52c0b08

After the 648 `holder_creator_vault` memcmp (orig +0x1f48), the original spills three values that ours keeps:

| value | orig | ours |
| --- | --- | --- |
| `&a.holder_creator_vault` (gep accounts+264) | `stxdw [r10-0x8e0]` at its def | `r8` until the native/token arm |
| `native` (`quote_mint == native_mint`) | `r9` -> `[r10-0x918]` | `r7` -> `[r10-0x918]` (same slot) |
| `bump` (`ctx.bumps.creator_vault`, hoisted to the sweep top by opt in both) | `r7` -> `[r10-0x910]`, reloaded for the vsigner `stxb` | `r9`, never spilled |

- The coin_creator_vault_ata data-Rc spill at orig 0xb48 (w13a29 idea 3) **is already matched on main 52c0b08** (0x259b8
  `stxdw [r10-0xb48], r4` is aligned). The only original spill slot ours lacks is 0xc38: the `program:` clone of
  `TransferCreatorFeesToPumpV2`, where the original spills `is_signer` and keeps `owner` (read last) in r3, and ours
  reads `owner` right after the lamports clone (fieldscan territory; w13a47 found no single/pair above main).
- `tools/regdiff.py` (per-0x800 region, unmatched original instructions with frame masked / frame+registers masked):
  the clone run 0x2800-0x3800 has 84+64+51 frame-masked but only 6+8+19 structural differences. It is register
  assignment, not code shape. `tools/regperm.py` gives the orig->ours register map per region (clone run: orig r5->r0,
  r6->r0/r9, r8->r6, r9->r7). In 0x26c8-0x2ec8 ours never touches r8 (the vault pointer); the original uses all ten.

## Source forms for the vault pointer (measure.sh, 0 losses unless noted)

| trial | form | bytes | ratio |
| --- | --- | ---: | ---: |
| main | | 27,400 | 0.62103 |
| `bind_top_late`, `bind_top_all`, `bind_after_late` | `let hv=&a.holder_creator_vault;` at the sweep top / after the dest check, uses via `hv` | 27,400 | 0.62103 (byte-identical) |
| `tuple_dest_late` | `let (dest,hv)=(PDA.0,&a.holder_creator_vault);`, late uses via `hv` | 27,400 | 0.62103 (byte-identical) |
| `arg_late`, `arg_native` | `sweep(&ctx,&holder_key,&a.holder_creator_vault)` with `hv:&AccountInfo<'info>` (needs `fn sweep<'info>(ctx:&Context<'_,'_,'_,'_,AdminCto<'info>>,..)`), late uses via `hv` | 27,400 | 0.62103 (byte-identical) |
| `arg_cmp`, `arg_all`, `tuple_dest_all` | the 648 compare reads `hv.key()` | 27,400 | 0.55932 |

LLVM sees one `gep +264` in every by-reference/argument/tuple form, so none of them reaches the register allocator.
Routing the 648 compare through `hv` hoists the key load to the sweep top (`ldxdw r6,[r7+0x108]` before the PDA) and costs 0.062.

## IR probes: does an early spill help by itself? (IR, `ir-probes/mk.py`)

The probe stores the value to a stack slot at its def (or at the top of the post-memcmp block `bb7.i87`, the original's
split shape) and reloads it before each later use. The plain ratio drops because a named slot shifts the frame; the
frame-masked `abs` ratio isolates the register effect (main abs 0.7121).

| IR edit | main 52c0b08 abs | hk1 abs (hk1 build 0.57293, abs 0.65837) |
| --- | ---: | ---: |
| vault spilled at def, all later uses | 0.71122 | 0.5602 |
| vault, token-arm clone use only | 0.71221 | 0.65847 |
| bump spilled at def | 0.69442 | **0.70303** |
| bump + vault at def | 0.67836 | 0.60219 |
| split after the memcmp: bump / vault / both | 0.69311 / 0.70983 / 0.70243 | 0.70202 / 0.62131 / 0.69616 |

- On main, forcing the original's early spills never improves register similarity: freeing r8/r9 makes the clone
  run use the freed register differently (0x2800 region 84 -> 101..160 unmatched). The original's spills are a
  consequence of a higher register demand in its clone run, not a lever.
- On hk1 (w13a32 hk-first), the bump spill repairs most of hk1's clone-run collapse (region 0x3000 213 -> 103,
  0x3800 115 -> 53), so the bump's register is what triggers hk1's cascade.

## Source forms for bump and native (measure.sh)

| trial | form | bytes | ratio |
| --- | --- | ---: | ---: |
| `bumptop`, `bumpafterdest`, `bumparg` | `let bump=..` at the sweep top / after the dest check / as a `u8` sweep argument | 27,400 | 0.62103 (byte-identical) |
| `bumparr_top` | `let bumpa=[ctx.bumps.creator_vault];` at the sweep top, seeds use `&bumpa` (bump lives in memory) | 27,408 | 0.58889 |
| `bumparr_late` | the same array at the vsigner site | 27,384 | 0.61912 |
| `bump_fromref` | seeds use `std::slice::from_ref(&ctx.bumps.creator_vault)` | 27,384 | 0.58885 |
| `nativeafterdest` | `native` computed after the dest check | 27,392 | 0.61633 |
| `nativearg`, `bothargs` | `native` (and bump) as sweep arguments | 27,384 | 0.37309 |

`bumparr_top` / `bump_fromref` are the source forms of the IR bump-spill probe (same abs ~0.70). On main they cost 0.032.

## hk-first retries on 52c0b08 (measure.sh)

| trial | bytes | ratio |
| --- | ---: | ---: |
| `hk1` (w13a32 form) | 27,360 | 0.57293 |
| `hk1` + `bumparr_top` | 27,368 | **0.60402** |
| `hk1` + `bump_fromref` | 27,344 | 0.60369 |
| `hk1` + `bumparr_late` | 27,344 | 0.57040 |
| `hk1` + vault forms (`arglate` / `arg_cmp` / `tuple_dest_all`) | 27,360 / 27,320 / 27,320 | 0.57293 / 0.57306 / 0.57306 |
| `hk1` + `bumptop` / `bumparg` / `bumpafterdest` | 27,360 | 0.57293 (= hk1) |
| `hk1` + `nativeafterdest` | 27,352 | 0.56732 |
| `hkc_v1` (w13a33 holder_key by value) / `hk1` + `hkc_v1` | 27,360 / 27,328 | 0.55254 / 0.51207 |
| `hk1` + `bumparr_top` + `hkc_v1` / + `arg_all` / + `arg_late` | 27,328 / 27,320 / 27,368 | 0.52167 / 0.55836 / 0.60402 |

hk1 + `bumparr_top` lifts hk1 by +0.031 and keeps hk1's region-0 gain (frame-masked unmatched 128 -> 104), but the
clone run is still worse than main (0x2800 +16, 0x3000 +39) and its perfect-frame bound (0.64329) is below main's
(0.65009). It is not a route to a landable gain on this main.

## Map: which early spills can source control?

| original spill | source control | effect |
| --- | --- | --- |
| `&holder_creator_vault` at its def (0x8e0) | none: every binding/argument/tuple form is byte-identical | forcing it in IR does not help either |
| `native` (0x918) | already spilled in ours | moving its computation costs 0.005..0.25 |
| `bump` (0x910) | yes: an addressed `[u8;1]` at the sweep top or `slice::from_ref` keeps it out of registers | -0.032 on main, +0.031 on hk1 (still below main) |
| coin_creator_vault_ata data Rc (0xb48) | matched on main | |
| `program:` clone `is_signer` (0xc38) | clone field order (fieldscan) | exhausted by w13a47 |

## Re-measured on main 53abf28 (0.62672, wave-14 continuation)

Main 53abf28 (stitch9 #3168: `shared` as an `&&` chain, pool CPI args bound after `pool_updated`) is 0.62672 / 3,305 slots,
fbsplit `{plain 0.62672, named_only 0.63301, spill_only 0.65219, all 0.65818}`. The hk1 edits were re-based onto the `&&`
form (`$OUT/edits/*_m53.py`). Ledger keys `0x22a10-w13-53abf28-vaultspill-*`.

| trial | bytes | ratio | perfect-frame bound (`all`) |
| --- | ---: | ---: | ---: |
| main | 27,400 | 0.62672 | 0.65818 |
| `bumparr_top` | 27,408 | 0.59578 | 0.64071 |
| `bump_fromref` | 27,384 | 0.59515 | 0.63980 |
| `hk1` | 27,384 | 0.56578 | 0.60623 |
| `hk1` + `bumparr_top` | 27,384 | 0.60354 | 0.64819 |
| `hk1` + `bump_fromref` | 27,360 | 0.60321 | 0.64758 |
| `hk1` + `bumparr_late` | 27,368 | 0.56715 | 0.60761 |

The picture is unchanged from 52c0b08. Even with a perfect frame, every early-spill form stays below main's own bound, so size
knobs cannot turn any of them into a gain. `regdiff.py` on 53abf28: frame-masked 0.72588, frame+register-masked 0.8562. The
sweep/clone-run regions (0x2000-0x3800) have only 11/6/8/19 structural differences: what remains there is register assignment,
which the w13a40/w13a44 coalescing analysis owns. The structural gap is in 0x0-0x1800 (entry/validate, 86+124+72+35)
and 0x4000 (93).

## Tools (text only)

| tool | use |
| --- | --- |
| `tools/vrun.sh <name> <edits.py> <slot>` / `tools/batch.sh` | copy main's crate, apply `EDITS=[(old,new)]` (line count must not change), measure.sh, fbsplit |
| `tools/rec.py`, `tools/sumr.py` | ledger record / results summary |
| `tools/regdiff.py a.bin,b.bin,..` | per-region unmatched original instructions, frame-masked and frame+register-masked |
| `tools/regperm.py fn.bin lo hi` | orig -> candidate register map over aligned instructions in an orig offset range |
| `tools/spmap.py fn.bin [-a]` | candidate spill slot -> original slot votes (offset >= 0x6d0) |
| `tools/sobin.py so out.bin` | scorer-normalized admin_cto tokens from a linked build (input of fbsplit/regdiff) |
| `tools/ctoracle.py`, `framebound.py`, `fbsplit.py` | w13a35's llc oracle and frame bounds, repointed |
| `ir-probes/mk.py` | `make(uses)` vault spill-at-def, `bump()` bump spill-at-def, `late(vals)` split spill after the 648 memcmp, `chain()`; use as `ctoracle.py run m.ll out --edit e.py` |
| `tools/gen1.py`..`gen4.py` | the source edit sets above |
