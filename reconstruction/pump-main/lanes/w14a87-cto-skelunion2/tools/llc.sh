#!/bin/bash
# llc.sh in.ll out.s : release llc to asm like fastbuild
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
$SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $1 -filetype=asm -o $2
