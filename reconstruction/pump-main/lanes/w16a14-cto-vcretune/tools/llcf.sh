#!/bin/bash
# patched (w15a24 RAPRIO) llc; honours RAPRIO_FORCE/RAPRIO_STICKY from the environment. Experiment only.
exec /Users/shawwalters/.cache/pumpfun-reconstruction/lanes/w16a04-cto-lanchorceil/llvmb/bin/llc -O3 -relocation-model=pic -mattr=+store-imm,+jmp-ext -function-sections "$@"
