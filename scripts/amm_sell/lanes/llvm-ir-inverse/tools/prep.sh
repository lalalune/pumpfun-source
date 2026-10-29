#!/bin/bash
# prep.sh SLOT NAME : copy rcgu bc/o from build slot, name, reduce, verify reproduction
set -e
L=/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm/lanes/llvm-ir-inverse
B=/Users/shawwalters/Documents/Codex/2026-10-24/amm-sell-swarm/infra/sdk-native/rust/lib/rustlib/aarch64-apple-darwin/bin
D=$L/build$1/target/sbpf-solana-solana/release/deps
W=$L/work/$2; mkdir -p $W
cp $D/pump_amm_recovered.pump_amm_recovered.*-cgu.0.rcgu.bc $W/opt.bc
cp $D/pump_amm_recovered.pump_amm_recovered.*-cgu.0.rcgu.no-opt.bc $W/noopt.bc
cp $D/pump_amm_recovered.pump_amm_recovered.*-cgu.0.rcgu.o $W/rustc.o
$B/opt -passes=instnamer $W/opt.bc -o $W/named.bc
$B/llvm-dis $W/named.bc -o $W/named.ll
python3 -B $L/work/tools/reduce.py $W/named.ll $W/red
grep -v '^@[^=]* = [a-z_ ]*alias ' $W/red.head.ll > $W/h2 && mv $W/h2 $W/red.head.ll
cp $W/red.fn.ll $W/fn0.ll
cat $W/red.head.ll $W/red.fn.ll > $W/red.ll
$B/llvm-as $W/red.ll -o $W/red.bc
$B/llc -O3 -mattr=+store-imm,+jmp-ext -relocation-model=pic -function-sections -data-sections -trap-unreachable -no-trap-after-noreturn -filetype=obj $W/red.bc -o $W/red.o
S=_ZN18pump_amm_recovered12instructions4swap4sell8cashback17hccb72da5245169afE
python3 -B $L/work/tools/irscore.py $W/red.o
python3 -B $L/work/tools/irscore.py $W/rustc.o
cmp $W/red.cb.bin $W/rustc.cb.bin && echo REPRO_OK
