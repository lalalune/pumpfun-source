# Donation Relay lanes: brief

Goal: Rust in `programs/donation-relay` whose build equals `relay/live/deployed.elf` (929,176 B, sha256 `0985c3a0…`), the program live since slot 462,683,179. `$C` below is `~/.cache/pumpfun-reconstruction`.

## Where things stand

Base every lane on **`origin/swarm/w20-relay-scout`**. It holds a skeleton of the upgrade: the four new instructions, the marker accounts, the events and `ExactTransfer`.

| build of `programs/donation-relay` | functions matched of 571 | `.text` bytes matched of 851,888 | ratio |
|---|---:|---:|---:|
| origin/main, unchanged, compiled with v1.54 | 443 | 588,792 | 0.69116 |
| plus 3 enum variants on `DaasEventDiscriminator` | 449 | 606,344 | 0.71176 |
| plus the skeleton from the on-chain IDL | 538 | 740,872 | 0.86968 |
| plus `#[instruction]` trimmed, default mint error, two recover constraints | 540 | 768,112 | 0.90166 |
| plus `check_message` and `check_bps` in `require!` shape | 542 | 769,080 | 0.90279 |
| plus `check_relayer` key pointer, direct arguments to admit | 544 | 773,224 | 0.90766 |
| **branch tip**, plus direct arguments to recover | **545** | **776,384** | **0.91137** |

All numbers are normalized matches, not byte identity. No function is at its final address yet, and whole-ELF identity is the only acceptance test. Do not merge to main before that: main currently reproduces the old target, and its packet `reconstruction/donation-relay/native-linux-v148-20261030/verify.py` binds that source.

## The toolchain: platform-tools v1.54, Linux target libraries

The old recipe's v1.48 is **not** the compiler of this deploy. Use v1.54: rustc 1.89.0-dev, LLVM 20.1.7, cargo 1.89.0, Rust commit `daa3af4a`. Evidence:

- `core::error::Error::type_id` for alloc's `StringError` is `0xb48b06e23bc32191/0x802914a71efcf08e` in the deployed ELF. Of the rlibs I checked (macOS v1.52, v1.53, v1.54 and Linux v1.54), only **Linux x86_64 v1.54** `liballoc-91c82d13bc4939af.rlib` holds that constant. Linux v1.52 and v1.53 were not checked; the function counts below separate those.
- Sysroot functions found in the deployed ELF: v1.51 85, v1.52 133, v1.53 158, v1.54 185.
- v1.55 and v1.56 are excluded: with them `solana_rent::Rent::minimum_balance`, `is_exempt` and `u128_div_rem` change and stop matching (v1.55 fixed float-to-int). v1.57 and later ship Rust 1.95.
- Dependencies: the current `Cargo.lock` (anchor 0.32.1, spl-token-2022 8.0.1, ...) reproduces every library function that is matched so far, and nothing points to a version change. `serde`, `bincode` and `core::num::flt2dec` appear in the new ELF because `Account<ProgramData>` decodes `UpgradeableLoaderState`; they matched by themselves once `program_data` was declared.
- The old source still reproduces the old target on v1.48: a fresh macOS build matches 492/492 windows normalized, same `.text` size. Its `.rodata` differs only in `/Users/runner` against `/home/runner` paths.

`$C/toolchains/hybrid154` is the macOS v1.54 compiler with the Linux x86_64 target libraries, so `/home/runner` paths and TypeIds come out right.

## Build and measure

```bash
T=$C/relay/tools
$T/measure.sh <worktree>/programs/donation-relay $C/relay/lanes/<lane>/work $C/relay/lanes/<lane>/out
```

About 5 s per build. One work dir per concurrent build, and your work dir and out dir go under `$C/relay/lanes/<lane>/`. It prints one JSON line: `functions_matched`, `bytes_matched`, `ratio`, `strict_matched`, `same_address`, `raw_same_address`, `sections`, `gains`, `losses`, `unmatched_top`, `extra_top`, `whole_elf_equal`, `sha`, `stack_warnings`. `<out>` holds `unstripped.so`, `candidate.so`, `link.map`, `build.log`, `functions.json` (per-function table). `gains` and `losses` are against `$T/baseline.functions.json`, the branch tip. Pass a 4th argument for another baseline. **Zero losses is required.**

`strict_matched` also resolves what normalization masks: callee identity and the contents behind `lddw` (strings, `Location` line and column). A function with `strict: false` is normalized-equal but not finished.

Linux route, checked (`python3 $T/relay.py measure <out>/unstripped.so` scores its output): `$T/linux-build.sh <crate dir> <out dir>` runs the official v1.54 Linux archive in `localhost/codex-relay-build-deps:20261027` under podman (linux/amd64 through Rosetta), about 2 min 20 s cold, one build at a time. On the source before the bridge accounts it gave the same 465 function bodies as the Mac hybrid and byte-equal `.rodata`, `.dynstr` and `.dynsym`, with `.text` differing only in the order of same-named generics, because symbol hashes depend on the host. Once the skeleton pulls in classic `spl_token`, Linux has two more functions than the Mac (item 9 below), while `.rodata` stays byte-equal. Use the Mac route for iteration. The old packet's `launch.py` was not run: it refuses any host but its one admitted Debian 13 profile, and it targets the old ELF.

## Reading a function on both sides

```bash
python3 $T/relay.py list <out>/unstripped.so --unmatched          # target table with names
python3 $T/relay.py diff <out>/unstripped.so 0x20580 --sym 'admit_bridge_payment$' -c 2   # token diff, - target, + yours
python3 $T/relay.py diff <out>/unstripped.so 0x20580 --sym '...' -c 0 --mask frame,jumps,regs   # structure only: start here
python3 $T/relay.py fn 0x20580                                    # target listing with strings and callee names
python3 $T/relay.py sym <out>/unstripped.so 'check_'              # your symbols
python3 $T/xref.py $C/relay/live/deployed.elf 0x638               # callers, on either ELF
python3 $T/strref.py $C/relay/live/deployed.elf programs/contracts/src/state/v1/bridge_membership.rs   # refs and Location line/col
python3 $C/relay/rea/v.py new 0x20580                             # annotated pseudo-C of the target
```

Other material:

- `$C/relay/live/idl.onchain.json`: the program's own IDL from account `6mCmANHqUcqWCLAUtB3DFJSDv14yWPq4wXUzDhdMj3Ge`, with accounts, seeds, args, events, docs and constants. Readable form: `$C/relay/rea/IDL.md`.
- `$C/relay/rea/FINDINGS.md`: handler-by-handler reading from the REA session. `c/new/<addr>.c` has pseudo-C for 463 functions. It was written before the toolchain was known, so read its "almost no function is byte-identical" as the compiler change, not source change.
- `$C/relay/LOCATIONS.target.txt` against `LOCATIONS.skeleton.txt`: every panic `Location` (file, line, column, referencing function).
- `$C/relay/RODATA.skeleton.diff.txt`: `.rodata` diff against the skeleton.
- `$C/relay/DELTA.md` and `DELTA.json`: the full table.
- Fresh REA queries: `python3 $C/rea/reaq.py $C/relay/live/deployed.elf decompile 0x20580 --text`, at most 1 REA or Ghidra process at a time. **Trap:** for a stripped ELF, `reaq.py` falls back to Pump Main's function names as seeds, which would be wrong addresses here. I placed the right seeds for the shared session only. For `--session <lane>`, first copy `$T/seeds.target.tsv` to `$C/rea/reaq/0985c3a02b9f0203-<lane>/seeds.tsv`.

## Instructions

Order in `#[program]`, from the `Instruction:` strings in `.rodata`. Discriminators are from the IDL and the dispatcher at `0x843e0`.

| instruction | discriminator | status | `__global` wrapper | handler |
|---|---|---|---|---|
| donate_v1 | 8808669cd60411ab | existing | 0x876c0 | 0x12a90 |
| donate_pubkey_config_id_v1 | bb8dcfd83cf6c49b | existing | 0x87fe0 | 0x16268 |
| donate_native_v1 | 79a00f2cdb2b8607 | existing | 0x88900 | 0x13448 |
| donate_native_pubkey_config_id_v1 | c0fe8410d02b9a52 | existing | 0x89208 | 0x14b58 |
| donate_pubkey_config_id_with_payer_v1 | 78d939f187688bb8 | existing | 0x89b10 | 0x16c20 |
| **admit_bridge_payment_v1** | 3c5bb9058561e137 | **new** | 0x8a430 | 0x20580 |
| **recover_bridge_payment_v1** | fe88e1f5dc384f3e | **new** | 0x8af18 | 0x21608 |
| close_donation_epoch_v1 | ab1c36d68c89655a | existing | 0x8b800 | 0x175d8 |
| swap_then_distribute_v1 | da55edb218ae6629 | existing, body differs | 0x8bf30 | 0x1ec18 |
| just_swap_v1 | cc9f84758456df49 | existing | 0x8c600 | 0x1dc88 |
| distribute_after_just_swapping_v1 | d2b031be93697377 | existing, split | 0x8cbc8 | 0x18af0 |
| distribute_non_swap_output_mint_v1 | 9895643076ec09f3 | existing, split | 0x8d3d8 | 0x1b810 |
| **distribute_exact_non_swap_output_mint_v1** | 8e9155080e1404cd | **new** | 0x8dbe8 | 0x1c878 |
| **distribute_exact_after_just_swapping_v1** | 7d8d4ade90321fc9 | **new** | 0x8e3f8 | 0x19c80 |
| upsert_mint_whitelist_v1 | d185fd0c5009e780 | existing | 0x8ec08 | 0x20360 |

New types: `BridgeSourceV1`, `BridgePaymentV1` (empty, `#[account]` at `state/v1/bridge_membership.rs` lines 4 and 8), `BridgeDonationAdmittedV1Event`, `BridgePaymentRecoveredV1Event` (`#[event]` at line 5), `DonationEpochProcessedExactV1Event` (line 6), `ExactTransfer`, and three new `DaasEventDiscriminator` variants. The exact instructions share the existing `Accounts` structs.

## Delta

Against the old source rebuilt on v1.54: 443 identical (588,792 B), 16 modified (40,120 B), 112 added (222,976 B), 6 removed (24,280 B). Only 105 of the 571 are identical to a function of the old deployed ELF, which is the compiler change rather than source change. The removed ones are mostly splits: `donate_shared` became 0x28e48 + 0x29ca8, `distribute` became 0x24578 + 0x25f00, `distribute_after` became 0x18af0 + 0x18478 + 0x1a6d8, `distribute_non_swap` became 0x1b810 + 0x1b090 + 0x1d2d0.

26 functions are open, 75,504 B, in 7 clusters, largest first. `DELTA.md` lists them by address.

| cluster | bytes | functions | source area |
|---|---:|---|---|
| C1-distribute-bps | 24,048 | 0x18478 0x18af0 0x1a6d8 0x1b090 0x1b810 0x1d2d0 0x24578 0x25f00 | `settlement_handlers.rs`: `distribute_after`, `distribute_non_swap`; `tools/distribution/shared.rs`: `distribute` |
| C2-distribute-exact | 14,320 | 0x8eb0 0x19c80 0x1c878 0x24ec0 0x27048 | exact functions in `settlement_handlers.rs` and `tools/distribution/shared.rs` |
| C3-jupiter-swap | 11,120 | 0x11668 0x11f80 0x1ec18 | `cpi/jupiter.rs`, `swap_then_distribute` |
| C4-donate | 8,952 | 0x28e48 0x29ca8 | `tools/donate/shared.rs`, plus the five donate `Location`s (see below) |
| C5-bridge-handlers | 8,560 | 0x20580 0x21608 | `bridge_handlers.rs` |
| C6-checks | 5,792 | 0x227e8 0x22b78 0x23230 | `tools/checks.rs` |
| C7-framework-layout | 2,712 | 0x1590, plus 0xb3278 0xbcac0 (Linux build only, see below) | one generic instance, then `.text` order, `.rodata`, whole ELF |

C2 depends on C1's split helpers (0x18478, 0x1a6d8, 0x1b090, 0x1d2d0), and C5 depends on C4's signed-transfer core (0x29ca8). Agree on helper names through the branch: C1 and C4 should push their helper signature early.

## What I learned

Facts, checked by building:

1. **`require!` shape.** `if !(cond) {return Err(..)}` lays out differently from `if bad {return Err(..)}`, with the Ok path first. It took `check_message` and `check_bps` to exact. Much of this source was tuned for v1.48, so expect other sites to want the macro's shape.
2. **`#[instruction(...)]` stops at the last argument the seeds use:** four arrays in admit, three in recover. Listing all seven in admit cost 72 B of `try_accounts`.
3. **`address = X` uses the default `ConstraintAddress` (0x7dc) on the USDC mint.** Adding `@ InvalidMint` changes one token.
4. **Recover's constraints live in `try_accounts`, with `InvalidOwner` and `InvalidAdmin`:** `destination_owner != default && != receiver`, and `program_data.upgrade_authority_address == Some(authority.key())`.
5. **`DaasEventDiscriminator`'s niche is code:** `stb [r6+0x58], 0x7` was `0x4`. It is fixed on the branch.
6. **Boundaries.** `relaylib.Elf.functions()` reproduces all 492 old symbols, with no extras or misses. REA's `relayfn.py` misses a few. Pointers in `.data.rel.ro` are stored in the high 4 bytes of the word (`Elf.ptr`). `Location` file strings now include the trailing NUL in their length.
7. **Direct handler arguments.** Admit's handler takes `source_id, source_commitment, payment_id, config_id, amount, minimum_amount, tip_bps, receiver_bump, epoch_tracker_bump, debouncer_bump`, and recover's takes `source_id, source_commitment, payment_id, amount, receiver_bump`, not args structs. That took both wrappers (0x99d70, 0x933a0) to exact. Both bodies are still open. Admit builds its signer seeds later than the skeleton does. Recover is at 4,296 of 4,328 B: `accounts.program.try_borrow_data()?` then `UpgradeableLoaderState::try_deserialize_unchecked` is right, and the amount checks at line 95 still differ (the target has an overflow check on the destination side).
8. **`check_relayer`:** `let key=signer.key; if *key!=RELAYER {.. with_pubkeys((*key,RELAYER))}` is exact.
9. **The final build has to be Linux.** 0xb3278 and 0xbcac0 are not source work. The Linux build of the same source has them and the Mac build does not: in the deployed ELF and on Linux, `spl_token::instruction::transfer_checked` calls a different `RawVec::grow_one` instance from `spl_token_2022::instruction::*`, and on the Mac both call one. The likely cause is that rustc picks the upstream copy of a shared generic by crate hash, and Cargo's metadata hash includes the host. So the Mac route tops out at 569 of 571, and that is expected: use it for iteration and confirm with `linux-build.sh`.
10. **Line numbers are literals in the error macros.** The per-file sites are in `$C/relay/rea/source_lines.json`; `tools/donate/shared.rs` moved by +42 (applied), `tools/distribution/shared.rs` has new sites 82, 131-201.

Readings not yet confirmed by a build:

- **Recover's line 66** most likely compares the programdata address decoded from `program` with `program_data.key()`, as the skeleton now does. The rest of the function still differs, so this is not proved yet.
- **`Location`s pin source files.** The target has `donate.rs:116:34`, `donate_native.rs:165:34`, `donate_native_pubkey_config_id.rs:159:34`, `donate_pubkey_config_id.rs:118:34`, `donate_pubkey_config_id_with_payer.rs:129:34`. Those five handlers currently report `donation_handlers.rs` (strict false). So the handler bodies belong in the instruction files at those coordinates, and `donation_handlers.rs` must vanish from `.rodata`. The target has no `Location` in `tools/distribution/shared.rs`, so no panicking `[index]` there.
- **`with_values` has three instances in the target:** 0x638 (swap_observed, admit, exact), 0xe00 (the `admit_shares` sites), 0x1590 (14 try_accounts closures). The skeleton has two. 0x1590's body equals 0x638's, so check the argument types once the callers match.

## Whole-ELF route (C7)

1. All 571 functions matched and strict.
2. `python3 $T/mkorder.py <out>/unstripped.so <out>/link.map > ordered.ld`, then rebuild with `RELAY_LINKSCRIPT=$PWD/ordered.ld`, which both `measure.sh` and `linux-build.sh` honor. Tested on the Mac route at 542 functions: all matched functions came out in target order and `.rodata` was unchanged. Selectors carry this build's symbol hashes, so regenerate after any source change and use a Linux `link.map` for a Linux build.
3. `.rodata` and `.data.rel.ro` are laid out in codegen order. Natural order already gets most of it (see `RODATA.skeleton.diff.txt`), and the old source reached identity that way. What differs is tied to open source items, so re-check it after the functions close.
4. Then `whole_elf_equal` in the JSON. As I remember rustc's `items_in_deterministic_order` (not measured here), instances without a local DefId sort first by mangled name and local items then follow by DefId. If so, the target's order of local functions is also a reading of the original's item order.

Ordered selectors are host-keyed, so a Linux build needs selectors from its own `link.map`.

## Rules

asm!, global_asm!, include_bytes!/include_str! of original sections, transcribed machine code, ELF patching and scorer changes are forbidden. Read the deployed code to understand it and write Rust. No compiler-steering constructs (`black_box`, `read_volatile`, `core::intrinsics`) in this crate: the shim allowance was for `admin_cto.rs` only. Push your branch often. At most 4 processes, at most 1 REA or Ghidra process. Do not open notes-only PRs. Leave `programs/pump` alone.
