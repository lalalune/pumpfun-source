#!/bin/bash
# Build the "hybrid144" toolchain used by the identity lane:
#   rust/bin/rustc + rust/lib/{librustc_driver,libstd}.dylib = byte-identical APFS clones of the macOS arm64
#     platform-tools v1.44 compiler (rustc 1.79.0-dev, anza rust 08b7341888ab480dfaaa0698300cbbbbb2d75b53)
#   rust/lib/rustlib/aarch64-apple-darwin -> the same macOS v1.44 host libraries (proc macros / build scripts)
#   rust/lib/rustlib/sbpf-solana-solana   = the target libraries from the OFFICIAL Linux x86_64 platform-tools
#     v1.44 archive (platform-tools-linux-x86_64.tar.bz2, sha256 6719b889d60677a8a2fcf4c82f68441a1afe0ab093edd2efe9f84a67a808b3e9)
# rustc derives its default sysroot from the location of librustc_driver, so `hybrid144/rust/bin/rustc --print sysroot`
# is hybrid144/rust and no --sysroot/RUSTFLAGS change is needed.
# usage: make_hybrid144.sh <out-dir> <mac v1.44 rust dir> <linux v1.44 platform-tools dir (extracted)> [sha256 manifest]
set -euo pipefail
OUT=$1; MAC=$(cd "$2" && pwd -P); LNX=$(cd "$3" && pwd -P); MAN=${4:-}
rm -rf "$OUT"; mkdir -p "$OUT/rust/bin" "$OUT/rust/lib/rustlib"
cp -cp "$MAC/bin/rustc" "$OUT/rust/bin/rustc"
cp -cp "$MAC"/lib/librustc_driver-*.dylib "$MAC"/lib/libstd-*.dylib "$OUT/rust/lib/"
ln -s "$MAC/lib/rustlib/aarch64-apple-darwin" "$OUT/rust/lib/rustlib/aarch64-apple-darwin"
cp -cRp "$LNX/rust/lib/rustlib/sbpf-solana-solana" "$OUT/rust/lib/rustlib/sbpf-solana-solana"
cp -p "$LNX/version.md" "$OUT/version.md"
if [ -n "$MAN" ]; then (cd "$OUT/rust/lib/rustlib" && shasum -a 256 -c "$MAN" >/dev/null) && echo "target libs verified against $MAN"; fi
"$OUT/rust/bin/rustc" --print sysroot
