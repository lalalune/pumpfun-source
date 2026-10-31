#!/bin/bash
# argprom.sh <raw.ll> [fn-regex]: print post-ArgPromotion signatures of admin_cto helpers (which ctx fields get promoted to the call site).
OPT=$(ls ~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/*/bin/opt | head -1)
RE=${2:-'admin_cto(7execute|8validate)'}
F=$(grep -oE '^define [^@]*@"?_ZN[^ (]*' "$1" | grep -oE '_ZN[^ ("]*' | grep -E "$RE" | paste -sd, -)
"$OPT" -O3 "$1" -o /dev/null -print-after=argpromotion -filter-print-funcs="$F" 2>&1 | grep '^define' | sed -E 's/^define [^@]*@//' | cut -c1-400
