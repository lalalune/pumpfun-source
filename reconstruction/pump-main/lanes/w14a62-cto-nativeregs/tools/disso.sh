#!/bin/bash
# disso.sh <unstripped.so|m.o>: admin_cto::execute disasm as "<off> <insn>" (off relative to fn start)
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
case "$1" in *.o) exec bash $(dirname $0)/dis.sh $1;; esac
read v s <<<$($SDK/llvm-readelf -sW $1 | awk '/admin_cto7execute/{print $2, $3; exit}')
st=$((16#$v)); en=$((st+s))
$SDK/llvm-objdump -d --no-show-raw-insn --start-address=$st --stop-address=$en $1 | awk -v st=$st '/^ *[0-9a-f]+:/{n=$1; sub(":","",n); $1=""; printf "%04x %s\n", n*8-st, $0}'
