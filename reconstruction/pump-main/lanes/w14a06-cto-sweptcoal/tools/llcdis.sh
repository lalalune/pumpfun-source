#!/bin/bash
# llcdis.sh <m.ll> [llc args]: llc the slim module and print execute's disassembly (fn-relative byte offsets)
M=$1; shift; SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin; o=$(mktemp /tmp/llcdisXXXX).o
$SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $M -filetype=obj -o $o "$@" || exit 1
sec=$($SDK/llvm-objdump -h $o | grep -o '\.text\.\S*admin_cto7execute\S*' | head -1)
$SDK/llvm-objdump -d --no-show-raw-insn $o --section=$sec | python3 -c "
import sys,re
for l in sys.stdin:
    m=re.match(r'\s*(\d+):\s+(.*)',l)
    if m: print('%04x %s'%(int(m.group(1))*8,m.group(2).strip()))
"
rm -f $o
