# w14a28-cto-evauthlit: event-CPI authority AccountInfo clone forms (admin_cto::execute, 0x22a10)

Target `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`), pinned at 27,400 B.
Bases: main 7e6aa9caa (0.64140, 3,174 slots), re-checked on main d2d187555 (0.64170, 3,173 slots).
Ledger: approach `evauthlit`, keys `0x22a10-w14-{7e6aa9c,d2d1875}-evauthlit-*-v1`.

**Result: no gain. The angle is exhausted.** Both event-CPI authority clones in the original are outlined
`<AccountInfo as Clone>::clone` calls, and main already has both of them in the original's place and order:

| site | original | main | callee |
| --- | --- | --- | --- |
| AdminCtoEvent `emit_cpi!` (tail) | orig 0x5110 `call -0x2dd6`, r2 = accounts+0x138 | 0x50d0 `call -0x2dce` | same target (`AccountInfo as Clone>::clone`) |
| CollectCreatorFeeEvent (wallet) | orig 0x64f0 | 0x64d8 region | same (w14a25 poollit) |

So every `AccountInfo{..}` literal at either site removes the clone call (154 -> 152 calls), grows the function
by about 300 B and loses badly. Every spelling that keeps the call is byte-identical to main. Through-path reads
(the #3267 reloadarm mechanism) only matter where the original inlines the clone (the sharing CPI), which is not the
case at either event-CPI site.

## Screen (measure.sh builds)

| name | change | ratio | bytes | calls | result |
| --- | --- | ---: | ---: | --- | --- |
| t0 | tail `emit_cpi!(e)` hand-expanded verbatim (Anchor 0.31 text) | = main | 27,400 | 154 | byte-identical |
| tw | tail hand-expanded in the wallet block form (deferred `event_signers`, `event_infos=[authority_info]` before the signer seeds) | = main | 27,400 | 154 | byte-identical |
| ta | tail hand-expanded, `event_infos=[authority_info]` bound after `ix`, signer seeds inline | = main | 27,400 | 154 | byte-identical |
| tlK_thru | tail literal, order key,rent_epoch,lamports,is_signer,data,owner,is_writable,executable (#3260), reads through `ctx.accounts.event_authority.<f>` | 0.52145 | 27,688 | 152 | loss |
| tlL_thru | tail literal, declaration order, through-path reads | 0.52145 | 27,688 | 152 | loss |
| tlLD_thru | tail literal, lamports,data first (#3267 order), through-path reads | 0.52145 | 27,688 | 152 | loss |
| tlL_x | tail literal via `let x=&ctx.accounts.event_authority` | 0.52145 | 27,688 | 152 | loss |
| wlK_thru | wallet literal, #3260 order, through-path reads | 0.30652 | 27,704 | 152 | loss |
| wlLD_thru | wallet literal, lamports,data first, through-path reads | 0.30618 | 27,712 | 152 | loss |
| wlL_thru | wallet literal, declaration order, through-path reads | 0.30652 | 27,704 | 152 | loss |

The literal field order and the read path change nothing inside a literal at these sites (tl* rows share one ratio).
w14a25-cto-poollit already showed the collect-site `.clone()`, `AccountInfo::clone(&..)`, `a.` path, statement
orders and `event_signers` placements; together with the tail rows above, no event-CPI spelling remains.
Re-check on d2d1875: see `SUMMARY.json`.

## What the tail emit_cpi residual really is (main 7e6aa9c, `tools/sbs.py`)

The tail site is 81/82 skeleton-matched. Its only non-frame diff is a register swap between the clone destination
pointer (`r10-0x610`) and the bump byte:

```
orig                                   ours
50e8 add64 r6, 0x138                   50a8 add64 r8, 0x138        ; &event_authority (accounts in r6 vs r8)
50f0 mov64 r1, r10 / add64 r1,-0x610   50b0 mov64 r6, r10 / add64 r6,-0x610
5100 stxdw [r10-0x8d8], r1             50c0 mov64 r1, r6           ; orig spills the dest pointer
5120 ldxb r6, [r1+0x2e]                50e0 ldxb r1,[r1+0x2e]; stxdw [r10-0x8d8], r1   ; ours spills the bump
52e0 ldxdw r2, [r10-0x8d8]  (memcpy)   52a8 mov64 r2, r6
5340 stxb [r10-0x4e8], r6              5308 ldxdw r1,[r10-0x8d8]; stxb [r10-0x4e8], r1
```

Between `from_iter` and the memcpy five values compete for r6-r9 (dest pointer, bump, vec ptr, vec len, ix), so
one must spill. Which one is decided upstream: the original reaches the clone with the accounts pointer in r6
(reloaded at orig 0x4f38 because r6 held the `sharing_update` tag from the pool arm, orig 0x4d48, tested at 0x4f18),
so r6 is busy when the dest pointer is defined. Ours holds accounts in r8 from 0x4e40 and pool_updated in r6.
That is the sharing-tag r6 / pool_updated r8 assignment that w14a12-cto-tagreg owns (IR-only pin bound +0.0027),
not an event-CPI spelling. The same holds at the collect site (r9 vs r7 temporary class from the wallet coin flag,
w14a03 / w14a24).

## Tools

- `e/var.py`: variant library (literal builder `lit(order, path)`, tail hand-expansion forms `macro`/`wallet`/`arrfirst`).
- `tools/run.py <res.jsonl> <names..>`: two-worker measure.sh queue over `e/var.py`.
- `tools/sbs.py`, `sites.py`, `amap.py`, `ann.py`, `disso.sh`, `absratio.py`, `ch.py`: copied from w14a25-cto-poollit.
  They read `orig.rel` (w14a15's original disassembly, `$C/lanes/w14a15-cto-skelunion/orig.rel`; not committed).
