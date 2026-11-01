#!/bin/bash
# llc.sh in.ll out.s  (asm, like fastbuild)   |   llc.sh in.ll <llc args...>
SDK=$HOME/.cache/solana/v1.44/platform-tools/llvm/bin
if [ $# -eq 2 ] && [[ "$2" != -* ]]; then
  exec $SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$1" -filetype=asm -o "$2"
fi
exec $SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$@"
