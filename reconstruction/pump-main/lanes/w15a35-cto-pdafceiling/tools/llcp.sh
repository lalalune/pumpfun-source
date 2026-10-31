#!/bin/bash
exec /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w15a35-cto-pdafceiling/llvmb/bin/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$@"
