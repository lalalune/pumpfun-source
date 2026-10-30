#!/bin/sh
set -eu

root=${1:-"$(git rev-parse --show-toplevel)"}
out=${2:?usage: build_candidate.sh [repo-root] OUTPUT-DIRECTORY}
sdk=${SOLANA_PLATFORM_TOOLS:-"$HOME/.cache/solana/v1.44/platform-tools"}

test -x "$sdk/rust/bin/cargo"
test -x "$sdk/rust/bin/rustc"
test -x "$sdk/llvm/bin/llvm-objcopy"
mkdir -p "$out/target"

export CARGO_TARGET_DIR="$out/target"
export CARGO_NET_OFFLINE=true
export CARGO_TERM_COLOR=never
export RUSTC="$sdk/rust/bin/rustc"
export RUSTDOC="$sdk/rust/bin/rustdoc"
export CC="$sdk/llvm/bin/clang"
export AR="$sdk/llvm/bin/llvm-ar"
export OBJDUMP="$sdk/llvm/bin/llvm-objdump"
export OBJCOPY="$sdk/llvm/bin/llvm-objcopy"
export CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS=-Zremap-cwd-prefix=

"$sdk/rust/bin/cargo" rustc --release --target sbpf-solana-solana --locked --offline \
  --manifest-path "$root/programs/donation-relay/Cargo.toml" --lib -- \
  --remap-path-prefix=src/=programs/contracts/src/
"$sdk/llvm/bin/llvm-objcopy" --strip-all \
  "$out/target/sbpf-solana-solana/release/donation_relay_source_proposal.so" \
  "$out/donation_relay_candidate.so"
shasum -a 256 "$out/donation_relay_candidate.so"
