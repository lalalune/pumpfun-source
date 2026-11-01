#!/bin/bash
# sscprep.sh <name> [SSC_WSET spec]: pre-SSC MIR, PEI MIR and SSC debug log for rx/<name>/m.ll with the private llc
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour; cd $O; n=$1; L=$O/llvmb/bin/llc
A="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
[ -n "$2" ] && export SSC_WSET="$2"
$L $A rx/$n/m.ll -stop-before=stack-slot-coloring -o an/$n.pressc.mir &
$L $A rx/$n/m.ll -stop-after=prologepilog -o an/$n.pei.mir &
$L $A rx/$n/m.ll -filetype=obj -o an/$n.o -debug-only=stack-slot-coloring 2> ssc_$n.log &
wait
