#!/bin/bash
# pro.sh tag [n] : print first n insns of sell in oracle/tag.o
B=~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin
D=~/.cache/pumpfun-reconstruction/lanes/w4-sellv3-phi/oracle
S=$($B/llvm-objdump -h $D/$1.o | grep -o '\.text\.[^ ]*'${SYM:-5trade4sell17h}'[^ ]*' | head -1)
$B/llvm-objdump -d -j $S $D/$1.o | grep -E '^\s+[0-9a-f]+:' | head -${2:-16} | sed -E 's/^\s*([0-9a-f]+):\s+([0-9a-f]{2} ){8}\s*/\1 /'
