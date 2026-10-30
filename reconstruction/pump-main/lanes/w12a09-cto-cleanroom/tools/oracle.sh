#!/bin/bash
# oracle.sh <in.ll> <outprefix>: llc (identity flags) -> obj; disassemble admin_cto::execute -> <outprefix>.dis
# Prints bytes. Lane-local IR oracle (reproduces the fastbuild codegen for the function).
LLC=~/.cache/solana/v1.44/platform-tools/llvm/bin/llc; OD=~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump
$LLC -O3 -filetype=obj -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections ${LLCARGS:-} "$1" -o "$2.o" || exit 1
SEC=$($OD -h "$2.o" | grep -o '\.text\.[^ ]*admin_cto7execute[^ ]*' | head -1)
$OD -d --no-show-raw-insn "$2.o" --section="$SEC" > "$2.raw"
python3 - "$2.raw" > "$2.dis" <<'PY'
import sys,re
for l in open(sys.argv[1]):
    m=re.match(r'^\s*(\d+):\s+(.*)$',l)
    if not m: continue
    o=int(m.group(1))*8; s=re.sub(r'\s+<[^>]*>','',m.group(2).strip())
    print(f'{o:#06x}  {s}')
PY
echo "bytes $(( $(grep -c . $2.dis) * 8 ))"
