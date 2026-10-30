#!/bin/bash
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin; sec=$($SDK/llvm-objdump -h $1 | grep -o '\.text\.\S*admin_cto7execute\S*' | head -1)
$SDK/llvm-objdump -d --no-show-raw-insn $1 --section=$sec | awk '/^ *[0-9]+:/{n=$1; sub(":","",n); $1=""; printf "%04x %s\n", n*8, $0}'
