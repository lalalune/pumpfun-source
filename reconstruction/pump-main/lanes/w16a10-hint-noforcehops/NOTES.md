# w16a10-hint-noforcehops

Wave 16 lane. It replaces three compiler-steering constructs in Pump Main, all outside `admin_cto`, with ordinary
Rust that keeps every window byte-identical:

| site | construct | window(s) |
| --- | --- | --- |
| (a) | `admit_associated_token_account(.., payer:*const AccountInfo<'info>, ..)` + `let payer=unsafe{&*payer};` (buy_v2.rs:10, :61) | 0x14910 (and its callers, swap_hop 0x5b3b0 among them) |
| (b) | `let _=&c;` dummy borrow before `require_gte!(c.real_token_reserves,..)` (buy_v2.rs:996) | 0x13f630 `buy_exact_quote_in_v2` |
| (c) | `v3_buy_costs(..).map_err(core::convert::identity)?` (trade_v3.rs:814, #1878) | 0x147ba0 `buy_v3` |

Base: main 9bd38c7d5 (baseline `baseline-main-9bd38c7d5`: 1034/1034, admin_cto 0.67376 / 3124 / 27,400 B,
swap_hop matched, unstripped sha256 `d0c733f6…`).

## (b) dummy borrow: removed, byte-identical

`let _=&c;` is replaced by a `// layout-pad(1)` comment line, so `require_gte!` keeps line 997.

| | main 9bd38c7d5 | b0 |
| --- | --- | --- |
| normalized / raw | 1034 / 1034 | 1034 / 1034, no gains or losses |
| admin_cto | 0.67376 / 3124 / 27,400 B | same |
| swap_hop | 1.0 / 0 / 18,584 B | same |
| unstripped.so | `d0c733f630b54ee7…` | **cmp-equal** (stripped too) |

The borrow is not load-bearing on current main: the whole unstripped ELF is unchanged without it. It came in with the
8b905dc53 import and was presumably needed by an earlier shape of the handler.

Ledger: `0x13f630-w16-9bd38c7-noforcehops-dummyborrow-remove-v1`.

## (a) raw-pointer payer

| trial | form | result |
| --- | --- | --- |
| a1 | `payer:&AccountInfo<'info>`, no `unsafe` deref; callers unchanged | 1033 / 349: loses 0x14910 (6072 B vs 6080, ratio 0.6892); the payer stack arg is spilled to `[r10-0x308]` instead of held in r7, and owner / token_program swap r6/r7 |

## (c) map_err(identity)

| trial | form | result |
| --- | --- | --- |
| c0 | plain `v3_buy_costs(..)?` | 1033 / 301: loses 0x147ba0 (3688 B vs 3672); the shared Err return block is placed right after the costs Err test instead of later |
| c1 | `.map_err(Into::into)?` | does not compile (E0282/E0283: `?` applies `From` again, so the `Into` target is ambiguous) |

## Tools

- `tools/trial.sh <name> <slot> <edits.json>`: copy the lane crate, apply exact-once string edits that keep the line
  count, run `measure.sh`, and compare `candidate.so` / `unstripped.so` with the baseline's.
- `tools/capture2.py`: w16a01's `capture_ir.py` with raw rustc args as well (`--rustc -Zdump-mir=..`,
  `--llvm -print-after=..`), never used for proposals.
