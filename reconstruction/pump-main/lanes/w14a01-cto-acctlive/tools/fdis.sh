#!/bin/bash
# fdis.sh <fn.bin> : disassemble raw function bytes with function-relative offsets
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
T=$(mktemp -d); cp $1 $T/f.bin
$SDK/llvm-objcopy -I binary -O elf64-bpf --rename-section=.data=.text,code $T/f.bin $T/f.o 2>/dev/null
$SDK/llvm-objdump -d --no-show-raw-insn $T/f.o | grep -E "^\s+[0-9]+:" | awk '{n=$1; sub(":","",n); $1=""; printf "%04x%s\n", n*8, $0}'
rm -rf $T
