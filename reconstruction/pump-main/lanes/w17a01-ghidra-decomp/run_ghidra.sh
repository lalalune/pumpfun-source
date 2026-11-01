#!/bin/bash
# Reproduce the lane's Ghidra outputs (lane w17a01-ghidra-decomp).
#   run_ghidra.sh <tag> <elf> <entry[,entry...]> [out_dir]
# tag orig: evidence/original/pump/deployed.so; tag ours: main's unstripped.so ($C/w11/current-baseline/unstripped.so).
# Ghidra rejects project paths with a dot-prefixed element (~/.cache), so the project dir is reached via a symlink.
set -euo pipefail
tag=$1; elf=$2; entries=$3
HERE=$(cd "$(dirname "$0")" && pwd)
C=$HOME/.cache/pumpfun-reconstruction
OUT=${4:-$C/lanes/w17a01-ghidra-decomp/ghidra_out}
SYMS=${SYMS:-$C/w11/current-baseline/unstripped.so}
LINK=${TMPDIR:-/tmp}/w17a01-ghidra-projects
mkdir -p "$C/ghidra" "$OUT"
ln -sfn "$C/ghidra" "$LINK"
export JAVA_HOME=${JAVA_HOME:-$(brew --prefix openjdk@25)}
export GHIDRA_HEADLESS_MAXMEM=${GHIDRA_HEADLESS_MAXMEM:-6G}
GH=/opt/homebrew/opt/ghidra/libexec/support/analyzeHeadless
FACTS=$C/lanes/w17a01-ghidra-decomp/facts/$tag
python3 "$HERE/prep.py" "$elf" "$SYMS" "$FACTS"
# raw image up to the end of .rel.dyn (the deployed.so capture is zero-padded to 10 MiB)
len=$(python3 -c "r=[l.split('\t') for l in open('$FACTS/sections.tsv')];print(hex([int(a[1],16)+int(a[2],16) for a in r if a[0]=='.rel.dyn'][0]))")
"$GH" "$LINK" "w17a01_$tag" -import "$elf" -overwrite -loader BinaryLoader -loader-baseAddr 0x0 -loader-length "$len" \
  -loader-blockName image -processor eBPF:LE:64:default -noanalysis -scriptPath "$HERE/ghidra_scripts" \
  -postScript SbfDecomp.java "$FACTS" "$OUT" "$tag" "$entries"
