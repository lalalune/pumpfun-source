#!/bin/sh
# fn.sh obj symbol -> normalized listing (insn only)
SDK=~/.cache/solana/v1.44/platform-tools
read A S <<< "$($SDK/llvm/bin/llvm-readelf -sW "$1" | awk -v s="$2" '$8==s{print $2, $3}')"
$SDK/llvm/bin/llvm-objdump -d --no-show-raw-insn --no-leading-addr --start-address=0x$A --stop-address=$(printf '0x%x' $((0x$A + $S))) "$1" | grep -v '^\s*$' | grep -v ':$' | grep -v 'file format\|Disassembly' | sed 's/^\s*//; s/ <[^>]*>//'
