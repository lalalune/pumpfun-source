#!/bin/sh
# disobj.sh <file> : create_token_account_v2 instructions, normalized (no addrs, call imms masked)
B=~/.cache/solana/v1.44/platform-tools/llvm/bin
$B/llvm-objdump -d --no-show-raw-insn --symbolize-operands "$1" 2>/dev/null | awk '/^[0-9a-f]+ <_ZN14pump_recovered10migrate_v223create_token_account_v217h/{p=1;next} p&&/^[0-9a-f]+ <_ZN/{exit} p' | grep -E "^ +[0-9a-f]+:" | sed -E 's/^ *[0-9a-f]+:[[:space:]]*//; s/ <[^>]*>//; s/call -?0x[0-9a-f]+/call X/; s/lddw (r[0-9]+), -?0x[0-9a-f]+$/lddw \1, ADDR/'
