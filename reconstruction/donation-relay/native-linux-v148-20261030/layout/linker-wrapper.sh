#!/bin/bash
set -e
printf '%s\n' "$@" > /output/link-args.txt
args=("$@")
for ((i=0; i<${#args[@]}; i++)); do
  if [[ "${args[i]}" == "-T" || "${args[i]}" == "--script" ]]; then
    cp "${args[i+1]}" /output/default.ld
    args[i+1]=/config/ordered.ld
  elif [[ "${args[i]}" == --script=* ]]; then
    cp "${args[i]#--script=}" /output/default.ld
    args[i]=--script=/config/ordered.ld
  fi
done
printf '%s\n' "${args[@]}" > /output/effective-args.txt
exec /sdk/rust/lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld "${args[@]}"
