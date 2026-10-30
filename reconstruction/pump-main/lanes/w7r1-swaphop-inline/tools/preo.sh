#!/bin/bash
# preo.sh NAME EDIT.py : apply python edit (function edit(text)->text) to pre-opt module, opt -O3, extract swap_hop, llc oracle + callseq
H=~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin; O=~/.cache/pumpfun-reconstruction/lanes/w7r1-swaphop-inline; T=$O/tools
PRE=${PRE:-$O/ir/pre/module.ll}
D=$O/ir/p/$1; mkdir -p $D
python3 -c "import runpy,sys; t=open('$PRE').read(); t=runpy.run_path('$2')['edit'](t); open('$D/in.ll','w').write(t)" || exit 1
$H/opt -O3 -mattr=+store-imm,+jmp-ext $D/in.ll -S -o $D/opt.ll || exit 1
rm $D/in.ll
[ -n "$POST" ] && python3 $POST $D/opt.ll
python3 $T/extract.py $D/opt.ll $D/sh.ll 8swap_hop17h; rm $D/opt.ll
python3 $T/llcsh.py $D/sh.ll; python3 $T/callseq.py $D/sh.ll | cut -c1-400
