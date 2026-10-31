#!/bin/bash
# sb.sh <in.ll> <out.mir> : stop before branch-folder ; rt.sh <in.mir> <out.o> [args]: resume
O=~/.cache/pumpfun-reconstruction/lanes/w14a142-cto-holderflagtm
exec $O/bin/llcd -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$1" -stop-before=${STOP:-branch-folder} -o "$2" "${@:3}"
