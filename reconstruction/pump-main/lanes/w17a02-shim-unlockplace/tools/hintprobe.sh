#!/bin/bash
# hintprobe.sh: compile hintprobe.rs with the identity rustc (1.79.0-dev, LLVM 18.1.7) for sbpf-solana-solana and show
# which branch-hint spelling leaves a !prof on the optimized IR. No build slot; about 1 s.
R=~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/bin/rustc
D=$(mktemp -d); cp "$(dirname "$0")/hintprobe.rs" $D/a.rs; cd $D
$R --target sbpf-solana-solana --crate-type=lib -C opt-level=3 --emit=llvm-ir -o a.ll a.rs 2>/dev/null
$R --target sbpf-solana-solana --crate-type=lib -C opt-level=3 -C no-prepopulate-passes --emit=llvm-ir -o raw.ll a.rs 2>/dev/null
echo "== optimized IR (branches and weights)"; grep -n "^define\|br i1\|branch_weights" a.ll
echo "== raw IR of f1 (core::intrinsics::unlikely): the expect result is stored to an alloca and reloaded"; awk '/^define.*@f1/,/^}/' raw.ll | head -16
rm -rf $D
