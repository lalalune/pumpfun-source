#!/bin/bash
# llcscore.sh <m.ll> [llc args]: release llc like rx.py, then asmscore-style metric + error order
OUT=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a71-cto-chainscan2
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin
f=$1; shift; b=${f%.ll}
$SDK/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections $f -filetype=asm -o $b.s "$@" || exit 1
python3 $OUT/tools/asmscore.py $b.s | tr -d '\n'; echo -n " | "
python3 - $b.o <<'PY'
import sys,re,struct
sys.path.insert(0,'/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a71-cto-chainscan2/tools')
src=open('/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a71-cto-chainscan2/tools/rx.py').read(); g={}; exec(src[:src.index("OUT=os.environ")],g)
b=g['elf_fn'](sys.argv[1],g['KEEP']); i=0; out=[]; last=None
while i<len(b):
    op=b[i]
    if op==0x62:
        imm=struct.unpack_from('<i',b,i+4)[0]
        if 250<imm<800: last=imm
    if op==0x85 and last: out.append(last); last=None
    i+=16 if op==0x18 else 8
print(' '.join(map(str,out)))
PY
