#!/bin/bash
# phichk.sh file.ll : early SROA only, print _0 phi types at each phi block
OPT=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin/opt
$OPT -passes='sroa<modify-cfg>' "$1" -S -o - 2>&1 | awk '/^define.*buy_exact_quote_body17h/{f=1} f&&/^[^ ].*:/{b=$1} f&&/%_0\.sroa.*= phi/{printf "%s %s %s\n",b,$1,$4} f&&/^}/{exit}'
