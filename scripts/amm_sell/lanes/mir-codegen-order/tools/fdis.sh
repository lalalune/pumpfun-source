#!/bin/sh
# usage: fdis.sh obj  -> raw hex bytes of cashback section, one insn slot per line
B=$HOME/Documents/Codex/2026-10-24/amm-sell-swarm/infra/sdk-native/rust/lib/rustlib/aarch64-apple-darwin/bin
S=_ZN18pump_amm_recovered12instructions4swap4sell8cashback17hccb72da5245169afE
$B/llvm-objdump -d -j .text.$S "$1" | grep -E '^ +[0-9a-f]+:' | sed -E 's/^ +([0-9a-f]+):\s*//'
