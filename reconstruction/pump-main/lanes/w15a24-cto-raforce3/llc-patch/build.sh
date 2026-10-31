#!/bin/bash
# build.sh <lane-out-dir>: private RAPRIO llc. Copies the shared llvm-dbg build dir (never modified) into <out>/llvmb,
# applies RegAllocGreedy.patch / SBFAsmPrinter.patch to private copies of RegAllocGreedy.cpp and SBFAsmPrinter.cpp, recompiles only those two TUs,
# re-archives libLLVMCodeGen.a / libLLVMSBFCodeGen.a and relinks bin/llc (about 1 minute, single-threaded).
set -e
O=$1; D=~/.cache/pumpfun-reconstruction/llvm-dbg; B=$O/llvmb; P=$(cd $(dirname $0); pwd)
rsync -a $D/build/ $B/; mkdir -p $B/patch; cd $B/patch
cp $D/src/llvm/lib/CodeGen/RegAllocGreedy.cpp $D/src/llvm/lib/Target/SBF/SBFAsmPrinter.cpp .
patch -s RegAllocGreedy.cpp < $P/RegAllocGreedy.patch; patch -s SBFAsmPrinter.cpp < $P/SBFAsmPrinter.patch; python3 $P/extra.py RegAllocGreedy.cpp
cd $D/build
ninja -t commands bin/llc | grep -E 'RegAllocGreedy.cpp' | head -1 > $B/patch/cc1.sh
ninja -t commands bin/llc | grep -E 'SBFAsmPrinter.cpp' | head -1 > $B/patch/cc2.sh
ninja -t commands bin/llc | grep -E 'libtool" -static  -o lib/libLLVMCodeGen.a ' > $B/patch/ar1.sh
ninja -t commands bin/llc | grep -E 'libtool" -static  -o lib/libLLVMSBFCodeGen.a ' > $B/patch/ar2.sh
ninja -t commands bin/llc | grep -E -- '-o bin/llc ' > $B/patch/link.sh
cd $B/patch
sed -i '' "s#$D/build#$B#g" cc1.sh cc2.sh ar1.sh ar2.sh link.sh
sed -i '' "s#-c $D/src/llvm/lib/CodeGen/RegAllocGreedy.cpp#-c $B/patch/RegAllocGreedy.cpp#" cc1.sh
sed -i '' "s#-c $D/src/llvm/lib/Target/SBF/SBFAsmPrinter.cpp#-c $B/patch/SBFAsmPrinter.cpp#" cc2.sh
! grep -q "$D/build" cc1.sh cc2.sh ar1.sh ar2.sh link.sh
cd $B; rm -f lib/libLLVMCodeGen.a lib/libLLVMSBFCodeGen.a
bash patch/cc1.sh; bash patch/cc2.sh; bash patch/ar1.sh; bash patch/ar2.sh; bash patch/link.sh 2>&1 | grep -v 'duplicate libraries' || true
ls -la $B/bin/llc
