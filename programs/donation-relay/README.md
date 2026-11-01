# Donation Relay

Source for `RLAYHr9TRFcKB2ubYQhspcnXiaGpaVzNQvHytt47RZu`, the version deployed at slot 462,683,179 (2026-10-29).

Built with the recipe below, it produces a 929,176-byte ELF with SHA-256
`0985c3a02b9f02035e677b99d63b42b0484d0734e3e66e5e36fd4509dd600624`. Those are the bytes held by program data
account `5QH8Ay11KgpRMyECYofHwAr6SzfFEGkbtPoM6eXv8V7B` after its 45-byte header.

## Build

You need podman able to run `linux/amd64` containers. Only the first block uses the network. Run both from
`programs/donation-relay`, in one shell.

Toolchain and dependencies: platform-tools v1.54 (rustc 1.89.0-dev, LLVM 20.1.7), the Linux x86_64 archive, for which
GitHub publishes this digest, and the crates pinned by `Cargo.lock`.

```bash
WORK=$(mktemp -d); SDK=$WORK/sdk; CARGO_CACHE=$WORK/cargo; OUT=$WORK/out; mkdir -p "$SDK" "$CARGO_CACHE" "$OUT"
IMAGE=docker.io/solanafoundation/solana-verifiable-build@sha256:d7079331a2696eca570fbeeb5caa556cb09084f89ca96f0a0edb86e1cf83e165
curl -fL -o "$WORK/platform-tools.tar.bz2" https://github.com/anza-xyz/platform-tools/releases/download/v1.54/platform-tools-linux-x86_64.tar.bz2
echo "fcc41631c7f77561bf5412218bf297501dccf0305ea280f338f0ace2aab9f31e  $WORK/platform-tools.tar.bz2" | shasum -a 256 -c
tar -xjf "$WORK/platform-tools.tar.bz2" -C "$SDK"
podman run --rm --platform linux/amd64 -v "$SDK":/sdk:ro -v "$PWD":/source:ro -v "$CARGO_CACHE":/cargo "$IMAGE" \
  /usr/bin/env HOME=/tmp CARGO_HOME=/cargo RUSTC=/sdk/rust/bin/rustc /sdk/rust/bin/cargo fetch --locked --manifest-path /source/Cargo.toml
```

Build, offline, in a fresh target directory, and strip:

```bash
podman run --rm --platform linux/amd64 --network none \
  -v "$SDK":/sdk:ro -v "$PWD":/source:ro -v "$CARGO_CACHE":/cargo -v "$OUT":/output --workdir /source "$IMAGE" \
  /usr/bin/env -i PATH=/sdk/rust/bin:/sdk/llvm/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  HOME=/output/home CARGO_HOME=/cargo CARGO_TARGET_DIR=/target CARGO_NET_OFFLINE=true CARGO_TERM_COLOR=never CARGO_BUILD_JOBS=3 \
  CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS=-Zremap-cwd-prefix= RUSTC=/sdk/rust/bin/rustc RUSTDOC=/sdk/rust/bin/rustdoc \
  CC=/sdk/llvm/bin/clang AR=/sdk/llvm/bin/llvm-ar OBJDUMP=/sdk/llvm/bin/llvm-objdump OBJCOPY=/sdk/llvm/bin/llvm-objcopy \
  LANG=C.UTF-8 LC_ALL=C.UTF-8 /bin/bash -c 'mkdir -p /output/home && /sdk/rust/bin/cargo rustc --release --target sbpf-solana-solana \
    --locked --offline --manifest-path /source/Cargo.toml --lib -- --remap-path-prefix=src/=programs/contracts/src/ \
    -C linker=/source/link/linker-wrapper.sh && /sdk/llvm/bin/llvm-objcopy --strip-all \
    /target/sbpf-solana-solana/release/donation_relay_source_proposal.so /output/donation_relay.so'
shasum -a 256 "$OUT/donation_relay.so"
```

The build block was run unchanged from a clean `git archive` export, compiling all 178 crates, under podman on macOS
(`linux/amd64` through Rosetta). It printed the SHA-256 above, and `cmp` with the deployed bytes found no difference. The
toolchain and crate cache it used came from an earlier download with the same archive digest and `Cargo.lock`, so the
first block's download steps have not been rerun as written.

## What the identity rests on

- **Link order.** `link/ordered.ld` holds 571 `.text` section selectors in the deployed order, plus the default layout.
  It holds no machine code or data, but it was derived by comparing a build with the deployed ELF. Without it, the same
  source gives all 571 function bodies and an equal `.rodata` at the same total size, with 65,997 byte positions
  different, because functions land in another order. Selectors carry this crate's symbol hashes, so a code change
  can need a new script, and a stale selector shows up only as a different SHA-256.
- **Source text.** Byte identity shows that this source compiles to the deployed program, not that the original looked
  like this. Names such as the crate `donation_relay_source_proposal` and the module `anchor_framework` are this
  reconstruction's.
- **Host.** The build has to be Linux: a macOS toolchain of the same version links 569 of the 571 functions. No native
  Linux host has been tried.

The crate has no `unsafe`, `asm!`, `include_bytes!`, `black_box`, volatile access, `link_section`, `no_mangle` or `build.rs`.

## Earlier version

The version deployed at slot 415,422,992 (830,448-byte capture, SHA-256
`367f07a62e3f74d358187d175cf3228848e81a56c781a9a75b9df7fed1268563`, platform-tools v1.48) is no longer on chain. This
source does not reproduce it. Its source is `programs/donation-relay` at commit `5703df021`. Its capture and recipe are
at commit `3799b6618`, in `evidence/dependencies/donation_relay` and `reconstruction/donation-relay/native-linux-v148-20261030`.
