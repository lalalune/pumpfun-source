#!/bin/bash
# private llc (w15a24 RAPRIO + w15a32 SSC_WSET + w16a20 SSC_SEGB hooks; Release+Asserts) with fastbuild's llc flags
exec $HOME/.cache/pumpfun-reconstruction/lanes/w16a20-cto-s3flagcolour/llvmb/bin/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$@"
