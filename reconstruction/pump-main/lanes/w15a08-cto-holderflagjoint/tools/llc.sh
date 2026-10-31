#!/bin/bash
exec $HOME/.cache/solana/v1.44/platform-tools/llvm/bin/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$@"
