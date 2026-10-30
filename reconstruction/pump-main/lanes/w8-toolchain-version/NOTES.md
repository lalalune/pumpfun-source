# Lane w8-toolchain-version: which toolchain built the original?

Wave 8 (build inputs in scope, #2221). Angle: platform-tools, rustc, LLVM, cargo and host.
Baseline: origin/main `ce53d86` with the current identity recipe (`hybrid144`: macOS arm64 v1.44
rustc with the Linux x86_64 v1.44 `sbpf-solana-solana` libraries). It scores **1027 normalized /
276 raw**, unstripped sha256 `31ec6381…`. All outputs are under
`~/.cache/pumpfun-reconstruction/lanes/w8-toolchain-version/out/<trial>`.

## Result

The original was built with the **official platform-tools v1.44 `linux-x86_64` package**. The
current recipe already uses that compiler's code generation exactly. No other toolchain release
and no other host changes any of the 8 unmatched windows. For those windows, this angle is
exhausted. The only open toolchain input is the cargo host triple, which affects symbol hashes,
not code. The current macOS-host recipe is not the original host, but it scores best by
coincidence.

## Evidence

| question | evidence | verdict |
| --- | --- | --- |
| sysroot | Each v1.44 host package ships its own `sbpf` sysroot with different crate hashes (`libcore-52876eb403c2f847` linux-x86_64, `libcore-6130cd54e37b54ec` osx-x86_64; linux-aarch64 and osx-aarch64 also differ). TypeId constants encode those hashes. All 5 type_id bodies of our build (4x `core::error::Error::type_id`, 1x `<T as Any>::type_id`) occur verbatim in the original. Full builds with the linux-aarch64 and osx-x86_64 packages lose exactly those 5 windows (1022). The macOS recipe also gives 1022 (w8-elf-meta). | linux-x86_64 package only |
| host | A package ships its compiler and sysroot together. The original's std/alloc panic paths are `/home/runner/work/platform-tools/…` (the Linux GitHub-runner sysroot). | x86_64-unknown-linux-gnu host (unless someone mixed packages) |
| v1.43 | e_machine 263 in the original; v1.43 emits 247 (prior audit). Its rustc has no `sbpf-solana-solana` target. Its llc rejects `+store-imm,+jmp-ext` (w4-v3costs). | excluded |
| v1.45 | The v1.45 compiler with v1.44 sysroot gives **every function and every section byte-identical** to the baseline. The only differences are its rust-lld's LOAD `p_align 0x1000`; the original and v1.44 have `0x8`. | excluded by linker; codegen indistinguishable |
| v1.46 | 949/251 with v1.44 sysroot (78 normalized losses). The prior audit also found its sysroot helper bodies negative. | excluded |
| v1.46.1 (2026-09-15) | 776/141 (251 losses), `p_align 0x1000`. Release digest verified. The prior audit found `core::fmt::write` 1160 B, against 1056 B in the original. | excluded |
| v1.47+ | Rust 1.84 / 1.89 / 1.95 (release notes). | excluded |
| cargo-build-sbf | Agave v2.2.1–v2.2.2 are the only releases that default to v1.44. They run `cargo +solana build --release --target sbpf-solana-solana`. That is the platform-tools cargo 1.79.0 (`804e325`), with `CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS=" -Zremap-cwd-prefix="` and CC/AR/OBJDUMP/OBJCOPY from the SDK. The recipe already does exactly this. | matches |

## Builds (ledger rows by `w8-toolchain-version`)

| trial | normalized | raw | gains / losses vs base | notes |
| --- | ---: | ---: | --- | --- |
| base (hybrid144, macOS host) | 1027 | 276 | | `31ec6381` |
| **full Linux x86_64 v1.44** (podman linux/amd64, real cargo/rustc/LLVM/host) | 1027 | 270 | raw +2 −8 | `ca1b84ae`; the normalized set is identical, and the differences are all symbol-hash order |
| `-vV` host shim x86_64-unknown-linux-gnu | 1027 | 270 | raw +2 −8 (different +2) | not byte-identical to the real Linux build: 11 crates differ (host-side proc-macro deps) |
| `-vV` host shim x86_64-apple-darwin | 1027 | 269 | raw +2 −9 | |
| full osx-x86_64 v1.44 package (Rosetta) | 1022 | 269 | 5 TypeId losses | |
| full linux-aarch64 v1.44 package (podman arm64) | 1022 | 255 | 5 TypeId losses | |
| v1.45 compiler + v1.44 sysroot | 1027 | 276 | none | identical code, `p_align 0x1000` |
| v1.46 compiler + v1.44 sysroot | 949 | 251 | 78 losses | |
| v1.46.1 compiler + v1.44 sysroot | 776 | 141 | 251 losses | |
| Linux host + AMM lock's generic-array 0.14.7 / crypto-common 0.1.7 | 1027 | **280** | raw +5 −1 (`0x1a7b00`) | `2976eb3f`, see below |
| same lock change, macOS host | 1027 | 268 | raw +1 −9 | |

The 8 unmatched windows (`0x13f630 0x13b9b8 0x80df8 0x72810 0x1489f8 0x1e7c0 0x5b3b0 0x22a10`)
have identical size, slots_diff and ratio in base, Linux, Linux+lock and v1.45.

## Host and lock interact (for metadata/lock lanes)

- Cargo 1.79's `-C metadata` hashes `rustc -vV` (host), RUSTFLAGS, profile, features and every
  dependency's metadata. So the host and every `Cargo.lock` version below a crate decide its
  symbol hashes, and with them the hash order of generic instances inside each object (U and D blocks).
- With the Linux host plus generic-array 0.14.7 / crypto-common 0.1.7, the metadata of 116 of
  the 118 crates in `scripts/amm_sell/metadata-map.json` equals the AMM's Linux values. The 2
  that differ are anchor_lang and anchor_spl, whose features differ. D same-generic groups go
  from 21/27 to 23/27 exact (pairwise 290 → 295/317), and spl_token_2022's 3-instance `grow_one`
  group comes into original order. The one raw loss, `0x1a7b00`, is solana_pubkey's two
  `<&T as Debug>::fmt` instances (112 B and 168 B). Both originals (Pump `0x1a7b00/0x1a7b70`, AMM
  `0x10dcb0/0x10dd20`) have them in the order 112, 168; our Linux/AMM-metadata build has 168, 112.
  So **the AMM metadata map is not the original metadata either**. The AMM recipe fixes D order
  with its link script, and its map only names sections.
- The pump `Cargo.lock` contains versions published after the deployment. Last deploy slot
  458921440 is about 2026-10-15 (capture slot 461038878 = 2026-10-24T23:35Z). The lock has libc
  0.2.191 (2026-10-16) and cc 1.10.0 (2026-10-23). It is therefore not the original lock, and
  hash order cannot be reproduced from it.
- `tools/dgroups.py` measures per-crate hash-group order agreement against the original, using
  rlib symbol ownership. Each crate's order depends only on that crate's own metadata inputs. This
  is the discriminator a lock-date search needs.

## Tools

- `linuxbuild.py`: the complete official Linux v1.44 package in podman (`--platform linux/amd64`
  or `linux/arm64`), on the same workspace that fastbuild.py stages. It holds 2 build slots.
- `tools/xbuild.py` + `tools/rustc-hostvv`: alternative rustc/cargo (`--rustc`, `--cargo`) and a
  `-vV` host shim (`--fake-host`), for experiments only.
- `tools/dgroups.py`: per-crate hash-group agreement. `tools/grpagree2.py` is the census
  U/L/D agreement without re-running refine.

## Next ideas

1. If the link-script recipe (#2251) lands, hash order no longer reaches raw. The evidence-correct
   Linux x86_64 host could then become the recipe without raw losses. Regenerate `ordered.ld`
   from a Linux build (`linuxbuild.py` + regen), then check MergeFunctions twin choices (these
   depend on names) for gains.
2. Without a link script, run a lock-as-of-date search (T ≤ 2026-10-15, using crates.io
   `created_at`) under the Linux host, scored by `dgroups.py` agreement and raw. Full D-order
   agreement would be strong evidence for the original lock.
3. The toolchain cannot explain the residuals of the 8 windows (0x80df8's regalloc tie included):
   they are source-level.
