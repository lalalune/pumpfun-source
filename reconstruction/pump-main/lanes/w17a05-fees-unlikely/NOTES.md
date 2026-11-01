# w17a05-fees-unlikely: replace the two `core::intrinsics::unlikely` in Fees `social.rs`

Target: `programs/pump-fees/src/social.rs`, the claim rate-limit checks in `claim_v2` (line 9) and
`claim` (line 66), added by b992a381d. Goal: ordinary Rust with the Fees meaningful ELF unchanged
(`EXPECTED_CANDIDATE` 5b6ceda5…3dcf, `EXPECTED_SYMBOLS` 7ec99a69…4e66 in `programs/pump-fees/build_exact.py`).

## Result

Both checks now bind the `&&` chain to a local and branch on it:

```rust
// line 9 (claim_v2)
let rate_limit=ctx.accounts.fee_program_global.claim_rate_limit; let limited=rate_limit!=0 && state.last_claimed!=0 && now<state.last_claimed.saturating_add(rate_limit); if limited {msg!("Claim rate limit exceeded");return Ok(None);}
// line 66 (claim)
  let limited=rate_limit!=0 && state.last_claimed!=0 && now<state.last_claimed.saturating_add(rate_limit); if limited {
```

Line count and every other line are unchanged. `lib.rs` keeps `#![feature(core_intrinsics, try_blocks)]`
as instructed (the `core_intrinsics` gate is now unused; unused gates do not change codegen).
The only other edit is the `social.rs` digest in `programs/pump-fees/exact/qualified-source-inputs.json`
(ba03d153…c468 → cf78111f…cf2c), which the builder checks before compiling.

Evidence (see the PR body for the Linux exact-build receipt):

| build | social.rs | result |
| --- | --- | --- |
| native oracle, main | `unlikely(..)` | base (`0425e21a…`) |
| native oracle, v01 plain `if a && b && c` | no intrinsic | **different**: only `claim` and `claim_v2` IR differ (block order) |
| native oracle, v02 `let limited=..; if limited` | no intrinsic | **byte-identical** .so, IR identical modulo value names |
| Linux exact build (podman, pinned image, Rosetta), main | `unlikely(..)` | see PR |
| Linux exact build, v02 | no intrinsic | see PR |

## Mechanism: `unlikely` is a no-op as a weight but NOT as structure

The wave-17 note (w17a02 #3934) is right that no `!prof` survives: the intrinsic result goes through an
alloca, so LowerExpectIntrinsic never sees a branch. But **plain removal is not byte-identical here.**
`unlikely(..)` is a MIR `Call` terminator (`#[rustc_intrinsic]` with a fallback body; the MIR inliner
never inlines intrinsics). The `&&` chain is therefore evaluated into a bool local first, and only the
block after the call branches on it. rustc creates LLVM blocks in first-reference order while it
codegens MIR in reverse postorder, and a `switchInt` on a bool references its `0` (false) target first:

- `if a && b && c {..}` lowers through `then_else_break`: the `rate_limit==0` test references the
  continuation first, so the `last_claimed!=0 && now<sat` test block is created after it. In `claim` the
  test (`icmp ne` / `uadd.sat` / `icmp ult` / `select`) lands nine blocks later, after the
  continuation's AccountInfo clone (Rc `inc_strong` and trap blocks).
- `unlikely(a && b && c)` and `let limited = a && b && c; if limited` both evaluate the chain into a
  local. The false edges reference the bool-assignment blocks, not the continuation, so the
  continuation is first referenced only by the final branch on the bool. The test block is created right
  after the `rate_limit==0` test, before the continuation, and SROA/SimplifyCFG later fold the bool away
  without moving blocks.

The optimized instructions are the same in all three. Only the block order differs, and the BPF block
placement keeps it. Ordinary Rust that materializes the condition reproduces the order without an
intrinsic. Peel lanes that remove `likely`/`unlikely` elsewhere (for example from an admin_cto shim)
should expect the same effect: `unlikely(c)` → `c` can move blocks; `let x = c; if x` keeps them.

## Oracle (about 1.5 min per variant under swarm load)

Native macOS build of the builder's staged workspace (`build_exact.stage`, macro locator pointed back to
the staged `vendor/used-public`) with the identity rustc
(`$C/toolchains/hybrid144/rust/bin/rustc`) and the v1.44 cargo, target `sbpf-solana-solana`,
`RUSTFLAGS=-Zremap-cwd-prefix=`, `--emit=llvm-ir,link`. Its crate hashes differ from the Linux build's
(cargo hashes the host triple into `-C metadata` on a `-dev` rustc), so it is a differential oracle: it
compares variants against main on the same host, not against the pin. Cargo fingerprints by mtime, so
touch the variant after copying it in, or cargo silently reuses the previous object.

## Exact build on this Mac

`build_exact.py` runs unchanged. Inputs:

- `--sdk`: the official Linux x86_64 platform-tools v1.44 tree (cargo/rustc/rust-lld hashes equal the
  builder's `TOOLS`), APFS-cloned from an existing extraction of the pinned archive (6719b889…b3e9).
- `--registry`: `cargo fetch --locked` (v1.44 cargo) of the staged `programs/pump-fees/Cargo.lock`,
  251 registry packages under `index.crates.io-6f17d22bba15001f`.
- `--objcopy`: the macOS arm64 v1.52 `llvm-objcopy` (`~/.cache/solana/v1.52`). The repo pins the Linux
  v1.52 binary; the strip is host-independent, and the candidate hash is what the builder checks.
- `podman`: Homebrew podman 5.5.2 with the existing applehv machine `podman-machine-default`
  (Rosetta x86_64 binfmt). The pinned image
  `solanafoundation/solana-verifiable-build@sha256:6c73adc7…ac50` was already in its store, so
  `--pull=never` works. No podman shim was needed.

Under the swarm's load (load average about 160) a cold build takes far longer than the 64 s recorded on
native Linux, because `CARGO_BUILD_JOBS=2` runs about 250 crates under Rosetta.

## CI note

Two research packets bind the current `social.rs` digest and will report the change:

- `research/fees-exact-readme-stage-20261030/replay.py` requires the README pin to be the only pin that
  differs from its `ORIGINAL-PINS.json`.
- `research/fees-linux-fresh-rebuild-20261030/verify.py` binds its two recorded cold-run receipts to the
  current canonical source inventory.

Both record historical builds of the old source. This lane does not rewrite them; whether to re-bind
them (with fresh receipts for the new source) is the owner's call.

## Ledger keys

- `fees-social-w17-1647da0-unlikely-plain-removal-v1` (rejected: block order differs)
- `fees-social-w17-1647da0-unlikely-let-binding-v1` (byte-identical in the native oracle)
