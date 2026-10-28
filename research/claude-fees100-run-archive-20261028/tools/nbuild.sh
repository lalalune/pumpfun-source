#!/bin/bash
# Native macOS v1.44 diagnostic build of a Fees source tree (same normalized bodies as the Linux
# container build except 4 sysroot TypeId windows). Holds one native build slot.
# usage: nbuild.sh SRC_DIR TARGET_DIR OUT_PREFIX [extra rustc args...]
#   writes OUT_PREFIX-symbols.so, OUT_PREFIX-build.log, OUT_PREFIX-result.json
set -u
RR=/Users/shawwalters/fees100-run
T=$HOME/.cache/solana/v1.44/platform-tools
SRC=$(cd "$1" && pwd); TGT=$2; OUT=$3; shift 3
mkdir -p "$TGT" "$(dirname "$OUT")"
cd "$SRC"
export CARGO_HOME=$HOME/.cargo RUSTC=$T/rust/bin/rustc RUSTDOC=$T/rust/bin/rustdoc CC=$T/llvm/bin/clang AR=$T/llvm/bin/llvm-ar
export CARGO_TARGET_DIR=$TGT CARGO_NET_OFFLINE=true RUSTFLAGS=-Zremap-cwd-prefix= PATH=$T/rust/bin:$T/llvm/bin:/usr/bin:/bin
rm -f "$TGT/sbpf-solana-solana/release/pump_fees_candidate.so"
START=$(date +%s)
python3 $RR/shared/tools/sbf_lock.py --slots ${NSLOTS:-6} --name native -- $T/rust/bin/cargo rustc --verbose --manifest-path $SRC/programs/pump-fees/Cargo.toml --release --target sbpf-solana-solana --locked --offline --jobs ${JOBS:-2} --lib -- \
  --remap-path-prefix=$SRC/programs/pump-fees/src/../../../pump-fees-math/=pump-fees-math/ --remap-path-prefix=$SRC/pump-fees-math/=pump-fees-math/ \
  --remap-path-prefix=programs/pump-fees/src/../../../pump-fees-math/=pump-fees-math/ "$@" > "$OUT-build.log" 2>&1
RC=$?
END=$(date +%s)
if [ $RC -eq 0 ] && [ -f "$TGT/sbpf-solana-solana/release/pump_fees_candidate.so" ]; then
  cp "$TGT/sbpf-solana-solana/release/pump_fees_candidate.so" "$OUT-symbols.so"
  SHA=$(shasum -a 256 "$OUT-symbols.so" | cut -d' ' -f1)
else SHA=none; fi
echo "{\"exit_code\": $RC, \"elapsed_seconds\": $((END-START)), \"symbols_sha256\": \"$SHA\", \"src\": \"$SRC\"}" | tee "$OUT-result.json"
exit $RC
