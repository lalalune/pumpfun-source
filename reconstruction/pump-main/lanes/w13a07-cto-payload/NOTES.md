# w13a07-cto-payload: admin_cto sharing-payload pieces (notes)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 3912c47ac (0.48772 / 3,273 slots), then main 4394685 (#2892, 0.49071 / 3,313 slots).
Angle: the original's +80 B after `val.sroa.6.i`, which holds the unmerged 7/9 B pieces of the sharing payload
and a 32 B target. The question was which source values the original keeps as whole aggregates.
Scratch and builds are in `~/.cache/pumpfun-reconstruction/lanes/w13a07-cto-payload/` (not in git). Ledger keys are
`0x22a10-w13-*-payload-*`.

Result: no source change improved main. The payload pieces are a consequence of the entry copy of `new`, not an
independent source spelling, and frame-only they are worth at most about +0.001 to +0.003.

## What the original does (read from its code)

| orig | what |
| --- | --- |
| 0x22ee8..0x22f48 | Entry copy of `new`, made right after the CtoState stores. The tag goes to `[r10-0x8f8]`, `[1,8)` to a 7 B slot at T 0x658, `[8,16)` is an i64 spilled at 0x900, `[16,24)` is held in r9, and `[24,33)` goes to a 9 B slot at T 0x668. |
| 0x24260..0x242a0 | Non-holder shared arm: **P1** is copied from the entry copy (7 B to T 0x538, 9 B to T 0x548). The tag is `r0` (new's tag). |
| 0x23b48..0x23b88 | Holder shared arm (also reached from the non-holder path when `r8!=0`, by tail merge): P1 is copied from an **uninitialised** 7/9 B pair whose slots are coloured into T 0x450 and T 0x2d0. Tag 0. |
| 0x242e0 / 0x24388 | Not shared: tag 2. P1 is not written. |
| 0x243e0..0x24418 | Join: **P2** is copied from P1 (7 B to T 0x550, 9 B to T 0x560). |
| 0x24420..0x24458 | Join: the 32 B target E32 at T 0x580 is built from `[r10-0x918]` (i64) plus X24 (T 0x680, itself copied from T 0x530..0x520). |
| 0x26730..0x26790 | Sharing CPI `val` (T 0x651): tag `r6`, P2's 7 B, `[8,16)` from the entry spill 0x900, `[16,24)` from 0x948, and P2's 9 B. |

## Our MIR already has the original's shape

On main, `let (sharing_update,collect_old,skip)=if shared{..}` becomes these MIR locals:
- `_395` (MIR SROA piece of the if-tuple): assigned per arm. It is **P1** (`_395.sroa.6`, 32 B).
- `_49 = None; _48 = Some(move _49)`: the holder arm's temporary. It is the original's uninitialised 7/9 source.
- `_45 = _395` at bb22: the inner `sharing_update` binding. It is **P2** (`sharing_update.sroa.3`, 32 B).

There are two differences, and both are LLVM-level:
1. **Cut.** P1 and P2 are cut 7/[8]/[8]/9 in the original only because the non-holder arm copies from an alloca copy
   of `new` that SROA cuts at the `Result<Pubkey>` overlay (`t` / validate's `Ok(target)`, Error at [8,24)).
   Ours copies straight from the `%new` argument pointer, so P1/P2 stay whole 32 B allocas, and `_49` folds away.
   No spelling of the payload alone produces the cut. It needs the entry copy of `new` (lane w13a03-cto-entrycopy).
2. **Order.** P2 sits right after P1 in the original's alloca order. P2 must therefore be a high-index MIR local
   (a MIR SROA or MIR-inline local). Ours is `_45`, the low-index inner binding: CopyProp unifies every SSA copy
   (outer binding, `v.3`, tuple fields) into it.

## IR oracle measurements (llc oracle, tokens equal to the build)

| edit | base | ratio | bytes |
| --- | --- | ---: | ---: |
| main | 4394685 | 0.49071 | 27,400 |
| `mv:sharing_update.sroa.3:_366` (P2 right after P1) | 4394685 | **0.49161** (+0.0009) | 27,400 |
| `mv:target1:_366` (E32 early) | 4394685 | 0.49131 | 27,400 |
| both together | 3912c47 | 0.4835 (worse) | 27,400 |
| F1 `mv:_114.i:_179` | 4394685 | 0.51917 | 27,400 |
| F1 + P2 move | 4394685 | 0.51977 | 27,400 |
| P1/P2 cut 7/9, pieces after val.sroa.6.i (`tools/cut_payload.py val`) | 3912c47 | 0.49065 | 27,472 |
| same, pieces in place (`keep`) | 3912c47 | 0.45146 | 27,472 |
| cut + F1 + val6 move | 3912c47 | 0.52565 (F1+val6 alone 0.51528) | 27,472 |
| cut with `[8,24)` as long-lived i64 phis | 3912c47 | 0.465 | 27,496 |
| entry copy of new emulated, no cut (`tools/cut_entrycopy.py nop`) | 3912c47 | 0.46545 | 27,480 |
| entry copy + cut | 3912c47 | 0.39063 | 27,608 |
| no P1->P2 join copy (one payload alloca) | 4394685 | 0.4919 | 27,336 |
| fresh 24 B host slot near holder_key or st with a volatile write at the join (`tools/x24_host.py`) | 4394685 | 0.49064 | 27,408 |

Reading:
- Frame-only, the payload is worth +0.0009 (P2 order) up to about +0.003 (cut and placement, after F1). The 7/9 copies
  cost about +72 B of code in our shape.
- The emulated host slot (x24) is absorbed by the 384 B `_128.i` group (scmerge), so `_114.i` stays alone.
  A host for the wallet signer slice must conflict with every larger group, which a join-only lifetime does not.

## Execute-own frame scan (main 4394685, `iredit.py scan`, 207 single edits, all 27,400 B)

| edit | ratio |
| --- | ---: |
| `nolt:_68` (the 24 B `String` of the 410 `require!` error kept unmerged) | **0.50869** (+0.0180) |
| `nolt` of another 24 B execute buffer (`ix_data`, `_171`, `_366`, `_155`) | 0.5066..0.5075 |
| `sz:target1:56`, `sz:sharing_update.sroa.3:56`, `sz:val5:57` or `sz:old_creator:56` (24 B more in any unmerged execute slot between the inlined region and holder_key) | 0.50839 |
| `mv:mint:_366` | 0.49341 |
| `mv:holder_key:END` | 0.49221 |
| P2 move (`mv:sharing_update.sroa.3:_366`) | 0.49161 |
| `nolt:_68` + F1 (`mv:_114.i:_179`) | **0.53505** |
| F1 + `_114.i` grown to 24 B before holder_key (X24-like host) | 0.51708 |

The gain does not depend on which slot it is: about 24 B of unmerged frame space among execute's own slots between the
inlined region and holder_key is worth +0.018 with no code change. That fits the original's extra pieces in the region
(P1 7/9, P2 7/9, the 32 B E32, the F7/G9 entry copy and the 24 B X24) against our 32 B `target1` and 32 B P2.
A source form that adds such space needs a 24 B (or larger) execute local with no StorageLive/StorageDead that LLVM does
not fold away. The original's candidates are the 8/24 target pieces and the entry copy of `new`.

## Source trials (all on main 4394685 unless noted; all zero-loss builds, none better)

| key | change | result |
| --- | --- | --- |
| A2-v3-field | state block kept in `v`, sharing payload read as `v.3` at the CPI and the event | byte-identical |
| A3-su-tuple-v3 | inner if-tuple kept as `su`, block returns `su.0..2`, outer `v.3` | byte-identical |
| A4-su-tuple | inner if-tuple kept as `su`, no inner bindings | byte-identical |
| option-clone | C1: block returns `sharing_update.clone()` / C2: `match sharing_update.clone()` | 27,600 B 0.4665 / 27,472 B 0.47928 |
| shared-arm-validated-target | non-holder arm `Some(Some(t))` from validate's target | 27,496 B 0.47937 |
| su-after-validate | `let su=if holder{None}else{new}` after validate, both arms `Some(su)` | 27,344 B 0.45794 |
| mir-inline-some-new | E1 `shared.then_some(new)` / E2 `Some(if let Some(n)=new{Some(n)}else{None})` | byte-identical / 27,488 B 0.48991 |
| closure-tree | G1 whole sharing tree in an immediately-called closure / G2 payload constructors as closures | 27,264 B 0.46283 / byte-identical |
| (3912c47) A/B | `v.3` and `v.2`+`v.3` field reads | byte-identical |

Other lanes had already covered the entry-copy forms (`mut new` + `take()`, `&mut new`, `let mut new=new`, args aggregates),
and every one of them costs ratio (see w13a03-cto-entrycopy, w12a06, w12b10, w12a12 in the ledger).

## Tools

The scripts are for the trimmed module from `w12a02-cto-iroracle/scripts/{capture,trim,trim2}.py`. Their IR value names are those of main
3912c47 (`_401.sroa.6`, `val6`, `_51.sroa.*`). On 4394685 they are `_395.sroa.6`, `val5` and `_52.sroa.*`, so adjust the patterns.
- `tools/cut_payload.py`: cuts P1/P2 into 7/9 B pieces and reloads `[8,24)` from `new` at the CPI.
- `tools/cut_entrycopy.py`: emulates the entry copy of `new` (F7/G9 plus i64s at the CtoState point) that feeds validate's `t`,
  plus the optional P1/P2 cut.
- `tools/x24_host.py`: adds a 24 B host slot with a join-only write, to test whether `_114.i` can find a host.

## Next ideas

- The payload cut and the P1/P2/E32 order only pay off together with the entry copy of `new`, which every known
  spelling makes more expensive, and with F1 (a host for `_114.i`). Work on those first. The payload follows from them.
- A source shape in which P2 is a high-index MIR local without CopyProp unifying it: an MIR-inlined helper that
  returns the sharing value and is not a closure capturing `target`.
