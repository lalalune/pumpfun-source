#!/bin/bash
# mkjtf.sh <outdir>: build jtf.dylib, a private opt pass plugin "jt-force" = LLVM 18 JumpThreading with a per-block
# thread-through-two-blocks threshold override (env JTF_BLOCKS="bb75" or "bb75:bb18,...", JTF_T=<thr>, default 1000).
# Copies JumpThreading.{h,cpp} from the llvm-dbg source into <outdir> (the shared llvm-dbg tree is never modified).
# Use: opt -load-pass-plugin <outdir>/jtf.dylib -passes='function(jt-force,...)'; debug trace with -debug-only=jtf.
set -e
L=~/.cache/pumpfun-reconstruction/llvm-dbg; O=$1; mkdir -p $O; cd $O
cp $L/src/llvm/include/llvm/Transforms/Scalar/JumpThreading.h JTF.h; cp $L/src/llvm/lib/Transforms/Scalar/JumpThreading.cpp JTF.cpp
sed -i '' 's/JumpThreadingPass/JTForcePass/g; s/LLVM_TRANSFORMS_SCALAR_JUMPTHREADING_H/JTF_H_/g' JTF.h JTF.cpp
sed -i '' 's#"llvm/Transforms/Scalar/JumpThreading.h"#"JTF.h"#; s/"jump-threading-/"jtf-/g; s/^#define DEBUG_TYPE "jump-threading"/#define DEBUG_TYPE "jtf"/' JTF.cpp
python3 - <<'PY'
f='JTF.cpp'; s=open(f).read()
old="""  unsigned BBCost = getJumpThreadDuplicationCost(
      TTI, BB, BB->getTerminator(), BBDupThreshold);
  unsigned PredBBCost = getJumpThreadDuplicationCost(
      TTI, PredBB, PredBB->getTerminator(), BBDupThreshold);"""
new="""  unsigned SavedT = BBDupThreshold;
  if (const char *FB = getenv("JTF_BLOCKS")) {
    std::string L = std::string(",") + FB + ",";
    if (L.find("," + PredBB->getName().str() + ",") != std::string::npos ||
        L.find("," + PredBB->getName().str() + ":" + BB->getName().str() + ",") != std::string::npos)
      BBDupThreshold = getenv("JTF_T") ? atoi(getenv("JTF_T")) : 1000;
  }
"""+old+"""
  struct RestoreT { unsigned &R; unsigned V; ~RestoreT(){ R=V; } } RT{BBDupThreshold, SavedT};"""
assert s.count(old)==1; s=s.replace(old,new)
s+='''
#include "llvm/Passes/PassPlugin.h"
#include "llvm/Passes/PassBuilder.h"
extern "C" LLVM_ATTRIBUTE_WEAK ::llvm::PassPluginLibraryInfo llvmGetPassPluginInfo() {
  return {LLVM_PLUGIN_API_VERSION, "JTF", "0.1", [](PassBuilder &PB) {
    PB.registerPipelineParsingCallback([](StringRef N, FunctionPassManager &FPM, ArrayRef<PassBuilder::PipelineElement>) {
      if (N == "jt-force") { FPM.addPass(JTForcePass()); return true; } return false; });
  }};
}
'''
open(f,'w').write(s)
PY
/usr/bin/clang++ -std=c++17 -fno-rtti -fPIC -shared -undefined dynamic_lookup -O2 -w -I. -I$L/src/llvm/include -I$L/build/include JTF.cpp -o jtf.dylib
echo built $O/jtf.dylib
