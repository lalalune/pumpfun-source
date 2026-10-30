#!/bin/bash
# omap.sh <post.ll> <spec> <outdir>: apply spec, debug-llc, layout + objmap
cd /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w13a35-cto-irexact3
D=~/.cache/pumpfun-reconstruction/llvm-dbg/build/bin; mkdir -p $3
python3 -c "
import sys; sys.path.insert(0,'tools'); import iredit
open('$3/m.ll','w').write(iredit.apply(open('$1').read(),'''$2''') if '''$2''' else open('$1').read())"
$D/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections -debug-only=prologepilog,stack-coloring $3/m.ll -filetype=obj -o $3/m.o 2> $3/pe.log
bash tools/dis.sh $3/m.o > $3/cand.dis
python3 tools/layout.py $3/pe.log $3/m.ll > $3/layout.txt
python3 tools/objmap.py orig.rel $3/cand.dis $3/pe.log $3/m.ll > $3/objmap.txt
rm -f $3/m.ll $3/m.o
