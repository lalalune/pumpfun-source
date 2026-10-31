#!/bin/bash
# l.sh <m.ll> <out.o> [extra llc args] : debug llc
exec ~/.cache/pumpfun-reconstruction/lanes/w14a142-cto-holderflagtm/bin/llcd -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$1" -filetype=obj -o "$2" "${@:3}"
