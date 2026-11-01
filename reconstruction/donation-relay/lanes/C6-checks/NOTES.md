# C6-checks: `tools/checks.rs` leaf functions

Base: `origin/swarm/w20-relay-scout` at `dfcbfc6ae`. Numbers are from the Mac route (`measure.sh`). They are normalized matches, and these three functions are also `strict`. No function is at its final address yet and `whole_elf_equal` is false.

| step | source change | functions | `.text` bytes | gains | losses |
|---|---|---:|---:|---|---|
| base | | 545 | 776,384 | | |
| 1 | `pub fn native_mint_for_program` | 547 | 777,728 | 0x227e8, 0x22b78 | none |
| 2 | transfer fee test joined with `\|` in `typed_mint_safe` | 548 | 782,176 | 0x23230 | none |

Linux route (`linux-build.sh`, then `relay.py measure`) at the source of step 2: 550 functions, 782,896 B, zero losses. All three functions are `strict` there too, and 0xb3278 and 0xbcac0 are the two Linux-only gains the brief expects.

## 0x227e8, 0x22b78: visibility

The target keeps the lookup out of line although it has one caller. As a private `fn` it inlines into `native_mint_pair`. As `pub fn` it stays out of line (`-C remark=inline`: cost 345, threshold 250), and both functions are exact on the first build. The `require!` shape was not needed.

## 0x23230: the Default Account State extension has to inline

The target inlines `get_extension` for five extensions and calls it for `NonTransferable` only. The candidate also called it for `DefaultAccountState`, and that extra instance was the 552 B size gap (3,896 against 4,448 B).

`-C remark=inline` shows the decision:

| source | `get_extension::<DefaultAccountState>` |
|---|---|
| `\|\|` in the fee test | not inlined, cost 910, threshold 45 |
| `\|` in the fee test | inlined, cost -14090, threshold 250 |

`NonTransferable` stays at threshold 45 (cost 905) in both. My reading is that 45 is LLVM's cold call-site threshold, which also drops the last-call bonus, so one less branch before this call lifts it out of the cold range. I took that from memory of `InlineCost.cpp` and did not read the frequencies themselves.

Variants of the fee block, measured against the 540 target tokens:

| fee block | `get_extension` instances | size | tokens matched |
|---|---:|---:|---:|
| `auth.is_some() \| (older!=0) \| (newer!=0)` | 1 | 4,448 | **540, exact** |
| `let auth=..is_some(); if (older,newer)!=(0,0) \|\| auth` | 1 | 4,448 | 537 |
| `let auth=..is_some(); let older; let newer; if auth \|\| older!=0 \|\| newer!=0` | 1 | 4,448 | 536 |
| `let auth=..; let older; let newer; if older!=0 \|\| newer!=0 \|\| auth.is_some()` | 2 | 3,896 | 372 |
| `let auth=..; if older!=0 \|\| newer!=0 \|\| auth.is_some()` | 2 | 3,896 | 370 |
| `let safe=..is_none() && older==0 && newer==0; if !safe` | 2 | 3,896 | 349 |

## For other lanes

- Inliner remarks are cheap: add `-C remark=inline` after `--` in the `cargo rustc` line, about 5 s per build. A threshold of 45 on a call you expected inlined points at branches earlier in the same function, not at the callee. C1 and C2 may want this for their split helpers.
- `admit_shares` is still an extra 672 B function in `.text`. The target has no standalone copy. `#[inline(always)]` removes it, with no gains and no losses at this tip. I did not apply it, because it changes the handlers C1 is working on.
