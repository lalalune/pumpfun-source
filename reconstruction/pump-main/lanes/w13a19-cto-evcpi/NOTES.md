# w13a19-cto-evcpi: hand-expanded emit_cpi! in admin_cto::execute (0x22a10)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Angle: carry the 2f268ad0a mechanism (hand-expanded wallet `emit_cpi!` with a deferred-init `event_signers`)
to execute's own `AdminCtoEvent` `emit!(e);emit_cpi!(e);`, and screen the expansion's statement order,
deferred-init points and Vec forms. Screens use the w13a01 raw-IR oracle (`capvar.sh`/`rx.py`, tokens equal the
identity build) plus a post-opt `llc` what-if (`mv.py`/`lmv.py`: move an alloca or an IR line, re-run llc).
Ledger keys: `0x22a10-w13-<main7>-evcpi-*`.

## Step 1 (main 6ac6f9b, 0.56291 / 3,315 slots): superseded on main d81d0f5

Main d81d0f5 landed `let event_infos=[authority_info];` before the w13a23 block (0.571). On d81d0f5 the
match-scrutinee form below is **byte-identical** to that main (unstripped sha dd7cd212c81617ce): both spell the
same original order. The table and mechanism are kept as evidence of why it works.

| | bytes | ratio | slots | normalized/raw | losses |
| --- | ---: | ---: | ---: | --- | --- |
| main 6ac6f9b | 27,400 | 0.56291 | 3,315 | 1034/1034 | |
| this change | 27,400 | **0.56531** | 3,315 | 1034/1034 | none |

Unstripped sha `5fa487a492e10c5c`; runtime differential 363/363.

Mechanism. In the wallet's `CollectCreatorFeeEvent` CPI the original copies `authority_info` into the
`&[authority_info]` array (the 48 B `memcpy` at orig 0x66b8) **before** it writes the signer seeds; that is
the argument order of Anchor's `emit_cpi!` (`invoke_signed(&ix,&[authority_info],&[&[seeds,&[bump]]])`).
Main's w13a23 block form (`({let event_inner=..;event_signers=[event_inner];invoke_signed(..)})`) builds the
seeds first. The seeds must still be created after the `invoke_signed` destination (w13a23's MIR-index
finding) and `event_signers` must stay the deferred local declared before `collect` (2f268ad0a). A `match`
scrutinee in the third argument satisfies all three: its temporaries live to the end of the statement, so

```rust
invoke_signed(&ix,&[authority_info],
    match &[b"__event_authority" as &[u8],&[authority_bump]] as &[&[u8]]{event_inner=>{event_signers=[event_inner];&event_signers}})
    .map_err(anchor_lang::error::Error::from)?;
```

evaluates in the macro's order. The IR what-if (move the `lifetime.start`+`memcpy` of `_119.i` above the seeds
stores on 224ff93's post-opt IR) predicted exactly the same +0.0024 (0.55123 -> 0.55362) before any build.

Rejected spellings of the same order: `let ais=[authority_info];` (or `&[..]`, `&ais[..]`) first in the
block: -280 B, because a named array is dropped at the block end and the Err-path Rc drops merge.

## Screens on execute's own AdminCtoEvent emit_cpi! (no gain)

Literal hand-expansion is byte-identical to main. On mains 2f268ad, 1043a51 and 224ff93 every variant was at
or below main (ratios on 224ff93, main 0.55123):

| variant | bytes | ratio |
| --- | ---: | ---: |
| deferred `event_signers` before the event / before signer_seeds / before `swept` | 27,400 | 0.54973 / 0.54763 / 0.54733 |
| same at execute top / before CtoState | 27,400 / 27,392 | 0.51228 / 0.50457 |
| same after `(old_creator,old_fee)` / before `pool_updated` | 27,232 | 0.43246 |
| w13a23 block form with deferred `event_signers` (same points) | 27,400 | = the plain deferred rows |
| deferred `ix` / `ix_data` before the event | 27,392 | 0.54382 / 0.54532 |
| deferred `inner_data` / `authority_info` / `authority_bump` anywhere | 27,400 | = main (2f268ad) |
| bump read after `ix` (`ab_late`) | 27,384 | 0.55109 (bump kept in r9, no spill) |
| `inner_data` first / bump first / bump after inner_data | 27,400 | 0.54913 / 0.54104 / 0.55093 |
| signers before `inner_data`, `disc` first, `let ais=[authority_info]` | 27,400 | = main |
| ix_data via `extend_from_slice` / `concat` (2f268ad) | 27,352 / 27,344 | 0.47069 / 0.47106 |
| emit_cpi block before `emit!` | 27,392 | 0.54202 |
| `emit!` as `sol_log_data(&[&Event::data(&e)])` | 27,400 | = main |

`ab_late` paired with every applicable `sizeknobs-cto.json` knob stays below main (best 0.55109 at 27,384).

Execute's emit_cpi frame is already the original's on 224ff93 (authority_info -0x610, inner_data -0x5e0,
iterator -0x5c8, ix -0x450, invoke result -0x598). Its remaining difference is register allocation: the
original keeps the accounts pointer in r6 up to `add r6,0x138`, spills `&authority_info` into the
accounts-pointer slot [-0x8d8] and keeps the bump byte in r6; ours keeps `a` in r8, `&authority_info` in r6
and spills the bump. Unmerging any emit_cpi temporary (`nolt`) costs 0.04-0.09; moving non-leader allocas is
byte-identical (they sit in stack-coloring groups led by wallet locals).

## Tools (in `$OUT/tools`, from w13a01 with paths changed)

- `gen.py`: emits `e/<name>.py` edit lists for the execute emit_cpi expansion (deferred decls x anchor points,
  statement orders, Vec forms).
- `mv.py <m.ll> <name> mv:A:B|mva:A:B|swap:A:B|nolt:A`: post-opt llc what-if on allocas.
- `lmv.py <m.ll> <name> <lineA> <lineB> [after]`: move one IR line, re-run llc, score.
- `rec.py`: records oracle screens to the ledger.
