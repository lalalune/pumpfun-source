#!/bin/bash
# xo.sh <in.(bc|ll)> <outdir> [mir] : extract admin_cto::execute (internalize+globaldce), llc, ratio; mir => also PEI frame map
set -e
RB=~/.cache/solana/v1.44/platform-tools/rust/lib/rustlib/aarch64-apple-darwin/bin; B=~/.cache/solana/v1.44/platform-tools/llvm/bin; T=$(dirname "$0")
mkdir -p $2
case $1 in *.ll) S=$(grep -o '^define[^@]*@_ZN14pump_recovered9admin_cto7execute[A-Za-z0-9_]*' $1 | sed 's/.*@//');; *) S=$($RB/llvm-nm $1 2>/dev/null | grep " T .*admin_cto7execute" | awk '{print $3}');; esac
$RB/opt -passes='internalize,globaldce' -internalize-public-api-list=$S $1 -o $2/ex.bc
F="-O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections"
$B/llc $F $2/ex.bc -filetype=obj -o $2/ex.o 2>$2/llc.err
python3 $T/objfn.py $2/ex.o admin_cto7execute > $2/fn.txt
python3 $T/oratio.py /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a17-cto-outlineport/orig_fn.txt $2/fn.txt
if [ "$3" = mir ]; then $B/llc $F $2/ex.bc -stop-after=prologepilog -o $2/pei.mir; python3 $T/mirframe.py $2/pei.mir > $2/frame.txt; fi
