#!/bin/bash
# build.sh <lane-out-dir>: private SSC-hook llc (experiment only). Copies the shared llvm-dbg build dir (never modified) into
# <out>/llvmb, patches a private copy of StackSlotColoring.cpp, recompiles that TU, re-archives libLLVMCodeGen.a, relinks bin/llc.
set -e
O=$1; D=~/.cache/pumpfun-reconstruction/llvm-dbg; B=$O/llvmb; P=$(cd $(dirname $0); pwd)
rsync -a $D/build/ $B/; mkdir -p $B/patch; cd $B/patch
cp $D/src/llvm/lib/CodeGen/StackSlotColoring.cpp .
python3 $P/apply.py StackSlotColoring.cpp
cd $D/build
ninja -t commands bin/llc | grep -E 'StackSlotColoring.cpp' | head -1 > $B/patch/cc1.sh
ninja -t commands bin/llc | grep -E 'libtool" -static  -o lib/libLLVMCodeGen.a ' > $B/patch/ar1.sh
ninja -t commands bin/llc | grep -E -- '-o bin/llc ' > $B/patch/link.sh
cd $B/patch
sed -i '' "s#$D/build#$B#g" cc1.sh ar1.sh link.sh
sed -i '' "s#-c $D/src/llvm/lib/CodeGen/StackSlotColoring.cpp#-c $B/patch/StackSlotColoring.cpp#" cc1.sh
! grep -q "$D/build" cc1.sh ar1.sh link.sh
cd $B; rm -f lib/libLLVMCodeGen.a
bash patch/cc1.sh; bash patch/ar1.sh; bash patch/link.sh 2>&1 | grep -v 'duplicate libraries' || true
ls -la $B/bin/llc
