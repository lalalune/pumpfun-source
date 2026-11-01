#!/bin/bash
# Links with link/ordered.ld in place of the toolchain's default script. All other arguments pass through.
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  if [[ "${args[i]}" == "-T" || "${args[i]}" == "--script" ]]; then args[i+1]=/source/link/ordered.ld
  elif [[ "${args[i]}" == --script=* ]]; then args[i]=--script=/source/link/ordered.ld; fi
done
exec /sdk/rust/lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld "${args[@]}"
