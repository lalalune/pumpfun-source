# w14a56-cto-ctxref2: `&&Context` ArgPromotion lever across every admin_cto helper

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Base: **main 63308119b (0.65698, 3,193 slots, 1034/1035 normalized and raw)**. The baseline build is
`$C/w11/current-baseline`. Every number below comes from the raw-IR capture + rx opt/llc oracle on that main
(`m0` reproduces main exactly: 0.65698 @ 27400, eq_main).
Ledger approach `ctxref2`, keys `0x22a10-w14-6330811-ctxref2-<name>-v1`.

Result: **no gain. The angle is exhausted by its own premise.** All five ctx-field load sites in ours are already
in the same block, at the same point, as in the original. ArgPromotion fires on only one helper (`sweep`). The one
load that `&&Context` can move is the sweep bump, and the original loads that bump where main already does.

## 1. Which helpers ArgPromotion touches (tools/argprom.sh, `opt -O3 -print-after=argpromotion`)

| helper (single call, not MIR-inlined) | ctx/ptr args before | after ArgPromotion | promoted? |
| --- | --- | --- | --- |
| `execute::sweep(ctx:&Context, holder_key:&Pubkey)` | `ptr %ctx`, `ptr %holder_key` | `ptr %ctx.8.val, i8 %ctx.35.val, ptr %holder_key` | **yes**: accounts (+8) and `bumps.creator_vault` (+35) are loaded at the call site |
| `execute::wallet(ctx:&Context)` | `ptr %ctx` | unchanged | **no**: it reads 3 ctx fields (+8, +35, +46), over the 2-element limit |
| `validate(st:&CtoState, .., new, holder_key, sharing)` | 4 pointers | unchanged | no: `st` has 8 fields, and the Pubkey pointers go to memcmp |
| `execute::{closure}` / `wallet::{closure}` (`\|b\|*b` from emit_cpi) | `ptr %b` | `i8 %b.0.val` | yes, but trivial (byte copy) |
| sharing CPI, pool CPI, AdminCtoEvent build | inline in `execute` | - | - |
| `token_frozen` (5 calls), `token_raw_amount` (2) | outlined, multi-call | - | their bytes already match outside the window |

So `&&Context` (or `&mut &Context`) can only change anything on `sweep`. On `wallet` and `validate` it gives
byte-identical output (rows w1, w2, v1).

## 2. ctx-field load placement, original vs main (tools/ctxmap.py on lst.py listings)

The ctx pointer is spilled at entry (orig `[r10-0x938]` = -2360, main -2352) and reloaded once per field load.

| field | source site | original | main 6330811 | same block / same point? |
| --- | --- | --- | --- | --- |
| `bumps.creator_vault` (+35) | sweep head (argpromoted to the call site) | 0x1d58 -> r7, then accounts reload | 0x1d40 -> r9, then accounts reload | **yes** (only the register differs: orig spills r7 after the dest compare, main keeps r9) |
| `bumps.pool_authority` (+39) | `signer_seeds` before the sharing CPI | 0x3c68 | 0x3c40 | yes |
| `bumps.event_authority` (+46) | final `emit_cpi!`, after the authority clone | 0x5118 -> r6 | 0x50e0 -> r1, spilled to -2264 | yes (RA: orig keeps the bump in r6 and spills `&authority_info`; ours does the reverse) |
| `bumps.creator_vault` (+35) | wallet `collect` call | 0x6120 | 0x6120 | yes |
| `bumps.event_authority` (+46) | wallet event CPI | 0x64f8 | 0x64e0 | yes |
| `accounts` (+8) | execute entry (one GVN value) | 0x28 -> r8, spilled once to -2264 (0x280), 32 reloads | 0x28 -> r8, spilled to -2272 | yes (frame slot differs by 8) |

No load is hoisted in ours but in place in the original, so no helper meets the lane's precondition.

## 3. Screen (raw-IR capture + rx oracle, main 6330811, 0.65698 @ 27400)

| name | form | ratio @ bytes | eq_main | TCF seg 69 lvl1 / lvl2 / regdiff |
| --- | --- | --- | --- | --- |
| m0 | main | 0.65698 @ 27400 | yes | 496 / 594 / 127 |
| w1 | `wallet(&&ctx)` | 0.65698 @ 27400 | **yes** | = |
| w2 | `wallet(&mut &ctx)` | 0.65698 @ 27400 | **yes** | = |
| v1 | `validate(&&st,..)` | 0.65698 @ 27400 | **yes** | = |
| s3 | `sweep(&ctx,&&holder_key)` | 0.65698 @ 27400 | **yes** | = |
| s1 | `sweep(&&ctx,..)` (bump at its vsigner source position) | 0.61674 @ 27408 | no | 441 / **609** / 169 |
| s2 | `sweep(&mut &ctx,..)` | 0.61674 @ 27408 | no | = s1 |
| w1s1 | wallet && + sweep && | 0.61674 @ 27408 | no | = s1 |
| p0 | sweep && + `let bump` before `native` | 0.65698 @ 27400 | **yes** | = |
| p2 | sweep && + bump right after the 648 dest compare (where the original spills it) | 0.59886 @ 27400 | no | 386 / 586 / 162 |
| p3 | sweep && + bump after `amm_frozen` | 0.57921 @ 27472 | no | 315 / 585 / 184 |
| p5 | sweep && + bump just before `vsigner` | 0.61674 @ 27408 | no | = s1 |
| p6 | sweep && + bump after `old` | 0.61944 @ 27408 | no | 441 / 609 / 169 |

Readings:
- With `&&ctx`, the bump load lands where the source puts it. At the head (p0) the output is byte-identical to
  main, because ArgPromotion already puts it there. Every later position loses 0.04 to 0.08.
- A late bump improves the TCF clone run's **structure** (seg 69 lvl2 594 -> 609, +15: the Rc-overflow tail merging
  w14a45 saw). But it re-colours the run (regdiff 127 -> 169, lvl1 -55, raw -100 tokens), and the vsigner segment
  (orig 0x1fa8) loses 22 because the original reloads the bump from its spill slot.
- No candidate beats main, so none went on to the accounts-pointer (r8/r6) check (segregs/accprobe) or a full
  measure.sh build.

## Conclusion for other lanes

- ctx-field load placement is already original everywhere in admin_cto. The remaining sweep-head gap is register
  assignment (orig: bump r7 spilled to [-0x910] after the dest compare, native r9 spilled, +0x108 gep spilled). No
  source position of the load expresses it, and w14a45 showed that IR-forcing those spills does not fix the TCF names either.
- The final emit_cpi swap (orig bump in r6 with `&authority_info` spilled to -2264; ours the reverse) is RA, not load
  placement.
- `&&T` on a single-call helper matters only when ArgPromotion fires, which needs at most 2 promotable loads.
  `tools/argprom.sh <raw.ll>` lists which helpers it hits.

## Tools (tools/)

- `argprom.sh <raw.ll> [regex]`: post-ArgPromotion signatures of the admin_cto helpers.
- `ctxmap.py <lst>`: the ctx spill slot and every ctx reload with the field loads after it.
- `capvar.sh`, `capraw.py`, `rx.py`, `rec.py`, `lst.py`, `segdiff.py`, `segregs.py`, `splice.py`: w14a45/w14a38's
  tools, repointed to this lane.
