#!/bin/bash
# objdis.sh <m.o> <out.dis> : disassemble execute from an llc object in orig.dis format (addresses rebased to 0x22a10)
OD=~/.cache/solana/v1.44/platform-tools/llvm/bin/llvm-objdump
SEC=$($OD -h "$1" | grep -o '\.text\.[^ ]*admin_cto7execute[^ ]*' | head -1)
$OD -d --no-show-raw-insn "$1" --section="$SEC" | python3 -c "
import sys,re
for l in sys.stdin:
    m=re.match(r'^\s*(\d+):\s+(.*)$',l)
    if not m: continue
    o=int(m.group(1))*8+0x22a10; s=re.sub(r'\s+<[^>]*>','',m.group(2).strip())
    print(f'{o:#x}  {s}')
" > "$2"
