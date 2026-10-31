#!/bin/bash
# dis.sh <m.o> -> disassembly of execute's section with offsets
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
$SDK/llvm-objdump -d --no-show-raw-insn -j .text._ZN14pump_recovered9admin_cto7execute17h3bd6d7f34f2e30d7E "$1" | tail -n +7
