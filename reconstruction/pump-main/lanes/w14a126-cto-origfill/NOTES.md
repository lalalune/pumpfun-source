# w14a126-cto-origfill: the 307/312 outline basin splits — 312 is the cheap half (notes only)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: main ebe5387 (#3495, 0.67316, M 2,247, rfjM 2,810, 3,123 slots). Relaunch of the dead w14a123-cto-origfill;
continues w14a108-cto-crlrepay (#3495) and w14a106-cto-earlyload (#3490). Ledger approach `origfill`, keys
`0x22a10-w14-ebe5387-origfill-*`. Oracle: w14a108 raw-IR capture + opt + llc (`tools/two.sh`, ~15 s, no build slot);
`base O` = main with a call-site `noinline` on just the 307 and 312 `to_string` calls (`tools/ni.py`, not a source
construct), M 1,953 at 26,992 B. No landable change; best zero-loss measurement stays main (0.67316).

## Result: the 307/312 outline basin is two halves, and 312 is cheap

w14a108 (#3495) and w14a107 measured the two `to_string` outlines **together**: both outlined = -408 B, M 1,950
(rfjM unchanged). This lane split them with the call-site-`noinline` oracle. They are nothing alike:

| outline | bytes | M | ΔM vs main | rfjM | where the loss lands (`prov/chunk.py`) |
| --- | ---: | ---: | ---: | ---: | --- |
| main (neither) | 27,400 | 2,247 | 0 | 2,810 | — |
| **312 only** (`O312`) | 27,184 | **2,194** | **-53** | 2,779 | **all in validate**: chunks 0x0000/0x0800/0x1000 = -1/-16/-36; every chunk from 0x1800 on is **delta 0** |
| 307 only (`O307`) | 27,208 | 2,006 | -241 | 2,808 | local chunks 0x0800/0x1000 = 0/+4; loss is downstream 0x1800-0x3800 (-18 -14 -45 -106 -45): the TCF-run RA cascade |
| both (`O`) | 26,992 | 1,953 | -294 | 2,790 | sum of the two |

- **312 outlined costs only 53 M for 216 B**, and the loss is entirely local to validate (the error-block body that is
  no longer inlined). rfjM barely moves (2,810 -> 2,779): the skeleton is intact. The original outlines 312, so this is
  the faithful direction, and the repay target is small: a faithful +53 M inside validate at +216 B breaks even, and then
  the 312-cold source trigger wins outright.
- **307 outlined costs 241 M for 192 B, and the loss is not local.** Outlining 307 reorders the whole TCF/sharing clone
  run (0x1800-0x3800) — the same RA/placement cascade w14a106 (g1/GPF) and w14a89 (bb21) priced. rfjM actually *rises*
  (2,808), so the skeleton improves while the realized tokens collapse: pure register/frame assignment, no source handle.

So the long-standing "~400 B outline basin needs ~400 B of orig-only repay" framing (w14a108, w14a80) is misleading.
**Split it: 312 needs ~53 M of local repay; 307 is an RA cascade, not a repay problem.** A lane should target 312 alone.

## The OV (shared-target-override-in-arm) family all collapses — it is the and-1 basin

The task angle was to repay the basin with the original's orig-only runs (st.creator double copy at orig 0x0d90-0x0e08,
the 0x10f0 23-tok and 0x14b0 16-tok per-arm phi runs), via the OV form the original uses: validate chooses
`target = shared ? st.creator : t` inside the non-holder arm, before the fee checks, so JumpThreading reaches the sharing
tree from three exits (w14a89 §1 confirmed the original does thread `bb21`). Every OV spelling collapses on ebe5387:

| gene | form | bytes | M | rfjM | ΔM |
| --- | --- | ---: | ---: | ---: | ---: |
| `ov` | validate takes `shared`; non-holder arm `if shared{st.creator}else{t}`; execute drops `target=creator` | 27,360 | 1,481 | 2,185 | -766 |
| `ov_d` | `ov` + tree `!shared` arm first | 27,360 | 1,481 | 2,185 | -766 |
| `ov_a`/`ov_c` | `ov` + tree as `if shared&&holder/else if shared/else` (either order) | 27,384/27,440 | 1,445/1,442 | 2,187/2,170 | -802/-805 |
| `ov_b` | `ov` + `skip=!(shared&&holder)` split from the tree | 27,456 | 1,424 | 2,178 | -823 |
| `ov_e` | override as `ov:Option<Pubkey>=shared.then_some(st.creator)`, arm `ov.unwrap_or(t)` | 27,304 | **1,782** | **2,783** | -465 |
| `ov_f` | override as `Option<&Pubkey>`, arm `if let Some(c)=ov{*c}` | 27,360 | 1,481 | 2,185 | -766 |
| `ovt`/`ovt2` | whole `(target,collect_old,sharing_update,skip)` tree per arm inside validate | 27,608 | 1,331 | 2,391 | -916 |

`ov_e` is the least-bad (rfjM 2,783, only -27 skeleton) because `then_some`/`unwrap_or` keeps validate returning a single
`Pubkey` and the tree stays in execute; but M is still -465. `ovt` carrying the tree into validate adds 2 calls (157->159
internal... the `AdminCtoEvent`/clone count is unchanged at 157/3 at the window level, but the tree duplication inflates
bytes to 27,608) and collapses further. This matches w14a89: moving `target=shared?st.creator:t` into the arm is the
original's shape, but with LLVM's register assignment it is the and-1 / outline basin (M ~1,400-1,800), ~800 M below main.
The `prov/chunk.py` loss is concentrated in 0x2800-0x3800 (-180/-158/-124 for `ov`): the sharing+TCF clone run recolours.

**Conclusion.** The override-in-arm construct is faithful to the original's block outline but is realized ~800 M worse by
RA+MBP, exactly as w14a89 and w14a106 found for the head read order. It cannot be the repay vehicle for the 312 outline.
The useful residual this lane leaves is the split above: **312 outline is a 53-M local repay problem, not a 400-B one**,
and it is the only half of the basin worth another lane's time. The orig-only runs that would repay it are the validate
chunk-0x0800/0x1000 runs in `xtab_ebe5387.txt` (orig 0x0c08 56 B, 0x0e28/0x0ed8 40 B each, next to the 298/306 sites),
not the 0x10f0/0x14b0 per-arm runs (those are in the 307/TCF half, which is RA, not repay).

## Tools (experiment only)

- `tools/two.sh <name> <genes> <slot>`: w14a108 `cv.sh` capture, then score the variant and `base O` (307/312 noinline
  via `tools/ni.py`), printing `fr.py` masked tiers for both. `tools/par.sh <spec>` runs a name list two at a time.
- `tools/og.py`: the `ov*`/`ovt*` gene table (`G`) and hypotheses (`D`). `tools/rec2.py <results>`: ledger each row.
- `tools/es.py <cand>...`: error-site (`stw [r10-0x2b8],<line>`) order and internal call count per candidate.
- Reused from the dead w14a123 capture: `tools/*` (w14a108 `mm.py`/`fr.py`/`xled.py`/`xtab.py`/`rx.py`/`oracle.py`),
  `prov/*` (w14a106 `prov.py`/`provtab.py`/`chunk.py`/`skel.py`/`dis.py`). `xtab_ebe5387.txt` / `xtab_O_ebe5387.txt` are
  the extra-code ledgers of main and base O against the original; `screen_results.txt` is every oracle row.
