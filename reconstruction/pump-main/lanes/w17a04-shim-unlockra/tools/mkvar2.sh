#!/bin/bash
# mkvar2.sh <name> <edits.py>: like mkvar.sh, plus prepend #![feature(link_llvm_intrinsics)] to lib.rs line 1 (no new line)
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w17a04-shim-unlockra
$OUT/tools/mkvar.sh "$1" "$2" || exit 1
python3 - $OUT/var/$1/src/lib.rs <<'PY'
import sys
f=sys.argv[1]; s=open(f).read()
if not s.startswith('#![feature(link_llvm_intrinsics)]'): s='#![feature(link_llvm_intrinsics)]'+s
open(f,'w').write(s)
PY
