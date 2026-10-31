#!/bin/bash
O=~/.cache/pumpfun-reconstruction/lanes/w14a142-cto-holderflagtm
exec $O/bin/llcd -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$1" -start-before=${STOP:-branch-folder} -filetype=obj -o "$2" "${@:3}"
