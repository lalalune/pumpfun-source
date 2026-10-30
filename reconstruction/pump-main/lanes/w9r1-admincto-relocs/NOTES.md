# Lane w9r1-admincto-relocs (wave 9, round 1)

Target: `0x22a10` `admin_cto::execute` (`programs/pump/src/creator/admin_cto.rs`). Angle: pair every `lddw` of the
candidate with the original's and remove the 2 extra constant-address loads (86 vs 84 data relocations).
Base: origin/main 255a0fd2e (1031/337); rebased and re-measured on e491c5e95 (1032/337, includes #2214). Builds: `~/.cache/pumpfun-reconstruction/lanes/w9r1-admincto-relocs/`.

## lddw census (attempt f9db0fcc)

All `lddw` of both functions, the original's data addresses rebased by -0x60 (its `.rodata` starts 0x60 later because
`.text` is 96 B longer), each target classified by section and content:

- Every `.rodata` target (panic/error `Location` file strings, `&PumpError` constants, seeds, program ids, messages)
  and every other `.data.rel.ro` target pairs 1:1.
- The only multiset difference: `.data.rel.ro+0x128`, the `String as core::fmt::Write` vtable, 9 in the original,
  11 in ours. It is loaded by every inlined `<T as ToString>::to_string` (anchor's `error!` builds `error_msg` with it).
- Per `PumpError` site: the original calls the outlined `to_string` at `InvalidCreator` (312) and
  `CreatorShouldNotBeZero` (307), and main inlines both. That is w6r3-layout-rodata's finding
  (PR #2370), reproduced here. Both sites sit at 2.2% block frequency of `validate`'s entry, just above the 2%
  cold-call-site cut that drops the inline threshold from 325 to 45 (`to_string` costs 130).

## Change

1. PR #2370's change: the line-296 `HolderRewardDisabled` check moves inside the `if holder` arm. 307/312 go cold,
   `to_string` stays outlined there, and the lddw multiset equals the original's (86 = 86, String vtable 9 = 9).
   On its own this costs ratio: 0.37637 -> 0.32392, 26,928 B. The original is 472 B larger without the two
   inlined bodies.
2. New in this lane: `validate` takes `mut new` and both consumers use `new.take()` (298 `new.take().is_some()`,
   306 `let Some(t)=new.take() else`). The caller passes a copy of `new` (it is used again for `sharing_update`).
   While nothing wrote that copy, memcpyopt forwarded every read to execute's `readonly` `new` argument.
   The original keeps a local copy of `new` (it loads all 33 bytes at entry, before the mayhem branch, and reloads them
   from stack slots later). Writing the copy through `take()` keeps a local copy in ours too. Behaviour is unchanged,
   because `new` is `validate`'s own by-value parameter.

Fresh builds on origin/main e491c5e95 (after #2214):

| metric | main e491c5e | this PR (r1) | original |
| --- | ---: | ---: | ---: |
| admin_cto bytes | 27,240 | 27,128 | 27,400 |
| win.py ratio | 0.37650 | **0.39103** | 1 |
| calls (internal+external) | 154+3 | 154+3 | 154+3 |
| lddw total / String vtable | 88 / 11 | **86 / 9** | 86 / 9 |
| lddw target multiset | 2 extra | **equal** | |
| `.rel.dyn` size | 0x18050 | **0x18030** | 0x18030 |
| official normalized / raw | 1032 / 337 | 1032 / 337 | |
| gains / losses (norm, raw) | | 0 / 0, 0 / 0 | |
| unstripped sha256 | 11cc19d8... | 56143aaa... | |

On 255a0fd2e (before #2214) the same change measured main 27,344 B / 0.37637, t01 (#2370 only) 26,928 B / 0.32392,
t04 27,144 B / 0.39061.

Opcode bag of t04 against the original: stack reloads -46, stack stores -13. The remaining ~256 B are mostly spill
and reload traffic.

## Biggest remaining structural lever: sweep-tail placement (attempt 841847d9)

win.py's diff shows a 5 KB run (original offsets 0x2800-0x3c00) that is entirely original-only. It is the sweep tail:
the amm part (token_frozen, 660), the `transfer_creator_fees_to_pump_v2` account clones and CPI, and the native path. The original lays it out
**before** the post-sweep code (pool seeds, sharing_config CPI, admin_cto_pool, event). Ours lays it out after.

Oracle: `llc` on the captured post-opt IR (`--emit=llvm-ir`, experiment only) reproduces the 27,144-B function in 3 s.
`-print-after=block-placement` and `-print-machine-bfi` show the cause. The sweep's errors merge into
`sweep.exit`, where the caller's `?` re-checks the Result tag (`icmp eq tag, 2`). Its frequency is 0.0041, 79% of the sweep
entry; jump threading took the Ok paths away (`sweep.exit.thread`, 0.00014). BPI gives the re-check 50/50, so
MachineBlockPlacement chains `bb38` (the post-sweep join) behind `sweep.exit`. bb38's only other unplaced predecessor is
the tiny Ok thread. The original has the same re-check (`jne r7,2` / `ja post-sweep`) but does not chain post-sweep there.
Adding `!prof` branch_weights 1:2000 to that single `br` (IR experiment only) moves the whole tail back. The object-level
token ratio against the original goes from 0.2889 to 0.4452. A source form that makes the merged error re-check cold, or keeps the
post-sweep join from being the best successor there, is the next big step for this window. Tried without success: sweep
gate forms (t27-t30), inline sweep body (t15), inline(always) (t25), seed-local scoping (t23/t24), separate `if` for the
amm CPI (t11/t12).

The original gates the sweep on one bool (`[r10-0x8e0]`, 1 = skip) that is a phi of constants. It is set in the same paths that
build `sharing_update`/`collect_old`, and ours recomputes `holder & shared` at the gate.

## Attempts (ledger, approach `lddw-reloc-pairing`)

| trial | mechanism | result |
| --- | --- | --- |
| census | lddw pairing | only diff: String vtable 9 vs 11 (307/312 inlined to_string) |
| t01 | #2370 rebuilt on 255a0fd | 26,928 B, 0.32392, lddw equal |
| t02 | sharing_update computed before validate | rejected: validate stops being inlined (119 calls) |
| t03 | t01 + `mut new`, 306 `new.take()` | 27,104 B, 0.38940 |
| t04 | t03 + 298 `new.take().is_some()` | **27,144 B, 0.39061 (kept)** |
| t05 | t01 + take only at 298 | 27,120 B, 0.38115 |
| t06 | `let upd=if holder{None}else{new}` before validate | 27,256 B, 0.17447 (new now loaded before mayhem, but validation blocks move) |
| t07, t08 | plain `let upd=new` copy; new as first validate param | byte-identical to t04 |
| t09, t10 | swept definite assignment / if-expression (= #2214) | 27,128 B, 0.39103 (= rebased r1) |
| t11, t12 | amm CPI as a separate `if !amm_frozen&&..` | 27,136 B, 0.39037 |
| t13 | 296 back at top level, with take() | 27,528 B, 0.34788, 88 lddw (307/312 inline again) |
| t14 | `!(hr\|\|he)` spelling | byte-identical |
| t15, t16 | sweep / wallet body inline in execute | inliner flips (177 calls / loss 0xbc108) |
| t17, t18 | single take() at entry; 306 as `match` | identical / 0.37436 |
| t19, t20 | sharing_update spellings | byte-identical |
| t21, t22 | `holder.unwrap_or(false)` / `unwrap_or_default()` | 27,352 B (nearer size, orig-like `& 1`), but 0.31625 |
| t23, t24 | vault-seed locals inline / per branch | 0.21669 / 0.38498, 87 lddw |
| t25, t26 | `#[inline(always)]` on sweep / validate | 0.14462 (168 calls) / 0.38496 |
| t27-t30 | sweep gate: `if let Some(None)=sharing_update`, `holder&&shared`, phi-built bool | t27 breaks inlining; others byte-identical |
| llc | branch weight on the sweep.exit re-check (IR experiment) | object token ratio 0.2889 -> 0.4452 |
| r1 | branch rebased on e491c5e95 | 27,128 B, 0.39103, 0 losses |

## Merge review (notes-only)

Re-measured on origin/main 2de98cc1d (after #2412, which restored admin_cto to 27,344 B):
main 27,344 B / ratio 0.37637; main + this PR's source 27,144 B / ratio 0.39061; original 27,400 B.
Score 1032/347 on both, 0 gains and 0 losses. Under size-first ranking the change moves admin_cto
from 56 B to 256 B away from the original size, so the source change was not merged. Main's
programs/pump is kept; this lane's notes and SUMMARY.json are kept as the record.
