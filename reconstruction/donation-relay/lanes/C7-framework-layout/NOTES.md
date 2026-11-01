# C7-framework-layout: 0x1590, 0xb3278, 0xbcac0, `.text` order and the whole ELF

Base: `origin/swarm/w20-relay-scout` at `dfcbfc6ae` (545 of 571 functions, 776,384 of 851,888 `.text` B, 0.91137, normalized, zero losses).

## Result

The merged source on this branch, built on the Linux route with `ordered.ld`, gives an ELF that `cmp` finds identical to `relay/live/deployed.elf`:
929,176 B, sha256 `0985c3a02b9f02035e677b99d63b42b0484d0734e3e66e5e36fd4509dd600624`. 571 of 571 functions, strict 571, same address 571, raw same address 571.
`.text`, `.rodata`, `.data.rel.ro`, `.dynsym`, `.dynstr` and `.rel.dyn` are all equal.

| build | functions | `.text` B | strict | same address | `.rodata` | whole ELF |
|---|---:|---:|---:|---:|---|---|
| scout tip, Mac | 545 | 776,384 | 527 | 4 | differs | no |
| merged tip, Mac, natural order | 569 | 851,168 | 550 | 243 | equal | no |
| merged tip, Linux, natural order | 571 | 851,888 | 549 | 435 | equal | no |
| merged tip, Linux, `ordered.ld` | 571 | 851,888 | 571 | 571 | equal | **yes** |

### Reproduce

```bash
C=$HOME/.cache/pumpfun-reconstruction; D=reconstruction/donation-relay/lanes/C7-framework-layout
podman machine start   # if it is stopped
RELAY_LINKSCRIPT=$PWD/$D/ordered.ld $C/relay/tools/linux-build.sh programs/donation-relay <out dir>
cmp <out dir>/candidate.so $C/relay/live/deployed.elf
```

To regenerate the script after any source change, build once without `RELAY_LINKSCRIPT`, then run `python3 $D/mkorder2.py <out>/unstripped.so <out>/link.map > ordered.ld`, because selectors carry
this source's symbol hashes. A selector that no longer matches falls through to `*(.text*)` without an error, so a stale script fails at `cmp` and not at link time.

**Cold check.** The committed tree and committed `ordered.ld` at `d609f661f`, exported with `git archive` and built with the unmodified `linux-build.sh` and an empty `/target`: 178 crates compiled, none fresh, 133 s, and `cmp` reports no difference.
`relay/live/programdata-account.bin` after its 45 B header also equals `deployed.elf`, and that header records deploy slot 462,683,179.

### What this does and does not establish

- **The identity depends on `ordered.ld`.** It holds 571 `.text` section selectors in the deployed order, plus the stock layout. It holds no machine code, and it is target-derived link order, as the old packet's `ordered.ld` was. The natural-order link of the same source is not identical: 41 functions are out of order. 36 are same-named instances that I read as sorted by symbol hash, which depends on the crate's identity (see the last section). The other 5 are the donate handlers, because `settlement_handlers` is declared ahead of `instructions`.
- **Forbidden constructs:** the crate and `error-model` were scanned for `asm!`, `global_asm!`, `include_bytes!`, `include_str!`, `black_box`, volatile access, intrinsics, `link_section`, `no_mangle` and `.incbin`, with no hits. There is no `build.rs` and no `.cargo` directory. The compiled modules have no `unsafe` and no `hint` calls. Seven functions carry `#[inline(never)]`, an ordinary attribute.
- **Not the original source text.** The crate is still `donation_relay_source_proposal`, the program module is `anchor_framework::relay_anchor_idl_reconstruction_probe`, and the settlement handlers live in `settlement_handlers.rs`. Byte identity shows this source compiles to the deployed program, not that the original looked like this.
- **Host:** this ran under podman, linux/amd64 through Rosetta, in `localhost/codex-relay-build-deps:20261027`, with the official v1.54 Linux archive. No native Linux host was tried. The ELF was not executed.
- **`main` is not ready for this merge.** This source no longer reproduces the old target. `native-linux-v148-20261030/verify.py` run on this branch stops with `ValueError: source file inventory mismatch`, because the packet binds the 60 old inputs. 19 files under `reconstruction/`, `scripts/` and `tests/` name `programs/donation-relay`, and `.github/workflows/verify.yml` runs that packet's tests. How the old target's packet stays verifiable is a decision for the merge, and this lane did not make it.

## 0x1590: the third `with_values` instance

The target has three: 0x638 (1992 B: swap_observed, admit, exact distribution), 0xe00 (1936 B: the bps-sum sites) and 0x1590 (1992 B: 13 `try_accounts` closures and `__idl_set_buffer`).
0x638 and 0x1590 have identical listings, callees included. On the scout tip the 0x638 instance, whose arguments are `u64`, had one caller, `swap_observed`, and that call was inlined. The target's admit handler also calls it at the line 83 mismatch (`InputAmountMismatch`, line `0x53`):

```rust
.with_values((amounts.gross_amount,amount))
```

That second caller keeps the instance out of line: 546 of 571, 778,376 B, zero losses, gain 0x1590. C3 and C5 reached the same edit.
The 14 callers of 0x1590 reach Anchor's `(space, actual_field.data_len())`, so I read that instance as `(usize, usize)`. The two bodies are equal because both format through the same `_fmt`.

## 0xb3278 and 0xbcac0: no source work

Both appear on Linux and not on the Mac, as the scout measured. In the ordered Linux build both are raw-identical at their addresses. The Mac route tops out at 569 of 571 on this source, and its `.text` is short by exactly their 720 B.

## `.text` order: `mkorder2.py`

`relay.compare` pairs functions by normalized body, first free. Bodies are not unique (the `u64` and `usize` `with_values`, two `Signer::try_accounts`, two `Account::reload`, `finish_grow` and others), and a wrong pair scores the same but puts an instance at the other's address. That explains C4's and C3's "strict is lower on Linux" (549 here): with the pairing fixed, strict is 571.

`mkorder2.py` is `mkorder.py` with that one blocker fixed. It resolves each group from the k-th call of paired callers, from paired callees, from data content and from `.data.rel.ro` slots that point into `.text`. On the Linux build it pairs 571 of 571 with zero conflicting callees, and 8 pairs differ from `relay.compare`'s. One group stays ambiguous, `<&T as Display>::fmt` at 0xaccf0 and 0xb84b0. It pairs in address order, and the `cmp` result shows that was right.

## `.rodata` and `.data.rel.ro`: source order, no script needed

`.rodata` comes out byte-equal on the natural order, Mac and Linux, so nothing there depends on the script. Three source changes got it there:

1. **`#[access_control(check_relayer(&ctx.accounts.signer))]` on the nine relayer instructions** (C5 found this too). The target's wrappers run `donate_*`, recover, entrypoint and the allocator shims, then exact_after, exact_non_swap, non_swap, after, just_swap, swap_then_distribute, close, admit, which is reverse IDL order. The eight wrappers in that run are the ones that start with `check_relayer`, and the ninth, upsert, has no separate wrapper in the target. The attribute expands to the same statement and the wrappers land in the target's order. No function changed. My reading of the mechanism, from memory of rustc and not measured: their DefIds are allocated when the attribute expands, so later and in reverse.
2. **No direct `borsh` reference in `codec/wire.rs`** (`use anchor_lang::prelude::*`, `AnchorDeserialize`, `AnchorSerialize`). This is crate link order, not the symbol hash C5 suspected. The target runs `solana_pubkey, borsh, solana_sha256_hasher, serde_core, std`. The direct `use borsh::BorshDeserialize` gave `solana_pubkey, solana_sha256_hasher, serde_core, borsh, std`. Removing it moved `borsh` to the target's place and took `Unexpected length of input` out of the `.rodata` diff, with no gains or losses. My reading of the mechanism, also from memory: crate numbers are allocated on first reference, and the link line follows the reverse postorder over them.
3. **Module order and function placement from the other lanes:** C5's module order for `events`, `state` and `instructions`, C4's handler move, and C1 and C2's removal of the `tools/distribution/shared.rs` Locations.

## Merging

This branch merges C1 to C6, so it is the integrated tree. Its source matches each lane's tip at the time of writing. Conflicts resolved:

- `bridge_handlers.rs` stays deleted. C5 moved it, and the `with_values` edit from C3 and C7 is in C5's admit module.
- `codec/wire.rs` keeps the anchor derives, plus C2's `Copy` on `ShareType`.

## Not pursued: natural order without a script

Getting the 36 generic instances into order without `ordered.ld` would need the original crate's symbol hashes, which depend on its stable crate id. That id is cargo's metadata hash over the package name, version, workspace-relative path, features, profile and dependency set, and some local paths would also have to change (`#[program]` at the crate root, no `anchor_framework`). The IDL gives `donation_relay` 0.6.0, and the paths suggest `programs/contracts`. The rest is unknown, and a guess is all-or-nothing. The natural order can test a guess, because same-named instance groups would all fall into place, and on Linux the final crate rebuilds in about 10 s. Byte identity does not need it.
