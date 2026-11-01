#!/bin/bash
# build2.sh: private llc with BOTH the w15a24 RAPRIO/tag hooks (base build dir copied from w15a24-cto-raforce3/llvmb)
# and the w15a32 SSC_WSET hook (StackSlotColoring.cpp patched). Experiment only.
set -e
O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour
D=/Users/shawwalters/.cache/pumpfun-reconstruction/llvm-dbg
S=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a24-cto-raforce3/llvmb
B=$O/llvmb; P=$O/sscpatch
rsync -a $S/ $B/; mkdir -p $B/patch2; cd $B/patch2
cp $D/src/llvm/lib/CodeGen/StackSlotColoring.cpp .
python3 $P/apply.py StackSlotColoring.cpp
cd $D/build
ninja -t commands bin/llc | grep -E 'StackSlotColoring.cpp' | head -1 > $B/patch2/cc1.sh
ninja -t commands bin/llc | grep -E 'libtool" -static  -o lib/libLLVMCodeGen.a ' > $B/patch2/ar1.sh
ninja -t commands bin/llc | grep -E -- '-o bin/llc ' > $B/patch2/link.sh
cd $B/patch2
sed -i '' "s#$D/build#$B#g" cc1.sh ar1.sh link.sh
sed -i '' "s#-c $D/src/llvm/lib/CodeGen/StackSlotColoring.cpp#-c $B/patch2/StackSlotColoring.cpp#" cc1.sh
! grep -q "$D/build" cc1.sh ar1.sh link.sh
cd $B; rm -f lib/libLLVMCodeGen.a
bash patch2/cc1.sh; bash patch2/ar1.sh; bash patch2/link.sh 2>&1 | grep -v 'duplicate libraries' || true
ls -la $B/bin/llc
strings $B/bin/llc | grep -c SSC_WSET
strings $B/bin/llc | grep -c RAPRIO
