#!/bin/bash
# relink.sh <main.o> <out.so>
C=~/.cache/pumpfun-reconstruction/lanes/w8-profile-flags/cap
LLD=~/.cache/pumpfun-reconstruction/toolchains/hybrid144/rust/lib/rustlib/aarch64-apple-darwin/bin/rust-lld
python3 - "$1" "$2" "$LLD" <<'PY'
import json,sys,subprocess
a=json.load(open('$HOME/.cache/pumpfun-reconstruction/lanes/w8-profile-flags/cap/link.json'))
a=[sys.argv[3]]+[x.replace('@MAIN@',sys.argv[1]).replace('@OUT@',sys.argv[2]) for x in a[1:]]
r=subprocess.run(a,capture_output=True,text=True); sys.stderr.write(r.stderr); sys.exit(r.returncode)
PY
