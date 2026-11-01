# w17a05-fees-unlikely: replace the two `core::intrinsics::unlikely` in Fees `social.rs`

Target: `programs/pump-fees/src/social.rs`, the claim rate-limit checks in `claim_v2` (line 9) and
`claim` (line 66), added by b992a381d. Goal: ordinary Rust with the Fees meaningful ELF unchanged
(`EXPECTED_CANDIDATE` 5b6ceda5…3dcf, `EXPECTED_SYMBOLS` 7ec99a69…4e66 in `programs/pump-fees/build_exact.py`).

## Result: both pins reproduced by a cold `build_exact.py` run of the new source

Both checks now bind the `&&` chain to a local and branch on it:

```rust
// line 9 (claim_v2)
let rate_limit=ctx.accounts.fee_program_global.claim_rate_limit; let limited=rate_limit!=0 && state.last_claimed!=0 && now<state.last_claimed.saturating_add(rate_limit); if limited {msg!("Claim rate limit exceeded");return Ok(None);}
// line 66 (claim)
  let limited=rate_limit!=0 && state.last_claimed!=0 && now<state.last_claimed.saturating_add(rate_limit); if limited {
```

Line count and every other line are unchanged. `lib.rs` keeps `#![feature(core_intrinsics, try_blocks)]`
as instructed. The `core_intrinsics` gate is now unused, and an unused gate does not change codegen.
The only other edit is the `social.rs` digest in `programs/pump-fees/exact/qualified-source-inputs.json`
(ba03d153…c468 → cf78111f…cf2c), which the builder checks before compiling.

Linux exact builds (`build_exact.py` unchanged, podman + the pinned image on this Mac; full key fields in
`RECEIPTS.json`):

| run | source | target | exact_symbols_equal | exact_candidate_equal | candidate sha256 | time |
| --- | --- | --- | --- | --- | --- | ---: |
| `v02_2` (builder receipt) | **this PR** (social.rs cf78111f) | cold, empty | true | **true** | 5b6ceda5…3dcf (873,256 B) | 1,835 s |
| `base2` (builder receipt) | main (social.rs ba03d153) | deps reused from `base1` via `--dependency-target/--dependency-provenance`; both local crates fresh | true | true | 5b6ceda5…3dcf | 95 s |
| `base1` | main | cold, empty; builder SIGKILLed externally, container finished, post-processing by hand | equal | equal | 5b6ceda5…3dcf | 2,673 s |
| `quick_v02` (not a receipt) | this PR | `base1` deps, builder commands verbatim | equal | equal | 5b6ceda5…3dcf | 106 s |

Native identity-rustc oracle (same-host differential, see below), every spelling applied to both checks:

| spelling | .so vs main |
| --- | --- |
| `let limited=a && b && c; if limited {..}` (this PR) | **identical** (IR identical modulo value names) |
| `match a && b && c {true=>{..} false=>{}}` | **identical** |
| plain `if a && b && c {..}` | different: only `claim` and `claim_v2` differ, by block order |
| `if !(a && b && c) {} else {..}` | different (same bytes as plain) |
| `if a && b { if c {..} }` | different (same bytes as plain) |
| `(a) & (b) & (c)` (no short circuit) | different (a third shape) |

## Mechanism: `unlikely` is a no-op as a weight but NOT as structure

The wave-17 note (w17a02 #3934) is right that no `!prof` survives: the intrinsic result goes through an
alloca, so LowerExpectIntrinsic never sees a branch. But **plain removal is not byte-identical here.**
`unlikely(..)` is a MIR `Call` terminator (`#[rustc_intrinsic]` with a fallback body; the MIR inliner
never inlines intrinsics). The `&&` chain is therefore evaluated into a bool local first, and only the
block after the call branches on it. rustc creates LLVM blocks in first-reference order while it
codegens MIR in reverse postorder, and a `switchInt` on a bool references its `0` (false) target first.

Optimized MIR of `claim` (`--emit=mir`) shows the difference at the `rate_limit` switch:

| spelling | `switchInt(rate_limit)` | its `0` target |
| --- | --- | --- |
| `unlikely(a && b && c)` (main) | `[0: bb8, otherwise: bb5]` | `bb8: _15 = const false; goto bb9` → `bb9: _14 = unlikely(move _15)` → `bb10: switchInt(_14) [0: cont, ..]` |
| `if a && b && c` (plain) | `[0: bb10, otherwise: bb5]` | `bb10` is the continuation itself |
| `let limited = a && b && c; if limited` | `[0: bb8, otherwise: bb5]` | `bb8: _14 = const false; StorageLive(_18); goto bb10` (MIR jump threading already skips the bool test, but the assignment block stays) |

- With the plain `if`, codegen of the `rate_limit` block creates the continuation before the
  `last_claimed!=0 && now<sat` test blocks. In `claim` the test (`icmp ne` / `uadd.sat` / `icmp ult` /
  `select`) lands nine blocks later, after the continuation's AccountInfo clone (Rc `inc_strong` and trap
  blocks).
- With `unlikely(..)`, the `let` or the `match`, the `0` edge goes to a `limited = false` block, so the
  continuation is first referenced only after the test blocks exist. SROA/SimplifyCFG later fold the
  bool away and merge the test blocks into one `select` block, without moving it.

The optimized instructions are the same in all of these. Only the block order differs, and the BPF block
placement keeps it. Ordinary Rust that materializes the condition reproduces the order without an
intrinsic. Peel lanes that remove `likely`/`unlikely` elsewhere (for example from an admin_cto shim)
should expect the same effect: `unlikely(c)` → `c` can move blocks; `let x = c; if x` keeps them.

## Oracle (about 1.5 min per variant under swarm load)

Native macOS build of the builder's staged workspace (`build_exact.stage`, macro locator pointed back to
the staged `vendor/used-public`) with the identity rustc
(`$C/toolchains/hybrid144/rust/bin/rustc`) and the v1.44 cargo, target `sbpf-solana-solana`,
`RUSTFLAGS=-Zremap-cwd-prefix=`, `--emit=llvm-ir,link` (`--emit=mir` alone for MIR). Its crate hashes
differ from the Linux build's (cargo hashes the host triple into `-C metadata` on a `-dev` rustc), so it
is a differential oracle: it compares variants against main on the same host, not against the pin.
Cargo fingerprints by mtime, so touch the variant after copying it in, or cargo silently reuses the
previous object.

## Exact build on this Mac

`build_exact.py` runs unchanged. Inputs:

- `--sdk`: the official Linux x86_64 platform-tools v1.44 tree (cargo/rustc/rust-lld hashes equal the
  builder's `TOOLS`), APFS-cloned from an existing extraction of the pinned archive (6719b889…b3e9).
- `--registry`: `cargo fetch --locked` (v1.44 cargo) of the staged `programs/pump-fees/Cargo.lock`,
  251 registry packages under `index.crates.io-6f17d22bba15001f`.
- `--objcopy`: the macOS arm64 v1.52 `llvm-objcopy` (`~/.cache/solana/v1.52`). The repo pins the Linux
  v1.52 binary. The builder only records the strip tool's hash, and the stripped candidate equals the pin.
- `podman`: Homebrew podman 5.5.2 with the existing applehv machine `podman-machine-default`
  (Rosetta x86_64 binfmt). The pinned image
  `solanafoundation/solana-verifiable-build@sha256:6c73adc7…ac50` was already in its store, so
  `--pull=never` works. No podman shim was needed. (Docker Desktop was not used.)

A cold build took 31-45 min under the swarm's load (load average 120-200), against 64 s on native Linux,
because `CARGO_BUILD_JOBS=2` runs 178 crates under Rosetta. A rebuild of the two local crates with
`--dependency-target`/`--dependency-provenance` takes about 95 s, but the builder only allows that for an
unchanged source inventory, so every source variant needs its own cold run.

Robustness: at about 21:50 PDT every process this session had started (both builder processes and a
foreground cargo) was killed with SIGKILL, cause unknown, while the two podman containers kept running.
Later builds ran under a `setsid` launcher, and `base1` was finished from its container's output (see
the table).

## CI note

Two research packets bind the current `social.rs` digest and will report the change:

- `research/fees-exact-readme-stage-20261030/replay.py` requires the README pin to be the only pin that
  differs from its `ORIGINAL-PINS.json`.
- `research/fees-linux-fresh-rebuild-20261030/verify.py` binds its two recorded cold-run receipts to the
  current canonical source inventory.

Both record historical builds of the old source. This lane does not rewrite them; whether to re-bind
them (for example with the receipts above) is the owner's call.

## Ledger keys

- `fees-social-w17-1647da0-unlikely-plain-removal-v1` (rejected: block order differs)
- `fees-social-w17-1647da0-unlikely-let-binding-v1` (byte-identical in the native oracle)
- `fees-social-w17-1647da0-unlikely-mir-block-order-analysis-v1` (MIR mechanism)
- `fees-exact-mac-podman-rosetta-main-1647da0-v1` (main reproduces both pins on this Mac)
- `fees-social-w17-1647da0-unlikely-let-binding-linux-quick-v1` (quick check, warm deps)
- `fees-social-w17-1647da0-unlikely-let-binding-linux-cold-receipt-v1` (cold builder receipt)
- `fees-social-w17-1647da0-unlikely-{v03_match,v05_else,v06_nested,v04_bitand}-v1` (other spellings)
