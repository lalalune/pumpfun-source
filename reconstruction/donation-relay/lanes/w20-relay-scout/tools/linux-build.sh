#!/bin/bash
# Usage: linux-build.sh <crate dir> <out dir>
# Linux x86_64 build (podman machine, applehv + Rosetta) with the official platform-tools v1.54 archive, the same Cargo arguments as the
# old recipe and no ordered.ld. Writes <out>/unstripped.so, candidate.so, link.map, build.log. Target directory lives in the container.
# Start the machine first if it is stopped: podman machine start. Use one build at a time: the VM has 8 GB.
set -u
[ $# -ge 2 ] || { echo "usage: linux-build.sh <crate dir> <out dir>" >&2; exit 2; }
C=$HOME/.cache/pumpfun-reconstruction; R=$C/relay; T=$R/tools
CRATE=$(cd "$1" && pwd) || exit 2
OUT=$2; mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd)
SDK=$HOME/.cache/solana/v1.54-linux-x86_64/platform-tools
IMG=${RELAY_LINUX_IMAGE:-localhost/codex-relay-build-deps:20261027}
CH=$T/linux-cargo-home
if [ ! -d "$CH/registry/index" ]; then
  mkdir -p "$CH/registry/cache" "$CH/registry/src" "$CH/registry/index"
  cp -cR "$HOME/.cargo/registry/index/index.crates.io-1949cf8c6b5b557f" "$CH/registry/index/"
  cp -cR "$HOME/.cargo/registry/cache/index.crates.io-1949cf8c6b5b557f" "$CH/registry/cache/"
  cp -cR "$HOME/.cargo/registry/src/index.crates.io-1949cf8c6b5b557f" "$CH/registry/src/"
fi
exec podman run --rm --platform linux/amd64 --memory 6g --network none \
  -v "$SDK":/sdk:ro -v "$CRATE":/source:ro -v "$CH":/cargo -v "$OUT":/output \
  --workdir /source "$IMG" /usr/bin/env -i \
  PATH=/sdk/rust/bin:/sdk/llvm/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin HOME=/output/home CARGO_HOME=/cargo CARGO_TARGET_DIR=/target \
  CARGO_NET_OFFLINE=true CARGO_TERM_COLOR=never CARGO_BUILD_JOBS=3 "CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS=-Zremap-cwd-prefix=" \
  RUSTC=/sdk/rust/bin/rustc RUSTDOC=/sdk/rust/bin/rustdoc CC=/sdk/llvm/bin/clang AR=/sdk/llvm/bin/llvm-ar OBJDUMP=/sdk/llvm/bin/llvm-objdump OBJCOPY=/sdk/llvm/bin/llvm-objcopy LANG=C.UTF-8 LC_ALL=C.UTF-8 \
  /bin/bash -c 'mkdir -p /output/home; /sdk/rust/bin/cargo rustc --release --target sbpf-solana-solana --locked --offline --verbose --manifest-path /source/Cargo.toml --lib -- --remap-path-prefix=src/=programs/contracts/src/ -C link-arg=-Map=/output/link.map > /output/build.log 2>&1; rc=$?; echo rc=$rc >> /output/build.log; if [ $rc = 0 ]; then cp /target/sbpf-solana-solana/release/*.so /output/unstripped.so; /sdk/llvm/bin/llvm-objcopy --strip-all /output/unstripped.so /output/candidate.so; fi; exit $rc'
