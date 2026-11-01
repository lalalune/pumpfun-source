#!/bin/bash
# Usage: measure.sh <crate dir> <work dir> <out dir> [baseline functions.json]
# Fast Mac build of a programs/donation-relay-shaped crate with the macOS v1.54 compiler and the Linux x86_64 v1.54 sysroot
# (toolchains/hybrid154), then per-function comparison with relay/live/deployed.elf. Prints ONE JSON line.
# Outputs in <out dir>: unstripped.so, candidate.so, build.log, functions.json (per-function table).
# One <work dir> per concurrent build. Default baseline: relay/tools/baseline.functions.json (gains/losses against it).
# Environment: RELAY_ONLINE=1 lets Cargo fetch a new locked crate; RELAY_LINKSCRIPT=<ordered.ld> links with that script.
set -u
[ $# -ge 3 ] || { echo "usage: measure.sh <crate dir> <work dir> <out dir> [baseline functions.json]" >&2; exit 2; }
C=$HOME/.cache/pumpfun-reconstruction; R=$C/relay; T=$R/tools
CRATE=$(cd "$1" && pwd) || exit 2
WORK=$2; OUT=$3; mkdir -p "$WORK" "$OUT"; WORK=$(cd "$WORK" && pwd); OUT=$(cd "$OUT" && pwd)
BASE=${4:-$T/baseline.functions.json}
SDK=${RELAY_SDK:-$HOME/.cache/solana/v1.54/platform-tools}
HY=${RELAY_RUSTC_ROOT:-$C/toolchains/hybrid154/rust}
LOCK=$T/.slots; mkdir -p "$LOCK"
rsync -a --checksum --delete --exclude /target/ "$CRATE"/ "$WORK/source/" || { echo '{"ok": false, "error": "rsync failed"}'; exit 1; }
if [ ! -d "$WORK/target" ] && [ -d "$T/template-target" ]; then cp -cRp "$T/template-target" "$WORK/target" 2>/dev/null || true; fi
OFFLINE=--offline; [ "${RELAY_ONLINE:-0}" = 1 ] && OFFLINE=
EXTRA=(); WRAP=()
if [ -n "${RELAY_LINKSCRIPT:-}" ]; then
  cat > "$WORK/linker-wrapper.sh" <<WEOF
#!/bin/bash
args=("\$@")
for ((i=0; i<\${#args[@]}; i++)); do
  if [[ "\${args[i]}" == "-T" || "\${args[i]}" == "--script" ]]; then args[i+1]="$RELAY_LINKSCRIPT"
  elif [[ "\${args[i]}" == --script=* ]]; then args[i]=--script="$RELAY_LINKSCRIPT"; fi
done
exec "$SDK/rust/lib/rustlib/aarch64-apple-darwin/bin/rust-lld" "\${args[@]}"
WEOF
  chmod +x "$WORK/linker-wrapper.sh"; EXTRA=(-C "linker=$WORK/linker-wrapper.sh")
fi
cd "$WORK/source" || exit 2
S=$(date +%s)
env -i HOME="$HOME" PATH="$SDK/rust/bin:$SDK/llvm/bin:/usr/bin:/bin" CARGO_HOME="${CARGO_HOME:-$HOME/.cargo}" CARGO_TARGET_DIR="$WORK/target" \
  CARGO_TERM_COLOR=never CARGO_BUILD_JOBS=3 CARGO_NET_OFFLINE=$([ -n "$OFFLINE" ] && echo true || echo false) \
  CARGO_TARGET_SBPF_SOLANA_SOLANA_RUSTFLAGS="-Zremap-cwd-prefix=" RUSTC="$HY/bin/rustc" RUSTDOC="$SDK/rust/bin/rustdoc" \
  CC="$SDK/llvm/bin/clang" AR="$SDK/llvm/bin/llvm-ar" OBJDUMP="$SDK/llvm/bin/llvm-objdump" OBJCOPY="$SDK/llvm/bin/llvm-objcopy" LANG=C.UTF-8 LC_ALL=C.UTF-8 \
  "$SDK/rust/bin/cargo" rustc --release --target sbpf-solana-solana --locked $OFFLINE --verbose --manifest-path "$WORK/source/Cargo.toml" --lib -- \
  --remap-path-prefix=src/=programs/contracts/src/ -C link-arg=-Map="$OUT/link.map" "${EXTRA[@]+"${EXTRA[@]}"}" > "$OUT/build.log" 2>&1
RC=$?
E=$(date +%s)
if [ $RC -ne 0 ]; then
  python3 - "$OUT" "$RC" <<'PY'
import json,sys,re
out,rc=sys.argv[1],int(sys.argv[2])
t=open(out+'/build.log',errors='replace').read()
errs=[l for l in t.splitlines() if re.match(r'(error|warning: Function .*Stack)',l)]
print(json.dumps({"ok":False,"rc":rc,"errors":errs[:12],"tail":t[-800:],"out":out}))
PY
  exit 1
fi
SO=$(ls -t "$WORK"/target/sbpf-solana-solana/release/*.so | head -1)
cp -f "$SO" "$OUT/unstripped.so"
"$SDK/llvm/bin/llvm-objcopy" --strip-all "$OUT/unstripped.so" "$OUT/candidate.so"
python3 - "$T" "$OUT" "$BASE" "$((E-S))" <<'PY'
import sys,json,hashlib,subprocess
T,out,base,secs=sys.argv[1:5]
sys.path.insert(0,T)
import relay
r=relay.measure(out+'/unstripped.so',out+'/functions.json',base)
b=open(out+'/candidate.so','rb').read(); tgt=open(relay.TARGET,'rb').read()
r['sha']=hashlib.sha256(b).hexdigest(); r['candidate_bytes']=len(b); r['target_bytes']=len(tgt); r['whole_elf_equal']=b==tgt; r['build_seconds']=int(secs); r['out']=out
n=open(out+'/build.log',errors='replace').read().count('Stack offset of')
r['stack_warnings']=n
print(json.dumps(r))
PY
