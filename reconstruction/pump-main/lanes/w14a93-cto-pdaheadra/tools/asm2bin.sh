#!/bin/bash
# asm2bin.sh x.s -> x.bin (execute fn bytes)
SDK=~/.cache/solana/v1.44/platform-tools/llvm/bin; O=/Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w14a93-cto-pdaheadra
$SDK/clang -cc1as -triple sbf -target-feature +store-imm -target-feature +jmp-ext -filetype obj $1 -o ${1%.s}.o && python3 -c "
import sys;src=open('$O/tools/rx.py').read();g={'__name__':'x'};exec(src.split('OUT=os.environ')[0],g);open('${1%.s}.bin','wb').write(g['elf_fn']('${1%.s}.o',g['KEEP']))"
