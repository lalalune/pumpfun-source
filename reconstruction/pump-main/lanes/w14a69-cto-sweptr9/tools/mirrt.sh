#!/bin/bash
# mirrt.sh <m.ll> <out-prefix> [sed-script]: llc to MIR before register-coalescer, optional sed edit, resume to obj (experiment only)
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
A=(-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections)
$SDK/llc "${A[@]}" "$1" -stop-before=register-coalescer -o "$2.mir" || exit 1
[ -n "$3" ] && { sed -E -i '' -f "$3" "$2.mir" || exit 1; }
$SDK/llc "${A[@]}" "$2.mir" -start-before=register-coalescer -filetype=obj -o "$2.o" || exit 1
python3 $(dirname $0)/objscore.py "$2.o"
