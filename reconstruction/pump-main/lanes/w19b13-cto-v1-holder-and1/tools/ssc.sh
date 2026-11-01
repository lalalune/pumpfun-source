#!/bin/bash
# ssc.sh <name> <m.ll> : private llc with -debug-only=stack-slot-coloring, sharing on and off; writes ssc/<name>/{ssc.log,ns.log,ns.o,main.o}
OUT=$HOME/.cache/pumpfun-reconstruction/lanes/w19b13-cto-v1-holder-and1
PL=$HOME/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc
A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
n=$1; d=$OUT/ssc/$n; mkdir -p $d; cp $2 $d/m.ll
$PL $A $d/m.ll -filetype=obj -o $d/main.o -debug-only=stack-slot-coloring 2> $d/ssc.log
$PL $A $d/m.ll -filetype=obj -o $d/ns.o -no-stack-slot-sharing -debug-only=stack-slot-coloring 2> $d/ns.log
